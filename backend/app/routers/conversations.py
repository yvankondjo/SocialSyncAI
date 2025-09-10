from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
import logging

from app.db.session import get_authenticated_db
from app.schemas.conversation import (
    Conversation, Message, ConversationListResponse, MessageListResponse,
    SendMessageRequest, ConversationQueryParams
)
from app.services.conversation_service import ConversationService
from app.core.security import get_current_user_id
router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = logging.getLogger(__name__)

@router.get("", response_model=ConversationListResponse)
async def get_user_conversations(
    channel: Optional[str] = Query(None, description="Filtrer par canal: whatsapp, instagram, all"),
    limit: int = Query(50, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):  
    """
    Récupère toutes les conversations de l'utilisateur connecté
    """
    try:
        service = ConversationService(db)
        conversations = await service.get_user_conversations(
            user_id=current_user_id,
            channel=channel,
            limit=limit
        )
        
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )

@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, le=200),
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)    
):
    """
    Récupère les messages d'une conversation spécifique
    """
    try:
        service = ConversationService(db)
        messages = await service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user_id,
            limit=limit
        )
        
        return MessageListResponse(
            messages=messages,
            total=len(messages)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des messages: {str(e)}"
        )

@router.post("/{conversation_id}/messages", response_model=Message)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Envoie un message dans une conversation
    """
    try:
        service = ConversationService(db)
        message = await service.send_message(
            conversation_id=conversation_id,
            user_id=current_user_id,
            content=request.content,
            message_type=request.message_type
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'envoi du message: {str(e)}"
        )

@router.patch("/{conversation_id}/read")
async def mark_conversation_as_read(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Marque une conversation comme lue
    """
    try:
        service = ConversationService(db)
        success = await service.mark_conversation_as_read(
            conversation_id=conversation_id,
            user_id=current_user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Impossible de marquer cette conversation comme lue"
            )
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du marquage comme lu: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du marquage comme lu: {str(e)}"
        )
