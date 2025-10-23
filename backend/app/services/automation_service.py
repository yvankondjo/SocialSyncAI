from typing import List, Dict, Any, Optional, Literal
from app.db.session import get_db
import logging
import re

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self):
        self.db = get_db()

    def should_auto_reply(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        comment_id: Optional[str] = None,
        context_type: Literal["chat", "comment"] = "chat"
    ) -> Dict[str, Any]:
        """
        Check if the AI should automatically reply to this message

        Supports both:
        - Conversations/DMs (context_type="chat", requires conversation_id)
        - Comments (context_type="comment", requires comment_id)

        Args:
            user_id: User UUID
            conversation_id: Conversation UUID (for DMs/chats)
            comment_id: Comment UUID (for public comments)
            context_type: "chat" for DMs, "comment" for public comments

        Returns:
        {
            "should_reply": bool,
            "reason": str,  # Reason for the decision
            "matched_rules": List[str],  # Rules that matched
            "ai_settings": Dict[str, Any]  # AI settings (for chats only)
        }
        """
        try:
            if context_type == "chat":
                if not conversation_id:
                    return {
                        'should_reply': False,
                        'reason': 'conversation_id required for chat context',
                        'matched_rules': [],
                        'ai_settings': {}
                    }
                return self._check_conversation_automation(user_id, conversation_id)

            elif context_type == "comment":
                if not comment_id:
                    return {
                        'should_reply': False,
                        'reason': 'comment_id required for comment context',
                        'matched_rules': [],
                        'ai_settings': {}
                    }
                return self._check_comment_automation(user_id, comment_id)

            else:
                return {
                    'should_reply': False,
                    'reason': f'Invalid context_type: {context_type}. Must be "chat" or "comment"',
                    'matched_rules': [],
                    'ai_settings': {}
                }

        except Exception as e:
            logger.error(f'Error checking automation rules: {e}')
            return {
                'should_reply': False,
                'reason': f'Error checking automation: {str(e)}',
                'matched_rules': [],
                'ai_settings': {}
            }

    def _check_conversation_automation(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Check conversation automation rules (DMs/chats)

        Logic:
        1. Check if user has ai_settings (is_active=True)
        2. Check if conversation exists
        3. Check if conversation has ai_mode='OFF'
        """
        try:
            # Check if AI is active in general for the user
            response = self.db.table('ai_settings').select('*').eq('user_id', user_id).limit(1).single().execute()
            rules = response.data or {}
            logger.info(f'AI settings for user {user_id}: {rules}')

            if not rules:
                return {
                    'should_reply': False,
                    'reason': 'No conversation rules matched',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            # Check if the conversation exists and is active
            conversation = self.db.table('conversations').select('ai_mode').eq('id', conversation_id).limit(1).single().execute()
            conversation_data = conversation.data or {}

            if not conversation_data:
                logger.info(f'Conversation not found for user {user_id}: {conversation_id}')
                return {
                    'should_reply': False,
                    'reason': 'Conversation not found',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            # AI is disabled for the conversation
            if conversation_data.get('ai_mode') == 'OFF':
                logger.info(f'Conversation is not active for user {user_id}: {conversation_id}')
                return {
                    'should_reply': False,
                    'reason': 'Conversation is not active (ai_mode=OFF)',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            # Return the default rules
            logger.info(f'Conversation is active for user {user_id}: {conversation_id}')
            return {
                'should_reply': rules.get('is_active', True),
                'reason': 'Conversation rules matched' if rules.get('is_active', True) else 'Conversation rules not matched',
                'matched_rules': [rules.get('system_prompt', '')],
                'ai_settings': rules
            }

        except Exception as e:
            logger.error(f'Error checking conversation automation: {e}')
            return {
                'should_reply': False,
                'reason': f'Error: {str(e)}',
                'matched_rules': [],
                'ai_settings': {}
            }

    def _check_comment_automation(self, user_id: str, comment_id: str) -> Dict[str, Any]:
        """
        Check comment automation rules (public comments on posts)

        Logic:
        1. Get comment + post + social_account_id from DB
        2. Query monitoring_rules for ai_enabled_for_comments flag
        3. Try account-specific rules first, fallback to user-level rules
        4. Return should_reply decision
        """
        try:
            # Get comment with related post and social_account_id
            result = self.db.table("comments") \
                .select("""
                    *,
                    monitored_posts!inner(
                        id,
                        user_id,
                        platform,
                        social_accounts!inner(id)
                    )
                """) \
                .eq("id", comment_id) \
                .single() \
                .execute()

            if not result.data:
                logger.error(f'[AUTOMATION] Comment {comment_id} not found')
                return {
                    'should_reply': False,
                    'reason': 'Comment not found',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            comment = result.data
            post = comment.get("monitored_posts")

            if not post:
                logger.error(f'[AUTOMATION] Post not found for comment {comment_id}')
                return {
                    'should_reply': False,
                    'reason': 'Post not found for comment',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            social_account_id = post.get("social_accounts", {}).get("id") if "social_accounts" in post else None

            # Query monitoring_rules to check ai_enabled_for_comments flag
            # First, try account-specific rules
            rules_result = self.db.table("monitoring_rules") \
                .select("ai_enabled_for_comments") \
                .eq("user_id", user_id) \
                .eq("social_account_id", social_account_id) \
                .maybe_single() \
                .execute()

            # If no account-specific rules, fall back to user-level rules
            if not rules_result.data:
                rules_result = self.db.table("monitoring_rules") \
                    .select("ai_enabled_for_comments") \
                    .eq("user_id", user_id) \
                    .is_("social_account_id", "null") \
                    .maybe_single() \
                    .execute()

            # Check if AI is disabled for comments
            if rules_result.data:
                ai_enabled = rules_result.data.get("ai_enabled_for_comments", True)

                if not ai_enabled:
                    logger.info(
                        f"[AUTOMATION] AI disabled for comments (user_id={user_id}, "
                        f"account_id={social_account_id}). Skipping comment {comment_id}"
                    )
                    return {
                        'should_reply': False,
                        'reason': 'AI disabled for comments (monitoring_rules.ai_enabled_for_comments=False)',
                        'matched_rules': ['ai_enabled_for_comments=False'],
                        'ai_settings': {}
                    }

            # AI enabled for comments
            logger.info(f'[AUTOMATION] AI enabled for comments (user_id={user_id}, comment_id={comment_id})')
            return {
                'should_reply': True,
                'reason': 'AI enabled for comments',
                'matched_rules': ['ai_enabled_for_comments=True'],
                'ai_settings': {}
            }

        except Exception as e:
            # Fail-open strategy: if monitoring_rules query fails, allow processing
            # (don't block comment processing on config errors)
            logger.warning(
                f"[AUTOMATION] Failed to check ai_enabled_for_comments for comment {comment_id}: {e}. "
                f"Continuing with AI processing as fallback (fail-open)."
            )
            return {
                'should_reply': True,
                'reason': 'Error checking monitoring_rules, defaulting to enabled (fail-open)',
                'matched_rules': [],
                'ai_settings': {}
            }
