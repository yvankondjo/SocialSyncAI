"""
Debug Router for Comment Monitoring System
Temporary endpoints to troubleshoot comment polling
"""
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.session import get_authenticated_db, get_user_id_from_token
from app.workers.comments import poll_post_comments, process_comment
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug/comments", tags=["Debug Comments"])


@router.post("/force-poll")
async def force_poll_comments(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_user_id_from_token)
):
    """
    Force immediate polling of all monitored posts

    This bypasses the next_check_at schedule and polls all active posts immediately.
    Useful for debugging and testing the comment polling system.

    Returns:
        Poll metrics: posts_checked, comments_found, errors
    """
    try:
        logger.info(f"[DEBUG] Force polling triggered by user {current_user_id}")

        # Call the Celery task synchronously for immediate feedback
        result = poll_post_comments()

        logger.info(f"[DEBUG] Force poll completed: {result}")

        return {
            "success": True,
            "message": "Force polling completed",
            "metrics": result
        }

    except Exception as e:
        logger.error(f"[DEBUG] Error in force polling: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comment-context/{comment_id}")
async def get_comment_context(
    comment_id: str,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_user_id_from_token)
):
    """
    Get the full context that would be sent to AI for a comment

    Shows exactly what the AI sees when processing this comment:
    - Comment text
    - Post caption
    - Thread history
    - Media URLs
    - etc.

    Useful for debugging why AI made certain decisions.
    """
    try:
        # Fetch comment with full context
        result = db.table("comments") \
            .select("""
                *,
                monitored_posts!inner(
                    id,
                    caption,
                    media_url,
                    posted_at,
                    platform,
                    platform_post_id,
                    user_id,
                    social_accounts!inner(username, account_id)
                )
            """) \
            .eq("id", comment_id) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Comment not found")

        comment = result.data
        post = comment["monitored_posts"]

        # Check ownership
        if post["user_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not your comment")

        # Get thread (parent and replies)
        parent = None
        if comment.get("parent_id"):
            parent_result = db.table("comments") \
                .select("*") \
                .eq("id", comment["parent_id"]) \
                .single() \
                .execute()
            parent = parent_result.data if parent_result.data else None

        # Get replies to this comment
        replies_result = db.table("comments") \
            .select("*") \
            .eq("parent_id", comment_id) \
            .execute()
        replies = replies_result.data or []

        # Build context object (similar to what AI would receive)
        context = {
            "comment": {
                "id": comment["id"],
                "text": comment["text"],
                "author": comment.get("author_name"),
                "created_at": comment.get("created_at"),
                "like_count": comment.get("like_count", 0)
            },
            "post": {
                "caption": post.get("caption"),
                "media_url": post.get("media_url"),
                "posted_at": post.get("posted_at"),
                "platform": post.get("platform")
            },
            "thread": {
                "parent": parent,
                "replies": replies,
                "depth": 1 if parent else 0
            },
            "account": {
                "username": post["social_accounts"]["username"]
            },
            "ai_decision": {
                "triage": comment.get("triage"),
                "ai_decision_id": comment.get("ai_decision_id"),
                "replied_at": comment.get("replied_at"),
                "ai_reply_text": comment.get("ai_reply_text")
            }
        }

        return {
            "success": True,
            "comment_id": comment_id,
            "context": context,
            "note": "This is the context that would be passed to the AI for decision making"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] Error getting comment context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-should-respond")
async def test_should_respond(
    comment_text: str,
    owner_username: str = "your_account",
    parent_author: str | None = None,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_user_id_from_token)
):
    """
    Test the "should AI respond" logic without actually processing a comment

    Helps test the conversation detection rules:
    - @mentions detection
    - Reply-to-other-user detection
    - Direct question detection

    Args:
        comment_text: The comment text to test
        owner_username: Your Instagram username (default: "your_account")
        parent_author: If this is a reply, who wrote the parent comment

    Returns:
        Whether AI should respond and why
    """
    import re

    try:
        results = {
            "comment_text": comment_text,
            "should_respond": True,
            "reasons": []
        }

        # Rule 1: Check @mentions
        mentions = re.findall(r'@(\w+)', comment_text)
        if mentions:
            results["mentions_found"] = mentions
            if owner_username not in mentions:
                results["should_respond"] = False
                results["reasons"].append(
                    f"Comment mentions other users (@{', @'.join(mentions)}) but not you (@{owner_username})"
                )

        # Rule 2: Check if it's a reply to someone else
        if parent_author and parent_author != owner_username:
            results["should_respond"] = False
            results["reasons"].append(
                f"This is a reply to @{parent_author}'s comment (not yours)"
            )

        # Rule 3: Simple question detection (keywords)
        question_keywords = ['?', 'how', 'what', 'when', 'where', 'why', 'who', 'can you', 'could you', 'price', 'cost', 'available']
        has_question = any(keyword in comment_text.lower() for keyword in question_keywords)
        results["appears_to_be_question"] = has_question

        if not has_question and results["should_respond"]:
            results["should_respond"] = False
            results["reasons"].append(
                "Comment doesn't appear to be a question or request directed at you"
            )

        # Final decision
        if results["should_respond"]:
            results["reasons"] = ["Comment appears to be a direct question/request to the account owner"]

        results["decision"] = "RESPOND" if results["should_respond"] else "IGNORE (user_conversation)"

        return {
            "success": True,
            **results
        }

    except Exception as e:
        logger.error(f"[DEBUG] Error testing should_respond logic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitored-posts-status")
async def monitored_posts_status(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_user_id_from_token)
):
    """
    Get status of all monitored posts for debugging

    Shows:
    - Which posts are being monitored
    - When they were last checked
    - When next check is scheduled
    - How many comments they have
    """
    try:
        # Get all monitored posts for user
        result = db.table("monitored_posts") \
            .select("*, social_accounts!inner(username, platform)") \
            .eq("user_id", current_user_id) \
            .order("posted_at", desc=True) \
            .execute()

        posts = result.data or []

        # Get comment counts
        for post in posts:
            comments_result = db.table("comments") \
                .select("id", count="exact") \
                .eq("monitored_post_id", post["id"]) \
                .execute()
            post["comments_count"] = comments_result.count or 0

            # Get unprocessed comments count
            unprocessed_result = db.table("comments") \
                .select("id", count="exact") \
                .eq("monitored_post_id", post["id"]) \
                .is_("triage", "null") \
                .execute()
            post["unprocessed_count"] = unprocessed_result.count or 0

        summary = {
            "total_posts": len(posts),
            "monitoring_enabled": len([p for p in posts if p.get("monitoring_enabled")]),
            "monitoring_disabled": len([p for p in posts if not p.get("monitoring_enabled")]),
            "total_comments": sum(p.get("comments_count", 0) for p in posts),
            "unprocessed_comments": sum(p.get("unprocessed_count", 0) for p in posts)
        }

        return {
            "success": True,
            "summary": summary,
            "posts": posts
        }

    except Exception as e:
        logger.error(f"[DEBUG] Error getting monitored posts status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
