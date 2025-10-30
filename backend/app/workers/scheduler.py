"""
Celery Workers for Scheduled Posts Publishing
Automatically publishes posts at scheduled times
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.workers.celery_app import celery
from app.db.session import get_db
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)


@celery.task(name="app.workers.scheduler.enqueue_due_posts")
def enqueue_due_posts() -> Dict[str, int]:
    """
    Periodic task to find posts ready to publish and enqueue them
    Runs every 1 minute via Celery Beat

    Returns:
        Dict with counts of posts_found and posts_enqueued
    """
    supabase = get_db()
    now = datetime.now(timezone.utc)

    try:
        result = (
            supabase.table("scheduled_posts")
            .select("id, platform")
            .eq("status", "queued")
            .lte("publish_at", now.isoformat())
            .execute()
        )

        posts_found = len(result.data)
        posts_enqueued = 0

        for post in result.data:
            post_id = post["id"]

            update_result = (
                supabase.table("scheduled_posts")
                .update({"status": "publishing", "updated_at": now.isoformat()})
                .eq("id", post_id)
                .eq("status", "queued")
                .execute()
            )

            if update_result.data:
                publish_post.delay(post_id)
                posts_enqueued += 1

        logger.info(f"Enqueued {posts_enqueued}/{posts_found} due posts")

        return {
            "posts_found": posts_found,
            "posts_enqueued": posts_enqueued,
            "timestamp": now.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in enqueue_due_posts: {str(e)}")
        return {"posts_found": 0, "posts_enqueued": 0, "error": str(e)}


@celery.task(
    name="app.workers.scheduler.publish_post",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def publish_post(self, post_id: str) -> Dict[str, Any]:
    """
    Publish a scheduled post to its platform

    NOTE: This is a synchronous Celery task that calls async functions via asyncio.run()

    Args:
        post_id: UUID of the scheduled post

    Returns:
        Dict with publish result
    """
    import asyncio

    supabase = get_db()
    started_at = datetime.now(timezone.utc)

    try:
        post_result = (
            supabase.table("scheduled_posts")
            .select("*, social_accounts!channel_id(access_token, account_id, platform)")
            .eq("id", post_id)
            .execute()
        )

        if not post_result.data or len(post_result.data) == 0:
            raise ValueError(f"Post {post_id} not found")

        post = post_result.data[0]
        platform = post["platform"]
        content_json = post["content_json"]
        channel = post.get("social_accounts")

        logger.info(f"Publishing post {post_id} - Platform: {platform}")
        logger.info(f"Channel data type: {type(channel)}")
        logger.info(f"Channel data: {channel}")

        if not channel:
            raise ValueError(
                f"Social account not found for channel_id in post {post_id}"
            )

        if not channel.get("access_token"):
            raise ValueError(
                f"Access token not found for social account {post.get('channel_id')}"
            )

        logger.info(
            f"Access token found: {bool(channel.get('access_token'))}, length: {len(channel.get('access_token', '')) if channel.get('access_token') else 0}"
        )

        # ============================================================================
        # CREDIT CHECKS DISABLED FOR TESTING
        # ============================================================================
        # TODO: Uncomment this section when ready to enforce credit checks
        #
        # from app.services.credits_service import CreditsService
        # POSTING_CREDIT_COST = 1  # Define cost per post
        #
        # credits_service = CreditsService(supabase)
        # can_publish = asyncio.run(credits_service.check_credits_available(
        #     post["user_id"], POSTING_CREDIT_COST
        # ))
        #
        # if not can_publish:
        #     # Mark post as failed due to insufficient credits
        #     supabase.table("scheduled_posts").update({
        #         "status": "failed",
        #         "error_message": "Insufficient credits for publishing",
        #         "updated_at": datetime.now(timezone.utc).isoformat()
        #     }).eq("id", post_id).execute()
        #     return {"success": False, "error": "Insufficient credits"}
        # ============================================================================

        run_data = {
            "scheduled_post_id": post_id,
            "started_at": started_at.isoformat(),
            "status": "success",
        }

        if platform == "whatsapp":
            platform_post_id = asyncio.run(publish_to_whatsapp(channel, content_json))
        elif platform == "instagram":
            platform_post_id = asyncio.run(publish_to_instagram(channel, content_json))
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        finished_at = datetime.now(timezone.utc)
        supabase.table("scheduled_posts").update(
            {
                "status": "published",
                "platform_post_id": platform_post_id,
                "updated_at": finished_at.isoformat(),
                "retry_count": 0,
            }
        ).eq("id", post_id).execute()

        run_data["finished_at"] = finished_at.isoformat()
        run_data["status"] = "success"
        supabase.table("post_runs").insert(run_data).execute()

        # ============================================================================
        # CREDIT DEDUCTION DISABLED FOR TESTING
        # ============================================================================
        # TODO: Uncomment this section when ready to deduct credits
        #
        # asyncio.run(credits_service.deduct_credits(
        #     user_id=post["user_id"],
        #     credits_to_deduct=POSTING_CREDIT_COST,
        #     reason=f"Post published to {platform}",
        #     metadata={"post_id": post_id, "platform": platform}
        # ))
        # ============================================================================

        logger.info(
            f"Successfully published post {post_id} to {platform} (platform_id: {platform_post_id})"
        )

        return {
            "success": True,
            "post_id": post_id,
            "platform": platform,
            "platform_post_id": platform_post_id,
            "duration_seconds": (finished_at - started_at).total_seconds(),
        }

    except Exception as e:
        error_msg = str(e)
        finished_at = datetime.now(timezone.utc)

        logger.error(f"Error publishing post {post_id}: {error_msg}")

        post_result = (
            supabase.table("scheduled_posts")
            .select("retry_count")
            .eq("id", post_id)
            .single()
            .execute()
        )
        current_retries = (
            post_result.data.get("retry_count", 0) if post_result.data else 0
        )

        new_retry_count = current_retries + 1

        if new_retry_count < self.max_retries:
            supabase.table("scheduled_posts").update(
                {
                    "retry_count": new_retry_count,
                    "error_message": error_msg,
                    "updated_at": finished_at.isoformat(),
                }
            ).eq("id", post_id).execute()

            logger.info(
                f"Retrying post {post_id} (attempt {new_retry_count + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)
        else:
            supabase.table("scheduled_posts").update(
                {
                    "status": "failed",
                    "retry_count": new_retry_count,
                    "error_message": error_msg,
                    "updated_at": finished_at.isoformat(),
                }
            ).eq("id", post_id).execute()

            run_data = {
                "scheduled_post_id": post_id,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "status": "failed",
                "error": error_msg,
            }
            supabase.table("post_runs").insert(run_data).execute()

            logger.error(
                f"Post {post_id} failed after {new_retry_count} retries: {error_msg}"
            )

            return {
                "success": False,
                "post_id": post_id,
                "error": error_msg,
                "retries": new_retry_count,
            }


async def publish_to_whatsapp(channel: Dict[str, Any], content: Dict[str, Any]) -> str:
    """
    Publish content to WhatsApp

    Args:
        channel: Social account data with access_token, account_id
        content: Post content with text, media, and recipient

    Returns:
        platform_post_id: WhatsApp message ID
    """
    service = WhatsAppService(
        access_token=channel["access_token"], phone_number_id=channel["account_id"]
    )

    text = content.get("text", "")
    media = content.get("media", [])

    recipient = content.get("recipient", "")

    if not recipient:
        raise ValueError("WhatsApp posts require a 'recipient' field in content_json")

    if media:
        media_item = media[0]
        result = await service.send_media_message(
            to=recipient,
            media_type=media_item["type"],
            media_url=media_item["url"],
            caption=text or media_item.get("caption"),
        )
    else:
        result = await service.send_text_message(to=recipient, text=text)

    return result.get("message_id") or result.get("id")


async def publish_to_instagram(channel: Dict[str, Any], content: Dict[str, Any]) -> str:
    """
    Publish content to Instagram

    Args:
        channel: Social account data with access_token, account_id
        content: Post content with text and/or media

    Returns:
        platform_post_id: Instagram media ID
    """
    ig_user_id = channel["account_id"]
    access_token = channel["access_token"]

    service = InstagramService(access_token=access_token, page_id=ig_user_id)

    text = content.get("text", "")
    media = content.get("media", [])

    if not media:
        raise ValueError(
            "Instagram posts require at least one media item (image or video)"
        )

    media_item = media[0]

    # Step 1: Create media container
    container_result = await service.create_media_container(
        ig_user_id=ig_user_id,
        image_url=media_item["url"] if media_item["type"] == "image" else None,
        video_url=media_item["url"] if media_item["type"] == "video" else None,
        caption=text,
    )

    container_id = container_result.get("id")

    if not container_id:
        raise ValueError("Failed to create Instagram media container")

    # Step 2: Wait for container to be ready (Instagram needs time to process media)
    # This prevents "Media ID is not available" errors
    await service.wait_for_container_ready(
        container_id=container_id,
        access_token=access_token,
        max_wait_seconds=60,
        poll_interval=3
    )

    # Step 3: Publish the container
    publish_result = await service.publish_media(
        ig_user_id=ig_user_id, creation_id=container_id
    )

    return publish_result.get("id")
