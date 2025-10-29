"""
Content Creation Tools
Tools for AI-assisted social media content creation
"""
import logging
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from datetime import datetime

from app.schemas.scheduled_posts import ScheduledPostCreate, PostContent, Platform

logger = logging.getLogger(__name__)


class SchedulePostInput(BaseModel):
    """Input for scheduling a post"""
    platform: Literal["whatsapp", "instagram", "facebook", "twitter"] = Field(
        ..., description="The social media platform to post to"
    )
    content_text: str = Field(..., description="The text content of the post")
    publish_at: str = Field(
        ...,
        description="When to publish the post in ISO format (YYYY-MM-DDTHH:MM:SS)"
    )
    media_urls: Optional[List[str]] = Field(
        default=None,
        description="Optional list of media URLs to attach to the post"
    )


class PreviewPostInput(BaseModel):
    """Input for previewing a post"""
    platform: Literal["whatsapp", "instagram", "facebook", "twitter"] = Field(
        ..., description="The social media platform for the post"
    )
    content_text: str = Field(..., description="The text content to preview")
    media_urls: Optional[List[str]] = Field(
        default=None,
        description="Optional list of media URLs"
    )


class SchedulePostResult(BaseModel):
    """Result of scheduling a post"""
    success: bool
    post_id: Optional[str] = None
    scheduled_for: Optional[str] = None
    platform: Optional[str] = None
    message: str


class PreviewPostResult(BaseModel):
    """Result of previewing a post"""
    success: bool
    preview_text: str
    character_count: int
    estimated_reach: str
    platform_specific_notes: List[str]
    suggestions: List[str]


def create_schedule_post_tool(user_id: str, supabase_client):
    """Factory function to create schedule_post tool with user_id and database"""

    @tool
    def schedule_post(
        platform: str,
        content_text: str,
        publish_at: str,
        media_urls: Optional[List[str]] = None
    ) -> SchedulePostResult:
        """
        Schedule a social media post for future publication

        This tool creates a scheduled post that will be automatically published at the specified time.
        The post must be scheduled for a future date/time.

        Args:
            platform: The platform to post to (instagram, whatsapp, facebook, twitter) - LOWERCASE ONLY
            content_text: The text content of the post
            publish_at: When to publish in ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS)
            media_urls: Optional list of media URLs to attach

        Returns:
            SchedulePostResult with success status and details
        """
        try:

            platform = platform.lower().strip()

            logger.info(f"Attempting to schedule post - user_id: {user_id}, platform: {platform}, publish_at: {publish_at}")

            valid_platforms = ['instagram', 'whatsapp', 'facebook', 'twitter']
            if platform not in valid_platforms:
                return SchedulePostResult(
                    success=False,
                    message=f"Invalid platform '{platform}'. Must be one of: {', '.join(valid_platforms)}"
                )

            publish_datetime = None
            date_formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M",
            ]

            try:
                publish_datetime = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
            except ValueError:
                for fmt in date_formats:
                    try:
                        publish_datetime = datetime.strptime(publish_at, fmt)
                        break
                    except ValueError:
                        continue

            if not publish_datetime:
                return SchedulePostResult(
                    success=False,
                    message=f"Invalid date format '{publish_at}'. Use ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS"
                )

            logger.info(f"Parsed datetime: {publish_datetime}")

            now = datetime.now(publish_datetime.tzinfo) if publish_datetime.tzinfo else datetime.now()
            if publish_datetime <= now:
                return SchedulePostResult(
                    success=False,
                    message=f"Cannot schedule posts in the past. Specified time: {publish_datetime}, Current time: {now}"
                )

            logger.info(f"Querying social_accounts for user_id={user_id}, platform={platform}")
            channels_result = supabase_client.table("social_accounts")\
                .select("id, platform, username")\
                .eq("user_id", user_id)\
                .eq("platform", platform)\
                .eq("is_active", True)\
                .limit(1)\
                .execute()

            logger.info(f"Social accounts query result: {len(channels_result.data) if channels_result.data else 0} accounts found")

            if not channels_result.data:
                return SchedulePostResult(
                    success=False,
                    message=f"No active {platform} account found. Please connect a {platform} account first in /dashboard/connect"
                )

            channel = channels_result.data[0]
            logger.info(f"Found channel: {channel['id']} (@{channel['username']})")

            media = None
            if media_urls:
                media = [{"type": "image", "url": url} for url in media_urls]

            publish_at_iso = publish_datetime.isoformat()

            post_data = {
                "user_id": user_id,
                "channel_id": channel["id"],
                "platform": platform,
                "content_json": {
                    "text": content_text,
                    "media": media
                },
                "publish_at": publish_at_iso,
                "status": "queued",
                "retry_count": 0
            }

            logger.info(f"Inserting scheduled post: channel_id={channel['id']}, platform={platform}, publish_at={publish_at_iso}")

            result = supabase_client.table("scheduled_posts")\
                .insert(post_data)\
                .execute()

            if result.data:
                post = result.data[0]
                logger.info(f"Successfully created scheduled post: post_id={post['id']}")
                return SchedulePostResult(
                    success=True,
                    post_id=post["id"],
                    scheduled_for=publish_at_iso,
                    platform=platform,
                    message=f"✅ Post successfully scheduled for {publish_datetime.strftime('%Y-%m-%d at %H:%M')} on {platform} (@{channel['username']})"
                )
            else:
                logger.error(f"Failed to insert scheduled post - no data returned from database")
                return SchedulePostResult(
                    success=False,
                    message="Failed to create scheduled post in database"
                )

        except ValueError as e:
            logger.error(f"ValueError in schedule_post: {e}", exc_info=True)
            return SchedulePostResult(
                success=False,
                message=f"Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS): {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in schedule_post: {e}", exc_info=True)
            return SchedulePostResult(
                success=False,
                message=f"Error scheduling post: {str(e)}"
            )

    return schedule_post

