import logging
from app.db.session import get_db
logger = logging.getLogger(__name__)
class Escalation:
    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.db = get_db()
        self.conversation_id = conversation_id

    def create_escalation(self, message: str, confidence: float, reason: str) -> str:
        """Create an escalation and set the conversation to OFF
        Args:
            message: str the message that triggered the escalation
            confidence: float the confidence score of the escalation
            reason: str the reason for the escalation
        Returns:
            str: The escalation ID or None if the escalation failed
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
            
            self.db.table("conversations").update({
                "ai_mode": "OFF",
                "updated_at": "now()"
            }).eq("id", self.conversation_id).execute()
            
            logger.info(f"Escalation created: {escalation_id} for conversation {self.conversation_id}")
            return escalation_id
            
        except Exception as e:
            logger.error(f"Error creating escalation: {e}")
            return None
