"""
Instagram Platform Connector
Implementation of PlatformConnector for Instagram
"""
import logging
from typing import List, Dict, Tuple, Optional, Any
from app.services.platform_connector import PlatformConnector
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)


class InstagramConnector(PlatformConnector):
    """
    Instagram implementation of PlatformConnector

    Uses Instagram Graph API via InstagramService to fetch comments
    and post replies on Instagram posts.
    """

    name = "instagram"

    def __init__(self, access_token: str, page_id: str):
        """
        Initialize Instagram connector

        Args:
            access_token: Instagram/Facebook access token
            page_id: Instagram business account page ID
        """
        self.service = InstagramService(access_token, page_id)

    async def list_new_comments(
        self,
        post_platform_id: str,
        since_cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch comments from Instagram Graph API

        API: GET /{media_id}/comments
        Docs: https://developers.facebook.com/docs/instagram-api/reference/ig-media/comments

        Args:
            post_platform_id: Instagram media_id
            since_cursor: Pagination cursor (after parameter)

        Returns:
            (comments, next_cursor)
        """
        try:
            url = f'/{post_platform_id}/comments'
            params = {
                'fields': 'id,username,text,timestamp,from,parent_id,like_count',  # Added parent_id for threads
                'limit': 50,  # Max 50 per request
                'access_token': self.service.access_token
            }

            if since_cursor:
                params['after'] = since_cursor

            logger.info(f"[IG_CONNECTOR] Fetching comments for media {post_platform_id}")

            resp = await self.service.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            # Normalize comments to standard format
            comments = []
            for c in data.get('data', []):
                # Instagram API returns username in 'from' object: {"from": {"id": "...", "username": "..."}}
                # Fallback chain: from.username → username (root level) → "Unknown User"
                from_data = c.get('from', {})
                author_name = from_data.get('username') or c.get('username') or 'Unknown User'
                author_id = from_data.get('id')

                comments.append({
                    'id': c['id'],
                    'author_name': author_name,
                    'author_id': author_id,
                    'text': c['text'],
                    'created_at': c['timestamp'],
                    'parent_id': c.get('parent_id'),  # For thread reconstruction
                    'like_count': c.get('like_count', 0)
                })

            # Extract next cursor for pagination
            next_cursor = data.get('paging', {}).get('cursors', {}).get('after')

            logger.info(
                f"[IG_CONNECTOR] Fetched {len(comments)} comments for {post_platform_id}, "
                f"next_cursor={'exists' if next_cursor else 'none'}"
            )

            return (comments, next_cursor)

        except Exception as e:
            logger.error(f"[IG_CONNECTOR] Error fetching comments for {post_platform_id}: {e}")
            # Return empty list on error to avoid breaking the polling loop
            return ([], None)

    async def reply_to_comment(
        self,
        comment_platform_id: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Reply to Instagram comment

        Delegates to InstagramService.reply_to_comment which uses:
        POST /{comment_id}/replies

        Args:
            comment_platform_id: Instagram comment ID
            text: Reply text

        Returns:
            {success: bool, reply_id: str, error: str}
        """
        try:
            logger.info(
                f"[IG_CONNECTOR] Replying to comment {comment_platform_id}: "
                f"{text[:50]}..."
            )

            # Use existing service method
            result = await self.service.reply_to_comment(comment_platform_id, text)

            if result.get('success'):
                logger.info(
                    f"[IG_CONNECTOR] Successfully replied to {comment_platform_id}, "
                    f"reply_id={result.get('reply_id')}"
                )
            else:
                logger.error(
                    f"[IG_CONNECTOR] Failed to reply to {comment_platform_id}: "
                    f"{result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"[IG_CONNECTOR] Error replying to comment {comment_platform_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def hide_comment(
        self,
        comment_platform_id: str
    ) -> Dict[str, Any]:
        """
        Hide Instagram comment

        API: POST /{comment_id}?hide=true

        Args:
            comment_platform_id: Instagram comment ID

        Returns:
            {success: bool, error: str}
        """
        try:
            url = f'/{comment_platform_id}'
            params = {
                'hide': 'true',
                'access_token': self.service.access_token
            }

            logger.info(f"[IG_CONNECTOR] Hiding comment {comment_platform_id}")

            resp = await self.service.client.post(url, params=params)
            resp.raise_for_status()

            logger.info(f"[IG_CONNECTOR] Successfully hid comment {comment_platform_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"[IG_CONNECTOR] Error hiding comment {comment_platform_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def delete_comment(
        self,
        comment_platform_id: str
    ) -> Dict[str, Any]:
        """
        Delete Instagram comment

        API: DELETE /{comment_id}

        Args:
            comment_platform_id: Instagram comment ID

        Returns:
            {success: bool, error: str}
        """
        try:
            url = f'/{comment_platform_id}'
            params = {'access_token': self.service.access_token}

            logger.info(f"[IG_CONNECTOR] Deleting comment {comment_platform_id}")

            resp = await self.service.client.delete(url, params=params)
            resp.raise_for_status()

            logger.info(f"[IG_CONNECTOR] Successfully deleted comment {comment_platform_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"[IG_CONNECTOR] Error deleting comment {comment_platform_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def fetch_user_media(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch user's Instagram media posts

        API: GET /{ig_user_id}/media
        Docs: https://developers.facebook.com/docs/instagram-api/reference/ig-user/media

        Args:
            limit: Max number of posts to fetch (default 50, max 100)

        Returns:
            List of media objects with fields: id, caption, media_type, media_url, timestamp, etc.
        """
        try:
            # Get Instagram user ID from page_id
            page_id = self.service.page_id

            url = f'/{page_id}/media'
            params = {
                'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,comments_count,like_count',
                'limit': min(limit, 100),  # API max is 100
                'access_token': self.service.access_token
            }

            logger.info(f"[IG_CONNECTOR] Fetching user media (limit={limit})")

            resp = await self.service.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            media_list = data.get('data', [])

            logger.info(
                f"[IG_CONNECTOR] Fetched {len(media_list)} media posts "
                f"for user {page_id}"
            )

            return media_list

        except Exception as e:
            logger.error(f"[IG_CONNECTOR] Error fetching user media: {e}")
            # Return empty list on error to avoid breaking the flow
            return []

    async def fetch_post_details(
        self,
        media_id: str
    ) -> Dict[str, Any]:
        """
        Fetch details of a specific Instagram post

        API: GET /{media_id}
        Docs: https://developers.facebook.com/docs/instagram-api/reference/ig-media

        Args:
            media_id: Instagram media ID

        Returns:
            Media object with all details
        """
        try:
            url = f'/{media_id}'
            params = {
                'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,comments_count,like_count,username',
                'access_token': self.service.access_token
            }

            logger.info(f"[IG_CONNECTOR] Fetching details for media {media_id}")

            resp = await self.service.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            logger.info(
                f"[IG_CONNECTOR] Fetched details for media {media_id}: "
                f"type={data.get('media_type')}, comments={data.get('comments_count')}"
            )

            return data

        except Exception as e:
            logger.error(f"[IG_CONNECTOR] Error fetching post details for {media_id}: {e}")
            return {}
