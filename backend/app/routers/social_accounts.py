from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from supabase import Client
from jose import jwt, JWTError
from app.services.social_auth_service import social_auth_service
from app.schemas.social_account import AuthURL, SocialAccount
from app.core.security import get_current_user_id
from app.core.config import get_settings, Settings
from app.db.session import get_authenticated_db, get_db
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social-accounts", tags=["social-accounts"])

PLATFORMS = {
    "instagram": {
        "get_auth_url": social_auth_service.get_instagram_auth_url,
        "handle_callback": social_auth_service.handle_instagram_callback,
        "get_profile": social_auth_service.get_instagram_business_account,
    },
    "whatsapp": {
        "get_auth_url": social_auth_service.get_whatsapp_embedded_signup_url,
        "handle_callback": social_auth_service.handle_whatsapp_callback,
        "get_phone_profile": social_auth_service.get_whatsapp_phone_profile,
        "exchange_code": social_auth_service.exchange_whatsapp_code,
        "get_business_accounts": social_auth_service.get_whatsapp_business_accounts,
    },
    "messenger": {
        "get_auth_url": social_auth_service.get_messenger_auth_url,
        "handle_callback": social_auth_service.handle_messenger_callback,
        "get_pages": social_auth_service.get_facebook_pages,
        "subscribe_webhooks": social_auth_service.subscribe_page_to_webhooks,
    },
}


async def _upsert_whatsapp_account(
    db: Client,
    user_id: str,
    access_token: str,
    expires_in: Optional[int],
    phone_number_id: Optional[str],
    waba_id: Optional[str],
    display_phone: Optional[str],
    verified_name: Optional[str],
    business_id: Optional[str]
) -> Dict[str, Any]:
    profile_data: Dict[str, Any] = {}
    if phone_number_id:
        try:
            profile_data = await social_auth_service.get_whatsapp_phone_profile(access_token, phone_number_id)
            display_phone = display_phone or profile_data.get("display_phone_number")
            verified_name = verified_name or profile_data.get("verified_name")
        except HTTPException:
            # continue with available data
            profile_data = {}

    username = verified_name or display_phone or phone_number_id or "whatsapp_account"
    display_name = display_phone or verified_name or username

    wa_link = None
    if display_phone:
        digits = re.sub(r"\D", "", display_phone)
        if digits:
            wa_link = f"https://wa.me/{digits}"

    token_expires_at = None
    if expires_in:
        token_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    social_account_data = {
        "platform": "whatsapp",
        "account_id": phone_number_id or (waba_id or ""),
        "username": username,
        "display_name": display_name,
        "profile_url": wa_link,
        "access_token": access_token,
        "refresh_token": waba_id,
        "token_expires_at": token_expires_at,
        "user_id": user_id,
        "is_active": True,
    }

    db.table("social_accounts").upsert(
        social_account_data,
        on_conflict="user_id, platform"
    ).execute()

    if waba_id:
        await social_auth_service.subscribe_whatsapp_webhooks(access_token, waba_id)

    result = db.table("social_accounts").select("*").eq("user_id", user_id).eq("platform", "whatsapp").limit(1).execute()
    if result.data:
        return result.data[0]
    return social_account_data

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

    platform_config = PLATFORMS[platform]
    auth_url_func = platform_config["get_auth_url"]
    auth_url = auth_url_func(state=state_jwt)
    return {"authorization_url": auth_url}


@router.get("/connect/{platform}/callback")
async def handle_oauth_callback(
    platform: str,
    code: Optional[str] = Query(None),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Client = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Platform not supported")

    if error:
        error_payload = urlencode({
            "error": error_description or error,
            "platform": platform
        })
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/accounts?{error_payload}")

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

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing from callback.")

    try:
        platform_config = PLATFORMS.get(platform)
        token_data = await platform_config["handle_callback"](code)

        if platform == "whatsapp":
            logger.info("📥 WhatsApp callback - Échange du code...")
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in")
            
            logger.info("🔍 Récupération des comptes WhatsApp Business...")
            accounts = await platform_config["get_business_accounts"](access_token)
            if not accounts:
                logger.error("❌ Aucun compte WhatsApp Business trouvé")
                raise HTTPException(status_code=400, detail="No WhatsApp Business Account accessible for this user.")
            
            logger.info(f"✅ {len(accounts)} compte(s) trouvé(s)")
            account = accounts[0]
            waba_id = account.get("id")
            business_id = account.get("business_id")
            phone_numbers = account.get("phone_numbers", {}).get("data", []) if isinstance(account.get("phone_numbers"), dict) else account.get("phone_numbers", [])
            phone_entry = phone_numbers[0] if phone_numbers else {}
            phone_number_id = phone_entry.get("phone_number_id") or phone_entry.get("id")
            display_phone = phone_entry.get("display_phone_number")
            verified_name = phone_entry.get("verified_name")
            
            logger.info(f"📋 Infos extraites - WABA: {waba_id}, Phone: {phone_number_id}, Display: {display_phone}")

            logger.info("💾 Sauvegarde dans Supabase...")
            await _upsert_whatsapp_account(
                db=db,
                user_id=user_id,
                access_token=access_token,
                expires_in=expires_in,
                phone_number_id=phone_number_id,
                waba_id=waba_id,
                display_phone=display_phone,
                verified_name=verified_name,
                business_id=business_id,
            )

            logger.info(f"✅ Compte WhatsApp enregistré avec succès pour user {user_id}")
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/accounts?success=true&platform={platform}")

        if platform == "messenger":
            logger.info("📥 Messenger callback - Échange du code...")
            user_access_token = token_data["access_token"]

            # Get all Pages managed by user
            logger.info("🔍 Récupération des Pages Facebook...")
            get_pages_func = platform_config.get("get_pages")
            if not get_pages_func:
                raise HTTPException(status_code=500, detail="Page retrieval not configured for Messenger.")

            pages = await get_pages_func(user_access_token)

            if not pages:
                logger.error("❌ Aucune Page Facebook accessible pour cet utilisateur")
                raise HTTPException(status_code=400, detail="No Facebook Pages accessible for this user. Make sure you manage at least one Page.")

            logger.info(f"✅ {len(pages)} Page(s) trouvée(s)")

            # Auto-connect all Pages
            connected_pages = []
            subscribe_webhooks_func = platform_config.get("subscribe_webhooks")

            for page in pages:
                page_id = page.get("id")
                page_name = page.get("name")
                page_access_token = page.get("access_token")
                page_category = page.get("category", "")

                logger.info(f"📋 Connexion de la Page: {page_name} (ID: {page_id})")

                # Store each Page as separate social_account
                token_expires_at = None  # Page tokens typically don't expire unless revoked

                page_account_data = {
                    "platform": "messenger",
                    "account_id": page_id,
                    "account_name": page_name,
                    "username": page_name,
                    "display_name": page_name,
                    "access_token": page_access_token,
                    "token_expires_at": token_expires_at,
                    "user_id": user_id,
                    "is_active": True,
                    "metadata": {
                        "category": page_category,
                        "tasks": page.get("tasks", [])
                    }
                }

                # Upsert page account
                db.table("social_accounts").upsert(
                    page_account_data,
                    on_conflict="user_id,platform,account_id"
                ).execute()

                # Subscribe Page to webhooks
                if subscribe_webhooks_func:
                    webhook_result = await subscribe_webhooks_func(page_id, page_access_token)
                    if webhook_result.get("success") is False:
                        logger.warning(f"⚠️ Webhook subscription failed for Page {page_name}: {webhook_result.get('error')}")
                    else:
                        logger.info(f"✅ Page {page_name} subscribed to webhooks")

                connected_pages.append(page_name)

            logger.info(f"✅ {len(connected_pages)} Pages Messenger connectées avec succès pour user {user_id}")
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/accounts?success=true&platform={platform}&count={len(connected_pages)}")

        # Default OAuth flow for other platforms (Instagram, etc.)
        get_profile_func = platform_config.get("get_profile")
        if not get_profile_func:
            raise HTTPException(status_code=500, detail="Profile retrieval not configured for this platform.")

        profile_data = await get_profile_func(token_data["access_token"])

        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 0))
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


@router.get("/", response_model=list[SocialAccount])
async def get_social_accounts(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        # RLS applique automatiquement le filtre user_id = auth.uid()
        response = db.table("social_accounts").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting social accounts for user {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not get social accounts.")


@router.delete("/{account_id}")
async def delete_social_account(
    account_id: str,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
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
        logger.error(f"Error deleting social account {account_id} for user {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not delete social account.")
