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
        self.api_url = 'https://graph.instagram.com/v23.0'
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
        return await self._send_with_retry(url, payload)

    async def publish_feed_post(self, image_url: str, caption: str = '') -> Dict[str, Any]:
        container_data = {'image_url': image_url, 'caption': caption, 'access_token': self.access_token}
        url = f'/{self.page_id}/media'
        logger.info(f'Création container média Instagram: {image_url}')
        try:
            resp = await self.client.post(url, json=container_data)
            resp.raise_for_status()
            container_result = resp.json()
            container_id = container_result['id']
            publish_data = {'creation_id': container_id, 'access_token': self.access_token}
            publish_url = f'/{self.page_id}/media_publish'
            resp = await self.client.post(publish_url, json=publish_data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'Erreur publication Instagram: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur publication: {str(e)}')

    async def publish_story(self, image_url: str) -> Dict[str, Any]:
        container_data = {'image_url': image_url, 'media_type': 'STORIES', 'access_token': self.access_token}
        url = f'/{self.page_id}/media'
        logger.info(f'Création story Instagram: {image_url}')
        try:
            resp = await self.client.post(url, json=container_data)
            resp.raise_for_status()
            container_result = resp.json()
            container_id = container_result['id']
            publish_data = {'creation_id': container_id, 'access_token': self.access_token}
            publish_url = f'/{self.page_id}/media_publish'
            resp = await self.client.post(publish_url, json=publish_data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'Erreur story: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur story: {str(e)}')

    async def get_conversations(self, limit: int = 25) -> Dict[str, Any]:
        try:
            url = f'/{self.page_id}/conversations?fields=id,updated_time,message_count&limit={limit}&access_token={self.access_token}'
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'Erreur conversations: {e}')
            raise HTTPException(status_code=500, detail=f'Erreur conversations: {str(e)}')

    async def reply_to_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        url = f'/{comment_id}/replies'
        payload = {'message': message, 'access_token': self.access_token}
        logger.info(f'Réponse au commentaire {comment_id}: {message[:50]}...')
        return await self._send_with_retry(url, payload)

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
                    raise HTTPException(status_code=502, detail=f'Échec Instagram: {e.response.text}')
            except httpx.TimeoutException:
                if attempt < 2:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    raise HTTPException(status_code=504, detail='Timeout Instagram')

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