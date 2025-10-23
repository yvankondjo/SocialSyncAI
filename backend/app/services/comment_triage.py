"""
Comment Triage Service
Determines if AI should respond to a comment based on conversation context

Rules:
1. Ignore @mentions of other users (user-to-user conversations)
2. Ignore replies to other users' comments
3. Only respond to direct questions/requests to the account owner

This prevents AI from spamming user-to-user conversations
"""
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from app.services.rag_agent import RAGAgent

logger = logging.getLogger(__name__)


class CommentTriageService:
    """Service for determining if AI should respond to a comment"""

    def __init__(self, user_id: str, owner_username: str):
        """
        Initialize triage service

        Args:
            user_id: UUID of the account owner
            owner_username: Instagram username of the account owner (e.g., "your_brand")
        """
        self.user_id = user_id
        self.owner_username = owner_username.lower().strip('@')
        self.rag_agent = RAGAgent(user_id=user_id)

    def should_ai_respond(
        self,
        comment: Dict[str, Any],
        post: Dict[str, Any],
        all_comments: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Determine if AI should respond to this comment

        Args:
            comment: The comment to evaluate
            post: The post this comment is on
            all_comments: All comments on this post (for thread reconstruction)

        Returns:
            Tuple of (should_respond: bool, reason: str)

        Reasons:
            - "user_conversation" - Comment is between users, not directed at owner
            - "ignore" - Generic comment, not a question or request
            - "respond" - Direct question/request to account owner
        """
        comment_text = comment.get("text", "")
        author_name = comment.get("author_name", "")

        # Skip if comment is from the owner themselves
        if author_name.lower().strip('@') == self.owner_username:
            logger.debug(
                f"[TRIAGE] Comment from owner themselves, skipping"
            )
            return False, "ignore"

      
        should_respond, reason = self._check_mentions(comment_text)
        if not should_respond:
            logger.info(
                f"[TRIAGE] Comment mentions other users: {reason}"
            )
            return False, reason

    
        should_respond, reason = self._check_reply_to_others(comment, all_comments)
        if not should_respond:
            logger.info(
                f"[TRIAGE] Comment is reply to another user: {reason}"
            )
            return False, reason

       
        is_question = self._is_direct_question(comment_text)
        if not is_question:
            logger.info(
                f"[TRIAGE] Comment is not a direct question/request"
            )
            return False, "ignore"

       
        logger.info(
            f"[TRIAGE] Comment should be answered by AI"
        )
        return True, "respond"

    def _check_mentions(self, comment_text: str) -> Tuple[bool, str]:
        """
        Rule 1: Check if comment mentions other users (not the owner)

        Examples:
            "@user1 great point!" → SKIP (user-to-user)
            "@your_brand what's the price?" → RESPOND (directed at owner)
            "Nice! @user1" → SKIP (mentioning another user)
            "Love this!" → PASS (no mentions, continue to other rules)

        Args:
            comment_text: The comment text

        Returns:
            (should_respond, reason)
        """

        mentions = re.findall(r'@(\w+)', comment_text, re.IGNORECASE)

        if not mentions:
            return True, ""

        # Normalize mentions
        mentions_lower = [m.lower() for m in mentions]

        # Check if owner is mentioned
        if self.owner_username in mentions_lower:
            # Owner is mentioned - this is directed at us
            logger.debug(f"[TRIAGE] Owner mentioned in comment")
            return True, ""

        # Other users are mentioned but not the owner
        logger.debug(
            f"[TRIAGE] Comment mentions other users but not owner: "
            f"@{', @'.join(mentions)}"
        )
        return False, "user_conversation"

    def _check_reply_to_others(
        self,
        comment: Dict[str, Any],
        all_comments: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Rule 2: Check if comment is a reply to another user's comment

        Thread structure:
            Owner: "Check out our new product!"
            User1: "Looks great!"
            User2: "@user1 I agree!" ← SKIP (reply to User1, not Owner)

        Args:
            comment: The comment to check
            all_comments: All comments on this post

        Returns:
            (should_respond, reason)
        """
        parent_id = comment.get("parent_id")

        if not parent_id:
            # Top-level comment - not a reply
            return True, ""

        # Find parent comment
        parent = next(
            (c for c in all_comments if c.get("platform_comment_id") == parent_id),
            None
        )

        if not parent:
            # Parent not found - assume it's okay to respond
            logger.warning(
                f"[TRIAGE] Parent comment {parent_id} not found, "
                f"assuming safe to respond"
            )
            return True, ""

        parent_author = parent.get("author_name", "").lower().strip('@')

        # Check if parent was written by the owner
        if parent_author == self.owner_username:
            # Replying to owner - AI should respond
            logger.debug(
                f"[TRIAGE] Comment is reply to owner's comment"
            )
            return True, ""

        # Replying to another user - skip
        logger.debug(
            f"[TRIAGE] Comment is reply to @{parent_author}'s comment"
        )
        return False, "user_conversation"

    def _is_direct_question(self, comment_text: str) -> bool:
        """
        Rule 3: Detect if comment is a direct question or request

        Uses two methods:
        1. Keyword-based detection (fast, simple)
        2. LLM-based classification (accurate, slower)

        Examples:
            "What's the price?" → YES
            "Is this available?" → YES
            "Can you ship to France?" → YES
            "Nice!" → NO
            "Love this color" → NO
            "@user1 what do you think?" → NO (directed at another user)

        Args:
            comment_text: The comment text

        Returns:
            bool - True if it's a direct question/request
        """
        # Method 1: Quick keyword check
        question_indicators = [
            '?',                    # Question mark
            'how much',
            'what is', 'what are', 'what\'s',
            'when is', 'when can', 'when does', 'when will',
            'where is', 'where can', 'where do',
            'why is', 'why do',
            'who is', 'who makes',
            'can you', 'could you', 'would you',
            'do you', 'does this', 'do these',
            'is this', 'is it', 'are these', 'are they',
            'price', 'cost', 'how much',
            'available', 'in stock',
            'shipping', 'delivery',
            'size', 'sizes',
            'color', 'colors', 'colour',
            'link', 'where to buy',
            'dm me', 'message me', 'contact',
        ]

        comment_lower = comment_text.lower()

        # Check if any indicator is present
        has_indicator = any(
            indicator in comment_lower
            for indicator in question_indicators
        )

        if has_indicator:
            logger.debug(
                f"[TRIAGE] Comment has question indicator: "
                f"'{comment_text[:50]}...'"
            )
            return True

        # Method 2: LLM-based classification (for edge cases)
        # Only use if comment is long enough to be meaningful
        if len(comment_text.strip()) < 10:
            # Too short to be a meaningful question
            return False

        try:
            is_question = self._llm_classify_question(comment_text)
            logger.debug(
                f"[TRIAGE] LLM classification result: {is_question}"
            )
            return is_question

        except Exception as e:
            logger.error(f"[TRIAGE] Error in LLM classification: {e}")
            # Default to False if LLM fails
            return False

    def _llm_classify_question(self, comment_text: str) -> bool:
        """
        Use LLM to classify if comment is a direct question/request

        Prompt engineering to get yes/no answer from AI

        Args:
            comment_text: The comment to classify

        Returns:
            bool - True if LLM thinks it's a question/request
        """
        prompt = f"""
Analyze this Instagram comment and determine if it's a direct question or request to the account owner.

Comment: "{comment_text}"

Consider:
- Is this asking for information? (price, availability, details)
- Is this requesting action? (DM me, send link, contact)
- Is this a genuine inquiry vs just a reaction/compliment?

Answer with just "YES" or "NO".

Answer:"""

        try:
            # Use RAG agent for classification (fast, cached)
            response = self.rag_agent.generate_response(
                query=prompt,
                include_context=False  # Don't need RAG context for classification
            )

            answer = response.get("response", "").strip().upper()

            # Parse answer
            if "YES" in answer:
                return True
            elif "NO" in answer:
                return False
            else:
                # Ambiguous answer - default to False
                logger.warning(
                    f"[TRIAGE] LLM gave ambiguous answer: {answer}"
                )
                return False

        except Exception as e:
            logger.error(f"[TRIAGE] LLM classification failed: {e}")
            return False


def get_owner_username(db, social_account_id: str) -> str:
    """
    Helper function to get owner's Instagram username

    Args:
        db: Supabase client
        social_account_id: UUID of social_accounts

    Returns:
        Instagram username (str)
    """
    try:
        result = db.table("social_accounts") \
            .select("username") \
            .eq("id", social_account_id) \
            .single() \
            .execute()

        if result.data:
            return result.data.get("username", "")

        return ""

    except Exception as e:
        logger.error(f"[TRIAGE] Error getting owner username: {e}")
        return ""
