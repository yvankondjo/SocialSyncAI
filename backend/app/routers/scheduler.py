from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user_id
from app.db.session import get_db
from supabase import Client
from datetime import datetime
from zoneinfo import ZoneInfo
from app.schemas.scheduler import ScheduledPostCreate

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

PARIS_TZ = ZoneInfo("Europe/Paris")

def ensure_future_in_paris(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=PARIS_TZ)
    else:
        dt = dt.astimezone(PARIS_TZ)
    now_paris = datetime.now(PARIS_TZ)
    if dt <= now_paris:
        raise HTTPException(status_code=400, detail="La date de programmation doit être dans le futur (Europe/Paris)")
    return dt

@router.post("/posts")
async def create_scheduled_post(
    payload: ScheduledPostCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    scheduled_at_paris = ensure_future_in_paris(payload.scheduled_at)

    # Enregistrement minimal dans la table content (mode brouillon planifié)
    try:
        data = {
            "title": (payload.text[:60] or "Post programmé"),
            "content": payload.text,
            "content_type": "text",
            "status": "scheduled",
            "scheduled_at": scheduled_at_paris.isoformat(),
            "media_url": str(payload.media_url) if payload.media_url else None,
            "social_account_id": payload.social_account_id,
            "created_by": user_id,
        }
        res = db.table("content").insert(data).execute()
        created = res.data[0]
        return {"id": created["id"], "scheduled_at": created["scheduled_at"], "status": created["status"]}
    except Exception as e:
        print("Error inserting scheduled content:", e)
        raise HTTPException(status_code=500, detail="Impossible de créer le post planifié")

