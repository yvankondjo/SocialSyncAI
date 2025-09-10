from typing import List, Dict, Any, Optional
from supabase import Client
import logging
import re

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def should_auto_reply(
        self, 
        conversation_id: str, 
        message_content: str,
        user_id: str
    ) -> Dict[str, Any]:
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
            # 1. Vérifier si l'automation est désactivée pour cette conversation
            conv_check = await self._check_conversation_automation(conversation_id)
            if not conv_check["enabled"]:
                return {
                    "should_reply": False,
                    "reason": "Automation désactivée pour cette conversation",
                    "matched_rules": []
                }

            # 2. Vérifier les règles de mots-clés
            keyword_check = await self._check_keyword_rules(
                conversation_id, message_content, user_id
            )
            if not keyword_check["should_reply"]:
                return keyword_check

            return {
                "should_reply": True,
                "reason": "Toutes les conditions sont remplies",
                "matched_rules": keyword_check["matched_rules"]
            }

        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'automation: {e}")
            # En cas d'erreur, on désactive l'auto-réponse par sécurité
            return {
                "should_reply": False,
                "reason": f"Erreur système: {str(e)}",
                "matched_rules": []
            }

    async def _check_conversation_automation(self, conversation_id: str) -> Dict[str, Any]:
        """Vérifie si l'automation est activée pour cette conversation"""
        try:
            response = self.supabase.table('conversations').select(
                'automation_disabled'
            ).eq('id', conversation_id).single().execute()
            
            if not response.data:
                return {"enabled": False, "reason": "Conversation non trouvée"}
            
            automation_disabled = response.data.get('automation_disabled', False)
            return {
                "enabled": not automation_disabled,
                "reason": "Automation désactivée" if automation_disabled else "OK"
            }
            
        except Exception as e:
            logger.error(f"Erreur vérification conversation automation: {e}")
            return {"enabled": False, "reason": f"Erreur: {str(e)}"}

    async def _check_keyword_rules(
        self, 
        conversation_id: str, 
        message_content: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Vérifie les règles de mots-clés"""
        try:
            # Récupérer toutes les règles actives pour cet utilisateur
            response = self.supabase.table('automation_keyword_rules').select(
                '*'
            ).eq('user_id', user_id).eq('is_enabled', True).execute()  # Nécessaire pour logique métier (règles utilisateur)
            
            if not response.data:
                # Pas de règles = répondre à tout (comportement par défaut)
                return {
                    "should_reply": True,
                    "reason": "Aucune règle définie, réponse autorisée",
                    "matched_rules": []
                }
            
            rules = response.data
            matched_rules = []
            
            # Récupérer les infos de la conversation pour le scope
            conv_response = self.supabase.table('conversations').select(
                'social_account_id'
            ).eq('id', conversation_id).single().execute()
            
            if not conv_response.data:
                return {
                    "should_reply": False,
                    "reason": "Conversation non trouvée",
                    "matched_rules": []
                }
            
            social_account_id = conv_response.data['social_account_id']
            
            # Vérifier chaque règle
            for rule in rules:
                scope_type = rule['scope_type']
                scope_id = rule['scope_id']
                
                # Vérifier si cette règle s'applique à ce contexte
                if scope_type == 'user':
                    # Règle globale pour l'utilisateur
                    applies = True
                elif scope_type == 'account':
                    # Règle pour un compte social spécifique
                    applies = (scope_id == social_account_id)
                elif scope_type == 'conversation':
                    # Règle pour cette conversation spécifique
                    applies = (scope_id == conversation_id)
                else:
                    applies = False
                
                if not applies:
                    continue
                
                # Vérifier si le message matche les mots-clés
                if self._message_matches_keywords(
                    message_content, 
                    rule['keywords'], 
                    rule['match_type']
                ):
                    matched_rules.append(f"{rule['description'] or 'Règle sans nom'} (ID: {rule['id']})")
            
            # Si au moins une règle matche, on peut répondre
            if matched_rules:
                return {
                    "should_reply": True,
                    "reason": f"Message matche {len(matched_rules)} règle(s)",
                    "matched_rules": matched_rules
                }
            else:
                return {
                    "should_reply": False,
                    "reason": "Aucune règle de mots-clés ne correspond",
                    "matched_rules": []
                }
                
        except Exception as e:
            logger.error(f"Erreur vérification règles mots-clés: {e}")
            return {
                "should_reply": False,
                "reason": f"Erreur: {str(e)}",
                "matched_rules": []
            }

    def _message_matches_keywords(
        self, 
        message: str, 
        keywords: List[str], 
        match_type: str
    ) -> bool:
        """Vérifie si un message correspond aux mots-clés"""
        if not keywords:
            return True
        
        message_lower = message.lower()
        
        if match_type == 'contains':
            # Vérification simple: au moins un mot-clé présent
            return any(keyword.lower() in message_lower for keyword in keywords)
        
        elif match_type == 'regex':
            # Vérification par regex (plus avancée)
            try:
                for pattern in keywords:
                    if re.search(pattern, message, re.IGNORECASE):
                        return True
                return False
            except re.error as e:
                logger.warning(f"Regex invalide dans les mots-clés: {e}")
                return False
        
        return False

    async def toggle_conversation_automation(
        self, 
        conversation_id: str, 
        user_id: str, 
        enabled: bool
    ) -> bool:
        """Active/désactive l'automation pour une conversation"""
        try:
            # Vérifier que l'utilisateur a accès à cette conversation
            access_check = self.supabase.table('conversations').select(
                'id, social_accounts: social_account_id (user_id)'
            ).eq('id', conversation_id).execute()
            
            if not access_check.data:
                return False
            
            social_account = access_check.data[0].get('social_accounts')
            if not social_account or social_account.get('user_id') != user_id:
                return False
            
            # Mettre à jour le flag automation_disabled
            self.supabase.table('conversations').update({
                'automation_disabled': not enabled
            }).eq('id', conversation_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur toggle automation conversation: {e}")
            return False

    async def create_keyword_rule(
        self,
        user_id: str,
        scope_type: str,
        scope_id: Optional[str],
        keywords: List[str],
        description: Optional[str] = None,
        match_type: str = 'contains'
    ) -> Optional[str]:
        """Crée une nouvelle règle de mots-clés"""
        try:
            rule_data = {
                'user_id': user_id,
                'scope_type': scope_type,
                'scope_id': scope_id,
                'keywords': keywords,
                'description': description,
                'match_type': match_type,
                'is_enabled': True
            }
            
            response = self.supabase.table('automation_keyword_rules').insert(
                rule_data
            ).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Erreur création règle mots-clés: {e}")
            return None

    async def get_user_keyword_rules(self, user_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les règles de mots-clés d'un utilisateur"""
        try:
            response = self.supabase.table('automation_keyword_rules').select(
                '*'
            ).eq('user_id', user_id).order('created_at', desc=False).execute()  # Nécessaire pour logique métier (règles utilisateur)
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Erreur récupération règles: {e}")
            return []
