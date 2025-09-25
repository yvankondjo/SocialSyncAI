from typing import List, Dict, Any, Optional
from app.db.session import get_db
import logging
import re

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self):
        self.db = get_db()

    async def should_auto_reply(self, user_id: str) -> Dict[str, Any]:
        """
        Vérifie si l'IA doit répondre automatiquement à ce message
        
        Returns:
        {
            "should_reply": bool,
            "reason": str,  # Raison du refus si should_reply = False
            "matched_rules": List[str],  # Règles qui ont matché
            "ai_settings": Dict[str, Any]  # Paramètres de l'IA
        }
        """
        try:
            conv_check = await self._check_conversation_automation(user_id)
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

    def _check_conversation_automation(self, user_id: str) -> Dict[str, Any]:
        """Vérifie les règles de conversation"""
        try:
            response = self.db.table('ai_settings').select('*').eq('user_id', user_id).limit(1).single().execute()
            rules = response.data or []
            
            if not rules:
                return {
                    'should_reply': False,
                    'reason': 'No conversation rules matched',
                    'matched_rules': [],
                    'ai_settings': {}
                }
                    
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
                'reason': f'Erreur: {str(e)}',
                'matched_rules': [],
                'ai_settings': {}
            }