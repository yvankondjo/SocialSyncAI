import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
import resend
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    """Service d'envoi d'emails utilisant Resend"""

    def __init__(self):
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            logger.warning("RESEND_API_KEY non configuré - les emails ne seront pas envoyés")
            self.emails_client = None
        else:
            resend.api_key = api_key
            self.emails_client = resend.Emails()

        self.from_email = os.getenv("FROM_EMAIL", "noreply@your-app.vercel.app")

    async def send_escalation_email(
        self,
        to_email: str,
        escalation_data: Dict[str, Any],
        conversation_link: str
    ) -> bool:
        """Send an escalation email to the support team

        Args:
            to_email: Email address of the recipient
            escalation_data: Data of the escalation
            conversation_link: Link to the conversation

        Returns:
            bool: True if the email has been sent successfully
        """
        if not self.emails_client:
            logger.error("Resend not configured - impossible to send the email")
            return False

        try:
    
            html_content, text_content = self._render_escalation_template(
                escalation_data,
                conversation_link
            )

            from resend import Tag
            email_data = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Customer Support Request",
                "html": html_content,
                "text": text_content,
                "reply_to": [self.from_email],
                "tags": [
                    Tag(name="type", value="escalation"),
                    Tag(name="conversation_id", value=str(escalation_data.get('conversation_id', '')))
                ]
            }

            response = self.emails_client.send(email_data)

            message_id = None
            if isinstance(response, dict):
                message_id = response.get("id") or response.get("MessageID")
            elif hasattr(response, "id"):
                message_id = getattr(response, "id")

            if message_id:
                logger.info(f"Email d'escalade envoyé avec succès: {message_id}")
                return True

            if response:
                logger.info("Email d'escalade envoyé (ID non retourné)")
                return True

            logger.error("Échec de l'envoi de l'email d'escalade")
            return False

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'escalade: {e}")
            return False

    def _render_escalation_template(self, data: Dict[str, Any], link: str) -> str:
        """Render the HTML template for the escalation

        Args:
            data: Data of the escalation
            link: Link to the conversation

        Returns:
            str: HTML template rendered
        """
        template = Template("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Human Support</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #f8fafc;
                }
                .container {
                    background-color: white;
                    margin: 20px;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .content {
                    padding: 30px 20px;
                }
                .cta-button {
                    display: inline-block;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: 500;
                    margin: 20px 0;
                }
                .footer {
                    background-color: #f9fafb;
                    padding: 20px;
                    text-align: center;
                    color: #6b7280;
                    font-size: 12px;
                    border-top: 1px solid #e5e7eb;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h1>Customer Support Request</h1>

                    <p>{{ reason }}</p>

                    <div style="text-align: center;">
                        <a href="{{ conversation_link }}" class="cta-button">
                            Access Conversation
                        </a>
                    </div>

                    <p>This link expires in 24 hours.</p>
                </div>

                <div class="footer">
                    <p>
                        A customer requested human assistance.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            reason=data.get('reason', ''),
            conversation_link=link
        )

        text_content = f"""Customer Support Request

{data.get('reason', '')}

Access Conversation: {link}

This link expires in 24 hours.

A customer requested human assistance.
"""

        return html_content, text_content





def get_email_service() -> EmailService:
    """Dépendance FastAPI pour injecter le service Email."""
    return EmailService()
