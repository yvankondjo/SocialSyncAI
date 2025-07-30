from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from jose import jwt, JWTError
from app.services.social_auth_service import social_auth_service
from app.schemas.social_account import AuthURL, TokenData, SocialAccountCreate
from app.core.security import get_current_user_id
from app.core.config import get_settings, Settings
from app.db.session import get_db
from typing import Dict, Any
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/social-accounts", tags=["social-accounts"])

PLATFORMS = {
    "instagram": {
        "get_auth_url": social_auth_service.get_instagram_auth_url,
        "handle_callback": social_auth_service.handle_instagram_callback,
        "get_profile": social_auth_service.get_instagram_business_account,
    },
    "linkedin": {
        "get_auth_url": social_auth_service.get_linkedin_auth_url,
        "handle_callback": social_auth_service.handle_linkedin_callback,
        "get_profile": social_auth_service.get_linkedin_business_profile,
    },
    "twitter": {
        "get_auth_url": social_auth_service.get_twitter_auth_url,
        "handle_callback": social_auth_service.handle_twitter_callback,
        "get_profile": social_auth_service.get_twitter_profile,
    },
    "tiktok": {
        "get_auth_url": social_auth_service.get_tiktok_auth_url,
        "handle_callback": social_auth_service.handle_tiktok_callback,
        "get_profile": social_auth_service.get_tiktok_profile,
    },
    "whatsapp": {
        "get_auth_url": social_auth_service.get_whatsapp_auth_url,
        "handle_callback": social_auth_service.handle_whatsapp_callback,
        "get_profile": social_auth_service.get_whatsapp_profile,
    },
}

@router.get("/connect/{platform}", response_model=AuthURL)
async def get_authorization_url(
    platform: str,
    settings: Settings = Depends(get_settings),
    current_user: Dict[str, Any] = Depends(get_current_user_id)
):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")
    
    user_id = current_user["id"]
    
    # Méthode de production : Créer un JWT de courte durée pour le paramètre 'state'
    state_payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15) # Expiration de 15 minutes
    }
    state_jwt = jwt.encode(
        state_payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.SUPABASE_JWT_ALGORITHM
    )

    auth_url_func = PLATFORMS[platform]["get_auth_url"]
    auth_url = auth_url_func(state=state_jwt)
    return {"authorization_url": auth_url}


@router.get("/connect/{platform}/callback")
async def handle_oauth_callback(
    platform: str, 
    code: str = Query(...),
    state: str = Query(...),
    db: Client = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")

    # Méthode de production : Décoder et valider le JWT reçu dans 'state'
    try:
        payload = jwt.decode(
            state,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.SUPABASE_JWT_ALGORITHM]
        )
        user_id: str = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid state parameter: user_id missing.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid state parameter: JWT could not be decoded.")

    platform_config = PLATFORMS.get(platform)
    if not platform_config:
         raise HTTPException(status_code=404, detail="Platform not supported")

    handle_callback_func = platform_config["handle_callback"]
    token_data = await handle_callback_func(code)
    
    # Appel dynamique à la fonction de récupération de profil
    get_profile_func = platform_config["get_profile"]
    profile_data = await get_profile_func(token_data["access_token"])
    
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])

    social_account_data = SocialAccountCreate(
        platform=platform,
        account_id=profile_data["id"],
        username=profile_data["username"],
        access_token=token_data["access_token"],
        token_expires_at=token_expires_at,
        user_id=user_id,
        profile_url=profile_data.get("profile_picture_url")
    )

    try:
        # On tente de sauvegarder les données
        db_response = db.table("social_accounts").upsert(
            social_account_data.model_dump(), 
            on_conflict="user_id, platform"
        ).execute()
        
        # On retourne seulement les données du premier (et unique) enregistrement affecté
        return db_response.data[0] if db_response.data else None

    except HTTPException as e:
        # Si l'erreur vient de notre logique (ex: compte business non trouvé), on la propage au frontend
        if e.status_code == 404 and "No Instagram Business Account" in e.detail:
            raise HTTPException(
                status_code=422, # Unprocessable Entity - plus sémantique
                detail="A professional Instagram account is required. Please convert your account and try again."
            )
        # On propage les autres erreurs HTTP
        raise e
    except Exception as e:
        # Pour toute autre erreur (ex: base de données)
        print(f"Error upserting social account: {e}")
        raise HTTPException(status_code=500, detail="Could not save social account details.") 