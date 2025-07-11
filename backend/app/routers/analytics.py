from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.analytics_service import analytics_service
from app.auth import get_current_user
from app.models import User
from typing import Dict

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/sync/{content_id}")
async def sync_content_analytics(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Synchronise les analytics d'un contenu spécifique"""
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
    current_user: User = Depends(get_current_user)
):
    """Synchronise tous les analytics d'un utilisateur (tâche en arrière-plan)"""
    # Vérifier que l'utilisateur peut accéder à ces données
    if str(current_user.id) != user_id and current_user.role != 'admin':
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
    current_user: User = Depends(get_current_user)
):
    """Récupère l'historique des analytics d'un contenu"""
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.models import AnalyticsHistory
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(AnalyticsHistory)
        .where(
            AnalyticsHistory.content_id == content_id,
            AnalyticsHistory.user_id == str(current_user.id),
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
    current_user: User = Depends(get_current_user)
):
    """Récupère les tendances analytics d'un utilisateur"""
    if str(current_user.id) != user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    from datetime import datetime, timedelta
    from sqlalchemy import select, func
    from app.models import AnalyticsHistory
    
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