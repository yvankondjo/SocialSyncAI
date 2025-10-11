from typing import List, Dict, Any, Optional
from app.db.session import get_db
import logging
import re

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self):
        self.db = get_db()

    def should_auto_reply(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Check if the AI should automatically reply to this message
        
        Returns:
        {
            "should_reply": bool,
            "reason": str,  # Reason for the refusal if should_reply = False
            "matched_rules": List[str],  # Rules that have matched
            "ai_settings": Dict[str, Any]  # AI settings
        }
        """
        try:
            conv_check = self._check_conversation_automation(user_id, conversation_id)
            if not conv_check['should_reply']:
                return conv_check
                
            return {
                'should_reply': True,
                'reason': 'All automation rules passed',
                'matched_rules': conv_check['matched_rules'],
                'ai_settings': conv_check['ai_settings']
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
        """Check the conversation rules"""
        try:
            #check if AI is active in general fot the user
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
            #check if the conversation is active
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
                #AI is disabled for the conversation
            if conversation_data.get('ai_mode') == 'OFF':
                logger.info(f'Conversation is not active for user {user_id}: {conversation_id}')
                return {
                    'should_reply': False,
                    'reason': 'Conversation is not active',
                    'matched_rules': [],
                    'ai_settings': {}
                }
                #return the default rules
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