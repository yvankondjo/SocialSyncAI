import os
import uuid
import httpx
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException
import asyncio
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, access_token: Optional[str] = None, phone_number_id: Optional[str] = None):
        """
        WhatsApp Business API service

        Args:
            access_token: WhatsApp access token (defaults from .env)
            phone_number_id: Phone number ID (defaults from .env)
        """
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")

        if not self.access_token:
            raise RuntimeError("Missing WHATSAPP_ACCESS_TOKEN")
        if not self.phone_number_id:
            raise RuntimeError("Missing WHATSAPP_PHONE_NUMBER_ID")

        graph_version = os.getenv("META_GRAPH_VERSION", "v24.0")
        self.api_url = f"https://graph.facebook.com/{graph_version}"
        
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=10.0),
        )

    async def validate_credentials(self) -> Dict[str, Any]:
        """Validate credentials and fetch phone number info."""
        try:
            url = f"/{self.phone_number_id}?fields=display_phone_number,verified_name,code_verification_status,quality_rating"
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            data = resp.json()
            logger.info(f"Credentials valid. Number: {data.get('display_phone_number', 'N/A')}")
            return {
                "valid": True,
                "phone_info": data
            }
        except Exception as e:
            logger.error(f"Invalid credentials: {e}")
            return {
                "valid": False,
                "error": str(e)
            }

    async def send_text_message(self, to: str, text: str, skip_validation: bool = True) -> Dict[str, Any]:
        """
        Send a WhatsApp text message.
        
        Args:
            to: Recipient phone number (format: 33612345678)
            text: Message content
            skip_validation: Skip validation to optimize performance
        """
        if not skip_validation:
            validation = await self.validate_credentials()
            if not validation["valid"]:
                raise HTTPException(status_code=401, detail="Invalid WhatsApp credentials")

        text = (text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Parameter 'text' is required for type 'text'")
        if len(text) > 4096:
            text = text[:4096]

        url = f"/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        logger.info(f"Sending message to {to}: {text[:50]}...")
        return await self._send_with_retry(url, payload, headers)

    async def send_template_message(self, to: str, template_name: str = "hello_world", language_code: str = "en_US") -> Dict[str, Any]:
        """
        Send an approved WhatsApp template.
        
        Args:
            to: Recipient phone number
            template_name: Template name (default: hello_world)
            language_code: Language code (default: en_US)
        """
        url = f"/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        
        logger.info(f"Sending template '{template_name}' to {to}")
        
        return await self._send_with_retry(url, payload, headers)

    async def send_media_message(self, to: str, media_type: str, media_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Send a WhatsApp media message (image, video, audio, document).
        
        Args:
            to: Recipient phone number
            media_type: Media type (image, video, audio, document)
            media_url: Media URL
            caption: Optional caption
        """
        url = f"/{self.phone_number_id}/messages"
        
        media_payload = {"link": media_url}
        if caption and media_type in ["image", "video", "document"]:
            media_payload["caption"] = caption
            
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": media_type,
            media_type: media_payload
        }
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        
        logger.info(f"Sending {media_type} to {to}: {media_url}")
        
        return await self._send_with_retry(url, payload, headers)


    async def send_typing_and_mark_read(self, to: str, last_wamid: str, skip_validation: bool = True) -> Dict[str, Any]:
        """
        Show 'typing…' indicator and mark last message as read.
        """
        if not skip_validation:
            validation = await self.validate_credentials()
            if not validation["valid"]:
                raise HTTPException(status_code=401, detail="Invalid WhatsApp credentials")

        url = f"/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "status": "read",
            "message_id": last_wamid,
            "typing_indicator": {"type": "text"}
        }
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        logger.info(f"Sending typing indicator to {to} (wamid={last_wamid})")
        return await self._send_with_retry(url, payload, headers)

    async def get_business_profile(self) -> Dict[str, Any]:
        """Fetch the WhatsApp business profile."""
        try:
            url = f"/{self.phone_number_id}/whatsapp_business_profile"
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching business profile: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching business profile: {e}")

    async def _send_with_retry(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Internal helper to send with automatic retries."""
        backoff = 0.5
        
        for attempt in range(3):
            try:
                resp = await self.client.post(url, json=payload, headers=headers)
                
                logger.info(f"Attempt {attempt + 1}: Status {resp.status_code}")
                
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError("transient", request=resp.request, response=resp)
                    
                resp.raise_for_status()
                result = resp.json()
                
                message_id = result.get('messages', [{}])[0].get('id', 'N/A')
                logger.info(f"Message sent successfully. ID: {message_id}")
                
                return result
                
            except httpx.HTTPStatusError as e:
                error_body = e.response.text
                logger.error(f"HTTP error {e.response.status_code}: {error_body}")
                
                if attempt < 2 and e.response.status_code in (429, 500, 502, 503, 504):
                    logger.info(f"Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                    
                raise HTTPException(
                    status_code=502, 
                    detail={
                        "msg": "Failed to send WhatsApp message", 
                        "status": e.response.status_code,
                        "body": error_body,
                        "url": str(e.request.url)
                    }
                )
                
            except httpx.TimeoutException:
                logger.error(f"Timeout attempt {attempt + 1}")
                if attempt < 2:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise HTTPException(status_code=504, detail="WhatsApp request timeout")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


_whatsapp_service: Optional[WhatsAppService] = None

async def get_whatsapp_service(access_token: Optional[str] = None, phone_number_id: Optional[str] = None) -> WhatsAppService:
    """Factory to get a WhatsAppService instance."""
    global _whatsapp_service
   
    if access_token or phone_number_id:
        return WhatsAppService(access_token, phone_number_id)
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
        
    return _whatsapp_service

if __name__ == "__main__":
    async def main():
        service = await get_whatsapp_service()
        print(await service.validate_credentials())
        print(await service.get_business_profile())

    asyncio.run(main())