import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from dotenv import load_dotenv
from urllib.parse import urlencode
import httpx
import logging
load_dotenv()
logger = logging.getLogger(__name__)
class SocialAuthService:
    def __init__(self):
        self.INSTAGRAM_CLIENT_ID = os.getenv('INSTAGRAM_CLIENT_ID')
        self.INSTAGRAM_CLIENT_SECRET = os.getenv('INSTAGRAM_CLIENT_SECRET')
        self.INSTAGRAM_REDIRECT_URI = os.getenv('INSTAGRAM_REDIRECT_URI')
        self.META_APP_ID = os.getenv('META_APP_ID')
        self.META_APP_SECRET = os.getenv('META_APP_SECRET')
        self.META_CONFIG_ID = os.getenv('META_CONFIG_ID')
        self.META_GRAPH_VERSION = os.getenv('META_GRAPH_VERSION', 'v24.0')
        self.WHATSAPP_REDIRECT_URI = os.getenv('WHATSAPP_REDIRECT_URI') or os.getenv('WHATSAPP_EMBEDDED_REDIRECT_URI')
        self.WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'whatsapp_verify_token')
        self.REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
        self.REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
        self.REDDIT_REDIRECT_URI = os.getenv('REDDIT_REDIRECT_URI')
        self.TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
        self.TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
        self.TWITTER_REDIRECT_URI = os.getenv('TWITTER_REDIRECT_URI')

    def get_instagram_auth_url(self, state: str) -> str:
        """Construit l'URL d'autorisation pour le flux Instagram Business."""
        if not self.INSTAGRAM_CLIENT_ID or not self.INSTAGRAM_REDIRECT_URI:
            raise HTTPException(status_code=500, detail='Instagram auth is not configured on the server.')
        scopes = ['instagram_business_basic', 'instagram_business_content_publish', 'instagram_business_manage_messages', 'instagram_business_manage_comments']
        logger.info(f"🔍 DEBUG get_instagram_auth_url - scopes: {scopes}")
        logger.info(f"🔍 DEBUG get_instagram_auth_url - client_id: {self.INSTAGRAM_CLIENT_ID}")
        logger.info(f"🔍 DEBUG get_instagram_auth_url - redirect_uri: {self.INSTAGRAM_REDIRECT_URI}")
        logger.info(f"🔍 DEBUG get_instagram_auth_url - state: {state}")
        params = {'client_id': self.INSTAGRAM_CLIENT_ID, 'redirect_uri': self.INSTAGRAM_REDIRECT_URI, 'scope': ','.join(scopes), 'response_type': 'code', 'state': state}
        auth_url = f'https://api.instagram.com/oauth/authorize?{urlencode(params)}'
        return auth_url

    def get_whatsapp_embedded_signup_url(self, state: str, prefill: Optional[Dict[str, Dict[str, Optional[str]]]] = None) -> str:
        """Génère l'URL hébergée par Meta pour l'Embedded Signup WhatsApp."""
        if not self.META_APP_ID or not self.META_CONFIG_ID:
            raise HTTPException(status_code=500, detail='WhatsApp embedded signup is not configured on the server.')

        setup_data = prefill if prefill else {
            "business": {"id": None, "name": None, "email": None, "phone": {"code": None, "number": None}, "website": None, "address": {"streetAddress1": None, "streetAddress2": None, "city": None, "state": None, "zipPostal": None, "country": None}, "timezone": None},
            "phone": {"displayName": None, "category": None, "description": None},
            "preVerifiedPhone": {"ids": None},
            "solutionID": None,
            "whatsAppBusinessAccount": {"ids": None}
        }

        extras = {
            "setup": setup_data,
            "featureType": "whatsapp_business_app_onboarding",
            "sessionInfoVersion": "3",
            "version": "v3"
        }

        import json
        extras_encoded = urlencode({"extras": json.dumps(extras)})
        
        base_url = "https://business.facebook.com/messaging/whatsapp/onboard/"
        params = f"app_id={self.META_APP_ID}&config_id={self.META_CONFIG_ID}&state={state}&{extras_encoded}"
        
        logger.info(f"🔗 URL Embedded Signup générée: {base_url}?{params[:200]}...")
        
        return f"{base_url}?{params}"

    async def handle_instagram_callback(self, code: str) -> dict:
        """Échange le code d'autorisation contre un token d'accès longue durée."""
        if not self.INSTAGRAM_CLIENT_ID or not self.INSTAGRAM_CLIENT_SECRET or not self.INSTAGRAM_REDIRECT_URI:
            raise HTTPException(status_code=500, detail='Instagram auth is not configured on the server.')
        async with httpx.AsyncClient() as client:
            try:
                short_lived_token_url = 'https://api.instagram.com/oauth/access_token'
                short_lived_payload = {'client_id': self.INSTAGRAM_CLIENT_ID, 'client_secret': self.INSTAGRAM_CLIENT_SECRET, 'grant_type': 'authorization_code', 'redirect_uri': self.INSTAGRAM_REDIRECT_URI, 'code': code}
                response = await client.post(short_lived_token_url, data=short_lived_payload)
                response.raise_for_status()
                short_lived_token_data = response.json()
                long_lived_token_url = 'https://graph.instagram.com/access_token'
                params = {'grant_type': 'ig_exchange_token', 'client_secret': self.INSTAGRAM_CLIENT_SECRET, 'access_token': short_lived_token_data['access_token']}
                response = await client.get(long_lived_token_url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f'Error exchanging Instagram code: {e.response.text}')
                raise HTTPException(status_code=400, detail=f'Failed to exchange code for token: {e.response.text}')
            except Exception as e:
                print(f'An unexpected error occurred: {e}')
                raise HTTPException(status_code=500, detail='An unexpected error occurred during Instagram authentication.')

    async def exchange_whatsapp_code(self, code: str, redirect_uri: Optional[str] = None) -> dict:
        """Échange un code Embedded Signup contre un business token WhatsApp."""
        if not self.META_APP_ID or not self.META_APP_SECRET:
            raise HTTPException(status_code=500, detail='WhatsApp auth is not configured on the server.')

        token_endpoint = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/oauth/access_token'

        params = {
            'client_id': self.META_APP_ID,
            'client_secret': self.META_APP_SECRET,
            'code': code,
        }

        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        elif self.WHATSAPP_REDIRECT_URI:
            params['redirect_uri'] = self.WHATSAPP_REDIRECT_URI

        logger.info(f"🔄 Échange du code WhatsApp avec params: {params}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(token_endpoint, params=params)
                response.raise_for_status()
                token_data = response.json()
                logger.info(f"✅ Token obtenu: {token_data.get('access_token', 'N/A')[:20]}...")
                if 'access_token' not in token_data:
                    raise HTTPException(status_code=400, detail='Failed to obtain WhatsApp business token.')
                return token_data
            except httpx.HTTPStatusError as e:
                logger.error(f'❌ Erreur échange code WhatsApp: {e.response.text}')
                raise HTTPException(status_code=400, detail=f'Failed to exchange code for WhatsApp token: {e.response.text}')
            except Exception as e:
                logger.error(f'❌ Erreur inattendue échange code: {e}')
                raise HTTPException(status_code=500, detail='Unexpected error during WhatsApp authentication.')

    async def get_instagram_user_profile(self, access_token: str) -> dict:
        """Récupère le profil utilisateur d'Instagram en utilisant le token d'accès."""
        profile_url = f'https://graph.instagram.com/v23.0/me?fields=id,username&access_token={access_token}'
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(profile_url)
                response.raise_for_status()
                print(f"🔍 DEBUG get_instagram_user_profile - response: {response.json()}")
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f'Error fetching Instagram profile: {e.response.text}')
                raise HTTPException(status_code=400, detail=f'Failed to fetch Instagram profile: {e.response.text}')
            except Exception as e:
                print(f'An unexpected error occurred while fetching profile: {e}')
                raise HTTPException(status_code=500, detail='An unexpected error occurred while fetching Instagram profile.')

    async def get_instagram_business_account(self, access_token: str) -> dict:
        """Récupère l'ID et le nom d'utilisateur du compte Instagram Business via l'API Graph d'Instagram."""
        url = 'https://graph.instagram.com/v23.0/me?fields=id,user_id,username,account_type,profile_picture_url'
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                print(f"🔍 DEBUG get_instagram_business_account - response: {response.json()}")
                data = response.json()
                if data.get('account_type') not in ['BUSINESS', 'CREATOR']:
                    raise HTTPException(status_code=400, detail='The authenticated account is not an Instagram Business or Creator account.')
                # Utiliser user_id (IG ID) au lieu de id (app-scoped ID) pour correspondre aux webhooks
                ig_id = data.get('user_id', data.get('id'))  # Fallback vers id si user_id n'est pas disponible
                return {'id': ig_id, 'username': data['username'], 'profile_picture_url': data.get('profile_picture_url')}
            except httpx.HTTPStatusError as e:
                print(f'Error fetching Instagram Business Account: {e.response.text}')
                raise HTTPException(status_code=400, detail=f'Failed to fetch Instagram Business Account: {e.response.text}')
            except Exception as e:
                print(f'An unexpected error occurred: {e}')
                raise HTTPException(status_code=500, detail='An unexpected error occurred while fetching Instagram Business Account.')

    async def get_linkedin_business_profile(self, access_token: str) -> dict:
        return {'id': 'linkedin_id', 'username': 'linkedin_user'}

    async def get_twitter_profile(self, access_token: str) -> dict:
        """Récupère le profil utilisateur Twitter/X via l'API v2."""
        async with httpx.AsyncClient() as client:
            try:
                headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
                params = {'user.fields': 'id,username,name,profile_image_url,public_metrics'}
                response = await client.get('https://api.twitter.com/2/users/me', headers=headers, params=params)
                response.raise_for_status()
                profile_data = response.json()
                user_data = profile_data.get('data', {})
                return {'id': user_data.get('id'), 'username': user_data.get('username'), 'name': user_data.get('name'), 'profile_picture_url': user_data.get('profile_image_url')}
            except httpx.HTTPStatusError as e:
                print(f'Error fetching Twitter profile: {e.response.text}')
                raise HTTPException(status_code=400, detail=f'Failed to fetch Twitter profile: {e.response.text}')
            except Exception as e:
                print(f'An unexpected error occurred while fetching profile: {e}')
                raise HTTPException(status_code=500, detail='An unexpected error occurred while fetching Twitter profile.')

    async def get_tiktok_profile(self, access_token: str) -> dict:
        return {'id': 'tiktok_id', 'username': 'tiktok_user'}

    async def get_whatsapp_phone_profile(self, access_token: str, phone_number_id: str) -> dict:
        """Récupère les informations d'un numéro WhatsApp Business."""
        async with httpx.AsyncClient() as client:
            try:
                url = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/{phone_number_id}'
                response = await client.get(url, params={'fields': 'display_phone_number,verified_name'}, headers={'Authorization': f'Bearer {access_token}'})
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error('Error fetching WhatsApp phone profile: %s', e.response.text)
                raise HTTPException(status_code=400, detail=f'Failed to fetch WhatsApp phone profile: {e.response.text}')
            except Exception as e:
                logger.error('Unexpected error fetching WhatsApp phone profile: %s', e)
                raise HTTPException(status_code=500, detail='Unexpected error while fetching WhatsApp phone profile.')

    async def subscribe_whatsapp_webhooks(self, access_token: str, waba_id: str, subscribed_fields: Optional[List[str]] = None) -> Optional[dict]:
        """Souscrit l'application aux webhooks du WABA."""
        if not waba_id:
            return None

        fields = subscribed_fields or ['messages']
        async with httpx.AsyncClient() as client:
            try:
                url = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/{waba_id}/subscribed_apps'
                response = await client.post(url, json={'subscribed_fields': fields}, headers={'Authorization': f'Bearer {access_token}'})
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning('WhatsApp webhook subscription failed: %s', e.response.text)
                return {'error': e.response.text}
            except Exception as e:
                logger.warning('Unexpected error subscribing WhatsApp webhooks: %s', e)
                return {'error': str(e)}

    async def get_whatsapp_business_accounts(self, access_token: str) -> List[Dict[str, any]]:
        """Récupère les comptes WhatsApp via /me/businesses."""
        async with httpx.AsyncClient() as client:
            try:
                url = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/me/businesses'
                params = {
                    'fields': 'owned_whatsapp_business_accounts{id,name,phone_numbers{phone_number_id,display_phone_number,verified_name}}'
                }
                response = await client.get(url, params=params, headers={'Authorization': f'Bearer {access_token}'})
                response.raise_for_status()
                data = response.json()
                businesses = data.get('data', [])
                results: List[Dict[str, any]] = []
                for business in businesses:
                    waba_list = business.get('owned_whatsapp_business_accounts', {}).get('data', []) if isinstance(business.get('owned_whatsapp_business_accounts'), dict) else business.get('owned_whatsapp_business_accounts', [])
                    for account in waba_list:
                        account['business_id'] = business.get('id')
                        results.append(account)
                return results
            except httpx.HTTPStatusError as e:
                logger.error('Error fetching WhatsApp businesses: %s', e.response.text)
                raise HTTPException(status_code=400, detail=f'Failed to fetch WhatsApp businesses: {e.response.text}')
            except Exception as e:
                logger.error('Unexpected error fetching WhatsApp businesses: %s', e)
                raise HTTPException(status_code=500, detail='Unexpected error while fetching WhatsApp businesses.')

    def get_reddit_auth_url(self, state: str) -> str:
        """Construit l'URL d'autorisation pour Reddit."""
        if not self.REDDIT_CLIENT_ID or not self.REDDIT_REDIRECT_URI:
            raise HTTPException(status_code=500, detail='Reddit auth is not configured on the server.')
        scopes = ['identity', 'read', 'submit', 'edit', 'privatemessages', 'modposts']
        params = {'client_id': self.REDDIT_CLIENT_ID, 'response_type': 'code', 'state': state, 'redirect_uri': self.REDDIT_REDIRECT_URI, 'duration': 'permanent', 'scope': ' '.join(scopes)}
        auth_url = f'https://www.reddit.com/api/v1/authorize?{urlencode(params)}'
        return auth_url

    async def handle_whatsapp_callback(self, code: str) -> dict:
        """Compatibilité: échange le code via le flux OAuth standard."""
        return await self.exchange_whatsapp_code(code)

    def get_messenger_auth_url(self, state: str) -> str:
        """
        Generate Facebook OAuth URL for Messenger (Page access).

        Args:
            state: JWT state token for CSRF protection

        Returns:
            Authorization URL string
        """
        if not self.META_APP_ID:
            raise HTTPException(status_code=500, detail='Messenger auth is not configured on the server.')

        # Scopes needed for Messenger DMs
        scopes = [
            'pages_messaging',           # Send/receive messages
            'pages_read_engagement',     # Read engagement data
            'pages_manage_metadata',     # Manage page metadata
        ]

        redirect_uri = os.getenv('MESSENGER_REDIRECT_URI')
        if not redirect_uri:
            raise HTTPException(status_code=500, detail='MESSENGER_REDIRECT_URI not configured.')

        params = {
            'client_id': self.META_APP_ID,
            'redirect_uri': redirect_uri,
            'scope': ','.join(scopes),
            'response_type': 'code',
            'state': state
        }

        auth_url = f'https://www.facebook.com/v{self.META_GRAPH_VERSION}/dialog/oauth?{urlencode(params)}'
        logger.info(f"Generated Messenger auth URL with scopes: {scopes}")
        return auth_url

    async def handle_messenger_callback(self, code: str) -> dict:
        """
        Exchange authorization code for user access token.
        Note: This returns a user token. We'll need to fetch Page tokens separately.

        Args:
            code: Authorization code from Facebook OAuth

        Returns:
            Dict with 'access_token' and other token data
        """
        if not self.META_APP_ID or not self.META_APP_SECRET:
            raise HTTPException(status_code=500, detail='Messenger auth is not configured on the server.')

        token_url = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/oauth/access_token'
        redirect_uri = os.getenv('MESSENGER_REDIRECT_URI')

        params = {
            'client_id': self.META_APP_ID,
            'client_secret': self.META_APP_SECRET,
            'code': code,
            'redirect_uri': redirect_uri
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(token_url, params=params)
                response.raise_for_status()
                token_data = response.json()

                logger.info(f"✅ Messenger user token obtained: {token_data.get('access_token', 'N/A')[:20]}...")
                return token_data
            except httpx.HTTPStatusError as e:
                logger.error(f'❌ Error exchanging Messenger code: {e.response.text}')
                raise HTTPException(
                    status_code=400,
                    detail=f'Failed to exchange code for Messenger token: {e.response.text}'
                )
            except Exception as e:
                logger.error(f'❌ Unexpected error during Messenger auth: {e}')
                raise HTTPException(
                    status_code=500,
                    detail='Unexpected error during Messenger authentication.'
                )

    async def get_facebook_pages(self, user_access_token: str) -> List[Dict[str, Any]]:
        """
        Get all Facebook Pages managed by the user with their Page access tokens.

        Args:
            user_access_token: User's access token from OAuth

        Returns:
            List of dicts with page info including:
            - id: Page ID
            - name: Page name
            - access_token: Page access token (for API calls)
            - category: Page category
            - tasks: List of permissions
        """
        url = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/me/accounts'
        params = {
            'access_token': user_access_token,
            'fields': 'id,name,access_token,category,tasks'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                pages = data.get('data', [])
                logger.info(f"✅ Retrieved {len(pages)} Facebook Pages for user")

                return pages
            except httpx.HTTPStatusError as e:
                logger.error(f'❌ Error fetching Facebook Pages: {e.response.text}')
                raise HTTPException(
                    status_code=400,
                    detail=f'Failed to fetch Facebook Pages: {e.response.text}'
                )
            except Exception as e:
                logger.error(f'❌ Unexpected error fetching Pages: {e}')
                raise HTTPException(
                    status_code=500,
                    detail='Unexpected error while fetching Facebook Pages.'
                )

    async def subscribe_page_to_webhooks(
        self,
        page_id: str,
        page_access_token: str,
        subscribed_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Subscribe a Facebook Page to app webhooks.

        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            subscribed_fields: List of webhook fields to subscribe to

        Returns:
            Dict with subscription result
        """
        fields = subscribed_fields or ['messages', 'messaging_postbacks', 'message_reads']

        url = f'https://graph.facebook.com/{self.META_GRAPH_VERSION}/{page_id}/subscribed_apps'
        params = {
            'subscribed_fields': ','.join(fields),
            'access_token': page_access_token
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, params=params)
                response.raise_for_status()
                result = response.json()

                logger.info(f"✅ Page {page_id} subscribed to webhooks: {fields}")
                return result
            except httpx.HTTPStatusError as e:
                logger.warning(f'⚠️ Webhook subscription failed for Page {page_id}: {e.response.text}')
                return {'error': e.response.text, 'success': False}
            except Exception as e:
                logger.warning(f'⚠️ Unexpected error subscribing webhooks for Page {page_id}: {e}')
                return {'error': str(e), 'success': False}


social_auth_service = SocialAuthService()