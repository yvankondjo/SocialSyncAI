import logging
import os
from typing import Optional

from app.db.session import get_db
from app.services.email_service import EmailService
from app.services.link_service import LinkService

logger = logging.getLogger(__name__)


class Escalation:
    def __init__(self, user_id: str, conversation_id: str):
        # ✅ SECURITY FIX (2025-11-02): Validate user_id to prevent injection
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if not conversation_id or not isinstance(conversation_id, str):
            raise ValueError("conversation_id must be a non-empty string")

        self.user_id = user_id
        self.conversation_id = conversation_id
        # Note: Using get_db() (service role) - all queries MUST filter by user_id
        # TODO (Phase 2): Migrate to get_authenticated_db() for RLS enforcement
        self.db = get_db()
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

            # ✅ SECURITY: Verify escalation belongs to user (defensive validation)
            created_escalation = self.db.table("support_escalations") \
                .select("user_id") \
                .eq("id", escalation_id) \
                .single() \
                .execute()
            if created_escalation.data.get("user_id") != self.user_id:
                logger.error(f"🚨 SECURITY ALERT: Escalation {escalation_id} user_id mismatch!")
                raise RuntimeError("Escalation user_id validation failed")

            # ✅ SECURITY: Filter conversation by user_id (service role bypass mitigation)
            self.db.table("conversations").update({
                "ai_mode": "OFF",
                "updated_at": "now()"
            }).eq("id", self.conversation_id) \
              .eq("user_id", self.user_id) \
              .execute()

            # Get user email (already filtered by user_id)
            user_result = self.db.table("users").select("email").eq("id", self.user_id).single().execute()
            user_email = user_result.data.get("email") if user_result.data else None

            if not user_email:
                logger.error(f"Email utilisateur non trouvé pour user_id: {self.user_id}")
                return escalation_id  # Escalation created but no email

            # Generate secure link to the conversation
            conversation_link = self.link_service.generate_conversation_link(
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                escalation_id=escalation_id
            )

            # Prepare email data
            email_data = {
                "id": escalation_id,
                "conversation_id": self.conversation_id,
                "user_id": self.user_id,
                "user_email": user_email,
                "message": message,
                "confidence": confidence,
                "reason": reason
            }

            # Send notification email to the support team
            email_sent = await self.email_service.send_escalation_email(
                to_email=user_email,
                escalation_data=email_data,
                conversation_link=conversation_link
            )

            # Mark as notified if email has been sent
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
            dict: Data of the escalation or None (only if belongs to user)
        """
        try:
            # ✅ SECURITY: Filter by BOTH escalation_id AND user_id
            # Prevents user A from accessing user B's escalation data
            result = self.db.table("support_escalations") \
                .select("*") \
                .eq("id", escalation_id) \
                .eq("user_id", self.user_id) \
                .single() \
                .execute()

            if result.data and result.data.get("user_id") != self.user_id:
                logger.error(f"🚨 SECURITY: Attempted access to escalation {escalation_id} by wrong user {self.user_id}")
                return None

            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting escalation status {escalation_id}: {e}")
            return None
