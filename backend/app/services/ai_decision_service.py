"""
AI Decision Service
Service pour évaluer si l'IA doit répondre à un message basé sur les règles utilisateur
et OpenAI Moderation API
"""
import os
import logging
from typing import Tuple, Optional, Dict, Any
from difflib import SequenceMatcher
from supabase import Client
from openai import OpenAI
from app.schemas.ai_rules import AIDecision
from app.db.session import get_db
logger = logging.getLogger(__name__)


class AIDecisionService:
    """Service pour évaluer si l'IA doit répondre à un message"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.moderation_enabled = os.getenv("OPENAI_MODERATION_ENABLED", "true").lower() == "true"
        self.db = get_db()

    def check_message(
        self,
        message_text: str,
        context_type: str = "chat"
    ) -> Tuple[AIDecision, float, str, str]:
        """
        Check if the AI should respond to a message based on user rules and OpenAI Moderation API

        Decision flow (priority order):
        1. Scope check (chats vs comments) → IGNORE if disabled
        2. AI Control OFF? → IGNORE
        3. OpenAI Moderation check → If flagged: ESCALATE or IGNORE
        4. Custom user rules (instructions + examples) → Apply
        5. Default: RESPOND

        Args:
            message_text: The text of the message to analyze
            context_type: Context type - "chat" (DMs) or "comment" (posts publics)

        Returns:
            Tuple (decision, confidence, reason, matched_rule)
            - decision: AIDecision enum (RESPOND, IGNORE, ESCALATE)
            - confidence: float between 0.0 and 1.0
            - reason: str readable explanation
            - matched_rule: str identifier of the matched rule
        """
        rules = self._get_user_rules()


        if context_type == "chat":
            if rules and not rules.get("ai_enabled_for_chats", True):
                return (
                    AIDecision.IGNORE,
                    1.0,
                    "AI disabled for private messages (chats)",
                    "chats_disabled"
                )
        elif context_type == "comment":
            if rules and not rules.get("ai_enabled_for_comments", True):
                return (
                    AIDecision.IGNORE,
                    1.0,
                    "AI disabled for comments",
                    "comments_disabled"
                )

        if rules is not None:
            if not rules.get("ai_control_enabled", True):
                return (
                    AIDecision.IGNORE,
                    1.0,
                    "AI Control disabled by user",
                    "ai_control_disabled"
                )

        if self.moderation_enabled:
            moderation_result = self._check_openai_moderation(message_text)

            if moderation_result["flagged"]:
                return (
                    AIDecision.IGNORE,
                    0.95,
                    f"OpenAI Moderation: {moderation_result['reason']}",
                    "openai_moderation"
                )

        flagged_keywords = rules.get("flagged_keywords", []) if rules else []
        flagged_phrases = rules.get("flagged_phrases", []) if rules else []
        message_lower = message_text.lower()

        for keyword in flagged_keywords:
            if keyword.lower() in message_lower:
                reason = f"Guardrail: Flagged keyword detected: '{keyword}'"
                return (
                    AIDecision.IGNORE,
                    0.95,
                    reason,
                    f"flagged_keyword:{keyword[:30]}"
                )

        for phrase in flagged_phrases:
            if phrase.lower() in message_lower:
                reason = f"Guardrail: Flagged phrase detected: '{phrase[:50]}...'"
                return (
                    AIDecision.IGNORE,
                    0.95,
                    reason,
                    f"flagged_phrase:{phrase[:30]}"
                )

        

        return (
            AIDecision.RESPOND,
            1.0,
            "No blocking rule detected",
            "default_respond"
        )

    def _check_openai_moderation(self, text: str) -> Dict[str, Any]:
        """
        Call OpenAI Moderation API

        Args:
            text: Text to moderate

        Returns:
            Dict avec {
                "flagged": bool,
                "categories": dict (optional),
                "category_scores": dict (optional),
                "reason": str (optional),
                "error": str (optional)
            }
        """
        try:
            response = self.openai_client.moderations.create(
                model="omni-moderation-latest",
                input=text
            )

            result = response.results[0]

            if result.flagged:
                categories_dict = result.categories.model_dump()
                flagged_cats = [cat for cat, val in categories_dict.items() if val]

                logger.info(f"[MODERATION] Content flagged for user {self.user_id}: {flagged_cats}")

                return {
                    "flagged": True,
                    "categories": categories_dict,
                    "category_scores": result.category_scores.model_dump(),
                    "reason": f"Violates: {', '.join(flagged_cats)}"
                }

            logger.debug(f"[MODERATION] Content passed moderation for user {self.user_id}")
            return {"flagged": False}

        except Exception as e:
            logger.error(f"[MODERATION] OpenAI Moderation API error: {e}")
            return {"flagged": False, "error": str(e)}

    def _get_user_rules(self) -> Optional[Dict[str, Any]]:
        """Retrieve AI rules for the user from DB"""
        try:
            result = self.db.table("ai_rules") \
                .select("*") \
                .eq("user_id", self.user_id) \
                .maybe_single() \
                .execute()

            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error fetching AI rules for user {self.user_id}: {e}")
            return None

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate the similarity between two texts (0.0 to 1.0)
        Uses SequenceMatcher from difflib for a simple comparison
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def log_decision(
        self,
        message_id: Optional[str],
        message_text: str,
        decision: AIDecision,
        confidence: float,
        reason: str,
        matched_rule: str
    ) -> Optional[Dict[str, Any]]:
        """
        Log an AI decision in DB for tracking

        Args:
            message_id: ID of the message (optional)
            message_text: Text of the analyzed message
            decision: Decision taken (RESPOND, IGNORE, ESCALATE)
            confidence: Confidence score 0.0-1.0
            reason: Reason for the decision
            matched_rule: Rule that was matched

        Returns:
            Dict with the ID of the created decision (or None if error)
        """
        try:
            data = {
                "user_id": self.user_id,
                "message_id": message_id,
                "decision": decision.value,
                "confidence": float(confidence),
                "reason": reason,
                "matched_rule": matched_rule,
                "message_text": message_text[:500],  # Limiter taille
                "snapshot_json": {"version": "1.0"}
            }

            result = self.db.table("ai_decisions").insert(data).execute()
            logger.info(
                f"[AI_DECISION] User {self.user_id}: {decision.value} - {reason}"
            )

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error logging AI decision: {e}")
            return None
