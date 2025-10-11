from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List
import logging
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

from app.schemas.whatsapp import (
    TextMessageRequest,
    WhatsAppMessageResponse, WhatsAppCredentialsValidation,
    WhatsAppCredentials
)
from app.services.whatsapp_service import get_whatsapp_service, WhatsAppService
from app.services.response_manager import (
    get_user_credentials_by_platform_account,
    process_webhook_change_for_user,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger(__name__)

@router.post("/validate-credentials", response_model=WhatsAppCredentialsValidation)
async def validate_whatsapp_credentials(credentials: WhatsAppCredentials):
    """
    Validate the WhatsApp Business API credentials
    """
    try:
        async with WhatsAppService(credentials.access_token, credentials.phone_number_id) as service:
            validation_result = await service.validate_credentials()
            return WhatsAppCredentialsValidation(**validation_result)
    except Exception as e:
        logger.error(f"Error validation credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validation: {str(e)}"
        )

@router.post("/send-text", response_model=WhatsAppMessageResponse)
async def send_text_message(
    request: TextMessageRequest
):
    """
    Send a WhatsApp text message
    
    Uses the credentials of the connected user from the database
    """
    try:
        user_credentials = get_user_credentials_by_platform_account(platform="whatsapp", account_id=request.to)
        
        if not user_credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No WhatsApp account configured for this user"
            )
        service = await get_whatsapp_service(
            user_credentials["access_token"], 
            user_credentials["phone_number_id"]
        )
        
        result = await service.send_text_message(
            to=request.to,
            text=request.text,
            skip_validation=True  
        )
        
        return WhatsAppMessageResponse(
            messaging_product=result["messaging_product"],
            contacts=result["contacts"],
            messages=result["messages"],
            message_type="text"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error sending text message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify the WhatsApp webhook signature
    """
    if not secret:
        logger.warning("WHATSAPP_WEBHOOK_SECRET not configured - signature not verified")
        return True  
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature.replace('sha256=', '') if signature.startswith('sha256=') else signature
    
    return hmac.compare_digest(expected_signature, received_signature)

@router.get("/webhook")
async def webhook_verification(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"), 
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Verification of the WhatsApp webhook (activation step)
    
    Meta sends a GET request to verify that your endpoint is valid
    """
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    
    if not verify_token:
        logger.error("WHATSAPP_VERIFY_TOKEN not configured")
        raise HTTPException(status_code=500, detail="Verification token not configured")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook WhatsApp verified successfully")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning(f"Webhook WhatsApp verification failed: mode={hub_mode}, token_match={hub_verify_token == verify_token}")
    raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    Main handler for WhatsApp webhooks
    
    Receives:
    - Incoming messages from users
    - Statuts de livraison des messages envoyés
    - Read/write events
    """
    try:
        
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")

        webhook_secret = os.getenv("META_APP_SECRET")
        # TODO: Réactiver la vérification HMAC lorsque la configuration Meta sera stabilisée
        # if not verify_webhook_signature(payload, signature, webhook_secret):
        #     logger.warning("Signature webhook invalide")
        #     raise HTTPException(status_code=403, detail="Signature invalide")
        
        webhook_data = await request.json()
        logger.info(f"Webhook received: {webhook_data}")
        
        for entry in webhook_data.get("entry", []):
            await process_webhook_entry_with_user_routing(entry)
        
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}



async def process_webhook_entry_with_user_routing(entry: dict):
    """Process an entry of WhatsApp webhook with user routing"""
    phone_number_id = entry.get("changes")[0].get("value").get("metadata").get("phone_number_id")
    changes = entry.get("changes", [])

    credentials = await get_user_credentials_by_platform_account(platform="whatsapp", account_id=phone_number_id)

    if not credentials:
        logger.warning(f"No user found for WhatsApp account: {phone_number_id}")
        return

    user_info = {
        "user_id": str(credentials.get("user_id")) if credentials.get("user_id") else None,
        "social_account_id": str(credentials.get("id")),
        "account_id": credentials.get("account_id"),
        "phone_number_id": credentials.get("account_id"),
        "platform": "whatsapp",
        "access_token": credentials.get("access_token"),
        "display_name": credentials.get("display_name"),
        "username": credentials.get("username"),
    }

    logger.info(f"Webhook routed to user {user_info['user_id']} (phone: {phone_number_id})")
    
    
    for change in changes:
        await process_webhook_change_for_user(change, user_info)
