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

        # Use META_GRAPH_VERSION from config instead of hardcoded v23.0
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
            # Services should raise RuntimeError, not HTTPException (router's responsibility)
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
                    # Services should raise RuntimeError, not HTTPException (router's responsibility)
                    raise RuntimeError(f'Échec Instagram: {e.response.text}')
            except httpx.TimeoutException:
                if attempt < 2:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    # Services should raise RuntimeError, not HTTPException (router's responsibility)
                    raise RuntimeError('Timeout Instagram')

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