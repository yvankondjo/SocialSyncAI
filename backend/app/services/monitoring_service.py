"""
Monitoring Service
Manages comment monitoring for all posts (scheduled + imported)
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from supabase import Client
from app.schemas.monitored_posts import (
    MonitoredPostCreate,
    MonitoredPostInDB,
    MonitoringRulesBase,
    MonitoringRulesInDB
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for managing post monitoring and auto-rules"""

    def __init__(self, supabase: Client, user_id: str):
        """
        Initialize monitoring service

        Args:
            supabase: Supabase client
            user_id: UUID of current user
        """
        self.supabase = supabase
        self.user_id = user_id

    async def sync_instagram_posts(
        self,
        social_account_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Import Instagram posts and apply auto-rules

        Args:
            social_account_id: UUID of social_accounts
            limit: Max number of posts to import

        Returns:
            Dict with posts_imported and posts_monitored counts

        Raises:
            ValueError: If account not found or not connected
        """
        try:
            # 1. Get account credentials
            account = self.supabase.table("social_accounts") \
                .select("*") \
                .eq("id", social_account_id) \
                .eq("user_id", self.user_id) \
                .single() \
                .execute()

            if not account.data:
                raise ValueError("Social account not found")

            if account.data.get("platform") != "instagram":
                raise ValueError("Only Instagram accounts are supported for import")

            logger.info(
                f"[MONITORING_SERVICE] Found Instagram account {social_account_id}, "
                f"has_token={bool(account.data.get('access_token'))}, "
                f"has_account_id={bool(account.data.get('account_id'))}"
            )

            # 2. Fetch posts from Instagram Graph API
            from app.services.instagram_connector import InstagramConnector

            access_token = account.data.get("access_token")
            page_id = account.data.get("account_id")  # Instagram user/page ID

            if not access_token:
                raise ValueError(
                    "Instagram access token missing. Please reconnect your Instagram account."
                )

            if not page_id:
                raise ValueError(
                    "Instagram account ID (page_id) missing. Please reconnect your Instagram account."
                )

            connector = InstagramConnector(access_token, page_id)
            media_list = await connector.fetch_user_media(limit=limit)

            logger.info(
                f"[MONITORING_SERVICE] Fetched {len(media_list)} posts "
                f"from Instagram for account {social_account_id}"
            )

            # 3. Insert/update monitored_posts
            imported_count = 0
            for media in media_list:
                post_data = {
                    "user_id": self.user_id,
                    "social_account_id": social_account_id,
                    "platform_post_id": media["id"],
                    "platform": "instagram",
                    "caption": media.get("caption"),
                    "media_url": media.get("media_url") or media.get("thumbnail_url"),
                    "posted_at": media["timestamp"],
                    "source": "imported"
                }

                # Upsert (insert or update on conflict)
                result = self.supabase.table("monitored_posts") \
                    .upsert(
                        post_data,
                        on_conflict="user_id,platform_post_id"
                    ) \
                    .execute()

                if result.data:
                    imported_count += 1

            logger.info(
                f"[MONITORING_SERVICE] Imported {imported_count} posts "
                f"for user {self.user_id}"
            )

            # 4. Apply auto-rules
            monitored_count = await self.apply_auto_rules(social_account_id)

            return {
                "success": True,
                "posts_imported": imported_count,
                "posts_monitored": monitored_count
            }

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error syncing Instagram posts: {e}")
            raise

    async def apply_auto_rules(self, social_account_id: str) -> int:
        """
        Apply auto-monitoring rules to latest posts

        Args:
            social_account_id: UUID of social_accounts

        Returns:
            Number of posts that were enabled for monitoring
        """
        try:
            # Get rules for this account
            rules = await self.get_rules(social_account_id)

            if not rules.auto_monitor_enabled:
                logger.info(
                    f"[MONITORING_SERVICE] Auto-monitoring disabled "
                    f"for account {social_account_id}"
                )
                return 0

            auto_count = rules.auto_monitor_count
            duration_days = rules.monitoring_duration_days

            # Get latest X posts that are NOT already monitored
            posts = self.supabase.table("monitored_posts") \
                .select("id, posted_at") \
                .eq("user_id", self.user_id) \
                .eq("social_account_id", social_account_id) \
                .eq("monitoring_enabled", False) \
                .order("posted_at", desc=True) \
                .limit(auto_count) \
                .execute()

            monitored_count = 0
            for post in (posts.data or []):
                await self.enable_monitoring(post["id"], duration_days)
                monitored_count += 1

            logger.info(
                f"[MONITORING_SERVICE] Auto-enabled monitoring on "
                f"{monitored_count} posts for account {social_account_id}"
            )

            return monitored_count

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error applying auto-rules: {e}")
            return 0

    async def enable_monitoring(
        self,
        post_id: str,
        duration_days: Optional[int] = None
    ) -> MonitoredPostInDB:
        """
        Enable monitoring on a post

        Args:
            post_id: UUID of monitored_posts
            duration_days: Custom duration (uses rules default if None)

        Returns:
            Updated MonitoredPostInDB

        Raises:
            ValueError: If post not found
        """
        try:
            # Get duration from rules if not specified
            if duration_days is None:
                rules = await self.get_rules()
                duration_days = rules.monitoring_duration_days

            # Use timezone-aware datetime for consistency with database
            now = datetime.now(timezone.utc)
            ends_at = now + timedelta(days=duration_days)

            result = self.supabase.table("monitored_posts") \
                .update({
                    "monitoring_enabled": True,
                    "monitoring_started_at": now.isoformat(),
                    "monitoring_ends_at": ends_at.isoformat(),
                    "next_check_at": now.isoformat()  # Poll immediately
                }) \
                .eq("id", post_id) \
                .eq("user_id", self.user_id) \
                .execute()

            if not result.data:
                raise ValueError("Post not found or access denied")

            logger.info(
                f"[MONITORING_SERVICE] Enabled monitoring on post {post_id} "
                f"for {duration_days} days"
            )

            return MonitoredPostInDB(**result.data[0])

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error enabling monitoring: {e}")
            raise

    async def disable_monitoring(self, post_id: str) -> MonitoredPostInDB:
        """
        Disable monitoring on a post

        Args:
            post_id: UUID of monitored_posts

        Returns:
            Updated MonitoredPostInDB

        Raises:
            ValueError: If post not found
        """
        try:
            result = self.supabase.table("monitored_posts") \
                .update({
                    "monitoring_enabled": False,
                    "monitoring_ends_at": None
                }) \
                .eq("id", post_id) \
                .eq("user_id", self.user_id) \
                .execute()

            if not result.data:
                raise ValueError("Post not found or access denied")

            logger.info(f"[MONITORING_SERVICE] Disabled monitoring on post {post_id}")

            return MonitoredPostInDB(**result.data[0])

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error disabling monitoring: {e}")
            raise

    async def get_monitored_posts(
        self,
        limit: int = 50,
        offset: int = 0,
        monitoring_enabled: Optional[bool] = None
    ) -> List[MonitoredPostInDB]:
        """
        Get all monitored posts for user with pagination

        Args:
            limit: Max results
            offset: Pagination offset
            monitoring_enabled: Filter by monitoring status (optional)

        Returns:
            List of MonitoredPostInDB with comments_count and days_remaining
        """
        try:
            query = self.supabase.table("monitored_posts") \
                .select("*, comments:comments(count)") \
                .eq("user_id", self.user_id)

            if monitoring_enabled is not None:
                query = query.eq("monitoring_enabled", monitoring_enabled)

            result = query \
                .order("posted_at", desc=True) \
                .range(offset, offset + limit - 1) \
                .execute()

            # Debug: Log raw data from database
            if result.data:
                first_raw = result.data[0]
                logger.info(
                    f"[MONITORING_SERVICE] Raw DB data sample - "
                    f"has_id={'id' in first_raw}, "
                    f"id_value={first_raw.get('id')}, "
                    f"platform_post_id={first_raw.get('platform_post_id')}"
                )

            posts = []
            # Use timezone-aware datetime to match database timestamps
            now = datetime.now(timezone.utc)

            for post_data in (result.data or []):
                post = MonitoredPostInDB(**post_data)

                # Add computed fields
                post.comments_count = len(post_data.get("comments", []))

                if post.monitoring_ends_at:
                    # Calculate days remaining
                    if isinstance(post.monitoring_ends_at, str):
                        ends_at = datetime.fromisoformat(
                            post.monitoring_ends_at.replace('Z', '+00:00')
                        )
                    else:
                        ends_at = post.monitoring_ends_at

                    # Both datetimes are now timezone-aware, can subtract safely
                    days_remaining = (ends_at - now).days
                    post.days_remaining = max(0, days_remaining)

                posts.append(post)

            return posts

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error getting monitored posts: {e}")
            raise

    async def get_rules(
        self,
        social_account_id: Optional[str] = None
    ) -> MonitoringRulesInDB:
        """
        Get or create monitoring rules for user/account

        Args:
            social_account_id: Optional account filter

        Returns:
            MonitoringRulesInDB (creates default if not exists)
        """
        try:
            # Query all rules for user, then filter by account
            query = self.supabase.table("monitoring_rules") \
                .select("*") \
                .eq("user_id", self.user_id)

            result = query.execute()

            # Filter results manually to find matching rule
            matching_rule = None
            if result and hasattr(result, 'data') and result.data:
                for rule in result.data:
                    rule_account_id = rule.get("social_account_id")
                    if social_account_id:
                        if rule_account_id == social_account_id:
                            matching_rule = rule
                            break
                    else:
                        if rule_account_id is None:
                            matching_rule = rule
                            break

            # Check if we found a matching rule
            if not matching_rule:
                # Create default rules
                logger.info(
                    f"[MONITORING_SERVICE] No existing rules found for user {self.user_id}, "
                    f"creating defaults..."
                )

                default_rules = {
                    "user_id": self.user_id,
                    "social_account_id": social_account_id,
                    "auto_monitor_enabled": True,
                    "auto_monitor_count": 5,
                    "monitoring_duration_days": 7
                }

                result = self.supabase.table("monitoring_rules") \
                    .insert(default_rules) \
                    .execute()

                logger.info(
                    f"[MONITORING_SERVICE] Created default rules "
                    f"for user {self.user_id}"
                )

                # Use the newly created rule
                if result and hasattr(result, 'data'):
                    if isinstance(result.data, dict):
                        matching_rule = result.data
                    elif isinstance(result.data, list) and len(result.data) > 0:
                        matching_rule = result.data[0]

            # Return the matching rule
            if matching_rule:
                return MonitoringRulesInDB(**matching_rule)
            else:
                raise ValueError("Failed to get or create monitoring rules")

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error getting rules: {e}")
            raise

    async def update_rules(
        self,
        rules: MonitoringRulesBase,
        social_account_id: Optional[str] = None
    ) -> MonitoringRulesInDB:
        """
        Update monitoring rules

        Args:
            rules: MonitoringRulesBase with new values
            social_account_id: Optional account filter

        Returns:
            Updated MonitoringRulesInDB
        """
        try:
            result = self.supabase.table("monitoring_rules") \
                .upsert({
                    "user_id": self.user_id,
                    "social_account_id": social_account_id,
                    **rules.dict()
                }, on_conflict="user_id,social_account_id") \
                .execute()

            logger.info(
                f"[MONITORING_SERVICE] Updated rules for user {self.user_id}: "
                f"auto_enabled={rules.auto_monitor_enabled}, "
                f"count={rules.auto_monitor_count}, "
                f"duration={rules.monitoring_duration_days} days"
            )

            return MonitoringRulesInDB(**result.data[0])

        except Exception as e:
            logger.error(f"[MONITORING_SERVICE] Error updating rules: {e}")
            raise
