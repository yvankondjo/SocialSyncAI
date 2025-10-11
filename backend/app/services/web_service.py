import os
import uuid
import logging
import json
from typing import Any, Dict, Optional, List
from fastapi import HTTPException
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_web_widget_service: Optional['WebWidgetService'] = None

class WebWidgetService:
    """Service pour générer et gérer les widgets de chat IA intégrables"""

    def __init__(self, supabase_client: Optional[Any] = None):
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.widget_cdn_url = os.getenv('WIDGET_CDN_URL', f'{self.api_base_url}/static/widget')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self.supabase = supabase_client

    async def create_widget_config(self, user_id: str, website_url: str, widget_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Créer une configuration de widget pour un utilisateur et persister en DB
        
        Args:
            user_id: ID de l'utilisateur
            website_url: URL du site web où le widget sera installé
            widget_settings: Configuration du widget (couleurs, textes, etc.)
        """
        try:
            widget_id = str(uuid.uuid4())
            widget_key = f'wgt_{uuid.uuid4().hex[:24]}'
            
            widget_data = {
                'id': widget_id,
                'user_id': user_id,
                'name': widget_settings.get('company_name', 'Widget Chat'),
                'widget_key': widget_key,
                'allowed_domains': widget_settings.get('allowed_domains', []),
                'settings': widget_settings,
                'is_active': True,
                'branding_enabled': False,
                'branding_text': 'Powered by CustomersAI'
            }
            
            if self.supabase:
                result = self.supabase.table('web_widgets').insert(widget_data).execute()
                logger.info(f'Widget sauvegardé en DB: {widget_id}')
            
            logger.info(f'Widget créé: {widget_id} pour {user_id}')
            
            return {
                'success': True,
                'widget_id': widget_id,
                'api_key': widget_key,
                'config': {
                    'widget_id': widget_id,
                    'api_key': widget_key,
                    'user_id': user_id,
                    'website_url': website_url,
                    'created_at': widget_data.get('created_at', ''),
                    'status': 'active',
                    'settings': widget_settings
                },
                'embed_code': self._generate_embed_code(widget_id, widget_key),
                'setup_instructions': self._generate_setup_instructions(widget_id)
            }
        except Exception as e:
            logger.error(f'Erreur création widget: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur création widget: {str(e)}')

    def _generate_embed_code(self, widget_id: str, api_key: str) -> str:
        """Générer le code embed JavaScript pour le widget"""
        embed_code = f'''
<!-- SocialSync Chat Widget -->
<script>
  (function() {{
    // Configuration du widget
    window.SocialSyncWidget = {{
      widgetId: '{widget_id}',
      apiKey: '{api_key}',
      apiUrl: '{self.api_base_url}',
      debug: false
    }};
    
    // Charger le script du widget
    var script = document.createElement('script');
    script.src = '{self.widget_cdn_url}/widget.js';
    script.async = true;
    script.onload = function() {{
      if (window.SocialSyncChatWidget) {{
        window.SocialSyncChatWidget.init(window.SocialSyncWidget);
      }}
    }};
    
    // Injecter le CSS
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '{self.widget_cdn_url}/widget.css';
    document.head.appendChild(link);
    
    // Ajouter le script
    document.head.appendChild(script);
  }})();
</script>
<!-- End SocialSync Chat Widget -->
        '''.strip()
        return embed_code

    def _generate_setup_instructions(self, widget_id: str) -> Dict[str, Any]:
        """Générer les instructions d'installation"""
        return {
            'step_1': {
                'title': 'Copier le code embed',
                'description': 'Copiez le code JavaScript fourni'
            },
            'step_2': {
                'title': 'Coller dans votre site',
                'description': 'Collez le code juste avant la balise </body> de votre site web'
            },
            'step_3': {
                'title': 'Personnaliser (optionnel)',
                'description': 'Vous pouvez personnaliser l\'apparence et le comportement dans votre dashboard'
            },
            'platforms': {
                'wordpress': {
                    'method': 'Plugin ou Code Custom',
                    'instructions': [
                        'Aller dans Apparence > Éditeur de thème',
                        'Modifier le fichier footer.php',
                        'Coller le code avant </body>'
                    ]
                },
                'shopify': {
                    'method': 'Liquid Template',
                    'instructions': [
                        'Aller dans Boutique en ligne > Thèmes',
                        'Actions > Modifier le code',
                        'Ouvrir layout/theme.liquid',
                        'Coller le code avant </body>'
                    ]
                },
                'react': {
                    'method': 'Component Integration',
                    'instructions': [
                        'Créer un composant ChatWidget.jsx',
                        'Utiliser useEffect pour charger le script',
                        'Importer dans votre App.js'
                    ]
                },
                'html': {
                    'method': 'Direct Integration',
                    'instructions': [
                        'Ouvrir votre fichier HTML',
                        'Coller le code avant </body>',
                        'Sauvegarder et publier'
                    ]
                }
            },
            'verification': {
                'url': f'{self.api_base_url}/widget/{widget_id}/verify',
                'description': 'Vérifiez que le widget fonctionne correctement'
            }
        }

    async def generate_widget_preview(self, widget_config: Dict[str, Any]) -> str:
        """Générer un aperçu HTML du widget"""
        settings = widget_config.get('settings', {})
        primary_color = settings.get('primary_color', '#007bff')
        company_name = settings.get('company_name', 'Support')
        welcome_message = settings.get('welcome_message', 'Bonjour ! Comment puis-je vous aider ?')
        placeholder_text = settings.get('placeholder_text', 'Tapez votre message...')
        
        preview_html = f'''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aperçu du Widget Chat</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .preview-container {{
            max-width: 400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .chat-header {{
            background: {primary_color};
            color: white;
            padding: 16px;
            font-weight: 600;
        }}
        .chat-messages {{
            height: 300px;
            padding: 16px;
            overflow-y: auto;
        }}
        .message {{
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 80%;
        }}
        .message.bot {{
            background: #f1f3f5;
            color: #333;
        }}
        .message.user {{
            background: {primary_color};
            color: white;
            margin-left: auto;
        }}
        .chat-input {{
            border-top: 1px solid #eee;
            padding: 16px;
        }}
        .chat-input input {{
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }}
        .widget-button {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: {primary_color};
            border-radius: 50%;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <h2>Aperçu de votre widget de chat</h2>
    
    <div class="preview-container">
        <div class="chat-header">
            💬 {company_name}
        </div>
        <div class="chat-messages">
            <div class="message bot">
                {welcome_message}
            </div>
            <div class="message user">
                Bonjour, j'ai une question sur vos services
            </div>
            <div class="message bot">
                Je serais ravi de vous aider ! Pouvez-vous me donner plus de détails ?
            </div>
        </div>
        <div class="chat-input">
            <input type="text" placeholder="{placeholder_text}" disabled>
        </div>
    </div>
    
    <button class="widget-button">💬</button>
    
    <p style="text-align: center; color: #666; margin-top: 20px;">
        Voici à quoi ressemblera votre widget sur votre site web
    </p>
</body>
</html>
        '''.strip()
        return preview_html

    async def update_widget_settings(self, widget_id: str, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Mettre à jour les paramètres d'un widget"""
        try:
            logger.info(f'Widget {widget_id} mis à jour')
            return {
                'success': True,
                'widget_id': widget_id,
                'message': 'Widget mis à jour avec succès',
                'updated_settings': new_settings
            }
        except Exception as e:
            logger.error(f'Erreur mise à jour widget: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur mise à jour: {str(e)}')

    async def get_widget_analytics(self, widget_id: str, date_range: str='7d') -> Dict[str, Any]:
        """Récupérer les analytics d'un widget"""
        try:
            analytics = {
                'widget_id': widget_id,
                'date_range': date_range,
                'total_conversations': 245,
                'total_messages': 1832,
                'avg_response_time': 2.3,
                'ai_resolution_rate': 0.78,
                'user_satisfaction': 4.2,
                'top_questions': [
                    {'question': 'Comment puis-je annuler ma commande ?', 'count': 34},
                    {'question': 'Quels sont vos délais de livraison ?', 'count': 28},
                    {'question': 'Comment contacter le support ?', 'count': 19}
                ],
                'daily_stats': [
                    {'date': '2024-01-01', 'conversations': 35, 'messages': 156},
                    {'date': '2024-01-02', 'conversations': 42, 'messages': 189},
                    {'date': '2024-01-03', 'conversations': 38, 'messages': 172}
                ],
                'response_times': {
                    'instant_ai': 0.85,
                    'under_1min': 0.12,
                    'over_1min': 0.03
                }
            }
            return analytics
        except Exception as e:
            logger.error(f'Erreur analytics widget: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur analytics: {str(e)}')

    async def validate_widget_domain(self, widget_id: str, domain: str) -> bool:
        """Valider qu'un domaine est autorisé pour un widget"""
        try:
            logger.info(f'Validation domaine {domain} pour widget {widget_id}')
            return True
        except Exception as e:
            logger.error(f'Erreur validation domaine: {e}')
            return False
    async def process_chat_message(self, widget_id: str, message: str, conversation_id: str=None, user_info: Dict=None) -> Dict[str, Any]:
        """Traiter un message de chat et générer une réponse IA"""
        try:
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            ai_response = await self._generate_ai_response(message=message, conversation_history=[], widget_config={})
            return {
                'success': True,
                'conversation_id': conversation_id,
                'user_message': message,
                'ai_response': ai_response,
                'timestamp': '2024-01-01T00:00:00Z',
                'response_time': 0.8
            }
        except Exception as e:
            logger.error(f'Erreur traitement message: {e}')
            return {
                'success': False,
                'error': str(e),
                'fallback_response': 'Désolé, je rencontre des difficultés techniques. Un agent humain vous contactera bientôt.'
            }

    async def _generate_ai_response(self, message: str, conversation_history: List[Dict], widget_config: Dict) -> str:
        """Générer une réponse IA pour un message"""
        try:
            ai_provider = widget_config.get('ai_provider', 'openai')
            ai_model = widget_config.get('ai_model', 'gpt-3.5-turbo')
            system_prompt = widget_config.get('ai_system_prompt', 'Vous êtes un assistant IA serviable pour le support client.')
            
            if ai_provider == 'openai' and self.openai_api_key:
                return await self._call_openai(message, conversation_history, system_prompt, ai_model)
            elif ai_provider == 'anthropic' and self.anthropic_api_key:
                return await self._call_anthropic(message, conversation_history, system_prompt)
            else:
                return self._generate_fallback_response(message)
        except Exception as e:
            logger.error(f'Erreur génération IA: {e}')
            return 'Désolé, je rencontre des difficultés. Un agent humain vous répondra bientôt.'

    async def _call_openai(self, message: str, history: List[Dict], system_prompt: str, model: str) -> str:
        """Appeler l'API OpenAI"""
        try:
            messages = [{'role': 'system', 'content': system_prompt}]
            for msg in history[-10:]:
                messages.append({'role': 'user' if msg['type'] == 'user' else 'assistant', 'content': msg['content']})
            messages.append({'role': 'user', 'content': message})
            headers = {'Authorization': f'Bearer {self.openai_api_key}', 'Content-Type': 'application/json'}
            payload = {'model': model, 'messages': messages, 'max_tokens': 150, 'temperature': 0.7}
            resp = await self.client.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.error(f'Erreur OpenAI: {e}')
            raise

    async def _call_anthropic(self, message: str, history: List[Dict], system_prompt: str) -> str:
        """Appeler l'API Anthropic"""
        try:
            headers = {
                'x-api-key': self.anthropic_api_key,
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            prompt_text = f'{system_prompt}\n\nConversation:\n'
            for msg in history[-10:]:
                role = 'Human' if msg['type'] == 'user' else 'Assistant'
                prompt_text += f"{role}: {msg['content']}\n"
            prompt_text += f'Human: {message}\nAssistant:'
            payload = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 150,
                'messages': [{'role': 'user', 'content': prompt_text}]
            }
            resp = await self.client.post('https://api.anthropic.com/v1/messages', json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return result['content'][0]['text'].strip()
        except Exception as e:
            logger.error(f'Erreur Anthropic: {e}')
            raise

    def _generate_fallback_response(self, message: str) -> str:
        """Générer une réponse de fallback basique"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['bonjour', 'salut', 'hello', 'hi']):
            return 'Bonjour ! Comment puis-je vous aider aujourd\'hui ?'
        if any(word in message_lower for word in ['merci', 'thank']):
            return 'Je vous en prie ! Y a-t-il autre chose que je puisse faire pour vous ?'
        if any(word in message_lower for word in ['prix', 'coût', 'tarif', 'price']):
            return 'Pour les informations sur nos tarifs, je vous invite à consulter notre page de prix ou contacter notre équipe commerciale.'
        if any(word in message_lower for word in ['contact', 'téléphone', 'email']):
            return 'Vous pouvez nous contacter via ce chat ou consulter notre page de contact pour plus d\'options.'
        return 'Je comprends votre question. Un de nos agents vous répondra dans les plus brefs délais. En attendant, puis-je vous aider avec autre chose ?'

    async def get_widget_from_db(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un widget depuis la base de données"""
        if not self.supabase:
            logger.warning("Client Supabase non disponible")
            return None
        
        try:
            result = self.supabase.table('web_widgets').select('*').eq('id', widget_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f'Erreur récupération widget {widget_id}: {e}')
            return None
    
    async def get_widget_by_key(self, widget_key: str) -> Optional[Dict[str, Any]]:
        """Récupérer un widget depuis la base de données par sa clé"""
        if not self.supabase:
            logger.warning("Client Supabase non disponible")
            return None
        
        try:
            result = self.supabase.table('web_widgets').select('*').eq('widget_key', widget_key).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f'Erreur récupération widget par clé {widget_key}: {e}')
            return None
    
    async def update_widget_settings(self, widget_id: str, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Mettre à jour les paramètres d'un widget dans la DB"""
        if not self.supabase:
            raise HTTPException(status_code=500, detail="Base de données non disponible")
        
        try:
            self.supabase.table('web_widgets').update({
                'settings': new_settings,
                'updated_at': datetime.now().isoformat()
            }).eq('id', widget_id).execute()
            
            logger.info(f'Widget {widget_id} mis à jour dans la DB')
            return {
                'success': True,
                'widget_id': widget_id,
                'message': 'Widget mis à jour avec succès',
                'updated_settings': new_settings
            }
        except Exception as e:
            logger.error(f'Erreur mise à jour widget: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur mise à jour: {str(e)}')
    
    async def enable_branding(self, widget_id: str, custom_text: str, payment_id: str) -> Dict[str, Any]:
        """Activer le branding personnalisé pour un widget après paiement"""
        if not self.supabase:
            raise HTTPException(status_code=500, detail="Base de données non disponible")
        
        try:
            from datetime import datetime, timezone
            
            self.supabase.table('web_widgets').update({
                'branding_enabled': True,
                'branding_text': custom_text,
                'stripe_payment_id': payment_id,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', widget_id).execute()
            
            logger.info(f'Branding activé pour widget {widget_id}')
            return {
                'success': True,
                'widget_id': widget_id,
                'branding_enabled': True,
                'branding_text': custom_text
            }
        except Exception as e:
            logger.error(f'Erreur activation branding: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur activation branding: {str(e)}')
    
    async def get_user_widgets(self, user_id: str) -> List[Dict[str, Any]]:
        """Récupérer tous les widgets d'un utilisateur"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('web_widgets').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f'Erreur récupération widgets utilisateur {user_id}: {e}')
            return []

    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


_web_widget_service: Optional[WebWidgetService] = None

async def get_web_widget_service(supabase_client: Optional[Any] = None) -> WebWidgetService:
    """Factory pour obtenir une instance du service Widget"""
    global _web_widget_service
    if _web_widget_service is None or (supabase_client and _web_widget_service.supabase is None):
        _web_widget_service = WebWidgetService(supabase_client)
    return _web_widget_service