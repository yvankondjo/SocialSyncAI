from typing import List, Dict, Any, Optional
from supabase import Client
import logging
import re

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def should_auto_reply(self, user_id: str) -> Dict[str, Any]:
        """
        Vérifie si l'IA doit répondre automatiquement à ce message
        
        Returns:
        {
            "should_reply": bool,
            "reason": str,  # Raison du refus si should_reply = False
            "matched_rules": List[str]  # Règles qui ont matché
        }
        """
        try:
            conv_check = await self._check_conversation_automation(user_id)
            if not conv_check['should_reply']:
                return conv_check
                
            time_check = await self._check_time_automation(user_id)
            if not time_check['should_reply']:
                return time_check
                
            keyword_check = await self._check_keyword_automation(user_id)
            if not keyword_check['should_reply']:
                return keyword_check
                
            return {
                'should_reply': True,
                'reason': 'All automation rules passed',
                'matched_rules': conv_check['matched_rules'] + time_check['matched_rules'] + keyword_check['matched_rules']
            }
        except Exception as e:
            logger.error(f'Error checking automation rules: {e}')
            return {
                'should_reply': False,
                'reason': f'Error checking automation: {str(e)}',
                'matched_rules': []
            }

    async def _check_conversation_automation(self, user_id: str) -> Dict[str, Any]:
        """Vérifie les règles de conversation"""
        try:
            response = self.supabase.table('automation_rules').select('*').eq('user_id', user_id).eq('type', 'conversation').eq('is_active', True).execute()
            rules = response.data or []
            
            matched_rules = []
            for rule in rules:
                if rule.get('condition') == 'first_message':
                    # Vérifier si c'est le premier message de la conversation
                    # Cette logique devrait être implémentée selon votre structure de données
                    matched_rules.append(rule['name'])
                elif rule.get('condition') == 'no_reply_24h':
                    # Vérifier si aucun agent n'a répondu dans les 24h
                    # Cette logique devrait être implémentée selon votre structure de données
                    matched_rules.append(rule['name'])
                    
            return {
                'should_reply': len(matched_rules) > 0,
                'reason': 'No conversation rules matched' if not matched_rules else 'Conversation rules matched',
                'matched_rules': matched_rules
            }
        except Exception as e:
            logger.error(f'Error checking conversation automation: {e}')
            return {
                'should_reply': False,
                'reason': f'Erreur: {str(e)}',
                'matched_rules': []
            }

    async def _check_time_automation(self, user_id: str) -> Dict[str, Any]:
        """Vérifie les règles de temps"""
        try:
            response = self.supabase.table('automation_rules').select('*').eq('user_id', user_id).eq('type', 'time').eq('is_active', True).execute()
            rules = response.data or []
            
            matched_rules = []
            for rule in rules:
                # Logique de vérification des heures de travail
                # À implémenter selon vos besoins
                matched_rules.append(rule['name'])
                    
            return {
                'should_reply': len(matched_rules) > 0,
                'reason': 'No time rules matched' if not matched_rules else 'Time rules matched',
                'matched_rules': matched_rules
            }
        except Exception as e:
            logger.error(f'Error checking time automation: {e}')
            return {
                'should_reply': False,
                'reason': f'Erreur: {str(e)}',
                'matched_rules': []
            }

    async def _check_keyword_automation(self, user_id: str) -> Dict[str, Any]:
        """Vérifie les règles de mots-clés"""
        try:
            response = self.supabase.table('automation_rules').select('*').eq('user_id', user_id).eq('type', 'keyword').eq('is_active', True).execute()
            rules = response.data or []
            
            matched_rules = []
            for rule in rules:
                # Logique de vérification des mots-clés
                # À implémenter selon vos besoins
                matched_rules.append(rule['name'])
                    
            return {
                'should_reply': len(matched_rules) > 0,
                'reason': 'No keyword rules matched' if not matched_rules else 'Keyword rules matched',
                'matched_rules': matched_rules
            }
        except Exception as e:
            logger.error(f'Error checking keyword automation: {e}')
            return {
                'should_reply': False,
                'reason': f'Erreur: {str(e)}',
                'matched_rules': []
            }