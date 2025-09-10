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
        
        self.REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
        self.REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
        self.REDDIT_REDIRECT_URI = os.getenv("REDDIT_REDIRECT_URI")
        
        self.TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
        self.TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
        self.TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI")

    def get_instagram_auth_url(self, state: str) -> str:
        """Construit l'URL d'autorisation pour le flux Instagram Business."""
        if not self.INSTAGRAM_CLIENT_ID or not self.INSTAGRAM_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Instagram auth is not configured on the server.")
        
        scopes = [
            "instagram_business_basic",
            "instagram_business_content_publish",
            "instagram_business_manage_messages",
            "instagram_business_manage_comments"
        ]
        
        params = {
            "client_id": self.INSTAGRAM_CLIENT_ID,
            "redirect_uri": self.INSTAGRAM_REDIRECT_URI,
            "scope": ",".join(scopes),
            "response_type": "code",
            "state": state
        }
        auth_url = f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"
        return auth_url

    async def handle_instagram_callback(self, code: str) -> dict:
        """Échange le code d'autorisation contre un token d'accès longue durée."""
        if not self.INSTAGRAM_CLIENT_ID or not self.INSTAGRAM_CLIENT_SECRET or not self.INSTAGRAM_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Instagram auth is not configured on the server.")
        
        async with httpx.AsyncClient() as client:
            try:
                # Étape 1: Échanger le code contre un token de courte durée
                short_lived_token_url = "https://api.instagram.com/oauth/access_token"
                short_lived_payload = {
                    "client_id": self.INSTAGRAM_CLIENT_ID,
                    "client_secret": self.INSTAGRAM_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.INSTAGRAM_REDIRECT_URI,
                    "code": code,
                }
                response = await client.post(short_lived_token_url, data=short_lived_payload)
                response.raise_for_status()
                short_lived_token_data = response.json()

                # Étape 2: Échanger le token de courte durée contre un token de longue durée
                long_lived_token_url = "https://graph.instagram.com/access_token"
                params = {
                    "grant_type": "ig_exchange_token",
                    "client_secret": self.INSTAGRAM_CLIENT_SECRET,
                    "access_token": short_lived_token_data["access_token"],
                }
                response = await client.get(long_lived_token_url, params=params)
                response.raise_for_status()
                long_lived_token_data = response.json()

                return {
                    "access_token": long_lived_token_data["access_token"],
                    "token_type": long_lived_token_data["token_type"],
                    "expires_in": long_lived_token_data["expires_in"],
                    "user_id": short_lived_token_data.get("user_id"),
                }

            except httpx.HTTPStatusError as e:
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
        """Récupère l'ID et le nom d'utilisateur du compte Instagram Business via l'API Graph d'Instagram."""
        # Avec un token d'utilisateur Instagram, on utilise l'endpoint graph.instagram.com
        url = f"https://graph.instagram.com/me?fields=id,username,account_type,profile_picture_url"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Vérifier que c'est bien un compte BUSINESS ou CREATOR
                if data.get("account_type") not in ["BUSINESS", "CREATOR"]:
                    raise HTTPException(status_code=400, detail="The authenticated account is not an Instagram Business or Creator account.")
                
                # L'endpoint /me renvoie directement les infos du compte business
                return {
                    "id": data["id"],
                    "username": data["username"],
                    "profile_picture_url": data.get("profile_picture_url")
                }

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
        """Récupère le profil utilisateur Twitter/X via l'API v2."""
        async with httpx.AsyncClient() as client:
            try:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                # API Twitter v2 pour récupérer le profil utilisateur
                # On utilise l'endpoint /2/users/me avec les champs profile
                params = {
                    "user.fields": "id,username,name,profile_image_url,public_metrics"
                }
                
                response = await client.get(
                    "https://api.twitter.com/2/users/me", 
                    headers=headers, 
                    params=params
                )
                response.raise_for_status()
                profile_data = response.json()
                
                user_data = profile_data.get("data", {})
                
                return {
                    "id": user_data.get("id"),
                    "username": user_data.get("username"),
                    "name": user_data.get("name"),
                    "profile_picture_url": user_data.get("profile_image_url")
                }

            except httpx.HTTPStatusError as e:
                print(f"Error fetching Twitter profile: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch Twitter profile: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred while fetching profile: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching Twitter profile.")

    async def get_tiktok_profile(self, access_token: str) -> dict:
        # TODO: Implémenter la récupération de profil pour TikTok
        return {"id": "tiktok_id", "username": "tiktok_user"}
        
    async def get_whatsapp_profile(self, access_token: str) -> dict:
        # TODO: Implémenter la récupération de profil pour WhatsApp
        return {"id": "whatsapp_id", "username": "whatsapp_user"}

    def get_reddit_auth_url(self, state: str) -> str:
        """Construit l'URL d'autorisation pour Reddit."""
        if not self.REDDIT_CLIENT_ID or not self.REDDIT_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Reddit auth is not configured on the server.")
        
        scopes = [
            "identity",
            "read",
            "submit",
            "edit",
            "privatemessages",
            "modposts"
        ]
        
        params = {
            "client_id": self.REDDIT_CLIENT_ID,
            "response_type": "code",
            "state": state,
            "redirect_uri": self.REDDIT_REDIRECT_URI,
            "duration": "permanent",
            "scope": " ".join(scopes)
        }
        auth_url = f"https://www.reddit.com/api/v1/authorize?{urlencode(params)}"
        return auth_url

    async def handle_reddit_callback(self, code: str) -> dict:
        """Échange le code d'autorisation contre un token d'accès Reddit."""
        if not self.REDDIT_CLIENT_ID or not self.REDDIT_CLIENT_SECRET or not self.REDDIT_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Reddit auth is not configured on the server.")
        
        async with httpx.AsyncClient() as client:
            try:
                # Reddit nécessite l'authentification basic avec client_id:client_secret
                auth = (self.REDDIT_CLIENT_ID, self.REDDIT_CLIENT_SECRET)
                
                token_url = "https://www.reddit.com/api/v1/access_token"
                payload = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.REDDIT_REDIRECT_URI,
                }
                
                headers = {
                    "User-Agent": "SocialSync:v1.0.0 (by /u/socialsync_app)"
                }
                
                response = await client.post(token_url, data=payload, auth=auth, headers=headers)
                response.raise_for_status()
                token_data = response.json()

                return {
                    "access_token": token_data["access_token"],
                    "token_type": token_data["token_type"],
                    "expires_in": token_data["expires_in"],
                    "refresh_token": token_data.get("refresh_token"),
                    "scope": token_data.get("scope"),
                }

            except httpx.HTTPStatusError as e:
                print(f"Error exchanging Reddit code: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred during Reddit authentication.")

    async def get_reddit_profile(self, access_token: str) -> dict:
        """Récupère le profil utilisateur Reddit."""
        async with httpx.AsyncClient() as client:
            try:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": "SocialSync:v1.0.0 (by /u/socialsync_app)"
                }
                
                response = await client.get("https://oauth.reddit.com/api/v1/me", headers=headers)
                response.raise_for_status()
                profile_data = response.json()
                
                return {
                    "id": profile_data["id"],
                    "username": profile_data["name"],
                    "profile_picture_url": profile_data.get("icon_img", "").split("?")[0] if profile_data.get("icon_img") else None
                }

            except httpx.HTTPStatusError as e:
                print(f"Error fetching Reddit profile: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch Reddit profile: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred while fetching profile: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching Reddit profile.")

    async def refresh_reddit_token(self, refresh_token: str) -> dict:
        """Rafraîchit le token d'accès Reddit en utilisant le refresh token."""
        if not self.REDDIT_CLIENT_ID or not self.REDDIT_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Reddit auth is not configured on the server.")
        
        async with httpx.AsyncClient() as client:
            try:
                auth = (self.REDDIT_CLIENT_ID, self.REDDIT_CLIENT_SECRET)
                
                token_url = "https://www.reddit.com/api/v1/access_token"
                payload = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
                
                headers = {
                    "User-Agent": "SocialSync:v1.0.0 (by /u/socialsync_app)"
                }
                
                response = await client.post(token_url, data=payload, auth=auth, headers=headers)
                response.raise_for_status()
                token_data = response.json()

                return {
                    "access_token": token_data["access_token"],
                    "token_type": token_data["token_type"],
                    "expires_in": token_data.get("expires_in", 86400),
                    "refresh_token": refresh_token,  # Le refresh token reste le même
                    "scope": token_data.get("scope"),
                }

            except httpx.HTTPStatusError as e:
                print(f"Error refreshing Reddit token: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to refresh Reddit token: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred during Reddit token refresh.")

    def get_linkedin_auth_url(self, state: str) -> str:
        # Stub: retourner une URL d'auth factice incluant le state pour rester compatible
        params = {
            "response_type": "code",
            "client_id": "TEST_LINKEDIN_CLIENT_ID",
            "redirect_uri": "https://example.com/linkedin/callback",
            "scope": "r_liteprofile r_emailaddress",
            "state": state,
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

    def handle_linkedin_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_linkedin_token"}
        
    def get_twitter_auth_url(self, state: str) -> str:
        """Construit l'URL d'autorisation pour Twitter/X OAuth 2.0 avec PKCE."""
        if not self.TWITTER_CLIENT_ID or not self.TWITTER_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Twitter auth is not configured on the server.")
        
        # Pour Twitter OAuth 2.0, on utilise les scopes v2
        scopes = [
            "tweet.read",
            "tweet.write", 
            "users.read",
            "offline.access"  # Pour avoir un refresh token
        ]
        
        # Note: Twitter OAuth 2.0 PKCE nécessiterait code_challenge mais pour simplifier 
        # on utilise la méthode standard avec client_secret
        params = {
            "response_type": "code",
            "client_id": self.TWITTER_CLIENT_ID,
            "redirect_uri": self.TWITTER_REDIRECT_URI,
            "scope": " ".join(scopes),
            "state": state
        }
        auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
        return auth_url

    async def handle_twitter_callback(self, code: str) -> dict:
        """Échange le code d'autorisation contre un token d'accès Twitter."""
        if not self.TWITTER_CLIENT_ID or not self.TWITTER_CLIENT_SECRET or not self.TWITTER_REDIRECT_URI:
            raise HTTPException(status_code=500, detail="Twitter auth is not configured on the server.")
        
        async with httpx.AsyncClient() as client:
            try:
                # Twitter OAuth 2.0 utilise Basic auth
                auth = (self.TWITTER_CLIENT_ID, self.TWITTER_CLIENT_SECRET)
                
                token_url = "https://api.twitter.com/2/oauth2/token"
                payload = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.TWITTER_REDIRECT_URI,
                }
                
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                response = await client.post(token_url, data=payload, auth=auth, headers=headers)
                response.raise_for_status()
                token_data = response.json()

                return {
                    "access_token": token_data["access_token"],
                    "token_type": token_data["token_type"],
                    "expires_in": token_data.get("expires_in", 7200),  # 2h par défaut
                    "refresh_token": token_data.get("refresh_token"),
                    "scope": token_data.get("scope"),
                }

            except httpx.HTTPStatusError as e:
                print(f"Error exchanging Twitter code: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {e.response.text}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred during Twitter authentication.")

    def get_tiktok_auth_url(self, state: str) -> str:
        # Stub: inclure state pour compatibilité
        params = {
            "client_key": "TEST_TIKTOK_CLIENT_ID",
            "response_type": "code",
            "redirect_uri": "https://example.com/tiktok/callback",
            "scope": "user.info.basic,video.list",
            "state": state,
        }
        return f"https://www.tiktok.com/v2/auth/authorize?{urlencode(params)}"

    def handle_tiktok_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_tiktok_token"}

    def get_whatsapp_auth_url(self, state: str) -> str:
        # Stub: inclure state pour compatibilité
        params = {
            "client_id": "TEST_META_APP_ID",
            "redirect_uri": "https://example.com/whatsapp/callback",
            "response_type": "code",
            "scope": "whatsapp_business_messaging",
            "state": state,
        }
        return f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"

    def handle_whatsapp_callback(self, code: str) -> dict:
        # TODO: Implémenter l'échange du code contre un token
        return {"access_token": "fake_whatsapp_token"}

social_auth_service = SocialAuthService()
