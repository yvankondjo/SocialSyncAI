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
        1. Check if user has ai_settings with ai_control_enabled=True (master toggle)
        2. Check if ai_enabled_for_chats=True (chat-specific toggle)
        3. Check if is_active=True (legacy global toggle)
        4. Check if conversation exists
        5. Check if conversation has ai_mode='OFF' (conversation-level override)
        """
        try:
            # Get AI settings for user
            response = self.db.table('ai_settings').select('*').eq('user_id', user_id).limit(1).single().execute()
            rules = response.data or {}
            logger.info(f'AI settings for user {user_id}: {rules}')

            if not rules:
                return {
                    'should_reply': False,
                    'reason': 'No AI settings found',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            # Check master toggle (ai_control_enabled) - highest priority
            if not rules.get('ai_control_enabled', True):
                logger.info(f'AI globally disabled for user {user_id} (ai_control_enabled=False)')
                return {
                    'should_reply': False,
                    'reason': 'AI globally disabled (ai_control_enabled=False)',
                    'matched_rules': ['ai_control_enabled=False'],
                    'ai_settings': rules
                }

            # Check chat-specific toggle (ai_enabled_for_chats)
            if not rules.get('ai_enabled_for_chats', True):
                logger.info(f'AI disabled for chats for user {user_id} (ai_enabled_for_chats=False)')
                return {
                    'should_reply': False,
                    'reason': 'AI disabled for chats (ai_enabled_for_chats=False)',
                    'matched_rules': ['ai_enabled_for_chats=False'],
                    'ai_settings': rules
                }

            # Check legacy global toggle (is_active) for backwards compatibility
            if not rules.get('is_active', True):
                logger.info(f'AI inactive for user {user_id} (is_active=False)')
                return {
                    'should_reply': False,
                    'reason': 'AI inactive (is_active=False)',
                    'matched_rules': ['is_active=False'],
                    'ai_settings': rules
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

            # Check conversation-level override (ai_mode)
            if conversation_data.get('ai_mode') == 'OFF':
                logger.info(f'Conversation AI disabled for user {user_id}: {conversation_id}')
                return {
                    'should_reply': False,
                    'reason': 'Conversation AI disabled (ai_mode=OFF)',
                    'matched_rules': ['ai_mode=OFF'],
                    'ai_settings': {}
                }

            # All checks passed - AI should respond
            logger.info(f'AI enabled for conversation {conversation_id} (user {user_id})')
            return {
                'should_reply': True,
                'reason': 'AI enabled for chats',
                'matched_rules': ['ai_control_enabled=True', 'ai_enabled_for_chats=True', 'is_active=True'],
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
        1. Get AI settings for user
        2. Check ai_control_enabled=True (master toggle)
        3. Check ai_enabled_for_comments=True (comment-specific toggle)
        4. Check is_active=True (legacy global toggle)
        5. Get comment to verify it exists
        6. Return should_reply decision
        """
        try:
            # Get AI settings for user
            response = self.db.table('ai_settings').select('*').eq('user_id', user_id).limit(1).single().execute()
            rules = response.data or {}
            logger.info(f'[AUTOMATION] AI settings for user {user_id}: {rules}')

            if not rules:
                logger.info(f'[AUTOMATION] No AI settings found for user {user_id}')
                return {
                    'should_reply': False,
                    'reason': 'No AI settings found',
                    'matched_rules': [],
                    'ai_settings': {}
                }

            # Check master toggle (ai_control_enabled) - highest priority
            if not rules.get('ai_control_enabled', True):
                logger.info(f'[AUTOMATION] AI globally disabled for user {user_id} (ai_control_enabled=False)')
                return {
                    'should_reply': False,
                    'reason': 'AI globally disabled (ai_control_enabled=False)',
                    'matched_rules': ['ai_control_enabled=False'],
                    'ai_settings': rules
                }

            # Check comment-specific toggle (ai_enabled_for_comments)
            if not rules.get('ai_enabled_for_comments', True):
                logger.info(f'[AUTOMATION] AI disabled for comments for user {user_id} (ai_enabled_for_comments=False)')
                return {
                    'should_reply': False,
                    'reason': 'AI disabled for comments (ai_enabled_for_comments=False)',
                    'matched_rules': ['ai_enabled_for_comments=False'],
                    'ai_settings': rules
                }

            # Check legacy global toggle (is_active) for backwards compatibility
            if not rules.get('is_active', True):
                logger.info(f'[AUTOMATION] AI inactive for user {user_id} (is_active=False)')
                return {
                    'should_reply': False,
                    'reason': 'AI inactive (is_active=False)',
                    'matched_rules': ['is_active=False'],
                    'ai_settings': rules
                }

            # Verify comment exists
            result = self.db.table("comments") \
                .select("id, text") \
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

            # All checks passed - AI should respond
            logger.info(f'[AUTOMATION] AI enabled for comments (user_id={user_id}, comment_id={comment_id})')
            return {
                'should_reply': True,
                'reason': 'AI enabled for comments',
                'matched_rules': ['ai_control_enabled=True', 'ai_enabled_for_comments=True', 'is_active=True'],
                'ai_settings': rules
            }

        except Exception as e:
            # Fail-open strategy: if query fails, allow processing
            # (don't block comment processing on config errors)
            logger.warning(
                f"[AUTOMATION] Failed to check AI settings for comment {comment_id}: {e}. "
                f"Continuing with AI processing as fallback (fail-open)."
            )
            return {
                'should_reply': True,
                'reason': 'Error checking AI settings, defaulting to enabled (fail-open)',
                'matched_rules': [],
                'ai_settings': {}
            }
