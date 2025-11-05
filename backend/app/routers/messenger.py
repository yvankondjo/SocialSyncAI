from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import PlainTextResponse
import logging
import hmac
import hashlib
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

from app.services.messenger_service import get_messenger_service, MessengerService
from app.services.response_manager import (
    process_incoming_message_for_user,
    get_user_credentials_by_platform_account,
)

router = APIRouter(prefix="/messenger", tags=["Messenger"])
logger = logging.getLogger(__name__)


def verify_messenger_webhook_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    """
    Verify Messenger webhook signature using HMAC-SHA256.

    Facebook/Meta signs all webhook payloads with SHA256 and includes the signature
    in X-Hub-Signature-256 header, preceded with 'sha256='.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (e.g., 'sha256=abc123...')
        secret: META_APP_SECRET from Meta for Developers dashboard

    Returns:
        True if signature is valid, False otherwise

    Raises:
        RuntimeError: If META_APP_SECRET is not configured (security requirement)
    """
    if not secret:
        logger.error("🚨 CRITICAL: META_APP_SECRET not configured - webhook validation impossible")
        raise RuntimeError(
            "META_APP_SECRET must be configured for webhook security. "
            "Get it from Meta for Developers > App Settings > Basic > App Secret"
        )

    # Generate expected HMAC-SHA256 signature
    expected_signature = hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()

    # Extract received signature (remove 'sha256=' prefix if present)
    received_signature = (
        signature.replace("sha256=", "")
        if signature.startswith("sha256=")
        else signature
    )

    # Secure constant-time comparison (prevents timing attacks)
    is_valid = hmac.compare_digest(expected_signature, received_signature)

    if not is_valid:
        logger.warning(
            f"❌ Invalid Messenger webhook signature. "
            f"Expected: {expected_signature[:16]}..., "
            f"Received: {received_signature[:16]}..."
        )

    return is_valid


@router.get("/webhook")
async def messenger_webhook_verification(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    """
    Verification of the Messenger webhook (activation step).

    Meta sends a GET request to verify that your endpoint is valid.
    You must return the hub.challenge value to complete verification.

    Required env var: MESSENGER_VERIFY_TOKEN
    """
    verify_token = os.getenv("MESSENGER_VERIFY_TOKEN")

    if not verify_token:
        logger.error("MESSENGER_VERIFY_TOKEN not configured")
        raise HTTPException(status_code=500, detail="Verification token not configured")

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("✅ Messenger webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)

    logger.warning(
        f"❌ Messenger webhook verification failed: mode={hub_mode}, token_match={hub_verify_token == verify_token}"
    )
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def messenger_webhook_handler(request: Request):
    """
    Main handler for Facebook Messenger webhooks.

    Receives:
    - Incoming messages from users
    - Message delivery confirmations
    - Message read receipts
    - Messaging postbacks (button clicks)

    Security: Validates HMAC-SHA256 signature using META_APP_SECRET
    """
    try:
        payload = await request.body()
        signature = request.headers.get(
            "X-Hub-Signature-256", ""
        ) or request.headers.get("X-Hub-Signature", "")
        webhook_secret = os.getenv("META_APP_SECRET")

        # ✅ SECURITY: HMAC-SHA256 signature validation ENABLED
        # Prevents webhook forgery attacks - CRITICAL for production
        if not verify_messenger_webhook_signature(payload, signature, webhook_secret):
            logger.error("❌ Messenger webhook signature validation FAILED - request rejected")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature - verify META_APP_SECRET configuration"
            )

        webhook_data = await request.json()
        logger.info(f"📨 Messenger webhook received: {webhook_data.get('object', 'unknown')}")

        # Messenger webhook structure:
        # {
        #   "object": "page",
        #   "entry": [
        #     {
        #       "id": "page_id",
        #       "time": 1234567890,
        #       "messaging": [
        #         {
        #           "sender": {"id": "psid"},
        #           "recipient": {"id": "page_id"},
        #           "timestamp": 1234567890,
        #           "message": {...}
        #         }
        #       ]
        #     }
        #   ]
        # }

        for entry in webhook_data.get("entry", []):
            logger.info(f"Processing Messenger webhook entry for Page ID: {entry.get('id')}")
            await process_messenger_webhook_entry_with_user_routing(entry)

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing Messenger webhook: {e}", exc_info=True)
        # Return 200 to prevent Meta from retrying (we logged the error)
        return {"status": "error", "message": str(e)}


async def process_messenger_webhook_entry_with_user_routing(entry: Dict[str, Any]):
    """
    Process a Messenger webhook entry with user routing.

    Args:
        entry: Webhook entry dict containing Page ID and messaging events
    """
    page_id = entry.get("id")
    messaging = entry.get("messaging", [])

    # Find user credentials for this Facebook Page
    credentials = await get_user_credentials_by_platform_account(
        platform="messenger", account_id=page_id
    )

    if not credentials:
        logger.warning(
            f"⚠️ No user found for Facebook Page ID: {page_id}. "
            "Make sure the Page is connected via /social-accounts/connect/messenger"
        )
        return

    user_info = {
        "user_id": (
            str(credentials.get("user_id")) if credentials.get("user_id") else None
        ),
        "social_account_id": str(credentials.get("id")),
        "page_id": page_id,
        "account_id": page_id,
        "platform": "messenger",
        "access_token": credentials.get("access_token"),
        "display_name": credentials.get("display_name"),
        "username": credentials.get("username"),
    }

    logger.info(
        f"✅ Messenger webhook routed to user {user_info['user_id']} (Page: {page_id})"
    )

    # Process each messaging event in the entry
    for message_event in messaging:
        await process_messenger_message_event(message_event, user_info)


async def process_messenger_message_event(message_event: Dict[str, Any], user_info: Dict[str, Any]):
    """
    Process a Messenger messaging event (message, delivery, read, etc.).

    Args:
        message_event: Messaging event dict from webhook
        user_info: User credentials and account info
    """
    try:
        # Handle incoming messages
        if "message" in message_event:
            message = message_event["message"]

            # ⚠️ CRITICAL: Ignore echo messages (sent BY the page, not TO the page)
            # is_echo: True means the message was sent by the page itself
            if message.get("is_echo", False):
                logger.info(
                    f"Ignoring echo message (sent by page): {message.get('text', '')[:50] if message.get('text') else 'media message'}"
                )
                return

            # Extract sender information
            sender = message_event.get("sender", {})
            sender_psid = sender.get("id")

            if not sender_psid:
                logger.warning("⚠️ Messenger message event missing sender ID")
                return

            # Build contact info (we don't have username in webhook, will fetch if needed)
            contact_info = {
                "id": sender_psid,
                "name": f"User_{sender_psid[:8]}"  # Default name, will be enriched by response_manager
            }

            # Format message for unified processing
            formatted_message = {
                "id": message.get("mid"),
                "from": sender_psid,
                "timestamp": message_event.get("timestamp"),
                **message,
                "_contact_info": contact_info
            }

            logger.info(
                f"📨 Processing Messenger message from {sender_psid}: {message.get('text', '')[:50] if message.get('text') else message.keys()}"
            )

            # Process through unified message pipeline
            await process_incoming_message_for_user(formatted_message, user_info)

        # Handle message delivery confirmations
        elif "delivery" in message_event:
            delivery = message_event["delivery"]
            logger.debug(f"📬 Message delivery confirmed: {delivery.get('mids', [])}")
            # TODO: Update message status to 'delivered' in database

        # Handle message read receipts
        elif "read" in message_event:
            read = message_event["read"]
            logger.debug(f"👁️ Message read: watermark={read.get('watermark')}")
            # TODO: Update message status to 'read' in database

        # Handle postbacks (button clicks, get started, etc.)
        elif "postback" in message_event:
            postback = message_event["postback"]
            payload = postback.get("payload")
            logger.info(f"🔘 Postback received: {payload}")
            # TODO: Handle postback actions (e.g., menu buttons, get started button)

    except Exception as e:
        logger.error(f"❌ Error processing Messenger message event: {e}", exc_info=True)


@router.post("/send-message")
async def send_messenger_message(
    page_id: str,
    access_token: str,
    recipient_psid: str,
    text: str
):
    """
    Send a message via Messenger Send API.

    Args:
        page_id: Facebook Page ID
        access_token: Page access token
        recipient_psid: Recipient's page-scoped ID
        text: Message text to send

    Returns:
        Dict with success status and message_id
    """
    try:
        service = await get_messenger_service(access_token, page_id)
        result = await service.send_message(recipient_psid, text)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send message: {result.get('error')}"
            )

        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient_id": result.get("recipient_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending Messenger message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}",
        )


@router.post("/validate-credentials")
async def validate_messenger_credentials(
    page_id: str,
    access_token: str
):
    """
    Validate Messenger Page credentials.

    Args:
        page_id: Facebook Page ID
        access_token: Page access token

    Returns:
        Dict with 'valid' bool and 'account_info' or 'error'
    """
    try:
        async with MessengerService(access_token, page_id) as service:
            validation_result = await service.validate_credentials()
            return validation_result
    except Exception as e:
        logger.error(f"❌ Error validating Messenger credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating credentials: {str(e)}",
        )


@router.get("/health")
async def messenger_health_check():
    """Check the health of the Messenger service."""
    try:
        # Try to get service from environment variables
        service = await get_messenger_service()

        if not service:
            return {
                "service": "messenger",
                "status": "not_configured",
                "message": "MESSENGER_ACCESS_TOKEN and MESSENGER_PAGE_ID not set"
            }

        validation = await service.validate_credentials()

        return {
            "service": "messenger",
            "status": "healthy" if validation["valid"] else "unhealthy",
            "details": validation,
        }
    except Exception as e:
        logger.error(f"❌ Error in Messenger health check: {e}")
        return {"service": "messenger", "status": "unhealthy", "error": str(e)}
