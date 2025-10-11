import logging
import os
from typing import Optional

from app.db.session import get_db
from app.services.email_service import EmailService
from app.services.link_service import LinkService

logger = logging.getLogger(__name__)


class Escalation:
    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.db = get_db()
        self.conversation_id = conversation_id
        self.email_service = EmailService()
        self.link_service = LinkService()

    async def create_escalation(self, message: str, confidence: float, reason: str) -> Optional[str]:
        """Create an escalation, disable the IA and send an email to the client

        Args:
            message: Message that triggered the escalation
            confidence: Confidence score of the escalation (0-100)
            reason: Reason for the escalation

        Returns:
            str: ID of the escalation or None if failure
        """
        try:
            # 1. Créer l'escalade en base
            escalation_data = {
                "user_id": self.user_id,
                "conversation_id": self.conversation_id,
                "message": message,
                "confidence": confidence,
                "reason": reason,
                "notified": False
            }

            escalation_result = self.db.table("support_escalations").insert(escalation_data).execute()
            escalation_id = escalation_result.data[0]["id"] if escalation_result.data else None

            if not escalation_id:
                logger.error("Échec de création de l'escalade en base")
                return None

            # 2. Désactiver l'IA pour cette conversation
            self.db.table("conversations").update({
                "ai_mode": "OFF",
                "updated_at": "now()"
            }).eq("id", self.conversation_id).execute()

            # 3. Récupérer l'email de l'utilisateur
            user_result = self.db.table("users").select("email").eq("id", self.user_id).single().execute()
            user_email = user_result.data.get("email") if user_result.data else None

            if not user_email:
                logger.error(f"Email utilisateur non trouvé pour user_id: {self.user_id}")
                return escalation_id  # L'escalade est créée mais pas d'email

            # 4. Générer le lien sécurisé vers la conversation
            conversation_link = self.link_service.generate_conversation_link(
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                escalation_id=escalation_id
            )

            # 5. Préparer les données pour l'email
            email_data = {
                "id": escalation_id,
                "conversation_id": self.conversation_id,
                "user_id": self.user_id,
                "user_email": user_email,
                "message": message,
                "confidence": confidence,
                "reason": reason
            }

            # 6. Envoyer l'email de notification à l'équipe de support
            # L'email du client est récupéré mais utilisé seulement pour le contexte
            support_email = os.getenv("SUPPORT_EMAIL", "support@yourdomain.com")
            email_sent = await self.email_service.send_escalation_email(
                to_email=support_email,
                escalation_data=email_data,
                conversation_link=conversation_link
            )

            # 7. Marquer comme notifié si l'email a été envoyé
            if email_sent:
                self.db.table("support_escalations").update({
                    "notified": True
                }).eq("id", escalation_id).execute()

                logger.info(f"Escalation créée et email envoyé à l'équipe de support: {escalation_id}")
            else:
                logger.warning(f"Escalation créée mais email non envoyé à l'équipe de support: {escalation_id}")

            return escalation_id

        except Exception as e:
            logger.error(f"Erreur lors de la création de l'escalade: {e}")
            return None

    def get_escalation_status(self, escalation_id: str) -> Optional[dict]:
        """Get the status of an escalation

        Args:
            escalation_id: ID of the escalation

        Returns:
            dict: Data of the escalation or None
        """
        try:
            result = self.db.table("support_escalations").select("*").eq("id", escalation_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting escalation status {escalation_id}: {e}")
            return None
