import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class TimedMessage:
    message_data: Dict[str, Any]
    conversation_message_id: str
    external_message_id: Optional[str] = None


@dataclass
class TimerBatch:
    platform: str
    account_id: str
    contact_id: str
    first_message_at: datetime
    messages: List[TimedMessage] = field(default_factory=list)
    timer_task: Optional[asyncio.Task] = None


class MessageTimerBatcher:
    """In-memory batching with a fixed delay and bounded retries."""

    def __init__(
        self,
        batch_window_seconds: float = 0.5,
        max_attempts: int = 2,
    ) -> None:
        self.batch_window_seconds = batch_window_seconds
        self.max_attempts = max_attempts
        self._batches: Dict[str, TimerBatch] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._handler: Optional[Callable[[TimerBatch], Awaitable[bool]]] = None

    def set_handler(self, handler: Callable[[TimerBatch], Awaitable[bool]]) -> None:
        self._handler = handler

    def _get_lock(self, conversation_key: str) -> asyncio.Lock:
        if conversation_key not in self._locks:
            self._locks[conversation_key] = asyncio.Lock()
        return self._locks[conversation_key]

    def _conversation_key(self, platform: str, account_id: str, contact_id: str) -> str:
        return f"{platform}:{account_id}:{contact_id}"

    async def add_message(
        self,
        platform: str,
        account_id: str,
        contact_id: str,
        message_data: Dict[str, Any],
        conversation_message_id: str,
    ) -> bool:
        if not self._handler:
            logger.error("No handler configured for MessageTimerBatcher; cannot queue message")
            return False

        conversation_key = self._conversation_key(platform, account_id, contact_id)
        lock = self._get_lock(conversation_key)

        async with lock:
            batch = self._batches.get(conversation_key)
            if not batch:
                batch = TimerBatch(
                    platform=platform,
                    account_id=account_id,
                    contact_id=contact_id,
                    first_message_at=datetime.utcnow(),
                )
                self._batches[conversation_key] = batch

            batch.messages.append(
                TimedMessage(
                    message_data=message_data,
                    conversation_message_id=conversation_message_id,
                    external_message_id=message_data.get("external_message_id"),
                )
            )

            if not batch.timer_task or batch.timer_task.done():
                batch.timer_task = asyncio.create_task(self._flush_after_delay(conversation_key))
                logger.info(
                    "⏳ Timer started for %s (batch_window=%ss, messages=%s)",
                    conversation_key,
                    self.batch_window_seconds,
                    len(batch.messages),
                )
            else:
                logger.info(
                    "➕ Message appended to existing batch %s (messages=%s)",
                    conversation_key,
                    len(batch.messages),
                )

        return True

    async def _flush_after_delay(self, conversation_key: str) -> None:
        await asyncio.sleep(self.batch_window_seconds)
        await self._dispatch_batch(conversation_key)

    async def _dispatch_batch(self, conversation_key: str) -> None:
        lock = self._get_lock(conversation_key)
        async with lock:
            batch = self._batches.get(conversation_key)
            if not batch:
                return

            messages_snapshot = list(batch.messages)
            platform = batch.platform
            account_id = batch.account_id
            contact_id = batch.contact_id

            logger.info(
                "🚚 Dispatching batch for %s:%s:%s (messages=%s)",
                platform,
                account_id,
                contact_id,
                len(messages_snapshot),
            )

        success = False
        attempt = 0
        while attempt < self.max_attempts and not success:
            attempt += 1
            try:
                success = await self._handler(
                    TimerBatch(
                        platform=platform,
                        account_id=account_id,
                        contact_id=contact_id,
                        first_message_at=batch.first_message_at,
                        messages=messages_snapshot,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(
                    "❌ Error handling batch for %s:%s:%s on attempt %s: %s",
                    platform,
                    account_id,
                    contact_id,
                    attempt,
                    exc,
                    exc_info=True,
                )
                success = False

            if not success:
                logger.warning(
                    "🔁 Batch %s retry %s/%s failed",
                    conversation_key,
                    attempt,
                    self.max_attempts,
                )

        async with lock:
            # Cleanup regardless of outcome to avoid infinite loops
            self._batches.pop(conversation_key, None)
            logger.info(
                "🧹 Batch %s cleaned up (success=%s, attempts=%s)",
                conversation_key,
                success,
                attempt,
            )


# Shared instance used by webhook handlers
message_timer_batcher = MessageTimerBatcher()

