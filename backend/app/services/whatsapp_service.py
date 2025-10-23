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
        Service WhatsApp Business API

        Args:
            access_token: Token d'accès WhatsApp (par défaut depuis .env)
            phone_number_id: ID du numéro de téléphone (par défaut depuis .env)
        """
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")

        if not self.access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN manquant")
        if not self.phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID manquant")

        # Use META_GRAPH_VERSION from config instead of hardcoded v23.0
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
        """Valider les credentials et récupérer les infos du numéro"""
        try:
            url = f"/{self.phone_number_id}?fields=display_phone_number,verified_name,code_verification_status,quality_rating"
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            data = resp.json()
            logger.info(f"Credentials valides. Numéro: {data.get('display_phone_number', 'N/A')}")
            return {
                "valid": True,
                "phone_info": data
            }
        except Exception as e:
            logger.error(f"Credentials invalides: {e}")
            return {
                "valid": False,
                "error": str(e)
            }

    async def send_text_message(self, to: str, text: str, skip_validation: bool = True) -> Dict[str, Any]:
        """
        Envoyer un message texte WhatsApp
        
        Args:
            to: Numéro de téléphone destinataire (format: 33612345678)
            text: Contenu du message
            skip_validation: Éviter la validation pour optimiser les performances
        """
        if not skip_validation:
            validation = await self.validate_credentials()
            if not validation["valid"]:
                raise HTTPException(status_code=401, detail="Credentials WhatsApp invalides")

        text = (text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Paramètre 'text' requis pour type 'text'")
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
        logger.info(f"Envoi message vers {to}: {text[:50]}...")
        return await self._send_with_retry(url, payload, headers)

    async def send_template_message(self, to: str, template_name: str = "hello_world", language_code: str = "en_US") -> Dict[str, Any]:
        """
        Envoyer un template WhatsApp approuvé
        
        Args:
            to: Numéro de téléphone destinataire
            template_name: Nom du template (par défaut: hello_world)
            language_code: Code langue (par défaut: en_US)
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
        
        logger.info(f"Envoi template '{template_name}' vers {to}")
        
        return await self._send_with_retry(url, payload, headers)

    async def send_media_message(self, to: str, media_type: str, media_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Envoyer un message avec média (image, vidéo, audio, document)
        
        Args:
            to: Numéro de téléphone destinataire
            media_type: Type de média (image, video, audio, document)
            media_url: URL du média
            caption: Légende optionnelle
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
        
        logger.info(f"Envoi {media_type} vers {to}: {media_url}")
        
        return await self._send_with_retry(url, payload, headers)


    async def send_typing_and_mark_read(self, to: str, last_wamid: str, skip_validation: bool = True) -> Dict[str, Any]:
        """
        Affiche 'typing…' et marque le dernier message comme lu.
        """
        if not skip_validation:
            validation = await self.validate_credentials()
            if not validation["valid"]:
                raise HTTPException(status_code=401, detail="Credentials WhatsApp invalides")

        url = f"/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "status": "read",
            "message_id": last_wamid,
            "typing_indicator": {"type": "text"}
        }
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        logger.info(f"Envoi indicateur de frappe vers {to} (wamid={last_wamid})")
        return await self._send_with_retry(url, payload, headers)

    async def get_business_profile(self) -> Dict[str, Any]:
        """Récupérer le profil business WhatsApp"""
        try:
            url = f"/{self.phone_number_id}/whatsapp_business_profile"
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Erreur profil business: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur récupération profil: {e}")

    async def _send_with_retry(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Méthode interne pour envoyer avec retry automatique"""
        backoff = 0.5
        
        for attempt in range(3):
            try:
                resp = await self.client.post(url, json=payload, headers=headers)
                
                logger.info(f"Tentative {attempt + 1}: Status {resp.status_code}")
                
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError("transient", request=resp.request, response=resp)
                    
                resp.raise_for_status()
                result = resp.json()
                
                message_id = result.get('messages', [{}])[0].get('id', 'N/A')
                logger.info(f"Message envoyé avec succès. ID: {message_id}")
                
                return result
                
            except httpx.HTTPStatusError as e:
                error_body = e.response.text
                logger.error(f"Erreur HTTP {e.response.status_code}: {error_body}")
                
                if attempt < 2 and e.response.status_code in (429, 500, 502, 503, 504):
                    logger.info(f"Retry dans {backoff}s...")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                    
                raise HTTPException(
                    status_code=502, 
                    detail={
                        "msg": "Échec envoi WhatsApp", 
                        "status": e.response.status_code,
                        "body": error_body,
                        "url": str(e.request.url)
                    }
                )
                
            except httpx.TimeoutException:
                logger.error(f"Timeout tentative {attempt + 1}")
                if attempt < 2:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise HTTPException(status_code=504, detail="Timeout requête WhatsApp")

    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


_whatsapp_service: Optional[WhatsAppService] = None

async def get_whatsapp_service(access_token: Optional[str] = None, phone_number_id: Optional[str] = None) -> WhatsAppService:
    """Factory pour obtenir une instance du service WhatsApp"""
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