from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from supabase import Client
from jose import jwt, JWTError
from app.services.social_auth_service import social_auth_service
from app.schemas.social_account import AuthURL, SocialAccount, SocialAccountsResponse, SocialAccountWithStatus, PlatformStatus
from app.core.security import get_current_user_id
from app.core.config import get_settings, Settings
from app.db.session import get_authenticated_db
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

router = APIRouter(prefix="/social-accounts", tags=["social-accounts"])

PLATFORMS = {
    "instagram": {
        "get_auth_url": social_auth_service.get_instagram_auth_url,
        "handle_callback": social_auth_service.handle_instagram_callback,
        "get_profile": social_auth_service.get_instagram_business_account,
    },
    "reddit": {
        "get_auth_url": social_auth_service.get_reddit_auth_url,
        "handle_callback": social_auth_service.handle_reddit_callback,
        "get_profile": social_auth_service.get_reddit_profile,
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
    user_id: str = Depends(get_current_user_id)
):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")
    
    state_payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
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
    db: Client = Depends(get_authenticated_db),
    settings: Settings = Depends(get_settings)
):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")

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

    try:
        platform_config = PLATFORMS.get(platform)
        handle_callback_func = platform_config["handle_callback"]
        token_data = await handle_callback_func(code)
        
        get_profile_func = platform_config["get_profile"]
        profile_data = await get_profile_func(token_data["access_token"])
        
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 0))
        print(profile_data)
        social_account_data = {
            "platform": platform,
            "account_id": profile_data["id"],
            "username": profile_data["username"],
            "access_token": token_data["access_token"],
            "token_expires_at": token_expires_at.isoformat(),
            "user_id": user_id,
            "profile_url": profile_data.get("profile_picture_url"),
            "is_active": True,
        }
    
        db.table("social_accounts").upsert(
            social_account_data, 
            on_conflict="user_id, platform"
        ).execute()
        
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/accounts?success=true&platform={platform}")

    except HTTPException as e:
        error_message = urlencode({"error": e.detail, "platform": platform})
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/accounts?{error_message}")
    except Exception as e:
        print(f"Error upserting social account: {e}")
        error_message = urlencode({"error": "An unexpected error occurred while saving the account.", "platform": platform})
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/accounts?{error_message}")


@router.get("/", response_model=SocialAccountsResponse)
async def get_social_accounts(
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    try:
        # RLS applique automatiquement le filtre user_id = auth.uid()
        response = db.table("social_accounts").select("*").execute()
        
        accounts = []
        
        # Ajouter les comptes connectés
        for account_data in response.data:
            status = PlatformStatus.CONNECTED
            status_message = None
            
            # Vérifier l'expiration du token
            if account_data.get('token_expires_at'):
                expires_at = datetime.fromisoformat(account_data['token_expires_at'].replace('Z', '+00:00'))
                if expires_at <= datetime.now(timezone.utc):
                    status = PlatformStatus.EXPIRED
                    status_message = "Token expiré, reconnexion nécessaire"
            
            account = SocialAccountWithStatus(
                id=account_data['id'],
                platform=account_data['platform'],
                username=account_data.get('username'),
                account_id=account_data.get('account_id'),
                display_name=account_data.get('display_name'),
                profile_url=account_data.get('profile_url'),
                status=status,
                status_message=status_message,
                is_active=account_data.get('is_active', True),
                created_at=account_data.get('created_at'),
                updated_at=account_data.get('updated_at')
            )
            accounts.append(account)
        
        # Ajouter LinkedIn en stub s'il n'existe pas déjà
        existing_platforms = [acc.platform for acc in accounts]
        if 'linkedin' not in existing_platforms:
            linkedin_stub = SocialAccountWithStatus(
                platform='linkedin',
                username=None,
                account_id=None,
                display_name='LinkedIn Business',
                status=PlatformStatus.PENDING_SETUP,
                status_message='Configuration en cours - Disponible prochainement',
                is_active=False
            )
            accounts.append(linkedin_stub)
        
        return SocialAccountsResponse(
            accounts=accounts,
            total=len(accounts)
        )
        
    except Exception as e:
        print(f"Error getting social accounts: {e}")
        raise HTTPException(status_code=500, detail="Could not get social accounts.")


@router.delete("/{account_id}")
async def delete_social_account(
    account_id: str,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    try:
        # Vérifier que le compte appartient à l'utilisateur avant de le supprimer
        existing = db.table("social_accounts").select("*").eq("id", account_id).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Social account not found")

        # RLS assure que seul le propriétaire peut supprimer son compte
        db.table("social_accounts").delete().eq("id", account_id).execute()

        return {"message": "Social account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting social account: {e}")
        raise HTTPException(status_code=500, detail="Could not delete social account.")
