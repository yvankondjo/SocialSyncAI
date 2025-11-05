import os
import httpx
import logging
from typing import Any, Dict, Optional, List
from fastapi import HTTPException
import asyncio
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class MessengerService:
    """
    Service for Facebook Messenger API interactions.
    Handles sending messages, validating credentials, and managing Pages.
    """

    def __init__(self, access_token: str, page_id: str):
        """
        Initialize MessengerService with page access token.

        Args:
            access_token: Facebook Page access token
            page_id: Facebook Page ID
        """
        self.access_token = access_token
        self.page_id = page_id

        if not self.access_token:
            raise RuntimeError('Messenger access_token is required')
        if not self.page_id:
            raise RuntimeError('Messenger page_id is required')

        graph_version = os.getenv('META_GRAPH_VERSION', 'v24.0')
        self.api_url = f'https://graph.facebook.com/{graph_version}'
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            timeout=httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=15.0)
        )

    async def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate Messenger credentials by fetching Page info.

        Returns:
            Dict with 'valid' bool and 'account_info' or 'error'
        """
        try:
            url = f'/{self.page_id}'
            params = {
                'fields': 'id,name,username,category,followers_count',
                'access_token': self.access_token
            }
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            logger.info(f"Messenger credentials valid. Page: {data.get('name', 'N/A')}")
            return {'valid': True, 'account_info': data}
        except Exception as e:
            logger.error(f'Messenger credentials invalid: {e}')
            return {'valid': False, 'error': str(e)}

    async def send_message(self, recipient_psid: str, text: str) -> Dict[str, Any]:
        """
        Send a text message via Messenger Send API.

        Args:
            recipient_psid: Page-scoped ID of the recipient
            text: Message text to send

        Returns:
            Dict with 'success' bool, 'message_id' or 'error'
        """
        url = '/me/messages'
        payload = {
            'recipient': {'id': recipient_psid},
            'message': {'text': text},
            'access_token': self.access_token
        }

        logger.info(f'Sending Messenger message to {recipient_psid}: {text[:50]}...')

        try:
            result = await self._send_with_retry(url, payload)
            return {
                'success': True,
                'message_id': result.get('message_id'),
                'recipient_id': result.get('recipient_id'),
                'result': result
            }
        except Exception as e:
            logger.error(f'Error sending Messenger message: {e}')
            return {'success': False, 'error': str(e)}

    async def send_typing_indicator(self, recipient_psid: str, action: str = "typing_on") -> Dict[str, Any]:
        """
        Send typing indicator or mark as read via Messenger Send API.

        Args:
            recipient_psid: Page-scoped ID of the recipient
            action: "typing_on", "typing_off", or "mark_seen"

        Returns:
            Dict with 'success' bool and details
        """
        if action not in ["typing_on", "typing_off", "mark_seen"]:
            return {'success': False, 'error': f'Unsupported action: {action}'}

        url = '/me/messages'
        payload = {
            'recipient': {'id': recipient_psid},
            'sender_action': action,
            'access_token': self.access_token
        }

        logger.info(f'Sending Messenger action "{action}" to {recipient_psid}')

        try:
            result = await self._send_with_retry(url, payload)
            return {'success': True, 'action': action, 'result': result}
        except Exception as e:
            logger.error(f'Error sending Messenger action "{action}": {e}')
            return {'success': False, 'error': str(e), 'action': action}

    async def send_typing_and_mark_read(self, recipient_psid: str, last_message_id: str) -> Dict[str, Any]:
        """
        Send typing_on and mark_seen in sequence for better UX.

        Args:
            recipient_psid: Page-scoped ID of the recipient
            last_message_id: ID of the last message (for logging)

        Returns:
            Dict with results of both actions
        """
        logger.info(f'Sending typing_on + mark_seen Messenger to {recipient_psid}')

        results = {}

        try:
            # Send typing indicator
            typing_result = await self.send_typing_indicator(recipient_psid, "typing_on")
            results['typing'] = typing_result

            # Mark as seen
            seen_result = await self.send_typing_indicator(recipient_psid, "mark_seen")
            results['mark_seen'] = seen_result

            success = typing_result.get('success', False) or seen_result.get('success', False)

            return {
                'success': success,
                'recipient_id': recipient_psid,
                'results': results,
                'message': f'Sender actions sent: typing={typing_result.get("success")}, seen={seen_result.get("success")}'
            }
        except Exception as e:
            logger.error(f'Error sending typing+seen Messenger to {recipient_psid}: {e}')
            return {
                'success': False,
                'error': str(e),
                'recipient_id': recipient_psid,
                'results': results
            }

    async def get_conversations(self, limit: int = 25) -> Dict[str, Any]:
        """
        Get list of conversations for this Page.

        Args:
            limit: Maximum number of conversations to fetch

        Returns:
            Dict with conversation data from Messenger API
        """
        try:
            url = f'/{self.page_id}/conversations'
            params = {
                'fields': 'id,updated_time,message_count,participants',
                'limit': limit,
                'access_token': self.access_token
            }
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'Error fetching Messenger conversations: {e}')
            raise RuntimeError(f'Error fetching conversations: {str(e)}')

    async def _send_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request with exponential backoff retry logic.

        Args:
            url: API endpoint path
            payload: Request payload

        Returns:
            JSON response from API

        Raises:
            RuntimeError: If all retry attempts fail
        """
        backoff = 0.5
        for attempt in range(3):
            try:
                resp = await self.client.post(url, json=payload)
                logger.info(f'Attempt {attempt + 1}: Status {resp.status_code}')

                # Retry on transient errors
                if resp.status_code in [429, 500, 502, 503, 504]:
                    raise httpx.HTTPStatusError('transient', request=resp.request, response=resp)

                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPStatusError as e:
                if attempt < 2 and e.response.status_code in [429, 500, 502, 503, 504]:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    error_text = e.response.text if hasattr(e, 'response') else str(e)
                    raise RuntimeError(f'Messenger API error: {error_text}')

            except httpx.TimeoutException:
                if attempt < 2:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    raise RuntimeError('Messenger API timeout')

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Singleton instance management
_messenger_service: Optional[MessengerService] = None


async def get_messenger_service(
    access_token: Optional[str] = None,
    page_id: Optional[str] = None
) -> MessengerService:
    """
    Get or create MessengerService instance.

    Args:
        access_token: Page access token (required if creating new instance)
        page_id: Page ID (required if creating new instance)

    Returns:
        MessengerService instance
    """
    global _messenger_service

    if access_token and page_id:
        return MessengerService(access_token, page_id)

    if _messenger_service is None:
        # Try to get from environment variables
        access_token = os.getenv('MESSENGER_ACCESS_TOKEN')
        page_id = os.getenv('MESSENGER_PAGE_ID')
        if access_token and page_id:
            _messenger_service = MessengerService(access_token, page_id)

    return _messenger_service
