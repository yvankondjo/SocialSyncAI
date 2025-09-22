from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging
from datetime import datetime, timezone
import pytz

from app.db.session import get_authenticated_db
from app.schemas.scheduling import (
    SchedulePostRequest, SchedulePostResponse, PostPreviewRequest, PostPreviewResponse,
    ScheduledPost, CalendarPostsRequest, CalendarPostsResponse, PlatformPreview,
    PlatformType, PostStatus
)
from app.services.scheduling_service import SchedulingService
from app.core.security import get_current_user_id

router = APIRouter(prefix="/posts", tags=["Post Scheduling"])
logger = logging.getLogger(__name__)

# Timezone Paris
PARIS_TZ = pytz.timezone('Europe/Paris')

@router.post("/preview", response_model=PostPreviewResponse)
async def preview_post(
    request: PostPreviewRequest,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Génère des previews pour différentes plateformes
    """
    try:
        service = SchedulingService(db)
        previews = await service.generate_previews(
            content=request.content,
            platforms=request.platforms,
            media_urls=request.media_urls,
            post_type=request.post_type
        )
        
        return PostPreviewResponse(
            previews=previews,
            global_validation={"is_valid": all(p.is_valid for p in previews)}
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des previews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des previews: {str(e)}"
        )

@router.post("/schedule", response_model=SchedulePostResponse)
async def schedule_post(
    request: SchedulePostRequest,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Planifie un post sur plusieurs plateformes
    """
    try:
        # Valider la timezone Paris
        now_paris = datetime.now(PARIS_TZ)
        scheduled_paris = request.scheduled_at.replace(tzinfo=PARIS_TZ)
        
        if scheduled_paris <= now_paris:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de planification doit être dans le futur (timezone Europe/Paris)"
            )
        
        service = SchedulingService(db)
        scheduled_post = await service.schedule_post(
            user_id=current_user_id,
            content=request.content,
            platforms=request.platforms,
            scheduled_at=request.scheduled_at,
            media_urls=request.media_urls,
            post_type=request.post_type,
            metadata=request.metadata
        )
        
        return SchedulePostResponse(post=scheduled_post)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la planification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la planification: {str(e)}"
        )

@router.get("/calendar", response_model=CalendarPostsResponse)
async def get_calendar_posts(
    start_date: datetime,
    end_date: datetime,
    platforms: List[PlatformType] = None,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Récupère les posts planifiés pour une période donnée
    """
    try:
        service = SchedulingService(db)
        posts = await service.get_calendar_posts(
            user_id=current_user_id,
            start_date=start_date,
            end_date=end_date,
            platforms=platforms
        )
        
        return CalendarPostsResponse(
            posts=posts,
            total=len(posts)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des posts du calendrier: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des posts: {str(e)}"
        )

@router.get("/{post_id}", response_model=ScheduledPost)
async def get_scheduled_post(
    post_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Récupère un post planifié spécifique
    """
    try:
        service = SchedulingService(db)
        post = await service.get_scheduled_post(post_id, current_user_id)
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post planifié non trouvé"
            )
        
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du post: {str(e)}"
        )

@router.delete("/{post_id}")
async def cancel_scheduled_post(
    post_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """
    Annule un post planifié
    """
    try:
        service = SchedulingService(db)
        success = await service.cancel_scheduled_post(post_id, current_user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post planifié non trouvé"
            )
        
        return {"message": "Post annulé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation du post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'annulation du post: {str(e)}"
        )
