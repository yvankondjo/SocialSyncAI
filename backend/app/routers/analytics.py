from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from supabase import Client
from app.db.session import get_authenticated_db
from app.services.analytics_service import analytics_service
from app.core.security import get_current_user_id
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/sync/{content_id}")
async def sync_content_analytics(
    content_id: str,
    request: Request,
    db: Client = Depends(get_authenticated_db)
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
    request: Request,
    days: int = 7,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Synchronise tous les analytics d'un utilisateur (tâche en arrière-plan)"""
    # NOTE: Cette vérification pourrait être redondante avec RLS, mais garde sécurité explicite
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
    request: Request,
    days: int = 30,
    db: Client = Depends(get_authenticated_db),
):
    """Récupère l'historique des analytics d'un contenu"""
    from datetime import datetime, timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # NOTE: RLS sur content et analytics_history assure automatiquement la sécurité
    # L'utilisateur ne peut voir que ses propres données
    result = db.table("analytics_history").select("*").eq("content_id", content_id).gte("recorded_at", cutoff_date.isoformat()).order("recorded_at", desc=True).execute()

    return {
        "content_id": content_id,
        "history": result.data
    }

@router.get("/trends/{user_id}")
async def get_analytics_trends(
    user_id: str,
    request: Request,
    days: int = 30,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Récupère les tendances analytics d'un utilisateur"""
    from datetime import datetime, timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Agrégation par jour - RLS applique automatiquement user_id = auth.uid()
    result = db.table("analytics_history").select("recorded_at, likes, shares, comments, impressions, engagement_rate").gte("recorded_at", cutoff_date.isoformat()).execute()

    trends = {}
    for record in result.data:
        date_key = record["recorded_at"].split("T")[0]  # YYYY-MM-DD
        if date_key not in trends:
            trends[date_key] = {
                "date": date_key,
                "total_likes": 0,
                "total_shares": 0,
                "total_comments": 0,
                "total_impressions": 0,
                "avg_engagement_rate": 0,
                "count": 0
            }

        trends[date_key]["total_likes"] += record["likes"] or 0
        trends[date_key]["total_shares"] += record["shares"] or 0
        trends[date_key]["total_comments"] += record["comments"] or 0
        trends[date_key]["total_impressions"] += record["impressions"] or 0
        trends[date_key]["avg_engagement_rate"] += record["engagement_rate"] or 0
        trends[date_key]["count"] += 1

    # Calculer la moyenne des taux d'engagement
    for trend in trends.values():
        if trend["count"] > 0:
            trend["avg_engagement_rate"] = trend["avg_engagement_rate"] / trend["count"]
        del trend["count"]

    return {
        "user_id": user_id,
        "period_days": days,
        "trends": list(trends.values())
    }