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

logger = logging.getLogger(__name__)


class AIDecisionService:
    """Service pour évaluer si l'IA doit répondre à un message"""

    def __init__(self, user_id: str, db: Client):
        self.user_id = user_id
        self.db = db
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.moderation_enabled = os.getenv("OPENAI_MODERATION_ENABLED", "true").lower() == "true"

    def check_message(
        self,
        message_text: str,
        context_type: str = "chat"
    ) -> Tuple[AIDecision, float, str, str]:
        """
        Évalue si l'IA doit répondre au message

        Flow de décision (ordre de priorité):
        1. Scope check (chats vs comments) → IGNORE si désactivé
        2. AI Control OFF? → IGNORE
        3. OpenAI Moderation check → Si flagged: ESCALATE ou IGNORE selon severity
        4. Custom user rules (instructions + exemples) → Apply
        5. Fallback: RESPOND

        Args:
            message_text: Le texte du message à analyser
            context_type: Type de contexte - "chat" (DMs) ou "comment" (posts publics)

        Returns:
            Tuple (decision, confidence, reason, matched_rule)
            - decision: AIDecision enum (RESPOND, IGNORE, ESCALATE)
            - confidence: float entre 0.0 et 1.0
            - reason: str explication lisible par humain
            - matched_rule: str identifiant de la règle matchée
        """
        # 1. Récupérer les règles de l'utilisateur
        rules = self._get_user_rules()

        # 2. Vérifier scope spécifique (NOUVEAU - Granular control)
        if context_type == "chat":
            if rules and not rules.get("ai_enabled_for_chats", True):
                return (
                    AIDecision.IGNORE,
                    1.0,
                    "AI désactivée pour les messages privés (chats)",
                    "chats_disabled"
                )
        elif context_type == "comment":
            if rules and not rules.get("ai_enabled_for_comments", True):
                return (
                    AIDecision.IGNORE,
                    1.0,
                    "AI désactivée pour les commentaires publics",
                    "comments_disabled"
                )

        # 3. Vérifier AI Control global activé
        # Si pas de règles (None), on considère que AI Control est activé par défaut
        if rules is not None:
            if not rules.get("ai_control_enabled", True):
                return (
                    AIDecision.IGNORE,
                    1.0,
                    "AI Control désactivé par l'utilisateur",
                    "ai_control_disabled"
                )

        # 3. OpenAI Moderation check (NOUVEAU - Guardrail principal)
        if self.moderation_enabled:
            moderation_result = self._check_openai_moderation(message_text)

            if moderation_result["flagged"]:
                # Déterminer action selon severity
                severity = self._assess_severity(moderation_result.get("categories", {}))

                if severity == "HIGH":
                    return (
                        AIDecision.ESCALATE,
                        0.95,
                        f"OpenAI Moderation (HIGH): {moderation_result['reason']}",
                        "openai_moderation_high"
                    )
                else:
                    return (
                        AIDecision.IGNORE,
                        0.90,
                        f"OpenAI Moderation (LOW): {moderation_result['reason']}",
                        "openai_moderation_low"
                    )

        # 4. Vérifier similarité avec exemples à ignorer (custom rules)
        ignore_examples = rules.get("ignore_examples", []) if rules else []
        if ignore_examples:
            for example in ignore_examples:
                similarity = self._text_similarity(
                    message_text.lower(),
                    example.lower()
                )

                # Si similarité > 70%, on ignore
                if similarity > 0.7:
                    reason = f"Message similaire ({int(similarity*100)}%) à exemple: '{example[:50]}...'"
                    return (
                        AIDecision.IGNORE,
                        similarity,
                        reason,
                        f"ignore_example:{example[:30]}"
                    )

        # 5. Vérifier mots-clés d'escalation (custom keywords)
        escalation_keywords = [
            "remboursement", "urgent", "avocat", "poursuivre", "arnaque",
            "refund", "lawyer", "sue", "scam", "fraud"
        ]
        message_lower = message_text.lower()

        for keyword in escalation_keywords:
            if keyword in message_lower:
                reason = f"Mot-clé d'escalation détecté: '{keyword}'"
                return (
                    AIDecision.ESCALATE,
                    0.9,
                    reason,
                    f"escalation_keyword:{keyword}"
                )

        # 6. Par défaut: répondre
        return (
            AIDecision.RESPOND,
            0.8,
            "Aucune règle bloquante détectée",
            "default_respond"
        )

    def _check_openai_moderation(self, text: str) -> Dict[str, Any]:
        """
        Call OpenAI Moderation API

        Args:
            text: Texte à modérer

        Returns:
            Dict avec {
                "flagged": bool,
                "categories": dict (optionnel),
                "category_scores": dict (optionnel),
                "reason": str (optionnel),
                "error": str (optionnel)
            }
        """
        try:
            response = self.openai_client.moderations.create(
                model="omni-moderation-latest",  # Dernier modèle 2025
                input=text
            )

            result = response.results[0]

            if result.flagged:
                # Build reason from flagged categories
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
            # Fallback: ne pas bloquer si l'API est down (fail open)
            return {"flagged": False, "error": str(e)}

    def _assess_severity(self, categories: Dict[str, bool]) -> str:
        """
        Assess severity from flagged categories

        HIGH severity = Nécessite intervention humaine immédiate (ESCALATE)
        LOW severity = Bloquer seulement (IGNORE)

        Args:
            categories: Dict de catégories flaggées par OpenAI Moderation

        Returns:
            "HIGH" ou "LOW"
        """
        HIGH_SEVERITY_CATEGORIES = [
            "violence",
            "violence/graphic",
            "self-harm",
            "self-harm/intent",
            "self-harm/instructions",
            "harassment/threatening"
        ]

        for cat, val in categories.items():
            if val and any(hs in cat for hs in HIGH_SEVERITY_CATEGORIES):
                logger.info(f"[MODERATION] HIGH severity detected: {cat}")
                return "HIGH"

        logger.info(f"[MODERATION] LOW severity detected")
        return "LOW"

    def _get_user_rules(self) -> Optional[Dict[str, Any]]:
        """Récupère les règles AI de l'utilisateur depuis DB"""
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
        Calcule la similarité entre deux textes (0.0 à 1.0)
        Utilise SequenceMatcher de difflib pour une comparaison simple
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
        Log une décision IA en DB pour traçabilité

        Args:
            message_id: ID du message (optionnel)
            message_text: Texte du message analysé
            decision: Décision prise (RESPOND, IGNORE, ESCALATE)
            confidence: Score de confiance 0.0-1.0
            reason: Raison de la décision
            matched_rule: Règle qui a été matchée

        Returns:
            Dict avec l'ID de la décision créée (ou None si erreur)
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

            # Retourner l'ID de la décision créée
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error logging AI decision: {e}")
            return None
