from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import PlainTextResponse
import logging
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

from app.schemas.instagram import (
    DirectMessageRequest, FeedPostRequest, StoryRequest, CommentReplyRequest,
    InstagramCredentials, InstagramCredentialsValidation,
    InstagramMessageResponse,
    ConversationsResponse, CommentReplyResponse
)
from app.services.instagram_service import get_instagram_service, InstagramService
from app.services.response_manager import  process_incoming_message_for_user,get_user_credentials_by_platform_account

router = APIRouter(prefix="/instagram", tags=["Instagram"])
logger = logging.getLogger(__name__)

@router.post("/validate-credentials", response_model=InstagramCredentialsValidation)
async def validate_instagram_credentials(credentials: InstagramCredentials):
    """Valider les credentials Instagram Business API"""
    try:
        async with InstagramService(credentials.access_token, credentials.page_id) as service:
            validation_result = await service.validate_credentials()
            return InstagramCredentialsValidation(**validation_result)
    except Exception as e:
        logger.error(f"Error validation Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validation: {str(e)}"
        )

@router.post("/send-dm", response_model=InstagramMessageResponse)
async def send_direct_message(request: DirectMessageRequest):
    """Send a direct message Instagram"""
    try:
        service = await get_instagram_service(request.access_token, request.page_id)
        result = await service.send_direct_message(request.recipient_ig_id, request.text)
        
        return InstagramMessageResponse(
            success=True,
            message_id=result.get("message_id")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error send DM Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error send DM: {str(e)}"
        )


@router.post("/reply-comment", response_model=CommentReplyResponse)
async def reply_to_comment(request: CommentReplyRequest):
    """Reply to a comment Instagram"""
    try:
        service = await get_instagram_service(request.access_token, request.page_id)
        result = await service.reply_to_comment(request.comment_id, request.message)
        
        return CommentReplyResponse(
            success=True,
            reply_id=result.get("id")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error reply comment Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reply: {str(e)}"
        )

@router.get("/conversations", response_model=ConversationsResponse)
async def get_conversations(
    access_token: str = None,
    page_id: str = None,
    limit: int = 25
):
    """Get the conversations of direct messages"""
    try:
        service = await get_instagram_service(access_token, page_id)
        result = await service.get_conversations(limit)
        return ConversationsResponse(**result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error get conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error conversations: {str(e)}"
        )


@router.get("/health")
async def instagram_health_check():
    """Check the health of the Instagram service"""
    try:
        service = await get_instagram_service()
        validation = await service.validate_credentials()
        
        return {
            "service": "instagram",
            "status": "healthy" if validation["valid"] else "unhealthy",
            "details": validation
        }
    except Exception as e:
        logger.error(f"Error health check Instagram: {e}")
        return {
            "service": "instagram",
            "status": "unhealthy",
            "error": str(e)
        }



# ==================== WEBHOOKS INSTAGRAM ====================

def verify_instagram_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Check the signature of the Instagram webhook according to the Meta documentation"""
    if not secret:
        logger.warning("META_APP_SECRET non configuré - signature non vérifiée")
        return True

    # Generate the HMAC-SHA256 signature as specified in the Meta doc
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Extract the received signature (after sha256=)
    received_signature = signature.replace('sha256=', '') if signature.startswith('sha256=') else signature

    # Compare securely
    return hmac.compare_digest(expected_signature, received_signature)

@router.get("/webhook")
async def instagram_webhook_verification(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"), 
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Verification of the Instagram webhook (activation step)
    
    Meta sends a GET request to verify that your endpoint is valid
    """
    verify_token = os.getenv("INSTAGRAM_VERIFY_TOKEN")
    
    if not verify_token:
        logger.error("INSTAGRAM_VERIFY_TOKEN not configured")
        raise HTTPException(status_code=500, detail="Verification token not configured")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook Instagram verified successfully")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning(f"Webhook Instagram verification failed: mode={hub_mode}, token_match={hub_verify_token == verify_token}")
    raise HTTPException(status_code=403, detail="Invalid verification token")

@router.post("/webhook")
async def instagram_webhook_handler(request: Request):
    """
    Main handler for Instagram webhooks
    
    Receives:
    - Incoming direct messages
    - Comments on posts
    - Mentions in stories
    - Follow/unfollow events
    """
    try:
        
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "") or request.headers.get("X-Hub-Signature", "")
        webhook_secret = os.getenv("META_APP_SECRET")
        if not webhook_secret:
            logger.warning("META_APP_SECRET not configured - webhook ignored for security")
            raise HTTPException(status_code=403, detail="Configuration webhook manquante")

        # HMAC validation for security (re-enabled 2025-10-20)
        if not verify_instagram_webhook_signature(payload, signature, webhook_secret):
            logger.warning("Invalid Instagram webhook signature - check META_APP_SECRET in Meta for Developers")
            raise HTTPException(status_code=403, detail="Invalid signature")

        webhook_data = await request.json()
        logger.info(f"Webhook Instagram received: {webhook_data}")
        
        for entry in webhook_data.get("entry", []):
            logger.info(f"Processing Instagram webhook for entry: {entry}")
            await process_instagram_webhook_entry_with_user_routing(entry)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing Instagram webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_instagram_webhook_entry_with_user_routing(entry: dict):
    """Process an entry of Instagram webhook with user routing"""
    instagram_business_account_id = entry.get("id")
    messaging = entry.get("messaging", [])

    credentials = await get_user_credentials_by_platform_account(platform="instagram", account_id=instagram_business_account_id)

    if not credentials:
        logger.warning(f"No user found for Instagram Business Account: {instagram_business_account_id}")
        return

    user_info = {
        "user_id": str(credentials.get("user_id")) if credentials.get("user_id") else None,
        "social_account_id": str(credentials.get("id")),
        "instagram_business_account_id": credentials.get("account_id"),
        "account_id": credentials.get("account_id"),
        "platform": "instagram",
        "access_token": credentials.get("access_token"),
        "display_name": credentials.get("display_name"),
        "username": credentials.get("username"),
    }

    logger.info(f"Webhook Instagram routed to user {user_info['user_id']} (account: {instagram_business_account_id})")

    for message_event in messaging:
        await process_instagram_message_event(message_event, user_info)


async def process_instagram_message_event(message_event: dict, user_info: dict):
    """Process an Instagram messaging event (direct message, comment, etc.)"""
    try:
        if 'message' in message_event:
            # Extract sender information from the webhook
            sender = message_event.get('sender', {})
            sender_id = sender.get('id')
            message = message_event['message']

            # Build contact info from sender data
            contact_info = None
            if sender_id:
                sender_username = sender.get('username') or sender.get('name')
                if sender_username:
                    contact_info = {
                        'name': sender_username,
                        'id': sender_id
                    }

            formatted_message = {
                'id': message.get('mid'),
                'from': sender_id,
                'timestamp': message_event.get('timestamp'),
                **message
            }

            # Add contact info if available
            if contact_info:
                formatted_message['_contact_info'] = contact_info

            await process_incoming_message_for_user(formatted_message, user_info)
    except Exception as e:
        logger.error(f"Error processing Instagram messaging event: {e}")



