"""
Monitoring Router
API endpoints for managing comment monitoring on posts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.schemas.monitored_posts import (
    MonitoredPostInDB,
    MonitoredPostListResponse,
    MonitoringRulesBase,
    MonitoringRulesInDB,
    SyncInstagramPostsRequest,
    SyncInstagramPostsResponse,
    ToggleMonitoringRequest,
    ToggleMonitoringResponse,
)
from app.services.monitoring_service import MonitoringService
from app.db.session import get_authenticated_db, get_user_id_from_token
from supabase import Client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Comment Monitoring"])


@router.post("/sync", response_model=SyncInstagramPostsResponse)
async def sync_instagram_posts(
    request: SyncInstagramPostsRequest = SyncInstagramPostsRequest(),
    db: Client = Depends(get_authenticated_db),
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Import Instagram posts and apply auto-monitoring rules

    If no social_account_id specified, uses first connected Instagram account

    Args:
        request: Sync configuration (account_id, limit)

    Returns:
        SyncInstagramPostsResponse with import metrics
    """
    try:
        service = MonitoringService(db, user_id)

        social_account_id = request.social_account_id

        # If no account specified, use first Instagram account
        if not social_account_id:
            accounts = db.table("social_accounts") \
                .select("id") \
                .eq("user_id", user_id) \
                .eq("platform", "instagram") \
                .eq("is_active", True) \
                .execute()

            if not accounts.data:
                raise HTTPException(
                    status_code=404,
                    detail="No Instagram account connected"
                )

            social_account_id = accounts.data[0]["id"]

        result = await service.sync_instagram_posts(
            social_account_id,
            limit=request.limit
        )

        return SyncInstagramPostsResponse(
            success=result["success"],
            posts_imported=result["posts_imported"],
            posts_monitored=result["posts_monitored"],
            message=f"Successfully imported {result['posts_imported']} posts, "
                    f"{result['posts_monitored']} enabled for monitoring"
        )

    except ValueError as e:
        logger.error(f"[MONITORING_API] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[MONITORING_API] Error syncing Instagram posts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync Instagram posts: {str(e)}"
        )


@router.get("/posts", response_model=MonitoredPostListResponse)
async def get_monitored_posts(
    monitoring_enabled: Optional[bool] = Query(None, description="Filter by monitoring status"),
    limit: int = Query(50, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Client = Depends(get_authenticated_db),
    user_id: str = Depends(get_user_id_from_token)
):
    """
    List all monitored posts for current user

    Query Parameters:
        - monitoring_enabled: Filter by monitoring status (true/false)
        - limit: Max results (default 50, max 100)
        - offset: Pagination offset

    Returns:
        MonitoredPostListResponse with posts and total count
    """
    try:
        service = MonitoringService(db, user_id)

        posts = await service.get_monitored_posts(
            limit=limit,
            offset=offset,
            monitoring_enabled=monitoring_enabled
        )

        # Debug: Check if posts have IDs
        logger.info(f"[MONITORING_API] Returning {len(posts)} posts")
        if posts:
            first_post_dict = posts[0].dict() if posts else {}
            logger.info(f"[MONITORING_API] First post sample: id={first_post_dict.get('id')}, platform_post_id={first_post_dict.get('platform_post_id')}")
            posts_without_id = [p for p in posts if not p.id]
            if posts_without_id:
                logger.error(f"[MONITORING_API] ❌ {len(posts_without_id)} posts without ID!")

        # Get total count
        query = db.table("monitored_posts") \
            .select("id", count="exact") \
            .eq("user_id", user_id)

        if monitoring_enabled is not None:
            query = query.eq("monitoring_enabled", monitoring_enabled)

        count_result = query.execute()
        total = count_result.count or 0

        return MonitoredPostListResponse(
            posts=posts,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"[MONITORING_API] Error listing monitored posts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list monitored posts: {str(e)}"
        )


@router.patch("/posts/{post_id}/toggle", response_model=ToggleMonitoringResponse)
async def toggle_monitoring(
    post_id: str,
    request: ToggleMonitoringRequest = ToggleMonitoringRequest(),
    db: Client = Depends(get_authenticated_db),
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Toggle monitoring on/off for a post

    If enabling, can specify custom duration_days (otherwise uses rules default)

    Args:
        post_id: UUID of monitored_posts
        request: Optional duration_days override

    Returns:
        ToggleMonitoringResponse with updated post
    """
    try:
        service = MonitoringService(db, user_id)

        # Get current state
        post = db.table("monitored_posts") \
            .select("monitoring_enabled") \
            .eq("id", post_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found")

        # Toggle monitoring
        if post.data["monitoring_enabled"]:
            # Disable
            updated_post = await service.disable_monitoring(post_id)
            message = "Monitoring disabled"
        else:
            # Enable
            updated_post = await service.enable_monitoring(
                post_id,
                duration_days=request.duration_days
            )
            duration = request.duration_days or (await service.get_rules()).monitoring_duration_days
            message = f"Monitoring enabled for {duration} days"

        return ToggleMonitoringResponse(
            success=True,
            post=updated_post,
            message=message
        )

    except ValueError as e:
        logger.error(f"[MONITORING_API] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MONITORING_API] Error toggling monitoring: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle monitoring: {str(e)}"
        )


@router.get("/rules", response_model=MonitoringRulesInDB)
async def get_monitoring_rules(
    social_account_id: Optional[str] = Query(None, description="Filter by social account"),
    db: Client = Depends(get_authenticated_db),
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Get monitoring auto-rules for user

    Query Parameters:
        - social_account_id: Optional account filter

    Returns:
        MonitoringRulesInDB with current rules (creates default if not exists)
    """
    try:
        service = MonitoringService(db, user_id)

        rules = await service.get_rules(social_account_id)

        return rules

    except Exception as e:
        logger.error(f"[MONITORING_API] Error getting monitoring rules: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring rules: {str(e)}"
        )


@router.put("/rules", response_model=MonitoringRulesInDB)
async def update_monitoring_rules(
    rules: MonitoringRulesBase,
    social_account_id: Optional[str] = Query(None, description="Filter by social account"),
    db: Client = Depends(get_authenticated_db),
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Update monitoring auto-rules

    Body:
        - auto_monitor_enabled: Enable/disable auto-monitoring
        - auto_monitor_count: Number of latest posts to auto-monitor (1-20)
        - monitoring_duration_days: Days to monitor each post (1-30)

    Query Parameters:
        - social_account_id: Optional account filter

    Returns:
        MonitoringRulesInDB with updated rules
    """
    try:
        service = MonitoringService(db, user_id)

        updated_rules = await service.update_rules(rules, social_account_id)

        logger.info(
            f"[MONITORING_API] User {user_id} updated rules: "
            f"auto_enabled={rules.auto_monitor_enabled}, "
            f"count={rules.auto_monitor_count}, "
            f"duration={rules.monitoring_duration_days} days"
        )

        return updated_rules

    except Exception as e:
        logger.error(f"[MONITORING_API] Error updating monitoring rules: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update monitoring rules: {str(e)}"
        )
