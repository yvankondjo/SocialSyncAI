from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID

from supabase import Client

from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id


router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class PreviewRequest(BaseModel):
    content: str
    media_urls: Optional[List[HttpUrl]] = None


class PreviewResponse(BaseModel):
    normalized_text: str
    char_count: int
    word_count: int
    media_count: int


class ScheduleRequest(BaseModel):
    content: str
    platforms: List[str]
    scheduled_at: datetime
    timezone: str = "Europe/Paris"
    media_url: Optional[HttpUrl] = None


class ScheduledItem(BaseModel):
    platform: str
    content_id: str
    scheduled_at: datetime


class ScheduleResponse(BaseModel):
    items: List[ScheduledItem]


@router.post("/preview", response_model=PreviewResponse)
async def preview_post(payload: PreviewRequest):
    text = (payload.content or "").strip()
    normalized = " ".join(text.split())
    words = [w for w in normalized.split(" ") if w]
    return PreviewResponse(
        normalized_text=normalized,
        char_count=len(normalized),
        word_count=len(words),
        media_count=len(payload.media_urls or []),
    )


@router.post("/schedule", response_model=ScheduleResponse)
async def schedule_post(
    payload: ScheduleRequest,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    allowed = {"instagram", "reddit"}
    platforms = [p.lower() for p in payload.platforms if p.lower() in allowed]
    if not platforms:
        raise HTTPException(status_code=400, detail="No supported platforms provided")

    # Validation TZ Europe/Paris et pas dans le passé
    try:
        tz = ZoneInfo(payload.timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    scheduled_local = payload.scheduled_at.replace(tzinfo=tz) if payload.scheduled_at.tzinfo is None else payload.scheduled_at.astimezone(tz)
    now_local = datetime.now(tz)
    if scheduled_local <= now_local:
        raise HTTPException(status_code=400, detail="Cannot schedule in the past")

    # Convertir en UTC pour stockage
    scheduled_utc = scheduled_local.astimezone(ZoneInfo("UTC"))

    # Récupérer comptes sociaux de l'utilisateur
    items: List[ScheduledItem] = []
    for platform in platforms:
        acc_resp = db.table("social_accounts").select("id, platform, user_id, is_active").eq("platform", platform).eq("user_id", current_user_id).eq("is_active", True).limit(1).execute()
        if not acc_resp.data:
            raise HTTPException(status_code=400, detail=f"No active {platform} account connected")
        social_account_id = acc_resp.data[0]["id"]

        title = (payload.content or "").strip()[:60] or f"Scheduled post on {platform}"
        content_record = {
            "title": title,
            "content": payload.content,
            "content_type": "text",
            "status": "scheduled",
            "scheduled_at": scheduled_utc.isoformat(),
            "media_url": str(payload.media_url) if payload.media_url else None,
            "social_account_id": social_account_id,
            "created_by": current_user_id,
        }

        insert = db.table("content").insert(content_record).execute()
        if not insert.data:
            raise HTTPException(status_code=500, detail=f"Failed to schedule for {platform}")
        content_id = insert.data[0]["id"]
        items.append(ScheduledItem(platform=platform, content_id=content_id, scheduled_at=scheduled_utc))

    return ScheduleResponse(items=items)


