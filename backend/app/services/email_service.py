import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
import resend
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    """Email sending service using Resend"""

    def __init__(self):
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            logger.warning("RESEND_API_KEY not configured - emails will not be sent")
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
            logger.error("Resend not configured - unable to send the email")
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
                logger.info(f"Escalation email sent successfully: {message_id}")
                return True

            if response:
                logger.info("Escalation email sent (ID not returned)")
                return True

            logger.error("Failed to send escalation email")
            return False

        except Exception as e:
            logger.error(f"Error sending escalation email: {e}")
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

        # Version texte de l'email (fallback)
        text_content = f"""Customer Support Request

{data.get('reason', '')}

Access Conversation: {link}

This link expires in 24 hours.

A customer requested human assistance.
"""

        return html_content, text_content

    async def send_subscription_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        plan_name: str = "Premium Plan",
        trial_days: Optional[int] = None
    ) -> bool:
        """Send welcome email for new subscription

        Args:
            to_email: Email address of the recipient
            user_name: Name of the user (optional)
            plan_name: Name of the subscribed plan
            trial_days: Number of trial days (optional)

        Returns:
            bool: True if the email was sent successfully
        """
        if not self.emails_client:
            logger.error("Resend not configured - unable to send the email")
            return False

        try:
            html_content, text_content = self._render_welcome_template(
                user_name, plan_name, trial_days
            )

            from resend import Tag
            email_data = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"Welcome to {plan_name}! 🎉",
                "html": html_content,
                "text": text_content,
                "reply_to": [self.from_email],
                "tags": [
                    Tag(name="type", value="subscription_welcome"),
                    Tag(name="plan", value=plan_name)
                ]
            }

            response = self.emails_client.send(email_data)

            message_id = None
            if isinstance(response, dict):
                message_id = response.get("id") or response.get("MessageID")
            elif hasattr(response, "id"):
                message_id = getattr(response, "id")

            if message_id:
                logger.info(f"Welcome email sent successfully: {message_id}")
                return True

            logger.info("Welcome email sent (ID not returned)")
            return True

        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False

    async def send_subscription_cancelled_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        plan_name: str = "Premium Plan",
        end_date: Optional[str] = None
    ) -> bool:
        """Send cancellation confirmation email

        Args:
            to_email: Email address of the recipient
            user_name: Name of the user (optional)
            plan_name: Name of the cancelled plan
            end_date: Date when subscription ends (optional)

        Returns:
            bool: True if the email was sent successfully
        """
        if not self.emails_client:
            logger.error("Resend not configured - unable to send the email")
            return False

        try:
            html_content, text_content = self._render_cancellation_template(
                user_name, plan_name, end_date
            )

            from resend import Tag
            email_data = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"Your {plan_name} subscription has been cancelled",
                "html": html_content,
                "text": text_content,
                "reply_to": [self.from_email],
                "tags": [
                    Tag(name="type", value="subscription_cancelled"),
                    Tag(name="plan", value=plan_name)
                ]
            }

            response = self.emails_client.send(email_data)

            message_id = None
            if isinstance(response, dict):
                message_id = response.get("id") or response.get("MessageID")
            elif hasattr(response, "id"):
                message_id = getattr(response, "id")

            if message_id:
                logger.info(f"Cancellation email sent successfully: {message_id}")
                return True

            logger.info("Cancellation email sent (ID not returned)")
            return True

        except Exception as e:
            logger.error(f"Error sending cancellation email: {e}")
            return False

    def _render_welcome_template(self, user_name: Optional[str], plan_name: str, trial_days: Optional[int]) -> tuple[str, str]:
        """Render the HTML template for welcome email"""
        template = Template("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Your Subscription</title>
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
                .highlight {
                    background-color: #fef3c7;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                    border-left: 4px solid #f59e0b;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h1>Welcome aboard! 🎉</h1>

                    {% if user_name %}
                    <p>Hi {{ user_name }},</p>
                    {% else %}
                    <p>Hi there,</p>
                    {% endif %}

                    <p>Thank you for subscribing to <strong>{{ plan_name }}</strong>!</p>

                    {% if trial_days %}
                    <div class="highlight">
                        <h3>Free Trial Started! ⏰</h3>
                        <p>You have <strong>{{ trial_days }} days</strong> of free access to all features.</p>
                        <p>You won't be charged until {{ trial_days }} days from now.</p>
                    </div>
                    {% endif %}

                    <p>Here's what you can do now:</p>
                    <ul>
                        <li>Access all premium features</li>
                        <li>Generate unlimited AI content</li>
                        <li>Get priority support</li>
                    </ul>

                    <div style="text-align: center;">
                        <a href="{{ app_url }}/dashboard" class="cta-button">
                            Start Using Your Plan
                        </a>
                    </div>

                    <p>If you have any questions, feel free to contact our support team.</p>
                </div>

                <div class="footer">
                    <p>
                        This is an automated email. Please do not reply to this message.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            user_name=user_name,
            plan_name=plan_name,
            trial_days=trial_days,
            app_url=os.getenv("FRONTEND_URL", "https://your-app.vercel.app")
        )

        # Version texte (plain text fallback)
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        trial_line = ""
        if trial_days:
            trial_line = (
                f"You have {trial_days} days of free access to all features. "
                f"You won't be charged until {trial_days} days from now."
            )

        text_content = (
            "Welcome aboard! 🎉\n\n"
            f"{greeting}\n\n"
            f"Thank you for subscribing to {plan_name}!\n\n"
            f"{trial_line}\n\n"
            "Here's what you can do now:\n"
            "- Access all premium features\n"
            "- Generate unlimited AI content\n"
            "- Get priority support\n\n"
            f"Start using your plan: {os.getenv('FRONTEND_URL', 'https://your-app.vercel.app')}/dashboard\n\n"
            "If you have any questions, feel free to contact our support team.\n\n"
            "This is an automated email. Please do not reply to this message."
        )

        return html_content, text_content

    def _render_cancellation_template(self, user_name: Optional[str], plan_name: str, end_date: Optional[str]) -> tuple[str, str]:
        """Render the HTML template for cancellation email"""
        template = Template("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Subscription Cancelled</title>
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
                .warning {
                    background-color: #fef3c7;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                    border-left: 4px solid #f59e0b;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h1>Subscription Cancelled</h1>

                    {% if user_name %}
                    <p>Hi {{ user_name }},</p>
                    {% else %}
                    <p>Hi there,</p>
                    {% endif %}

                    <p>Your <strong>{{ plan_name }}</strong> subscription has been cancelled.</p>

                    {% if end_date %}
                    <div class="warning">
                        <h3>Access Until: {{ end_date }}</h3>
                        <p>You will continue to have access to all premium features until your subscription period ends.</p>
                    </div>
                    {% endif %}

                    <p>We're sorry to see you go! If there's anything we could have done better, we'd love to hear from you.</p>

                    <div style="text-align: center;">
                        <a href="{{ app_url }}/pricing" class="cta-button">
                            View Other Plans
                        </a>
                    </div>

                    <p>You can reactivate your subscription at any time before it expires.</p>
                </div>

                <div class="footer">
                    <p>
                        This is an automated email. Please do not reply to this message.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            user_name=user_name,
            plan_name=plan_name,
            end_date=end_date,
            app_url=os.getenv("FRONTEND_URL", "https://your-app.vercel.app")
        )

        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        end_date_line = ""
        if end_date:
            end_date_line = (
                "You will continue to have access to all premium features until "
                f"{end_date}."
            )

        text_content = (
            "Subscription Cancelled\n\n"
            f"{greeting}\n\n"
            f"Your {plan_name} subscription has been cancelled.\n\n"
            f"{end_date_line}\n\n"
            "We're sorry to see you go! If there's anything we could have done better, we'd love to hear from you.\n\n"
            f"View other plans: {os.getenv('FRONTEND_URL', 'https://your-app.vercel.app')}/pricing\n\n"
            "You can reactivate your subscription at any time before it expires.\n\n"
            "This is an automated email. Please do not reply to this message."
        )

        return html_content, text_content


# =====================================================
# FastAPI dependencies
# =====================================================

def get_email_service() -> EmailService:
    """FastAPI dependency to inject the Email service."""
    return EmailService()
