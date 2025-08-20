from fastapi import APIRouter, HTTPException, status
from typing import List
import logging

from app.schemas.instagram import (
    DirectMessageRequest, FeedPostRequest, StoryRequest, CommentReplyRequest,
    InstagramCredentials, InstagramCredentialsValidation,
    InstagramMessageResponse, InstagramPostResponse, InstagramStoryResponse,
    ConversationsResponse, CommentReplyResponse, BatchDirectMessageRequest, BatchResponse
)
from app.services.instagram_service import get_instagram_service, InstagramService

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
