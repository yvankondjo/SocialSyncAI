from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
import logging

from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
from app.services.response_manager import get_signed_url
from app.services.media_cache_service import media_cache_service

router = APIRouter(prefix="/media", tags=["Media"])
logger = logging.getLogger(__name__)


@router.get("/signed-url/{object_path:path}")
async def get_media_signed_url(
    object_path: str,
    expires_in: int = 3600,  # 1 heure par défaut
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Generate a temporary signed URL to access a stored media (with Redis cache)

    Args:
        object_path: Object path in Supabase Storage (ex: "uuid/message_id.jpg")
        expires_in: Duration of the URL in seconds (default: 1 hour)

    Returns:
        Signed URL to access the media
    """
    try:
        if not object_path or "/" not in object_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid object path"
            )

        
        await validate_media_access(object_path, current_user_id, db)


        signed_url = await media_cache_service.get_cached_signed_url(
            storage_object_name=object_path,
            bucket_id='message',
            expires_in=expires_in
        )

        if not signed_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found or unable to generate signed URL"
            )

        return {
            "signed_url": signed_url,
            "expires_in": expires_in,
            "object_path": object_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating signed URL for {object_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def validate_media_access(object_path: str, user_id: str, db) -> None:
    """
    Validate that the user has access to the requested media by verifying that it belongs
    to a conversation accessible by the user.
    """
    try:
        message_result = db.table('conversation_messages').select(
            'conversation_id, storage_object_name'
        ).eq('storage_object_name', object_path).execute()

        if not message_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )

        message = message_result.data[0]
        conversation_id = message['conversation_id']


        conversation_check = db.table('conversations').select(
            'id'
        ).select(
            'social_accounts!inner(user_id)'
        ).eq('id', conversation_id).eq('social_accounts.user_id', user_id).execute()

        if not conversation_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating media access for {object_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating media access"
        )


@router.get("/preview/{object_path:path}")
async def get_media_preview_url(
    object_path: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Generate a short preview URL (5 minutes) for media

    Useful for quick previews in the user interface
    """
    return await get_media_signed_url(
        object_path=object_path,
        expires_in=300,
        current_user_id=current_user_id,
        db=db
    )


@router.post("/batch-signed-urls")
async def get_batch_media_signed_urls(
    object_paths: List[str],
    expires_in: int = 3600,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Generate several signed URLs in a single request (with Redis cache)
    
    Args:
        object_paths: List of object paths in Supabase Storage
        expires_in: Duration of the URLs in seconds (default: 1 hour)
        
    Returns:
        Dictionary {object_path: signed_url} for each object
    """
    try:
        if not object_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="List of object paths is empty"
            )
        
        if len(object_paths) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many objects requested (maximum: 50)"
            )
        
        results = {}
        
        for object_path in object_paths:
            if not object_path or "/" not in object_path:
                results[object_path] = None
                continue
                
            try:
                await validate_media_access(object_path, current_user_id, db)
            except HTTPException:
                results[object_path] = None
                continue
        
        valid_paths = [path for path, result in results.items() if result is None and path and "/" in path]
        
        if valid_paths:
            signed_urls = await media_cache_service.get_batch_signed_urls(
                storage_object_names=valid_paths,
                bucket_id='message',
                expires_in=expires_in
            )
            results.update(signed_urls)
        
        return {
            "signed_urls": results,
            "expires_in": expires_in,
            "total_requested": len(object_paths),
            "total_generated": len([url for url in results.values() if url is not None])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération batch des URLs signées: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
