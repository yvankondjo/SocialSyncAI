"""
Celery Workers for Scheduled Posts Publishing
Automatically publishes posts at scheduled times
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.workers.celery_app import celery_app
from app.core.database import get_supabase_client
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.scheduler.enqueue_due_posts")
def enqueue_due_posts() -> Dict[str, int]:
    """
    Periodic task to find posts ready to publish and enqueue them
    Runs every 1 minute via Celery Beat

    Returns:
        Dict with counts of posts_found and posts_enqueued
    """
    supabase = get_supabase_client()
    now = datetime.now(timezone.utc)

    try:
        # Find posts that are due to be published
        # Status = queued AND publish_at <= NOW
        result = supabase.table("scheduled_posts").select("id, platform").eq("status", "queued").lte("publish_at", now.isoformat()).execute()

        posts_found = len(result.data)
        posts_enqueued = 0

        for post in result.data:
            post_id = post["id"]

            # Update status to "publishing" to prevent double-processing
            update_result = supabase.table("scheduled_posts").update({
                "status": "publishing",
                "updated_at": now.isoformat()
            }).eq("id", post_id).eq("status", "queued").execute()  # Only update if still queued

            # Only enqueue if update succeeded (prevents race condition)
            if update_result.data:
                # Enqueue publish task
                publish_post.delay(post_id)
                posts_enqueued += 1

        logger.info(f"Enqueued {posts_enqueued}/{posts_found} due posts")

        return {
            "posts_found": posts_found,
            "posts_enqueued": posts_enqueued,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Error in enqueue_due_posts: {str(e)}")
        return {
            "posts_found": 0,
            "posts_enqueued": 0,
            "error": str(e)
        }


@celery_app.task(
    name="app.workers.scheduler.publish_post",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def publish_post(self, post_id: str) -> Dict[str, Any]:
    """
    Publish a scheduled post to its platform

    Args:
        post_id: UUID of the scheduled post

    Returns:
        Dict with publish result
    """
    supabase = get_supabase_client()
    started_at = datetime.now(timezone.utc)

    try:
        # Fetch post details
        post_result = supabase.table("scheduled_posts").select(
            "*, social_accounts!channel_id(access_token, account_id, metadata)"
        ).eq("id", post_id).single().execute()

        if not post_result.data:
            raise ValueError(f"Post {post_id} not found")

        post = post_result.data
        platform = post["platform"]
        content_json = post["content_json"]
        channel = post["social_accounts"]

        # Create run record
        run_data = {
            "scheduled_post_id": post_id,
            "started_at": started_at.isoformat(),
            "status": "success"  # Will update if fails
        }

        # Publish based on platform
        if platform == "whatsapp":
            platform_post_id = publish_to_whatsapp(channel, content_json)
        elif platform == "instagram":
            platform_post_id = publish_to_instagram(channel, content_json)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        # Mark post as published
        finished_at = datetime.now(timezone.utc)
        supabase.table("scheduled_posts").update({
            "status": "published",
            "platform_post_id": platform_post_id,
            "updated_at": finished_at.isoformat(),
            "retry_count": 0
        }).eq("id", post_id).execute()

        # Update run record
        run_data["finished_at"] = finished_at.isoformat()
        run_data["status"] = "success"
        supabase.table("post_runs").insert(run_data).execute()

        logger.info(f"Successfully published post {post_id} to {platform} (platform_id: {platform_post_id})")

        return {
            "success": True,
            "post_id": post_id,
            "platform": platform,
            "platform_post_id": platform_post_id,
            "duration_seconds": (finished_at - started_at).total_seconds()
        }

    except Exception as e:
        error_msg = str(e)
        finished_at = datetime.now(timezone.utc)

        logger.error(f"Error publishing post {post_id}: {error_msg}")

        # Get current retry count
        post_result = supabase.table("scheduled_posts").select("retry_count").eq("id", post_id).single().execute()
        current_retries = post_result.data.get("retry_count", 0) if post_result.data else 0

        # Increment retry count
        new_retry_count = current_retries + 1

        # Check if we should retry
        if new_retry_count < self.max_retries:
            # Update retry count and keep status as "publishing"
            supabase.table("scheduled_posts").update({
                "retry_count": new_retry_count,
                "error_message": error_msg,
                "updated_at": finished_at.isoformat()
            }).eq("id", post_id).execute()

            # Retry task
            logger.info(f"Retrying post {post_id} (attempt {new_retry_count + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        else:
            # Max retries reached, mark as failed
            supabase.table("scheduled_posts").update({
                "status": "failed",
                "retry_count": new_retry_count,
                "error_message": error_msg,
                "updated_at": finished_at.isoformat()
            }).eq("id", post_id).execute()

            # Create failed run record
            run_data = {
                "scheduled_post_id": post_id,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "status": "failed",
                "error": error_msg
            }
            supabase.table("post_runs").insert(run_data).execute()

            logger.error(f"Post {post_id} failed after {new_retry_count} retries: {error_msg}")

            return {
                "success": False,
                "post_id": post_id,
                "error": error_msg,
                "retries": new_retry_count
            }


def publish_to_whatsapp(channel: Dict[str, Any], content: Dict[str, Any]) -> str:
    """
    Publish content to WhatsApp

    Args:
        channel: Social account data with access_token, account_id, metadata
        content: Post content with text and/or media

    Returns:
        platform_post_id: WhatsApp message ID
    """
    service = WhatsAppService()

    # Extract phone_number_id from metadata
    phone_number_id = channel["metadata"].get("phone_number_id") or channel["account_id"]

    # Get text and media
    text = content.get("text", "")
    media = content.get("media", [])

    # For WhatsApp, we need a recipient. Use broadcast list or status update
    # This is a simplified implementation - you may need to adjust based on your WhatsApp setup

    # Option 1: Send as status update (if supported)
    # Option 2: Send to a broadcast list
    # Option 3: Send to user's own number (for testing)

    # For now, we'll use the WhatsApp Cloud API to send a message
    # You'll need to specify recipient - this is placeholder logic
    recipient = channel["metadata"].get("default_recipient", "")

    if not recipient:
        raise ValueError("WhatsApp posts require a default_recipient in channel metadata")

    # Send message
    if media:
        # Send media message
        media_item = media[0]  # Take first media
        result = service.send_media_message(
            phone_number_id=phone_number_id,
            to=recipient,
            media_type=media_item["type"],
            media_url=media_item["url"],
            caption=text or media_item.get("caption"),
            access_token=channel["access_token"]
        )
    else:
        # Send text message
        result = service.send_text_message(
            phone_number_id=phone_number_id,
            to=recipient,
            text=text,
            access_token=channel["access_token"]
        )

    return result.get("message_id") or result.get("id")


def publish_to_instagram(channel: Dict[str, Any], content: Dict[str, Any]) -> str:
    """
    Publish content to Instagram

    Args:
        channel: Social account data with access_token, account_id
        content: Post content with text and/or media

    Returns:
        platform_post_id: Instagram media ID
    """
    service = InstagramService()

    ig_user_id = channel["account_id"]
    access_token = channel["access_token"]

    text = content.get("text", "")
    media = content.get("media", [])

    if not media:
        raise ValueError("Instagram posts require at least one media item (image or video)")

    media_item = media[0]  # Instagram supports carousel, but we'll do single media for now

    # Create media container
    container_result = service.create_media_container(
        ig_user_id=ig_user_id,
        image_url=media_item["url"] if media_item["type"] == "image" else None,
        video_url=media_item["url"] if media_item["type"] == "video" else None,
        caption=text,
        access_token=access_token
    )

    container_id = container_result.get("id")

    if not container_id:
        raise ValueError("Failed to create Instagram media container")

    # Publish container
    publish_result = service.publish_media(
        ig_user_id=ig_user_id,
        creation_id=container_id,
        access_token=access_token
    )

    return publish_result.get("id")
