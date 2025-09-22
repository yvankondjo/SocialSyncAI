# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /app/app/services/notification_service.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-09-21 18:47:41 UTC (1758480461)

import logging
from app.services.response_manager import get_user_credentials_by_platform_account
logger = logging.getLogger(__name__)

async def send_notification_to_user(user_id: str, message: str, platform: str) -> None:
    user_credentials = await get_user_credentials_by_platform_account(platform, user_id)
    if not user_credentials:
        logger.error(f'Utilisateur {user_id} non trouvé')
        return
    user_email = user_credentials.get('user_email')
    if not user_email:
        logger.error(f"Email de l'utilisateur {user_id} non trouvé")
        return
    logger.info(f"Envoi notification à l'utilisateur {user_id}: {message}")