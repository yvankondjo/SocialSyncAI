import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.message_batcher import message_batcher
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)


async def get_user_credentials_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db

    try:
        db = get_db()
        res = db.table("social_accounts").select(
            "id, account_id, access_token, display_name, username, expires_at"
        ).eq("user_id", user_id).eq("platform", "whatsapp").order("created_at", desc=True).limit(1).execute()

        rows = res.data or []
        if rows:
            row = rows[0]
            return {
                "user_id": user_id,
                "social_account_id": str(row["id"]),
                "phone_number_id": row["account_id"],
                "access_token": row["access_token"],
                "display_name": row.get("display_name"),
                "username": row.get("username"),
            }

        logger.warning(f"Aucun compte WhatsApp trouvé pour l'utilisateur {user_id}")
        return None

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des credentials WhatsApp: {e}")
        return None


async def get_user_by_phone_number_id(phone_number_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db

    try:
        db = get_db()
        res = db.table("social_accounts").select(
            "id, user_id, access_token, display_name, username"
        ).eq("account_id", phone_number_id).limit(1).execute()
        rows = res.data or []

        if rows:
            row = rows[0]
            return {
                "user_id": str(row["user_id"]),
                "social_account_id": str(row["id"]),
                "phone_number_id": phone_number_id,
                "access_token": row["access_token"],
                "display_name": row.get("display_name"),
                "username": row.get("username"),
            }

        logger.warning(f"Aucun utilisateur trouvé pour phone_number_id: {phone_number_id}")
        return None

    except Exception as e:
        logger.error(f"Erreur lors de la récupération utilisateur WhatsApp: {e}")
        return None


async def handle_messages_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    for message in value.get("messages", []):
        await process_incoming_message_for_user(message, user_info)

    for status in value.get("statuses", []):
        await process_message_status_for_user(status, user_info)


async def process_incoming_message_for_user(message: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    message_type = message.get("type")
    message_id = await save_incoming_message_to_db(message, user_info)
    if not message_id:
        # Message déjà traité (idempotent) → ne pas continuer ni re-batcher
        return

    if message_type == "text":
        text_body = message.get("text", {}).get("body", "")
        await handle_text_message_for_user(message.get("from"), text_body, user_info)
    elif message_type in ["image", "video", "audio", "document"]:
        await handle_media_message_for_user(message, user_info)


async def handle_text_message_for_user(sender_phone: str, text: str, user_info: Dict[str, Any]) -> None:
    logger.info(f"Message texte pour {user_info['user_id']} de {sender_phone}: {text}")


async def handle_media_message_for_user(message: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    logger.info(f"Message média reçu pour l'utilisateur {user_info['user_id']}")


async def process_message_status_for_user(status: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    message_id = status.get("id")
    status_type = status.get("status")
    logger.info(f"Statut '{status_type}' pour message {message_id} (utilisateur: {user_info['user_id']})")
    await update_message_status_in_user_db(message_id, status_type, user_info)


async def update_message_status_in_user_db(message_id: str, status: str, user_info: Dict[str, Any]) -> None:
    logger.info(f"Mise à jour statut {status} pour message {message_id} (utilisateur: {user_info['user_id']})")


async def handle_delivery_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    logger.info(f"Webhook de livraison pour l'utilisateur {user_info['user_id']}")


async def handle_read_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    logger.info(f"Webhook de lecture pour l'utilisateur {user_info['user_id']}")


async def process_webhook_change_for_user(change: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    field = change.get("field")
    value = change.get("value", {})

    logger.info(f"Traitement du changement '{field}' pour l'utilisateur {user_info['user_id']}")

    if field == "messages":
        await handle_messages_webhook_for_user(value, user_info)
    elif field == "message_deliveries":
        await handle_delivery_webhook_for_user(value, user_info)
    elif field == "message_reads":
        await handle_read_webhook_for_user(value, user_info)
    else:
        logger.info(f"Type de webhook non géré: {field}")


async def save_incoming_message_to_db(message: Dict[str, Any], user_info: Dict[str, Any]) -> Optional[str]:
    from app.db.session import get_db

    try:
        db = get_db()
        conversation_id = await get_or_create_conversation(
            social_account_id=user_info["social_account_id"],
            customer_identifier=message.get("from"),
            customer_name=None,
        )

        if not conversation_id:
            return None

        message_data: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "external_message_id": message.get("id"),
            "direction": "inbound",
            "message_type": message.get("type", "text"),
            "content": extract_message_content(message),
            "sender_id": message.get("from"),
            "status": "received",
            "metadata": message,
        }

        try:
            res = db.table("conversation_messages").insert(message_data).execute()
            message_id = None
            if res and res.data:
                first = res.data[0]
                message_id = first.get("id") if first else None

            try:
                await message_batcher.add_message_to_batch(
                    platform="whatsapp",
                    account_id=user_info.get("phone_number_id"),
                    contact_id=message.get("from"),
                    message_data=message_data,
                    conversation_id=str(conversation_id),
                )
            except Exception as redis_error:
                logger.error(f"Erreur Redis batching (message sauvé en BDD): {redis_error}")

            return message_id

        except Exception as db_unique_error:
            if "unique_external_message_id" in str(db_unique_error).lower():
                logger.info(f"Message {message.get('id')} déjà traité pour utilisateur {user_info['user_id']}")
                return None
            raise db_unique_error

    except Exception as e:
        logger.error(f"Erreur sauvegarde message en BDD: {e}")
        return None


async def get_or_create_conversation(
    social_account_id: str,
    customer_identifier: str,
    customer_name: Optional[str] = None,
) -> Optional[str]:
    from app.db.session import get_db

    try:
        db = get_db()
        res_find = db.table("conversations").select("id").eq("social_account_id", social_account_id).eq("customer_identifier", customer_identifier).order("created_at", desc=True).limit(1).execute()
        rows = res_find.data or []
        if rows:
            return str(rows[0]["id"])

        insert_payload = {
            "social_account_id": social_account_id,
            "customer_identifier": customer_identifier,
            "customer_name": customer_name,
            "status": "open",
            "priority": "normal",
        }
        res_create = db.table("conversations").insert(insert_payload).execute()
        if res_create and res_create.data:
            first = res_create.data[0]
            return str(first.get("id")) if first and first.get("id") else None
        return None

    except Exception as e:
        logger.error(f"Erreur gestion conversation: {e}")
        return None


def extract_message_content(message: Dict[str, Any]) -> str:
    message_type = message.get("type", "text")

    if message_type == "text":
        return message.get("text", {}).get("body", "")
    if message_type == "image":
        caption = message.get("image", {}).get("caption", "")
        return f"[Image] {caption}".strip()
    if message_type == "video":
        caption = message.get("video", {}).get("caption", "")
        return f"[Video] {caption}".strip()
    if message_type == "audio":
        return "[Audio]"
    if message_type == "document":
        filename = message.get("document", {}).get("filename", "document")
        return f"[Document: {filename}]"
    if message_type == "location":
        location = message.get("location", {})
        return f"[Location: {location.get('latitude', 0)}, {location.get('longitude', 0)}]"
    if message_type == "contacts":
        return "[Contact]"
    return f"[{message_type.upper()}]"


# ==================== Génération et envoi de réponses (auto) ====================

async def generate_smart_response(messages: List[Dict[str, Any]], context: List[Dict[str, Any]], platform: str) -> Optional[str]:
    contents: List[str] = []
    for msg in messages:
        content = msg.get("message_data", {}).get("content", "")
        if content:
            contents.append(content)
    if not contents:
        return None
    if len(contents) > 1:
        recent_content = " ".join(contents[-3:])
        return f"J'ai bien reçu tes messages. Tu mentionnes: {recent_content}. Comment puis-je t'aider avec ça ?"
    content = contents[0]
    return f"Merci pour ton message : \"{content}\". Comment puis-je t'assister ?"


async def get_user_credentials_by_platform_account(platform: str, account_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db

    try:
        if platform not in ("facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "whatsapp"):
            logger.error(f"Platform {platform} non supportée")
            return None

        db = get_db()
        res = db.table("social_accounts").select("*").eq("platform", platform).eq("account_id", account_id).eq("is_active", True).limit(1).execute()
        rows = res.data or []
        if rows:
            return rows[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des credentials {platform}:{account_id}: {e}")
    return None


async def send_response(platform: str, user_credentials: Dict[str, Any], contact_id: str, content: str) -> bool:
    try:
        if platform == "whatsapp":
            service = WhatsAppService(
                user_credentials.get("access_token"),
                user_credentials.get("account_id") or user_credentials.get("phone_number_id"),
            )
            result = await service.send_text_message(to=contact_id, text=content, skip_validation=True)
            return bool(result.get("messages"))

        if platform == "instagram":
            service = InstagramService()
            result = await service.send_direct_message(
                user_credentials["instagram_business_account_id"],
                user_credentials["access_token"],
                contact_id,
                content,
            )
            return result.get("success", False)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de réponse {platform}: {e}")
    return False


async def save_response_to_db(conversation_id: str, content: str, user_id: str) -> None:
    from app.db.session import get_db

    try:
        db = get_db()
        payload = {
            "conversation_id": conversation_id,
            "direction": "outbound",
            "content": content,
            "message_type": "text",
            "is_from_agent": False,
            "agent_id": user_id,
            "sender_id": "user",
            "metadata": {"auto_generated": True, "batch_response": True},
        }
        db.table("conversation_messages").insert(payload).execute()
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de réponse en BDD: {e}")


