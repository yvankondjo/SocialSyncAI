import os
from fastapi import HTTPException
from dotenv import load_dotenv
from urllib.parse import urlencode
import httpx

load_dotenv()

class SocialAuthService:
    def __init__(self):
        self.INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
        self.INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")
        self.INSTAGRAM_REDIRECT_URI = os.getenv("INSTAGRAM_REDIRECT_URI")
        # ... (d'autres secrets pour les autres plateformes seront ajoutés ici)

    def get_instagram_auth_url(self, state: str) -> str:
        """Construit l'URL d'autorisation pour Instagram Basic Display API."""
        if not self.INSTAGRAM_CLIENT_ID or not self.INSTAGRAM_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Instagram auth is not configured on the server.")
        
        # Permissions pour l'API Instagram Graph (Business & Creator)
        # Corrigé pour correspondre à l'URL de test fonctionnelle
        scopes = [
            "instagram_business_basic",
            "instagram_business_manage_messages",
            "instagram_business_manage_comments",
            "instagram_business_content_publish",
            "instagram_business_manage_insights" # Ajout de la permission pour les insights
        ]
        
        params = {
            "client_id": self.INSTAGRAM_CLIENT_ID,
            "redirect_uri": self.INSTAGRAM_REDIRECT_URI,
            "scope": ",".join(scopes), # Utilisation des scopes pour l'API Graph
            "response_type": "code",
            "state": state # Ajout du paramètre state pour la sécurité
        }
        auth_url = f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"
        return auth_url

    async def handle_instagram_callback(self, code: str) -> dict:
        """Échange le code d'autorisation contre un token d'accès."""
        if not self.INSTAGRAM_CLIENT_ID or not self.INSTAGRAM_CLIENT_SECRET or not self.INSTAGRAM_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Instagram auth is not configured on the server.")

        token_url = "https://api.instagram.com/oauth/access_token"
        payload = {
            "client_id": self.INSTAGRAM_CLIENT_ID,
            "client_secret": self.INSTAGRAM_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": self.INSTAGRAM_REDIRECT_URI,
            "code": code,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(token_url, data=payload)
                response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
                short_lived_token_data = response.json()

                # Échanger le token de courte durée contre un token de longue durée
                long_lived_token_url = f"https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret={self.INSTAGRAM_CLIENT_SECRET}&access_token={short_lived_token_data['access_token']}"
                response = await client.get(long_lived_token_url)
                response.raise_for_status()
                long_lived_token_data = response.json()

                return {
                    "access_token": long_lived_token_data["access_token"],
                    "token_type": long_lived_token_data["token_type"],
                    "expires_in": long_lived_token_data["expires_in"],
                    "user_id": short_lived_token_data["user_id"],
                }

            except httpx.HTTPStatusError as e:
                # Log l'erreur pour le débogage
                print(f"Error exchanging Instagram code: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred during Instagram authentication.")

    async def get_instagram_user_profile(self, access_token: str) -> dict:
        """Récupère le profil utilisateur d'Instagram en utilisant le token d'accès."""
        profile_url = f"https://graph.instagram.com/me?fields=id,username&access_token={access_token}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(profile_url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Error fetching Instagram profile: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch Instagram profile: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred while fetching profile: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching Instagram profile.")

    async def get_instagram_business_account(self, access_token: str) -> dict:
        """Récupère l'ID du compte Instagram Business via l'API Graph de Facebook."""
        # Cet endpoint est sur graph.facebook.com, pas graph.instagram.com
        url = f"https://graph.facebook.com/v19.0/me/accounts?fields=instagram_business_account{{id,username,profile_picture_url}}&access_token={access_token}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                # On cherche le premier compte qui a un "instagram_business_account" lié
                for page in data.get("data", []):
                    if "instagram_business_account" in page:
                        return page["instagram_business_account"]
                raise HTTPException(status_code=404, detail="No Instagram Business Account linked to this Facebook Page.")
            except httpx.HTTPStatusError as e:
                print(f"Error fetching Instagram Business Account: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch Instagram Business Account: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching Instagram Business Account.")

    async def get_linkedin_business_profile(self, access_token: str) -> dict:
        # TODO: Implémenter la récupération de profil pour LinkedIn
        return {"id": "linkedin_id", "username": "linkedin_user"}

    async def get_twitter_profile(self, access_token: str) -> dict:
        # TODO: Implémenter la récupération de profil pour Twitter/X
        return {"id": "twitter_id", "username": "twitter_user"}

    async def get_tiktok_profile(self, access_token: str) -> dict:
        # TODO: Implémenter la récupération de profil pour TikTok
        return {"id": "tiktok_id", "username": "tiktok_user"}
        
    async def get_whatsapp_profile(self, access_token: str) -> dict:
        # TODO: Implémenter la récupération de profil pour WhatsApp
        return {"id": "whatsapp_id", "username": "whatsapp_user"}

    def get_linkedin_auth_url(self) -> str:
        # TODO: Implémenter la logique pour construire l'URL d'auth LinkedIn
        return "https://www.linkedin.com/oauth/v2/authorization?..."

    def handle_linkedin_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_linkedin_token"}
        
    def get_twitter_auth_url(self) -> str:
        # TODO: Implémenter la logique pour construire l'URL d'auth X/Twitter
        return "https://twitter.com/i/oauth2/authorize?..."

    def handle_twitter_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_twitter_token"}

    def get_tiktok_auth_url(self) -> str:
        # TODO: Implémenter la logique pour construire l'URL d'auth TikTok
        return "https://www.tiktok.com/v2/auth/authorize?..."

    def handle_tiktok_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_tiktok_token"}

    def get_whatsapp_auth_url(self) -> str:
        # TODO: Implémenter la logique pour l'auth WhatsApp via Meta
        return "https://www.facebook.com/v18.0/dialog/oauth?..."

    def handle_whatsapp_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_whatsapp_token"}

social_auth_service = SocialAuthService() 