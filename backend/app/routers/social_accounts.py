from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.social_auth_service import SocialAuthService
from app.schemas.social_account import AuthURL, TokenData
from app.core.security import get_current_user_id
from typing import Dict, Any

router = APIRouter(prefix="/social-accounts", tags=["social-accounts"])

PLATFORMS = {
    "instagram": {
        "get_auth_url": SocialAuthService.get_instagram_auth_url,
        "handle_callback": SocialAuthService.handle_instagram_callback,
    },
    "linkedin": {
        "get_auth_url": SocialAuthService.get_linkedin_auth_url,
        "handle_callback": SocialAuthService.handle_linkedin_callback,
    },
    "twitter": {
        "get_auth_url": SocialAuthService.get_twitter_auth_url,
        "handle_callback": SocialAuthService.handle_twitter_callback,
    },
    "tiktok": {
        "get_auth_url": SocialAuthService.get_tiktok_auth_url,
        "handle_callback": SocialAuthService.handle_tiktok_callback,
    },
    "whatsapp": {
        "get_auth_url": SocialAuthService.get_whatsapp_auth_url,
        "handle_callback": SocialAuthService.handle_whatsapp_callback,
    },
}

@router.get("/connect/{platform}", response_model=AuthURL)
async def get_authorization_url(platform: str, current_user: Dict[str, Any] = Depends(get_current_user_id)):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")
    
    auth_url = PLATFORMS[platform]["get_auth_url"]()
    return {"authorization_url": auth_url}


@router.get("/connect/{platform}/callback", response_model=TokenData)
async def handle_oauth_callback(platform: str, code: str = Query(...), current_user: Dict[str, Any] = Depends(get_current_user_id)):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")

    # Ici, nous allons stocker le token et créer/mettre à jour le social_account
    # Pour l'instant, nous retournons juste le token
    token_data = PLATFORMS[platform]["handle_callback"](code)
    
    # TODO: Utiliser l'ID utilisateur de `current_user['sub']` et les données du token
    # pour créer ou mettre à jour l'enregistrement dans la table social_accounts.

    return token_data 