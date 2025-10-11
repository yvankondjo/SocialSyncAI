import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os

logger = logging.getLogger(__name__)


class LinkService:
    """Link service for generating secure links for escalations"""

    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret:
            logger.warning("JWT_SECRET_KEY not configured - link generation limited")
            self.jwt_secret = "dev-secret-key-change-in-production"

        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.link_expiration_hours = int(os.getenv("LINK_EXPIRATION_HOURS", "24"))

    def generate_conversation_link(
        self,
        conversation_id: str,
        user_id: str,
        escalation_id: Optional[str] = None
    ) -> str:
        """Generate a secure link to an escalation conversation

        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user
            escalation_id: ID of the escalation (optional)

        Returns:
            str: Complete URL with JWT token
        """
        try:
            # Créer le payload JWT
            payload = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "type": "escalation_link",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=self.link_expiration_hours)
            }

            if escalation_id:
                payload["escalation_id"] = escalation_id

            # Encoder le JWT
            token = jwt.encode(
                payload,
                self.jwt_secret,
                algorithm="HS256"
            )

            # Build the complete URL
            base_url = f"{self.frontend_url.rstrip('/')}"
            link = f"{base_url}/support/conversation/{conversation_id}?token={token}"

            logger.info(f"Conversation link generated for conversation {conversation_id}")
            return link

        except Exception as e:
            logger.error(f"Error generating conversation link: {e}")
            # Fallback: lien sans token (moins sécurisé)
            return f"{self.frontend_url}/support/conversation/{conversation_id}"

    def verify_conversation_token(self, token: str) -> Optional[dict]:
        """Verify and decode a JWT token for a conversation

        Args:
            token: Token JWT to verify

        Returns:
            dict: Decoded payload or None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"]
            )

            # Verify that it's a valid token (escalation or unsubscribe)
            token_type = payload.get("type")
            if token_type not in ["escalation_link", "unsubscribe_support"]:
                logger.warning("Token JWT invalide - type incorrect")
                return None

            # Vérifier que le token n'est pas expiré
            exp_timestamp = payload.get("exp")
            if exp_timestamp and datetime.utcfromtimestamp(exp_timestamp) < datetime.utcnow():
                logger.warning("Token JWT expiré")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expiré (signature)")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT invalide: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur vérification token JWT: {e}")
            return None

    def generate_admin_link(self, escalation_id: str) -> str:
        """Generate a link for the admin to manage the escalation

        Args:
            escalation_id: ID of the escalation

        Returns:
            str: URL to the admin page of the escalation
        """
        try:
            payload = {
                "escalation_id": escalation_id,
                "type": "admin_link",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=self.link_expiration_hours)
            }

            token = jwt.encode(
                payload,
                self.jwt_secret,
                algorithm="HS256"
            )

            base_url = f"{self.frontend_url.rstrip('/')}"
            return f"{base_url}/admin/escalation/{escalation_id}?token={token}"

        except Exception as e:
            logger.error(f"Erreur génération lien admin: {e}")
            return f"{self.frontend_url}/admin/escalation/{escalation_id}"
