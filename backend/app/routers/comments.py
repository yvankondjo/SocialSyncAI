"""
Comments Router
API endpoints for listing and managing comments on scheduled posts
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from supabase import Client
from typing import Optional
from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
from app.schemas.comments import CommentListResponse, CommentInDB
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.get("/", response_model=CommentListResponse)
async def list_comments(
    post_id: Optional[str] = Query(None, description="Filter by post ID"),
    triage: Optional[str] = Query(None, description="Filter by triage (respond, ignore, escalate)"),
    limit: int = Query(50, le=100, description="Max number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip for pagination"),
    current_user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_authenticated_db)
):
    """
    List comments for the current user's posts

    Query Parameters:
    - post_id: Optional UUID to filter comments by specific post
    - triage: Optional filter by AI decision (respond, ignore, escalate)
    - limit: Max results (default 50, max 100)
    - offset: Pagination offset (default 0)

    Returns:
        CommentListResponse with comments, total count, and pagination info

    Example:
        GET /api/comments?post_id=123&triage=escalate&limit=20&offset=0
    """
    try:
        # Build query with user ownership check via monitored_posts
        query = db.table("comments") \
            .select("*, ai_decisions(*), monitored_posts!inner(user_id, caption, platform)", count="exact")

        # Filter by user ownership via monitored_posts join
        query = query.eq("monitored_posts.user_id", current_user_id)

        # Optional filters
        if post_id:
            # post_id can be either monitored_post_id or legacy post_id
            # Try both for backwards compatibility
            query = query.or_(f"monitored_post_id.eq.{post_id},post_id.eq.{post_id}")

        if triage:
            # Validate triage value
            if triage not in ["respond", "ignore", "escalate"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid triage value. Must be: respond, ignore, or escalate"
                )
            query = query.eq("triage", triage)

        # Execute query with pagination
        result = query \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()

        comments = result.data or []
        total = result.count or 0

        logger.info(
            f"[COMMENTS_API] User {current_user_id}: "
            f"returned {len(comments)} comments (total={total}, post_id={post_id}, triage={triage})"
        )

        return CommentListResponse(
            comments=comments,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMMENTS_API] Error listing comments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching comments: {str(e)}"
        )


@router.get("/{comment_id}", response_model=CommentInDB)
async def get_comment(
    comment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_authenticated_db)
):
    """
    Get a single comment by ID

    Args:
        comment_id: Comment UUID

    Returns:
        CommentInDB with full comment data

    Raises:
        404: Comment not found or doesn't belong to user's posts
    """
    try:
        # Fetch comment with ownership check via monitored_posts
        result = db.table("comments") \
            .select("""
                *,
                ai_decisions(*),
                monitored_posts!inner(user_id, caption, platform)
            """) \
            .eq("id", comment_id) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Comment not found")

        comment = result.data

        # Verify ownership via monitored_posts
        if comment["monitored_posts"]["user_id"] != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this comment"
            )

        logger.info(f"[COMMENTS_API] User {current_user_id} fetched comment {comment_id}")

        return comment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMMENTS_API] Error fetching comment {comment_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching comment: {str(e)}"
        )
