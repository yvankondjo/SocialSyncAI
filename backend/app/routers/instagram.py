from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import PlainTextResponse
from typing import List
import logging
import hmac
import hashlib
import os

from app.schemas.instagram import (
    DirectMessageRequest, FeedPostRequest, StoryRequest, CommentReplyRequest,
    InstagramCredentials, InstagramCredentialsValidation,
    InstagramMessageResponse, InstagramPostResponse, InstagramStoryResponse,
    ConversationsResponse, CommentReplyResponse, BatchDirectMessageRequest, BatchResponse
)
from app.services.instagram_service import get_instagram_service, InstagramService
from app.services.message_batcher import message_batcher
from app.services.response_manager import get_or_create_conversation

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
        logger.error(f"Erreur validation Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur validation: {str(e)}"
        )

@router.post("/send-dm", response_model=InstagramMessageResponse)
async def send_direct_message(request: DirectMessageRequest):
    """Envoyer un message direct Instagram"""
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
        logger.error(f"Erreur envoi DM Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur envoi DM: {str(e)}"
        )

@router.post("/publish-post", response_model=InstagramPostResponse)
async def publish_feed_post(request: FeedPostRequest):
    """Publier un post sur le feed Instagram"""
    try:
        service = await get_instagram_service(request.access_token, request.page_id)
        result = await service.publish_feed_post(request.image_url, request.caption)
        
        return InstagramPostResponse(
            success=result["success"],
            post_id=result["post_id"],
            container_id=result["container_id"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur publication post Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur publication: {str(e)}"
        )

@router.post("/publish-story", response_model=InstagramStoryResponse)
async def publish_story(request: StoryRequest):
    """Publier une story Instagram"""
    try:
        service = await get_instagram_service(request.access_token, request.page_id)
        result = await service.publish_story(request.image_url)
        
        return InstagramStoryResponse(
            success=result["success"],
            story_id=result["story_id"],
            container_id=result["container_id"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur publication story Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur story: {str(e)}"
        )

@router.post("/reply-comment", response_model=CommentReplyResponse)
async def reply_to_comment(request: CommentReplyRequest):
    """Répondre à un commentaire Instagram"""
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
        logger.error(f"Erreur réponse commentaire Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur réponse: {str(e)}"
        )

@router.get("/conversations", response_model=ConversationsResponse)
async def get_conversations(
    access_token: str = None,
    page_id: str = None,
    limit: int = 25
):
    """Récupérer les conversations de messages directs"""
    try:
        service = await get_instagram_service(access_token, page_id)
        result = await service.get_conversations(limit)
        return ConversationsResponse(**result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur récupération conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur conversations: {str(e)}"
        )

@router.post("/send-batch-dm", response_model=BatchResponse)
async def send_batch_direct_messages(request: BatchDirectMessageRequest):
    """Envoyer plusieurs messages directs en lot"""
    try:
        service = await get_instagram_service(request.access_token, request.page_id)
        
        results = []
        successful = 0
        failed = 0
        
        for message in request.messages:
            try:
                result = await service.send_direct_message(
                    message.recipient_ig_id,
                    message.text
                )
                results.append({
                    "recipient": message.recipient_ig_id,
                    "success": True,
                    "message_id": result.get("message_id"),
                    "result": result
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "recipient": message.recipient_ig_id,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
                logger.error(f"Erreur DM batch vers {message.recipient_ig_id}: {e}")
        
        return BatchResponse(
            total_messages=len(request.messages),
            successful_messages=successful,
            failed_messages=failed,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Erreur batch DM Instagram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur batch: {str(e)}"
        )

@router.get("/health")
async def instagram_health_check():
    """Vérifier la santé du service Instagram"""
    try:
        service = await get_instagram_service()
        validation = await service.validate_credentials()
        
        return {
            "service": "instagram",
            "status": "healthy" if validation["valid"] else "unhealthy",
            "details": validation
        }
    except Exception as e:
        logger.error(f"Erreur health check Instagram: {e}")
        return {
            "service": "instagram",
            "status": "unhealthy",
            "error": str(e)
        }

# Routes utilitaires
@router.get("/capabilities")
async def get_instagram_capabilities():
    """Lister les fonctionnalités Instagram disponibles"""
    return {
        "messaging": [
            "send-dm - Envoyer message direct",
            "send-batch-dm - Messages directs en lot",
            "conversations - Lister les conversations"
        ],
        "publishing": [
            "publish-post - Publier post feed",
            "publish-story - Publier story",
            "reply-comment - Répondre aux commentaires"
        ],
        "analytics": [
            "conversations - Statistiques de conversations",
            "media-insights - Statistiques de posts (à venir)"
        ],
        "requirements": [
            "Instagram Business Account",
            "Page Facebook liée",
            "Token d'accès avec permissions appropriées"
        ]
    }

@router.get("/setup-guide")
async def get_setup_guide():
    """Guide de configuration Instagram Business API"""
    return {
        "steps": [
            "1. Créer une app Facebook/Meta for Developers",
            "2. Configurer le produit Instagram Basic Display",
            "3. Ajouter Instagram Business Account",
            "4. Générer un token d'accès longue durée",
            "5. Récupérer l'ID de la page Instagram Business"
        ],
        "required_permissions": [
            "instagram_basic",
            "instagram_content_publish",
            "instagram_manage_messages",
            "instagram_manage_comments",
            "pages_read_engagement",
            "pages_manage_metadata"
        ],
        "env_variables": {
            "INSTAGRAM_ACCESS_TOKEN": "Token d'accès longue durée",
            "INSTAGRAM_PAGE_ID": "ID de la page Instagram Business"
        },
        "test_endpoint": "/api/instagram/validate-credentials"
    }

# ==================== WEBHOOKS INSTAGRAM ====================

def verify_instagram_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Vérifier la signature du webhook Instagram"""
    if not secret:
        logger.warning("INSTAGRAM_WEBHOOK_SECRET non configuré - signature non vérifiée")
        return True
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Instagram envoie la signature au format "sha256=..."
    received_signature = signature.replace('sha256=', '') if signature.startswith('sha256=') else signature
    
    return hmac.compare_digest(expected_signature, received_signature)

@router.get("/webhook")
async def instagram_webhook_verification(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"), 
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Vérification du webhook Instagram (étape d'activation)
    
    Meta envoie une requête GET pour vérifier que votre endpoint est valide
    """
    verify_token = os.getenv("INSTAGRAM_VERIFY_TOKEN")
    
    if not verify_token:
        logger.error("INSTAGRAM_VERIFY_TOKEN non configuré")
        raise HTTPException(status_code=500, detail="Token de vérification non configuré")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook Instagram vérifié avec succès")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning(f"Échec vérification webhook Instagram: mode={hub_mode}, token_match={hub_verify_token == verify_token}")
    raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.post("/webhook")
async def instagram_webhook_handler(request: Request):
    """
    Gestionnaire principal des webhooks Instagram
    
    Reçoit :
    - Messages directs entrants
    - Commentaires sur les posts
    - Mentions dans les stories
    - Événements de suivi (follow/unfollow)
    """
    try:
        # Récupérer le payload et les headers
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Vérifier la signature (sécurité)
        webhook_secret = os.getenv("INSTAGRAM_WEBHOOK_SECRET")
        if not verify_instagram_webhook_signature(payload, signature, webhook_secret):
            logger.warning("Signature webhook Instagram invalide")
            raise HTTPException(status_code=403, detail="Signature invalide")
        
        # Parser le JSON
        webhook_data = await request.json()
        logger.info(f"Webhook Instagram reçu: {webhook_data}")
        
        # Traiter chaque entrée du webhook avec routage par utilisateur
        for entry in webhook_data.get("entry", []):
            await process_instagram_webhook_entry_with_user_routing(entry)
        
        # Répondre rapidement à Instagram (obligatoire)
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Erreur traitement webhook Instagram: {e}")
        # Toujours répondre 200 à Instagram pour éviter les retries
        return {"status": "error", "message": str(e)}

async def process_instagram_webhook_entry_with_user_routing(entry: dict):
    """Traiter une entrée de webhook Instagram avec routage utilisateur"""
    instagram_business_account_id = entry.get("id")  # Instagram Business Account ID direct
    changes = entry.get("changes", [])
    
    # Récupérer les infos utilisateur basées sur instagram_business_account_id
    user_info = await get_instagram_user_by_business_account_id(instagram_business_account_id)
    
    if not user_info:
        logger.warning(f"Aucun utilisateur trouvé pour Instagram Business Account: {instagram_business_account_id}")
        return
    
    logger.info(f"Webhook Instagram routé vers l'utilisateur {user_info['user_id']} (account: {instagram_business_account_id})")
    
    # Traiter les changements avec le contexte utilisateur
    for change in changes:
        await process_instagram_webhook_change_for_user(change, user_info)

# Fonctions fallback/legacy supprimées : tout passe par routing utilisateur + save + batching

async def handle_incoming_instagram_comment(commenter_id: str, comment_text: str, comment_id: str, media_id: str):
    """
    Logique métier pour les commentaires entrants Instagram
    """
    # Exemple : réponse automatique aux commentaires avec certains mots-clés
    if comment_text and any(word in comment_text.lower() for word in ["super", "génial", "merci", "love"]):
        try:
            service = await get_instagram_service()
            await service.reply_to_comment(
                comment_id=comment_id,
                message="Merci beaucoup ! 😊"
            )
            logger.info(f"Réponse automatique au commentaire {comment_id}")
        except Exception as e:
            logger.error(f"Erreur réponse commentaire Instagram: {e}")
    
    # TODO: Analyser le sentiment, modérer, alerter si négatif
    logger.info(f"Commentaire Instagram à traiter: {commenter_id} -> {comment_text}")

async def handle_instagram_mention(mentioner_id: str, mention_id: str, media_id: str):
    """
    Logique métier pour les mentions Instagram
    """
    # TODO: Notifier l'équipe des mentions
    # TODO: Analyser le contexte de la mention
    # TODO: Décider s'il faut réagir ou répondre
    
    logger.info(f"Mention Instagram à traiter: {mentioner_id} dans {media_id}")

# ==================== ENDPOINTS WEBHOOK UTILITAIRES ====================

@router.get("/webhook-info")
async def get_instagram_webhook_info():
    """
    Informations sur la configuration des webhooks Instagram
    """
    return {
        "webhook_url": "/api/instagram/webhook",
        "verification_url": "/api/instagram/webhook?hub.mode=subscribe&hub.challenge=CHALLENGE&hub.verify_token=TOKEN",
        "required_env_vars": [
            "INSTAGRAM_VERIFY_TOKEN - pour la vérification initiale",
            "INSTAGRAM_WEBHOOK_SECRET - pour vérifier les signatures (optionnel en dev)"
        ],
        "webhook_events": [
            "messages - messages directs entrants",
            "comments - commentaires sur les posts",
            "mentions - mentions dans les stories",
            "feed - événements du feed"
        ],
        "setup_steps": [
            "1. Configurer INSTAGRAM_VERIFY_TOKEN dans .env",
            "2. Configurer l'URL webhook dans Meta for Developers",
            "3. Activer les événements souhaités (messages, comments, mentions)",
            "4. Tester avec l'endpoint de vérification"
        ],
        "permissions_required": [
            "instagram_manage_messages",
            "instagram_manage_comments", 
            "pages_read_engagement",
            "pages_manage_metadata"
        ]
    }

@router.post("/webhook-test")
async def test_instagram_webhook_locally(payload: dict):
    """
    Tester le traitement des webhooks Instagram en local
    """
    try:
        logger.info("Test webhook Instagram local")
        for entry in payload.get("entry", []):
            await process_instagram_webhook_entry_with_user_routing(entry)
        return {"status": "success", "message": "Webhook Instagram testé avec succès"}
    except Exception as e:
        logger.error(f"Erreur test webhook Instagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FONCTIONS UTILITAIRES MULTI-TENANT INSTAGRAM ====================

async def get_instagram_user_by_business_account_id(instagram_business_account_id: str) -> dict:
    """
    Récupérer les informations utilisateur basées sur instagram_business_account_id (Supabase)
    """
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.table("social_accounts").select(
            "id, user_id, account_id, access_token, display_name, username, is_active"
        ).eq("platform", "instagram").eq("account_id", instagram_business_account_id).eq("is_active", True).limit(1).execute()
        rows = res.data or []
        if not rows:
            logger.warning(f"Aucun utilisateur Instagram trouvé pour account_id: {instagram_business_account_id}")
            return None
        row = rows[0]
        return {
            "user_id": str(row["user_id"]),
            "social_account_id": str(row["id"]),
            "instagram_business_account_id": row["account_id"],
            "access_token": row.get("access_token"),
            "display_name": row.get("display_name"),
            "username": row.get("username"),
            "is_active": row.get("is_active", True)
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération utilisateur Instagram: {e}")
        return None

async def process_instagram_webhook_change_for_user(change: dict, user_info: dict):
    """
    Traiter un changement de webhook Instagram pour un utilisateur spécifique
    """
    field = change.get("field")
    value = change.get("value", {})
    
    logger.info(f"Traitement du changement Instagram '{field}' pour l'utilisateur {user_info['user_id']}")
    
    if field == "messages":
        await handle_instagram_messages_webhook_for_user(value, user_info)
    elif field == "comments":
        await handle_instagram_comments_webhook_for_user(value, user_info)
    elif field == "mentions":
        await handle_instagram_mentions_webhook_for_user(value, user_info)
    elif field == "feed":
        await handle_instagram_feed_webhook_for_user(value, user_info)
    else:
        logger.info(f"Type de webhook Instagram non géré: {field}")

async def handle_instagram_messages_webhook_for_user(value: dict, user_info: dict):
    """
    Gérer les webhooks de messages Instagram pour un utilisateur spécifique
    """
    user_id = user_info["user_id"]
    
    for message in value.get("messages", []):
        await process_incoming_instagram_message_for_user(message, user_info)

async def process_incoming_instagram_message_for_user(message: dict, user_info: dict):
    """
    Traiter un message direct Instagram entrant pour un utilisateur spécifique
    """
    message_id = message.get("id")
    sender_id = message.get("from", {}).get("id")
    timestamp = message.get("timestamp")
    message_text = message.get("text")
    
    logger.info(f"Message direct Instagram reçu pour l'utilisateur {user_info['user_id']}: {message_id}")
    
    # Sauvegarder en BDD (idempotent) puis ajouter au batching
    saved_id = await save_incoming_instagram_message_to_db(message, user_info)
    if not saved_id:
        # Message déjà traité → ne pas re-batcher
        return
    try:
        message_data = {
            "conversation_id": None,  # fixé dans add_message_to_batch via historique ou ultérieur
            "external_message_id": message.get("id"),
            "direction": "inbound",
            "message_type": message.get("type", "text"),
            "content": extract_instagram_message_content(message),
            "sender_id": message.get("from", {}).get("id"),
            "status": "received",
            "metadata": message
        }
        await message_batcher.add_message_to_batch(
            platform="instagram",
            account_id=user_info.get("instagram_business_account_id"),
            contact_id=message.get("from", {}).get("id"),
            message_data=message_data,
            conversation_id=None
        )
        logger.info(f"Message ajouté au batching Instagram pour {user_info['instagram_business_account_id']}:{message.get('from',{}).get('id')}")
    except Exception as e:
        logger.error(f"Erreur ajout batching Instagram: {e}")
    
    # Logique métier spécifique à l'utilisateur Instagram
    if message_text and message_text.lower() in ["hello", "salut", "bonjour", "hi"]:
        await handle_instagram_text_message_for_user(sender_id, message_text, user_info)

async def handle_instagram_text_message_for_user(sender_id: str, text: str, user_info: dict):
    """
    Traiter un message texte Instagram pour un utilisateur spécifique
    """
    user_id = user_info["user_id"]
    logger.info(f"Message texte Instagram pour {user_id} de {sender_id}: {text}")
    
    # Exemples de logique métier par utilisateur Instagram :
    # - Réponse automatique personnalisée via Instagram API
    # - Ajout au CRM de l'utilisateur
    # - Notification à l'équipe de l'utilisateur
    # - Intégration avec les systèmes tiers de l'utilisateur
    
    # TODO: Implémenter votre logique métier Instagram ici
    pass

async def save_incoming_instagram_message_to_db(message: dict, user_info: dict):
    """
    Sauvegarder un message Instagram entrant en BDD avec association utilisateur
    """
    from app.db.session import get_db
    try:
        db = get_db()
        external_message_id = message.get("id")
        contact_id = message.get("from", {}).get("id")

        conversation_id = await get_or_create_conversation(
            social_account_id=user_info["social_account_id"],
            customer_identifier=contact_id,
            customer_name=None
        )
        if not conversation_id:
            return None

        exists_res = db.table("conversation_messages").select("id").eq("conversation_id", conversation_id).eq("external_message_id", external_message_id).limit(1).execute()
        if exists_res.data:
            logger.info(f"Message Instagram {external_message_id} déjà traité pour utilisateur {user_info['user_id']}")
            return None

        message_data = {
            "conversation_id": conversation_id,
            "external_message_id": external_message_id,
            "direction": "inbound",
            "message_type": message.get("type", "text"),
            "content": extract_instagram_message_content(message),
            "sender_id": contact_id,
            "status": "received",
            "metadata": message
        }
        res = db.table("conversation_messages").insert(message_data).execute()
        saved_id = res.data[0]["id"] if res and res.data else None
        logger.info(f"Message Instagram {external_message_id} sauvegardé en BDD (ID: {saved_id}) pour utilisateur {user_info['user_id']}")
        return saved_id
    except Exception as e:
        logger.error(f"Erreur sauvegarde message Instagram en BDD: {e}")
        logger.info(f"Fallback: Message Instagram {message.get('id')} pour utilisateur {user_info['user_id']}")
        return None

async def handle_instagram_comments_webhook_for_user(value: dict, user_info: dict):
    """
    Gérer les webhooks de commentaires Instagram pour un utilisateur spécifique
    """
    for comment in value.get("comments", []):
        await process_incoming_instagram_comment_for_user(comment, user_info)

async def process_incoming_instagram_comment_for_user(comment: dict, user_info: dict):
    """
    Traiter un commentaire Instagram entrant pour un utilisateur spécifique
    """
    comment_id = comment.get("id")
    commenter_id = comment.get("from", {}).get("id")
    media_id = comment.get("media", {}).get("id")
    comment_text = comment.get("text")
    timestamp = comment.get("timestamp")
    
    logger.info(f"Commentaire Instagram de {commenter_id} sur {media_id}: {comment_text}")
    
    # Logique métier pour les commentaires Instagram par utilisateur
    await handle_incoming_instagram_comment_for_user_logic(commenter_id, comment_text, comment_id, media_id, user_info)

async def handle_incoming_instagram_comment_for_user_logic(commenter_id: str, comment_text: str, comment_id: str, media_id: str, user_info: dict):
    """
    Logique métier pour les commentaires entrants Instagram par utilisateur
    """
    # Exemple : réponse automatique aux commentaires positifs
    if comment_text and any(word in comment_text.lower() for word in ["super", "génial", "merci", "love", "amazing"]):
        try:
            # TODO: Utiliser le service Instagram pour répondre
            # service = await get_instagram_service(user_info["access_token"], user_info["instagram_business_account_id"])
            # await service.reply_to_comment(comment_id, "Merci beaucoup ! 😊")
            logger.info(f"Réponse automatique prévue au commentaire Instagram {comment_id}")
        except Exception as e:
            logger.error(f"Erreur réponse commentaire Instagram: {e}")
    
    # TODO: Analyser le sentiment, modérer, alerter si négatif par utilisateur
    logger.info(f"Commentaire Instagram à traiter pour utilisateur {user_info['user_id']}: {commenter_id} -> {comment_text}")

async def handle_instagram_mentions_webhook_for_user(value: dict, user_info: dict):
    """
    Gérer les webhooks de mentions Instagram pour un utilisateur spécifique
    """
    for mention in value.get("mentions", []):
        await process_instagram_mention_for_user(mention, user_info)

async def process_instagram_mention_for_user(mention: dict, user_info: dict):
    """
    Traiter une mention Instagram pour un utilisateur spécifique
    """
    mention_id = mention.get("id")
    mentioner_id = mention.get("from", {}).get("id")
    media_id = mention.get("media_id")
    
    logger.info(f"Mention Instagram de {mentioner_id} dans {media_id} pour utilisateur {user_info['user_id']}")
    
    # TODO: Notifier l'équipe des mentions par utilisateur
    # TODO: Analyser le contexte de la mention
    # TODO: Décider s'il faut réagir ou répondre selon les règles de l'utilisateur
    
    logger.info(f"Mention Instagram à traiter pour utilisateur {user_info['user_id']}: {mentioner_id} dans {media_id}")

async def handle_instagram_feed_webhook_for_user(value: dict, user_info: dict):
    """
    Gérer les webhooks du feed Instagram pour un utilisateur spécifique
    """
    logger.info(f"Événement feed Instagram pour l'utilisateur {user_info['user_id']}: {value}")
    # TODO: Traiter les événements du feed Instagram si nécessaire par utilisateur

# ==================== FONCTIONS UTILITAIRES BASE DE DONNÉES INSTAGRAM ====================

# Legacy logging supprimé (migration vers Supabase directe)

# Legacy processed flag supprimé

# Legacy get_or_create_conversation Instagram supprimé (utilisation de response_manager.get_or_create_conversation)

def extract_instagram_message_content(message: dict) -> str:
    """Extraire le contenu d'un message Instagram"""
    message_type = message.get("type", "text")
    
    if message_type == "text":
        return message.get("text", "")
    elif message_type == "image":
        return "[Image Instagram]"
    elif message_type == "video":
        return "[Video Instagram]"
    elif message_type == "audio":
        return "[Audio Instagram]"
    elif message_type == "file":
        return "[Fichier Instagram]"
    elif message_type == "reaction":
        reaction = message.get("reaction", {}).get("emoji", "")
        return f"[Réaction: {reaction}]"
    elif message_type == "story_mention":
        return "[Mention dans une story]"
    elif message_type == "story_reply":
        return f"[Réponse à story: {message.get('text', '')}]"
    else:
        return f"[{message_type.upper()} Instagram]"


#     Récupérer les informations utilisateur Instagram basées sur page_id depuis la BDD
#     """
#     from app.database import get_database
    
#     try:
#         db = await get_database()
        
#         # Utiliser la fonction SQL créée dans le schéma
#         query = """
#             SELECT * FROM get_instagram_user_by_page_id($1);
#         """
        
#         result = await db.fetchrow(query, page_id)
        
#         if result:
#             user_info = {
#                 "user_id": str(result["user_id"]),
#                 "social_account_id": str(result["social_account_id"]),
#                 "page_id": page_id,
#                 "access_token": result["access_token"],
#                 "app_secret": result["app_secret"],
#                 "verify_token": result["verify_token"],
#                 "display_name": result["display_name"],
#                 "username": result["username"],
#                 "is_active": result["is_active"]
#             }
            
#             logger.info(f"Utilisateur Instagram trouvé: {user_info['user_id']} pour page_id: {page_id}")
#             return user_info
#         else:
#             logger.warning(f"Aucun utilisateur trouvé pour page_id Instagram: {page_id}")
#             return None
            
#     except Exception as e:
#         logger.error(f"Erreur lors de la récupération utilisateur Instagram: {e}")
#         # Fallback vers données fictives en cas d'erreur BDD (développement seulement)
#         fake_users_db = {
#             "123456789012345": {
#                 "user_id": "user_456",
#                 "social_account_id": "sa_456",
#                 "page_id": "123456789012345",
#                 "access_token": "IGQ...",
#                 "app_secret": "abc123...",
#                 "verify_token": "my_verify_token_ig",
#                 "display_name": "Mon Business Instagram",
#                 "username": "mon_business_ig"
#             }
#         }
#         return fake_users_db.get(page_id)

# async def process_instagram_webhook_change_for_user(change: dict, user_info: dict):
#     """
#     Traiter un changement de webhook Instagram pour un utilisateur spécifique
#     """
#     field = change.get("field")
#     value = change.get("value", {})
    
#     logger.info(f"Traitement du changement Instagram '{field}' pour l'utilisateur {user_info['user_id']}")
    
#     if field == "messages":
#         await handle_instagram_messages_webhook_for_user(value, user_info)
#     elif field == "comments":
#         await handle_instagram_comments_webhook_for_user(value, user_info)
#     elif field == "mentions":
#         await handle_instagram_mentions_webhook_for_user(value, user_info)
#     elif field == "feed":
#         await handle_instagram_feed_webhook_for_user(value, user_info)
#     else:
#         logger.info(f"Type de webhook Instagram non géré: {field}")

# async def handle_instagram_messages_webhook_for_user(value: dict, user_info: dict):
#     """
#     Gérer les webhooks de messages directs Instagram pour un utilisateur spécifique
#     """
#     user_id = user_info["user_id"]
    
#     for message in value.get("messages", []):
#         await process_instagram_incoming_message_for_user(message, user_info)

# async def handle_instagram_comments_webhook_for_user(value: dict, user_info: dict):
#     """
#     Gérer les webhooks de commentaires Instagram pour un utilisateur spécifique
#     """
#     user_id = user_info["user_id"]
    
#     for comment in value.get("comments", []):
#         await process_instagram_incoming_comment_for_user(comment, user_info)

# async def handle_instagram_mentions_webhook_for_user(value: dict, user_info: dict):
#     """
#     Gérer les webhooks de mentions Instagram pour un utilisateur spécifique
#     """
#     user_id = user_info["user_id"]
    
#     for mention in value.get("mentions", []):
#         await process_instagram_mention_for_user(mention, user_info)

# async def handle_instagram_feed_webhook_for_user(value: dict, user_info: dict):
#     """
#     Gérer les webhooks du feed Instagram pour un utilisateur spécifique
#     """
#     logger.info(f"Événement feed Instagram pour l'utilisateur {user_info['user_id']}")
#     # TODO: Traiter les événements du feed si nécessaire

# async def process_instagram_incoming_message_for_user(message: dict, user_info: dict):
#     """
#     Traiter un message direct Instagram entrant pour un utilisateur spécifique
#     """
#     message_id = message.get("id")
#     sender_id = message.get("from", {}).get("id")
#     timestamp = message.get("timestamp")
#     message_text = message.get("text")
    
#     logger.info(f"Message direct Instagram de {sender_id}: {message_text} (ID: {message_id}) pour utilisateur {user_info['user_id']}")
    
#     # Sauvegarder en BDD avec l'association utilisateur
#     await save_instagram_message_to_db(message, user_info)
    
#     # Logique métier spécifique à l'utilisateur
#     await handle_instagram_dm_for_user(sender_id, message_text, user_info)

# async def process_instagram_incoming_comment_for_user(comment: dict, user_info: dict):
#     """
#     Traiter un commentaire Instagram entrant pour un utilisateur spécifique
#     """
#     comment_id = comment.get("id")
#     commenter_id = comment.get("from", {}).get("id")
#     media_id = comment.get("media", {}).get("id")
#     comment_text = comment.get("text")
#     timestamp = comment.get("timestamp")
    
#     logger.info(f"Commentaire Instagram de {commenter_id} sur {media_id}: {comment_text} pour utilisateur {user_info['user_id']}")
    
#     # Sauvegarder en BDD
#     await save_instagram_comment_to_db(comment, user_info)
    
#     # Logique métier pour les commentaires par utilisateur
#     await handle_instagram_comment_for_user(commenter_id, comment_text, comment_id, media_id, user_info)

# async def process_instagram_mention_for_user(mention: dict, user_info: dict):
#     """
#     Traiter une mention Instagram pour un utilisateur spécifique
#     """
#     mention_id = mention.get("id")
#     mentioner_id = mention.get("from", {}).get("id")
#     media_id = mention.get("media_id")
    
#     logger.info(f"Mention Instagram de {mentioner_id} dans {media_id} pour utilisateur {user_info['user_id']}")
    
#     # Logique métier pour les mentions par utilisateur
#     await handle_instagram_mention_for_user_business(mentioner_id, mention_id, media_id, user_info)

# # ==================== LOGIQUE MÉTIER PAR UTILISATEUR ====================

# async def handle_instagram_dm_for_user(sender_id: str, message_text: str, user_info: dict):
#     """
#     Logique métier pour les messages directs Instagram par utilisateur
#     """
#     user_id = user_info["user_id"]
#     business_name = user_info.get("display_name", "Business")
    
#     logger.info(f"Message Instagram DM pour {business_name} de {sender_id}: {message_text}")
    
#     # Réponse automatique personnalisée par utilisateur
#     if message_text and message_text.lower() in ["hello", "salut", "bonjour", "hi"]:
#         try:
#             service = await get_instagram_service(user_info["access_token"], user_info["page_id"])
#             await service.send_direct_message(
#                 recipient_ig_id=sender_id,
#                 text=f"Bonjour ! Merci de contacter {business_name}. Notre équipe vous répondra bientôt."
#             )
#             logger.info(f"Réponse automatique Instagram envoyée à {sender_id} pour {business_name}")
#         except Exception as e:
#             logger.error(f"Erreur réponse automatique Instagram pour {user_id}: {e}")
    
#     # TODO: Ajouter au CRM de l'utilisateur spécifique
#     # TODO: Notifier l'équipe de l'utilisateur
#     # TODO: Déclencher des workflows automatisés par utilisateur

# async def handle_instagram_comment_for_user(commenter_id: str, comment_text: str, comment_id: str, media_id: str, user_info: dict):
#     """
#     Logique métier pour les commentaires Instagram par utilisateur
#     """
#     user_id = user_info["user_id"]
#     business_name = user_info.get("display_name", "Business")
    
#     # Réponse automatique aux commentaires positifs personnalisée
#     if comment_text and any(word in comment_text.lower() for word in ["super", "génial", "merci", "love", "parfait"]):
#         try:
#             service = await get_instagram_service(user_info["access_token"], user_info["page_id"])
#             await service.reply_to_comment(
#                 comment_id=comment_id,
#                 message=f"Merci beaucoup pour ce retour ! 😊 - L'équipe {business_name}"
#             )
#             logger.info(f"Réponse automatique au commentaire {comment_id} pour {business_name}")
#         except Exception as e:
#             logger.error(f"Erreur réponse commentaire Instagram pour {user_id}: {e}")
    
#     # TODO: Analyser le sentiment par utilisateur
#     # TODO: Modérer selon les règles de l'utilisateur
#     # TODO: Alerter si commentaire négatif selon les critères de l'utilisateur

# async def handle_instagram_mention_for_user_business(mentioner_id: str, mention_id: str, media_id: str, user_info: dict):
#     """
#     Logique métier pour les mentions Instagram par utilisateur
#     """
#     user_id = user_info["user_id"]
#     business_name = user_info.get("display_name", "Business")
    
#     logger.info(f"Mention Instagram pour {business_name} de {mentioner_id} dans {media_id}")
    
#     # TODO: Notifier l'équipe spécifique de l'utilisateur
#     # TODO: Analyser le contexte de la mention pour cet utilisateur
#     # TODO: Décider s'il faut réagir selon les règles de l'utilisateur

# # ==================== SAUVEGARDE BASE DE DONNÉES ====================

# async def save_instagram_message_to_db(message: dict, user_info: dict):
#     """
#     Sauvegarder un message direct Instagram en BDD avec association utilisateur
#     """
#     from app.database import get_database
    
#     try:
#         db = await get_database()
        
#         # 1. Logger le webhook
#         webhook_log_id = await log_instagram_webhook_to_db(
#             social_account_id=user_info["social_account_id"],
#             platform="instagram",
#             webhook_type="message",
#             payload=message,
#             external_message_id=message.get("id"),
#             customer_identifier=message.get("from", {}).get("id")
#         )
        
#         # 2. Créer/récupérer la conversation
#         conversation_id = await get_or_create_instagram_conversation(
#             social_account_id=user_info["social_account_id"],
#             customer_identifier=message.get("from", {}).get("id"),
#             customer_name=None  # À récupérer via l'API Instagram si besoin
#         )
        
#         # 3. Sauvegarder le message
#         message_data = {
#             "conversation_id": conversation_id,
#             "external_message_id": message.get("id"),
#             "direction": "inbound",
#             "message_type": extract_instagram_message_type(message),
#             "content": extract_instagram_message_content(message),
#             "sender_id": message.get("from", {}).get("id"),
#             "status": "received",
#             "metadata": message
#         }
        
#         query = """
#             INSERT INTO conversation_messages (
#                 conversation_id, external_message_id, direction, message_type,
#                 content, sender_id, status, metadata
#             ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
#             RETURNING id;
#         """
        
#         message_id = await db.fetchval(
#             query,
#             message_data["conversation_id"],
#             message_data["external_message_id"],
#             message_data["direction"],
#             message_data["message_type"],
#             message_data["content"],
#             message_data["sender_id"],
#             message_data["status"],
#             message_data["metadata"]
#         )
        
#         logger.info(f"Message Instagram {message.get('id')} sauvegardé en BDD (ID: {message_id}) pour utilisateur {user_info['user_id']}")
        
#         # Marquer le webhook comme traité
#         await mark_instagram_webhook_processed_in_db(webhook_log_id)
        
#         return message_id
        
#     except Exception as e:
#         logger.error(f"Erreur sauvegarde message Instagram en BDD: {e}")
#         logger.info(f"Fallback: Message Instagram {message.get('id')} pour utilisateur {user_info['user_id']}")
#         return None

# async def save_instagram_comment_to_db(comment: dict, user_info: dict):
#     """
#     Sauvegarder un commentaire Instagram en BDD
#     """
#     try:
#         # TODO: Implémenter la sauvegarde des commentaires
#         logger.info(f"Commentaire Instagram {comment.get('id')} pour utilisateur {user_info['user_id']}")
        
#         # Logger le webhook
#         await log_instagram_webhook_to_db(
#             social_account_id=user_info["social_account_id"],
#             platform="instagram",
#             webhook_type="comment",
#             payload=comment,
#             external_message_id=comment.get("id"),
#             customer_identifier=comment.get("from", {}).get("id")
#         )
        
#     except Exception as e:
#         logger.error(f"Erreur sauvegarde commentaire Instagram: {e}")

# # ==================== FONCTIONS UTILITAIRES ====================

# async def log_instagram_webhook_to_db(
#     social_account_id: str,
#     platform: str,
#     webhook_type: str,
#     payload: dict,
#     external_message_id: str = None,
#     customer_identifier: str = None
# ) -> str:
#     """Logger un webhook Instagram en base de données"""
#     from app.database import get_database
    
#     try:
#         db = await get_database()
        
#         query = """
#             SELECT log_webhook($1::uuid, $2::social_platform, $3, $4::jsonb, $5, $6);
#         """
        
#         webhook_log_id = await db.fetchval(
#             query,
#             social_account_id,
#             platform,
#             webhook_type,
#             payload,
#             external_message_id,
#             customer_identifier
#         )
        
#         return str(webhook_log_id)
        
#     except Exception as e:
#         logger.error(f"Erreur logging webhook Instagram: {e}")
#         return None

# async def mark_instagram_webhook_processed_in_db(
#     webhook_log_id: str,
#     processing_time_ms: int = None,
#     error_message: str = None
# ):
#     """Marquer un webhook Instagram comme traité en BDD"""
#     from app.database import get_database
    
#     try:
#         db = await get_database()
        
#         query = """
#             SELECT mark_webhook_processed($1::uuid, $2, $3);
#         """
        
#         await db.execute(query, webhook_log_id, processing_time_ms, error_message)
        
#     except Exception as e:
#         logger.error(f"Erreur mise à jour webhook Instagram status: {e}")

# async def get_or_create_instagram_conversation(
#     social_account_id: str,
#     customer_identifier: str,
#     customer_name: str = None
# ) -> str:
#     """Récupérer ou créer une conversation Instagram"""
#     from app.database import get_database
    
#     try:
#         db = await get_database()
        
#         # Chercher conversation existante
#         query_find = """
#             SELECT id FROM conversations 
#             WHERE social_account_id = $1::uuid 
#             AND customer_identifier = $2
#             ORDER BY created_at DESC
#             LIMIT 1;
#         """
        
#         conversation_id = await db.fetchval(query_find, social_account_id, customer_identifier)
        
#         if conversation_id:
#             return str(conversation_id)
        
#         # Créer nouvelle conversation
#         query_create = """
#             INSERT INTO conversations (
#                 social_account_id,
#                 customer_identifier,
#                 customer_name,
#                 status,
#                 priority
#             ) VALUES ($1::uuid, $2, $3, 'open', 'normal')
#             RETURNING id;
#         """
        
#         conversation_id = await db.fetchval(
#             query_create,
#             social_account_id,
#             customer_identifier,
#             customer_name
#         )
        
#         logger.info(f"Nouvelle conversation Instagram créée: {conversation_id} pour {customer_identifier}")
#         return str(conversation_id)
        
#     except Exception as e:
#         logger.error(f"Erreur gestion conversation Instagram: {e}")
#         return None


