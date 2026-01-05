import logging
from typing import Dict, Any, Optional
from contextvars import ContextVar
from dataclasses import dataclass, field

from app.services.credits_service import CreditsService

logger = logging.getLogger(__name__)


_credit_tracker: ContextVar[Optional['CreditTracker']] = ContextVar('credit_tracker', default=None)


@dataclass
class AICallInfo:
    """Information about an AI call in the batch."""
    model_name: str
    credit_cost: float
    has_tool_calls: bool = False
    timestamp: Optional[float] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CreditTracker:
    """
    Tracker for counting AI calls and managing credit deductions by batch.

    This tracker maintains the state of AI calls during the processing of a request
    and deducts credits only at the end of the batch (after the final response).
    """

    def __init__(self, user_id: str, credits_service: CreditsService):
        self.user_id = user_id
        self.credits_service = credits_service
        self.calls: list[AICallInfo] = []
        self.total_cost = 0.0
        self.final_response_sent = False

    @classmethod
    def get_current(cls) -> Optional['CreditTracker']:
        """Get the current tracker for this request."""
        return _credit_tracker.get()

    @classmethod
    def set_current(cls, tracker: 'CreditTracker') -> None:
        """Set the current tracker for this request."""
        _credit_tracker.set(tracker)

    async def track_ai_call(self, model_name: str, credit_cost: float,
                          has_tool_calls: bool = False,
                          conversation_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register an AI call in the batch.

        Returns:
            bool: True if the call can be performed, False if limit reached
        """
        try:
            feature_access = await self.credits_service.get_feature_access(self.user_id)
            if len(self.calls) >= feature_access.max_calls_per_batch:
                logger.warning(f"Batch call limit reached for {self.user_id}: {len(self.calls)}/{feature_access.max_calls_per_batch}")
                return False

            # Check if the user can use this model
            logger.info(f"[CREDIT_TRACKER] Checking model authorization {model_name} for user {self.user_id}")
            can_use_model = await self.credits_service.can_use_model(self.user_id, model_name)
            if not can_use_model:
                logger.warning(f"[CREDIT_TRACKER] Model not allowed for {self.user_id}: {model_name}")
                return False
            logger.info(f"[CREDIT_TRACKER] Model {model_name} allowed for user {self.user_id}")

            # Check if the credits are available (estimation for the whole batch)
            estimated_total_cost = self.total_cost + (credit_cost * (len(self.calls) + 1))
            logger.info(
                f"[CREDIT_TRACKER] Checking credits for {self.user_id}: need {estimated_total_cost}, unit_cost={credit_cost}, current_calls={len(self.calls)}"
            )
            credits_available = await self.credits_service.check_credits_available(self.user_id, estimated_total_cost)

            if not credits_available:
                # Try to fetch current balance for better logging.
                try:
                    balance_result = self.credits_service.db.table('user_credits').select('credits_balance').eq('user_id', self.user_id).single().execute()
                    current_balance = balance_result.data.get('credits_balance', 0) if balance_result.data else 0
                    logger.warning(
                        f"[CREDIT_TRACKER] Insufficient credits for {self.user_id}: need {estimated_total_cost}, available={current_balance}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[CREDIT_TRACKER] Insufficient credits for {self.user_id}: need {estimated_total_cost} (balance lookup error: {e})"
                    )
                return False
            logger.info(f"[CREDIT_TRACKER] Sufficient credits for {self.user_id}: need {estimated_total_cost}")

            # Register the call
            import time
            call_info = AICallInfo(
                model_name=model_name,
                credit_cost=credit_cost,
                has_tool_calls=has_tool_calls,
                timestamp=time.time(),
                conversation_id=conversation_id,
                metadata=metadata or {}
            )

            self.calls.append(call_info)
            self.total_cost += credit_cost

            logger.info(
                f"AI call tracked: {self.user_id} - {model_name} - Cost: {credit_cost} - Batch total: {len(self.calls)} calls"
            )
            return True

        except Exception as e:
            logger.error(f"Error tracking AI call for {self.user_id}: {e}")
            return False

    async def finalize_batch(self, conversation_id: Optional[str] = None) -> bool:
        """
        Finalize the batch and deduct the credits.

        This method must be called after sending the final response to the user.
        """
        if self.final_response_sent:
            logger.warning(f"Batch already finalized for {self.user_id}")
            return True

        if not self.calls:
            logger.info(f"No calls to bill for {self.user_id}")
            return True

        try:
            # Calculate the real total cost
            total_credits_to_deduct = sum(call.credit_cost for call in self.calls)

            # Create the summary of the calls for the metadata
            calls_summary = {
                "calls_count": len(self.calls),
                "models_used": list(set(call.model_name for call in self.calls)),
                "total_cost": total_credits_to_deduct,
                "conversation_id": conversation_id,
                "calls_detail": [
                    {
                        "model": call.model_name,
                        "cost": call.credit_cost,
                        "has_tools": call.has_tool_calls,
                        "timestamp": call.timestamp
                    }
                    for call in self.calls
                ]
            }

            # Deduct the credits
            await self.credits_service.deduct_credits(
                user_id=self.user_id,
                credits_to_deduct=total_credits_to_deduct,
                reason=f"AI batch: {len(self.calls)} calls - {', '.join(set(call.model_name for call in self.calls))}",
                metadata=calls_summary
            )

            self.final_response_sent = True

            logger.info(
                f"Batch finalized successfully: {self.user_id} - {len(self.calls)} calls - {total_credits_to_deduct} credits deducted"
            )
            return True

        except Exception as e:
            logger.error(f"Error finalizing batch for {self.user_id}: {e}")
            # If there is an error in billing, we don't block the user
            # but we log the error for investigation
            return False

    def get_batch_info(self) -> Dict[str, Any]:
        """Return the information about the current batch."""
        return {
            "calls_count": len(self.calls),
            "total_cost": self.total_cost,
            "models_used": list(set(call.model_name for call in self.calls)),
            "finalized": self.final_response_sent
        }

    def reset(self) -> None:
        """Reset the tracker (for tests mainly)."""
        self.calls.clear()
        self.total_cost = 0.0
        self.final_response_sent = False



async def get_or_create_credit_tracker(user_id: str, credits_service: CreditsService) -> CreditTracker:
    tracker = CreditTracker.get_current()

    if tracker and tracker.user_id == user_id:
        tracker.reset()
        return tracker

    tracker = CreditTracker(user_id, credits_service)
    CreditTracker.set_current(tracker)
    return tracker


async def get_model_credit_cost(model_name: str) -> float:
    """
    Get the cost of a model from Redis cache or DB.
    """
    try:
        from app.core.redis_client import get_redis_client
        from app.db.session import get_db
        
        redis_client = await get_redis_client()
        cache_key = f"model:cost:{model_name}"
        
        cached_cost = await redis_client.get(cache_key)
        if cached_cost:
            return float(cached_cost)
        
        db = get_db()
        result = db.table('ai_models').select('credit_cost').eq('openrouter_id', model_name).eq('is_active', True).single().execute()
        
        if result.data and 'credit_cost' in result.data:
            cost = float(result.data['credit_cost'])
            await redis_client.setex(cache_key, 3600, str(cost))
            return cost
        
        logger.warning(f"Model {model_name} not found in DB, using default cost 0.2")
        return 0.2
        
    except Exception as e:
        logger.error(f"Error retrieving model cost {model_name}: {e}")
        return 0.2
