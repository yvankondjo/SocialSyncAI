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

        NEW LOGIC: RESPOND TO ALL COMMENTS BY DEFAULT
        - Only skip self-comments (owner commenting on their own posts)
        - User can configure additional exclusion rules in AI settings

        Args:
            comment: The comment to evaluate
            post: The post this comment is on
            all_comments: All comments on this post (for thread reconstruction)

        Returns:
            Tuple of (should_respond: bool, reason: str)

        Reasons:
            - "ignore" - Self-comment (owner's own comment)
            - "respond" - All other comments (default behavior)
        """
        comment_text = comment.get("text", "")
        author_name = comment.get("author_name", "")

        # Skip if comment is from the owner themselves and not a reply to another user
        if author_name.lower().strip('@') == self.owner_username and not self._check_reply_to_others(comment, all_comments) and not self._check_mentions(comment_text):
            logger.info(
                f"[TRIAGE] Self-comment from owner @{author_name}, ignoring"
            )
            return False, "ignore"

        # Comment is not from the owner themselves and is not a reply to another user and not a mention to another user
        logger.info(
            f"[TRIAGE] Comment from @{author_name} will be processed by AI"
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

        mentions_lower = [m.lower() for m in mentions]

        if self.owner_username in mentions_lower:
            logger.debug(f"[TRIAGE] Owner mentioned in comment")
            return True, ""

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
            return True, ""

        parent = next(
            (c for c in all_comments if c.get("platform_comment_id") == parent_id),
            None
        )

        if not parent:
            logger.warning(
                f"[TRIAGE] Parent comment {parent_id} not found, "
                f"assuming safe to respond"
            )
            return True, ""

        parent_author = parent.get("author_name", "").lower().strip('@')


        if parent_author == self.owner_username:
            logger.debug(
                f"[TRIAGE] Comment is reply to owner's comment"
            )
            return True, ""

        logger.debug(
            f"[TRIAGE] Comment is reply to @{parent_author}'s comment"
        )
        return False, "user_conversation"



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
