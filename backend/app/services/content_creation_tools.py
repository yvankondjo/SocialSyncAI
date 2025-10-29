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
            # Normalize platform name to lowercase
            platform = platform.lower().strip()

            logger.info(f"Attempting to schedule post - user_id: {user_id}, platform: {platform}, publish_at: {publish_at}")

            # Validate platform
            valid_platforms = ['instagram', 'whatsapp', 'facebook', 'twitter']
            if platform not in valid_platforms:
                return SchedulePostResult(
                    success=False,
                    message=f"Invalid platform '{platform}'. Must be one of: {', '.join(valid_platforms)}"
                )

            # Parse date with multiple format support
            publish_datetime = None
            date_formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M",
            ]

            # Try ISO format first
            try:
                publish_datetime = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
            except ValueError:
                # Try other common formats
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

            # Check if date is in the future
            now = datetime.now(publish_datetime.tzinfo) if publish_datetime.tzinfo else datetime.now()
            if publish_datetime <= now:
                return SchedulePostResult(
                    success=False,
                    message=f"Cannot schedule posts in the past. Specified time: {publish_datetime}, Current time: {now}"
                )

            # Query for active social account
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

            # Convert datetime to ISO format string for database
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


def create_preview_post_tool(user_id: str):
    """Factory function to create preview_post tool"""

    @tool
    def preview_post(
        platform: str,
        content_text: str,
        media_urls: Optional[List[str]] = None
    ) -> PreviewPostResult:
        """
        Preview how a post will look on a specific platform

        This tool analyzes the post content and provides feedback including character count,
        platform-specific formatting, and suggestions for improvement.

        Args:
            platform: The platform to preview for (instagram, whatsapp, facebook, twitter) - LOWERCASE ONLY
            content_text: The text content to preview
            media_urls: Optional list of media URLs

        Returns:
            PreviewPostResult with preview details and suggestions
        """
        try:
            # Normalize platform name to lowercase
            platform = platform.lower().strip()

            logger.info(f"Previewing post for platform: {platform}, content length: {len(content_text)}")

            char_count = len(content_text)
            has_media = media_urls and len(media_urls) > 0

            platform_notes = []
            suggestions = []

            if platform == "instagram":
                platform_notes.append("Instagram allows up to 2,200 characters")
                platform_notes.append("First 125 characters visible without 'more' button")

                if char_count > 2200:
                    suggestions.append("Text is too long. Instagram limit is 2,200 characters.")
                elif char_count > 125:
                    suggestions.append("Consider putting key info in first 125 characters (visible without clicking 'more')")

                if not has_media:
                    suggestions.append("Instagram posts perform better with images or videos")

                if '#' not in content_text:
                    suggestions.append("Consider adding relevant hashtags to increase reach")

            elif platform == "twitter":
                platform_notes.append("Twitter allows 280 characters (4,000 for premium)")

                if char_count > 280:
                    suggestions.append(f"Tweet is too long ({char_count} chars). Standard limit is 280 characters.")
                elif char_count > 240:
                    suggestions.append("Tweet is near the character limit. Consider shortening.")

                if not has_media and char_count < 100:
                    suggestions.append("Short tweets with media get better engagement")

            elif platform == "whatsapp":
                platform_notes.append("WhatsApp supports messages up to 65,536 characters")
                platform_notes.append("Best practice: Keep messages concise and scannable")

                if char_count > 1000:
                    suggestions.append("Message is quite long. Consider breaking into multiple messages.")

            elif platform == "facebook":
                platform_notes.append("Facebook allows up to 63,206 characters")
                platform_notes.append("Posts with 40-80 characters get 86% more engagement")

                if char_count < 40:
                    suggestions.append("Very short post. Consider adding more context or a question to drive engagement.")
                elif char_count > 80 and not has_media:
                    suggestions.append("Posts with 40-80 characters typically get more engagement")

            if content_text.isupper():
                suggestions.append("ALL CAPS can seem aggressive. Consider mixed case.")

            if '!!!' in content_text or '???' in content_text:
                suggestions.append("Multiple punctuation marks can appear unprofessional")

            if has_media:
                estimated_reach = "High (posts with media get 2-3x more engagement)"
            elif char_count < 100:
                estimated_reach = "Medium (concise messages)"
            else:
                estimated_reach = "Medium"

            return PreviewPostResult(
                success=True,
                preview_text=content_text,
                character_count=char_count,
                estimated_reach=estimated_reach,
                platform_specific_notes=platform_notes,
                suggestions=suggestions if suggestions else ["Post looks good!"]
            )

        except Exception as e:
            logger.error(f"Error previewing post: {e}")
            return PreviewPostResult(
                success=False,
                preview_text="",
                character_count=0,
                estimated_reach="Unknown",
                platform_specific_notes=[],
                suggestions=[f"Error generating preview: {str(e)}"]
            )

    return preview_post
