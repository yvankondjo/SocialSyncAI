"""
Platform Connector Interface
Abstract interface for social media platform integrations
Provides unified API for comments, replies, and other platform-specific operations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any


class PlatformConnector(ABC):
    """
    Abstract base class for platform connectors

    Each platform (Instagram, Facebook, LinkedIn, etc.) should implement this interface
    to provide a unified API for interacting with comments and posts.
    """

    name: str  # Platform name: 'instagram', 'facebook', 'linkedin', etc.

    @abstractmethod
    async def list_new_comments(
        self,
        post_platform_id: str,
        since_cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch new comments on a post from the platform API

        Args:
            post_platform_id: The post ID on the platform (e.g., Instagram media_id)
            since_cursor: Pagination cursor to fetch only new comments after this point

        Returns:
            Tuple of (comments, next_cursor):
            - comments: List of comment dicts with keys:
                - id: Platform comment ID (str)
                - author_name: Username of comment author (str)
                - author_id: Platform user ID of author (str)
                - text: Comment text content (str)
                - created_at: ISO timestamp string (str)
            - next_cursor: Pagination cursor for next batch (str or None if end)

        Example:
            comments, cursor = await connector.list_new_comments(
                "17841405309211844",
                since_cursor="QVFIU..."
            )
            # Returns: ([{id: "123", text: "Nice!", ...}], "QVFIU...")
        """
        pass

    @abstractmethod
    async def reply_to_comment(
        self,
        comment_platform_id: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Reply to a comment on the platform

        Args:
            comment_platform_id: The comment ID on the platform
            text: Reply text content

        Returns:
            Dict with reply result:
            - success: True if reply was sent successfully (bool)
            - reply_id: Platform ID of the reply (str, optional)
            - error: Error message if success=False (str, optional)

        Example:
            result = await connector.reply_to_comment(
                "17841405309211844",
                "Thanks for your feedback!"
            )
            # Returns: {success: True, reply_id: "456"}
        """
        pass

    async def hide_comment(
        self,
        comment_platform_id: str
    ) -> Dict[str, Any]:
        """
        Hide a comment (optional - not all platforms support this)

        Args:
            comment_platform_id: The comment ID to hide

        Returns:
            Dict with result:
            - success: True if hidden successfully (bool)
            - error: Error message if failed (str, optional)

        Default implementation returns not supported.
        """
        return {
            "success": False,
            "error": f"hide_comment not supported for platform '{self.name}'"
        }

    async def delete_comment(
        self,
        comment_platform_id: str
    ) -> Dict[str, Any]:
        """
        Delete a comment (optional - not all platforms support this)

        Args:
            comment_platform_id: The comment ID to delete

        Returns:
            Dict with result:
            - success: True if deleted successfully (bool)
            - error: Error message if failed (str, optional)

        Default implementation returns not supported.
        """
        return {
            "success": False,
            "error": f"delete_comment not supported for platform '{self.name}'"
        }
