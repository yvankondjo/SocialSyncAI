from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.analytics_service import analytics_service
from app.core.security import get_current_user_id
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/sync/{content_id}")
async def sync_content_analytics(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Synchronise les analytics d'un contenu spécifique"""
    # L'ID utilisateur est dans `current_user['sub']`, nous pouvons le passer au service si nécessaire
    result = await analytics_service.sync_content_analytics(db, content_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/sync/user/{user_id}")
async def sync_user_analytics(
    user_id: str,
    days: int = 7,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Synchronise tous les analytics d'un utilisateur (tâche en arrière-plan)"""
    # Vérifier que l'utilisateur peut accéder à ces données
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Lancer la sync en arrière-plan
    background_tasks.add_task(
        analytics_service.sync_user_analytics,
        db,
        user_id,
        days
    )
    
    return {"message": "Analytics sync started in background"}

@router.get("/history/{content_id}")
async def get_analytics_history(
    content_id: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Récupère l'historique des analytics d'un contenu"""
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.schemas.analytics_history import AnalyticsHistory
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(AnalyticsHistory)
        .where(
            AnalyticsHistory.content_id == content_id,
            AnalyticsHistory.user_id == current_user_id,
            AnalyticsHistory.recorded_at >= cutoff_date
        )
        .order_by(AnalyticsHistory.recorded_at.desc())
    )
    
    history = result.scalars().all()
    
    return {
        "content_id": content_id,
        "history": [
            {
                "recorded_at": h.recorded_at,
                "platform": h.platform,
                "likes": h.likes,
                "shares": h.shares,
                "comments": h.comments,
                "impressions": h.impressions,
                "reach": h.reach,
                "clicks": h.clicks,
                "conversions": h.conversions,
                "engagement_rate": h.engagement_rate,
                "raw_metrics": h.raw_metrics
            }
            for h in history
        ]
    }

@router.get("/trends/{user_id}")
async def get_analytics_trends(
    user_id: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Récupère les tendances analytics d'un utilisateur"""
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from datetime import datetime, timedelta
    from sqlalchemy import select, func
    from app.models.analytics_history import AnalyticsHistory
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Agrégation par jour
    result = await db.execute(
        select(
            func.date(AnalyticsHistory.recorded_at).label('date'),
            func.sum(AnalyticsHistory.likes).label('total_likes'),
            func.sum(AnalyticsHistory.shares).label('total_shares'),
            func.sum(AnalyticsHistory.comments).label('total_comments'),
            func.sum(AnalyticsHistory.impressions).label('total_impressions'),
            func.avg(AnalyticsHistory.engagement_rate).label('avg_engagement_rate')
        )
        .where(
            AnalyticsHistory.user_id == user_id,
            AnalyticsHistory.recorded_at >= cutoff_date
        )
        .group_by(func.date(AnalyticsHistory.recorded_at))
        .order_by(func.date(AnalyticsHistory.recorded_at))
    )
    
    trends = result.all()
    
    return {
        "user_id": user_id,
        "period_days": days,
        "trends": [
            {
                "date": str(t.date),
                "total_likes": t.total_likes or 0,
                "total_shares": t.total_shares or 0,
                "total_comments": t.total_comments or 0,
                "total_impressions": t.total_impressions or 0,
                "avg_engagement_rate": float(t.avg_engagement_rate or 0)
            }
            for t in trends
        ]
    } 