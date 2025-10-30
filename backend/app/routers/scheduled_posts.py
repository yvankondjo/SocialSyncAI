"""
API Routes for Scheduled Posts management
Schedule posts for automatic publishing to social media
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from app.schemas.scheduled_posts import (
    ScheduledPostCreate,
    ScheduledPostUpdate,
    ScheduledPostResponse,
    ScheduledPostListResponse,
    PostRunResponse,
    PostRunListResponse,
    PostStatistics,
    PostStatus,
)
from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
router = APIRouter(prefix="/posts", tags=["Scheduled Posts"])


@router.post("", response_model=ScheduledPostResponse, status_code=201)
async def create_scheduled_post(
    post: ScheduledPostCreate,
    db=Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new scheduled post
    Post will be automatically published at the specified time
    """
    channel = db.table("social_accounts").select("id, platform").eq("id", post.channel_id).execute()

    if not channel.data:
        raise HTTPException(status_code=404, detail="Channel not found or you don't have access")

    platform = channel.data[0]["platform"]

    # Validate platform-specific requirements
    if platform == "instagram":
        if not post.content.media or len(post.content.media) == 0:
            raise HTTPException(
                status_code=400,
                detail="Instagram posts require at least one media item (image or video)"
            )

    post_data = {
        "user_id": current_user_id,
        "channel_id": post.channel_id,
        "platform": platform,
        "content_json": post.content.model_dump(),
        "publish_at": post.publish_at.isoformat(),
        "rrule": post.rrule,
        "status": PostStatus.QUEUED.value,
        "retry_count": 0,
    }

    result = db.table("scheduled_posts").insert(post_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create scheduled post")

    return ScheduledPostResponse(**result.data[0])


@router.get("", response_model=ScheduledPostListResponse)
async def list_scheduled_posts(
    status: Optional[str] = None,
    channel_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_authenticated_db)
):
    """
    List scheduled posts for current user

    Filters:
        status: Filter by status (queued, publishing, published, failed, cancelled)
        channel_id: Filter by specific channel
        platform: Filter by platform (whatsapp, instagram)
        limit: Max results (default 50, max 100)
        offset: Pagination offset
    """
    if limit > 100:
        limit = 100

    query = db.table("scheduled_posts").select("*", count="exact")

    if status:
        query = query.eq("status", status)
    else:
        # By default, exclude cancelled posts
        query = query.neq("status", PostStatus.CANCELLED.value)

    if channel_id:
        query = query.eq("channel_id", channel_id)
    if platform:
        query = query.eq("platform", platform)

    result = query.order("publish_at", desc=False).range(offset, offset + limit - 1).execute()

    return ScheduledPostListResponse(
        posts=[ScheduledPostResponse(**item) for item in result.data],
        total=result.count or 0,
        limit=limit,
        offset=offset
    )


@router.get("/{post_id}", response_model=ScheduledPostResponse)
async def get_scheduled_post(
    post_id: str,
    db=Depends(get_authenticated_db)
):
    """Get a specific scheduled post by ID"""
    result = db.table("scheduled_posts").select("*").eq("id", post_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    return ScheduledPostResponse(**result.data[0])


@router.patch("/{post_id}", response_model=ScheduledPostResponse)
async def update_scheduled_post(
    post_id: str,
    update: ScheduledPostUpdate,
    db=Depends(get_authenticated_db),
):
    """
    Update a scheduled post
    Only queued posts can be updated
    """
    existing = db.table("scheduled_posts").select("status, platform").eq("id", post_id).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if existing.data[0]["status"] not in [PostStatus.QUEUED.value, PostStatus.FAILED.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update post with status: {existing.data[0]['status']}. Only queued or failed posts can be updated."
        )

    update_data = update.model_dump(exclude_unset=True)

    # Validate platform-specific requirements if content is being updated
    if "content" in update_data and update_data["content"]:
        platform = existing.data[0]["platform"]
        if platform == "instagram":
            if not update_data["content"].media or len(update_data["content"].media) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Instagram posts require at least one media item (image or video)"
                )
        update_data["content_json"] = update_data.pop("content").model_dump()

    if "publish_at" in update_data and update_data["publish_at"]:
        update_data["publish_at"] = update_data["publish_at"].isoformat()

    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].value

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = db.table("scheduled_posts").update(update_data).eq("id", post_id).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update scheduled post")

    return ScheduledPostResponse(**result.data[0])


@router.delete("/{post_id}", status_code=204)
async def delete_scheduled_post(
    post_id: str,
    db=Depends(get_authenticated_db)
):
    """
    Delete a scheduled post permanently (hard delete)
    Published posts cannot be deleted
    """
    existing = db.table("scheduled_posts").select("status").eq("id", post_id).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if existing.data[0]["status"] == PostStatus.PUBLISHED.value:
        raise HTTPException(status_code=400, detail="Cannot delete published posts")

    # Hard delete - permanently remove from database
    db.table("scheduled_posts").delete().eq("id", post_id).execute()

    return


@router.get("/{post_id}/runs", response_model=PostRunListResponse)
async def get_post_runs(
    post_id: str,
    limit: int = 20,
    offset: int = 0,
    db=Depends(get_authenticated_db)
):
    """
    Get execution history (runs) for a scheduled post
    """
    post = db.table("scheduled_posts").select("id").eq("id", post_id).execute()

    if not post.data:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    result = db.table("post_runs").select("*", count="exact").eq("scheduled_post_id", post_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    return PostRunListResponse(
        runs=[PostRunResponse(**item) for item in result.data],
        total=result.count or 0,
        limit=limit,
        offset=offset
    )


@router.get("/statistics", response_model=PostStatistics)
async def get_post_statistics(db=Depends(get_authenticated_db)):
    """
    Get statistics on scheduled posts (count by status)
    """
    all_posts = db.table("scheduled_posts").select("status").execute()

    stats = {
        "queued": 0,
        "publishing": 0,
        "published": 0,
        "failed": 0,
        "cancelled": 0,
        "total": len(all_posts.data)
    }

    for post in all_posts.data:
        status = post.get("status")
        if status in stats:
            stats[status] += 1

    return PostStatistics(**stats)
