import os
import httpx
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException
import asyncio
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_instagram_service: Optional['InstagramService'] = None

class InstagramService:
    def __init__(self, access_token: Optional[str] = None, page_id: Optional[str] = None):
        self.access_token = access_token or os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.page_id = page_id or os.getenv('INSTAGRAM_PAGE_ID')
        if not self.access_token:
            raise RuntimeError('INSTAGRAM_ACCESS_TOKEN manquant')
        if not self.page_id:
            raise RuntimeError('INSTAGRAM_PAGE_ID manquant')

        graph_version = os.getenv('META_GRAPH_VERSION', 'v24.0')
        self.api_url = f'https://graph.instagram.com/{graph_version}'
        self.client = httpx.AsyncClient(base_url=self.api_url, timeout=httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=15.0))

    async def validate_credentials(self) -> Dict[str, Any]:
        try:
            url = f'/{self.page_id}?fields=id,username,name,followers_count&access_token={self.access_token}'
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Credentials Instagram valides. Compte: @{data.get('username', 'N/A')}")
            return {'valid': True, 'account_info': data}
        except Exception as e:
            logger.error(f'Credentials Instagram invalides: {e}')
            return {'valid': False, 'error': str(e)}

    async def send_direct_message(self, recipient_ig_id: str, text: str) -> Dict[str, Any]:
        url = f'/{self.page_id}/messages'
        payload = {'recipient': {'id': recipient_ig_id}, 'message': {'text': text}, 'access_token': self.access_token}
        logger.info(f'Envoi DM Instagram vers {recipient_ig_id}: {text[:50]}...')
        try:
            result = await self._send_with_retry(url, payload)
            return {'success': True, 'message_id': result.get('id'), 'result': result}
        except Exception as e:
            logger.error(f'Erreur envoi DM Instagram: {e}')
            return {'success': False, 'error': str(e)}

    async def send_typing_indicator(self, recipient_ig_id: str, action: str = "typing_on") -> Dict[str, Any]:
        """
        Envoie un indicateur de frappe ou marque comme lu via Instagram Messaging API

        Args:
            recipient_ig_id: ID Instagram du destinataire
            action: "typing_on", "typing_off", ou "mark_seen"

        Returns:
            Dict avec success et détails
        """
        if action not in ["typing_on", "typing_off", "mark_seen"]:
            return {'success': False, 'error': f'Action non supportée: {action}'}

        url = f'/{self.page_id}/messages'
        payload = {
            'recipient': {'id': recipient_ig_id},
            'sender_action': action,
            'access_token': self.access_token
        }

        logger.info(f'Envoi action "{action}" Instagram vers {recipient_ig_id}')

        try:
            result = await self._send_with_retry(url, payload)
            return {'success': True, 'action': action, 'result': result}
        except Exception as e:
            logger.error(f'Erreur envoi action "{action}" Instagram: {e}')
            return {'success': False, 'error': str(e), 'action': action}

    async def send_typing_and_mark_read(self, recipient_ig_id: str, last_message_id: str) -> Dict[str, Any]:
        """
        send typing_on et mark_seen in sequence optimized for Instagram

        Args:
            recipient_ig_id: ID Instagram of the recipient
            last_message_id: ID of the last message (used for logging)

        Returns:
            Dict with results of the two actions
        """
        logger.info(f'Envoi typing_on + mark_seen Instagram vers {recipient_ig_id}')

        results = {}

        try:
            typing_result = await self.send_typing_indicator(recipient_ig_id, "typing_on")
            results['typing'] = typing_result

            seen_result = await self.send_typing_indicator(recipient_ig_id, "mark_seen")
            results['mark_seen'] = seen_result

            success = typing_result.get('success', False) or seen_result.get('success', False)

            return {
                'success': success,
                'recipient_id': recipient_ig_id,
                'results': results,
                'message': f'Sender actions envoyés: typing={typing_result.get("success")}, seen={seen_result.get("success")}'
            }

        except Exception as e:
            logger.error(f'Erreur envoi typing+seen Instagram vers {recipient_ig_id}: {e}')
            return {
                'success': False,
                'error': str(e),
                'recipient_id': recipient_ig_id,
                'results': results
            }

    async def get_conversations(self, limit: int = 25) -> Dict[str, Any]:
        try:
            url = f'/{self.page_id}/conversations?fields=id,updated_time,message_count&limit={limit}&access_token={self.access_token}'
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'Erreur conversations: {e}')
            raise RuntimeError(f'Erreur conversations: {str(e)}')

    async def reply_to_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        url = f'/{comment_id}/replies'
        payload = {'message': message, 'access_token': self.access_token}
        logger.info(f'Response to comment {comment_id}: {message[:50]}...')
        try:
            result = await self._send_with_retry(url, payload)
            return {'success': True, 'reply_id': result.get('id'), 'result': result}
        except Exception as e:
            logger.error(f'Erreur réponse commentaire Instagram: {e}')
            return {'success': False, 'error': str(e)}

    async def _send_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        backoff = 0.5
        for attempt in range(3):
            try:
                resp = await self.client.post(url, json=payload)
                logger.info(f'Tentative {attempt + 1}: Status {resp.status_code}')
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
                    raise RuntimeError(f'Échec Instagram: {e.response.text}')
            except httpx.TimeoutException:
                if attempt < 2:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    raise RuntimeError('Timeout Instagram')

    async def create_media_container(
        self,
        ig_user_id: str,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        caption: str = "",
        access_token: str = None
    ) -> Dict[str, Any]:
        """
        Create a media container for Instagram post.
        Step 1 of Instagram publishing process.

        Args:
            ig_user_id: Instagram Business Account ID
            image_url: URL to image (for image posts)
            video_url: URL to video (for video posts)
            caption: Post caption/text
            access_token: Access token for the request

        Returns:
            Dict with 'id' (container ID) and other metadata

        Docs: https://developers.facebook.com/docs/instagram-api/reference/ig-user/media
        """
        token = access_token or self.access_token

        params = {
            "caption": caption,
            "access_token": token
        }

        if image_url:
            params["image_url"] = image_url
        elif video_url:
            params["video_url"] = video_url
            params["media_type"] = "VIDEO"
        else:
            raise ValueError("Either image_url or video_url must be provided")

        try:
            response = await self.client.post(
                f"/{ig_user_id}/media",
                params=params
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"Created Instagram media container: {result.get('id')}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Instagram create_media_container error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to create Instagram media container: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Instagram create_media_container unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def check_container_status(
        self,
        container_id: str,
        access_token: str = None
    ) -> Dict[str, Any]:
        """
        Check the status of a media container.

        Args:
            container_id: Container ID from create_media_container
            access_token: Access token for the request

        Returns:
            Dict with 'status_code' field. Possible values:
            - EXPIRED: Container expired (after 24h)
            - ERROR: Processing error
            - FINISHED: Ready to publish
            - IN_PROGRESS: Still processing
            - PUBLISHED: Already published

        Docs: https://developers.facebook.com/docs/instagram-api/reference/ig-container
        """
        token = access_token or self.access_token

        params = {
            "fields": "id,status_code",
            "access_token": token
        }

        try:
            response = await self.client.get(
                f"/{container_id}",
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Instagram check_container_status error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to check container status: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Instagram check_container_status unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def wait_for_container_ready(
        self,
        container_id: str,
        access_token: str = None,
        max_wait_seconds: int = 60,
        poll_interval: int = 3
    ) -> bool:
        """
        Wait for a media container to be ready for publishing.

        Args:
            container_id: Container ID from create_media_container
            access_token: Access token for the request
            max_wait_seconds: Maximum time to wait (default 60 seconds)
            poll_interval: Seconds between status checks (default 3 seconds)

        Returns:
            True if container is ready (FINISHED status)

        Raises:
            HTTPException if container status is ERROR or EXPIRED, or timeout
        """
        token = access_token or self.access_token
        elapsed = 0

        logger.info(f"Waiting for container {container_id} to be ready (max {max_wait_seconds}s)")

        while elapsed < max_wait_seconds:
            status_data = await self.check_container_status(container_id, token)
            status = status_data.get('status_code')

            logger.info(f"Container {container_id} status: {status} (waited {elapsed}s)")

            if status == 'FINISHED':
                logger.info(f"Container {container_id} is ready to publish")
                return True
            elif status == 'ERROR':
                raise HTTPException(
                    status_code=400,
                    detail=f"Container processing failed with ERROR status"
                )
            elif status == 'EXPIRED':
                raise HTTPException(
                    status_code=400,
                    detail=f"Container expired (24h limit)"
                )
            elif status == 'PUBLISHED':
                logger.warning(f"Container {container_id} already published")
                return True

            # Status is IN_PROGRESS, wait and retry
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Timeout reached
        logger.error(f"Timeout waiting for container {container_id} (waited {elapsed}s)")
        raise HTTPException(
            status_code=408,
            detail=f"Timeout waiting for media processing. Container still in IN_PROGRESS status after {max_wait_seconds}s. Try again later."
        )

    async def publish_media(
        self,
        ig_user_id: str,
        creation_id: str,
        access_token: str = None
    ) -> Dict[str, Any]:
        """
        Publish a media container to Instagram feed.
        Step 2 of Instagram publishing process.

        Args:
            ig_user_id: Instagram Business Account ID
            creation_id: Container ID from create_media_container
            access_token: Access token for the request

        Returns:
            Dict with 'id' (published media ID)

        Docs: https://developers.facebook.com/docs/instagram-api/reference/ig-user/media_publish
        """
        token = access_token or self.access_token

        params = {
            "creation_id": creation_id,
            "access_token": token
        }

        try:
            response = await self.client.post(
                f"/{ig_user_id}/media_publish",
                params=params
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"Published Instagram media: {result.get('id')}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Instagram publish_media error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to publish Instagram media: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Instagram publish_media unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


_instagram_service: Optional[InstagramService] = None

async def get_instagram_service(access_token: Optional[str] = None, page_id: Optional[str] = None) -> InstagramService:
    global _instagram_service
    if access_token or page_id:
        return InstagramService(access_token, page_id)
    if _instagram_service is None:
        _instagram_service = InstagramService()
    return _instagram_service