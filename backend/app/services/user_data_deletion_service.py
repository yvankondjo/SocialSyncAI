from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from supabase import Client

try:  # Lazy import to avoid circular references when running tests
    from app.services.message_batcher import message_batcher
except Exception:  # pragma: no cover - fallback when batcher not available
    message_batcher = None

try:
    from app.services.media_cache_service import redis_client as media_cache_redis
except Exception:  # pragma: no cover - redis cache optional in some envs
    media_cache_redis = None

logger = logging.getLogger(__name__)


@dataclass
class DeletionResult:
    user_id: str
    deleted_counts: Dict[str, int] = field(default_factory=dict)
    storage_deleted: List[str] = field(default_factory=list)
    cache_keys_deleted: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def record(self, resource: str, count: int) -> None:
        self.deleted_counts[resource] = self.deleted_counts.get(resource, 0) + count

    def add_error(self, resource: str, error: Exception) -> None:
        error_message = f"{resource}: {error}"
        logger.error(error_message)
        self.errors.append(error_message)


class UserDataDeletionService:
    """Service responsible for permanently deleting all user-related data."""

    def __init__(
        self,
        auth_db: Client,
        service_db: Client,
        user_id: str,
        storage_bucket_names: Optional[List[str]] = None,
    ) -> None:
        self.auth_db = auth_db
        self.service_db = service_db
        self.user_id = user_id
        self.storage_bucket_names = storage_bucket_names or ["message", "knowledge"]

    async def delete_user_data(self) -> DeletionResult:
        result = DeletionResult(user_id=self.user_id)

        social_account_ids = self._get_social_account_ids(result)
        conversation_ids = self._get_conversation_ids(result)
        document_entries = self._get_document_entries(result)

        await self._delete_conversation_messages(conversation_ids, result)
        await self._delete_conversation_cache(conversation_ids, result)
        self._delete_conversations(conversation_ids, result)
        self._delete_social_accounts(social_account_ids, result)

        self._delete_knowledge_chunks([entry["id"] for entry in document_entries], result)
        await self._delete_document_storage_objects(document_entries, result)
        self._delete_knowledge_documents(document_entries, result)

        self._delete_support_escalations(result)
        self._delete_ai_settings(result)
        self._delete_user_preferences(result)

        self._delete_user_record(result)

        return result

    # --- Fetch helpers ---

    def _get_social_account_ids(self, result: DeletionResult) -> List[str]:
        try:
            response = (
                self.auth_db.table("social_accounts")
                .select("id")
                .eq("user_id", self.user_id)
                .execute()
            )
            return [row["id"] for row in response.data or []]
        except Exception as exc:
            result.add_error("social_accounts.fetch", exc)
            return []

    def _get_conversation_ids(self, result: DeletionResult) -> List[str]:
        try:
            response = (
                self.auth_db.table("conversations")
                .select("id")
                .eq("user_id", self.user_id)
                .execute()
            )
            return [row["id"] for row in response.data or []]
        except Exception as exc:
            result.add_error("conversations.fetch", exc)
            return []

    def _get_document_entries(self, result: DeletionResult) -> List[Dict[str, Optional[str]]]:
        try:
            response = (
                self.auth_db.table("knowledge_documents")
                .select("id, storage_object_name")
                .eq("user_id", self.user_id)
                .execute()
            )
            return response.data or []
        except Exception as exc:
            result.add_error("knowledge_documents.fetch", exc)
            return []

    # --- Deletion helpers ---

    async def _delete_conversation_messages(
        self, conversation_ids: List[str], result: DeletionResult
    ) -> None:
        if not conversation_ids:
            return
        try:
            response = (
                self.service_db.table("conversation_messages")
                .delete()
                .in_("conversation_id", conversation_ids)
                .execute()
            )
            result.record("conversation_messages", len(response.data or []))
        except Exception as exc:
            result.add_error("conversation_messages", exc)

    async def _delete_conversation_cache(
        self, conversation_ids: List[str], result: DeletionResult
    ) -> None:
        if not conversation_ids:
            return
        try:
            redis_client = None
            if message_batcher and getattr(message_batcher, "redis_client", None):
                redis_client = message_batcher.redis_client
            elif media_cache_redis:
                redis_client = media_cache_redis

            if not redis_client:
                return
            for conversation_id in conversation_ids:
                cache_pattern = f"conv:*:{conversation_id}"
                try:
                    matching_keys = await redis_client.keys(cache_pattern)  # type: ignore[arg-type]
                    if not matching_keys:
                        continue
                    deleted = await redis_client.delete(*matching_keys)  # type: ignore[arg-type]
                    if deleted:
                        result.cache_keys_deleted.extend(matching_keys)
                except Exception as redis_exc:  # pragma: no cover - best effort cleanup
                    result.add_error(f"cache:{conversation_id}", redis_exc)
        except Exception as exc:
            result.add_error("cache.global", exc)

    def _delete_conversations(
        self, conversation_ids: List[str], result: DeletionResult
    ) -> None:
        if not conversation_ids:
            return
        try:
            response = (
                self.service_db.table("conversations")
                .delete()
                .in_("id", conversation_ids)
                .execute()
            )
            result.record("conversations", len(response.data or []))
        except Exception as exc:
            result.add_error("conversations", exc)

    def _delete_social_accounts(
        self, social_account_ids: List[str], result: DeletionResult
    ) -> None:
        if not social_account_ids:
            return
        try:
            response = (
                self.service_db.table("social_accounts")
                .delete()
                .in_("id", social_account_ids)
                .execute()
            )
            result.record("social_accounts", len(response.data or []))
        except Exception as exc:
            result.add_error("social_accounts", exc)

    def _delete_knowledge_chunks(
        self, document_ids: List[str], result: DeletionResult
    ) -> None:
        if not document_ids:
            return
        try:
            response = (
                self.service_db.table("knowledge_chunks")
                .delete()
                .in_("document_id", document_ids)
                .execute()
            )
            result.record("knowledge_chunks", len(response.data or []))
        except Exception as exc:
            result.add_error("knowledge_chunks", exc)

    async def _delete_document_storage_objects(
        self, document_entries: List[Dict[str, Optional[str]]], result: DeletionResult
    ) -> None:
        if not document_entries:
            return
        bucket = self.service_db.storage.from_("knowledge")
        for entry in document_entries:
            object_name = entry.get("storage_object_name")
            if not object_name:
                continue
            try:
                bucket.remove(object_name)  # type: ignore[arg-type]
                result.storage_deleted.append(object_name)
            except Exception as exc:  # pragma: no cover - relies on Supabase storage
                result.add_error(f"storage:{object_name}", exc)

    def _delete_knowledge_documents(
        self, document_entries: List[Dict[str, Optional[str]]], result: DeletionResult
    ) -> None:
        if not document_entries:
            return
        document_ids = [entry["id"] for entry in document_entries if entry.get("id")]
        if not document_ids:
            return
        try:
            response = (
                self.service_db.table("knowledge_documents")
                .delete()
                .in_("id", document_ids)
                .execute()
            )
            result.record("knowledge_documents", len(response.data or []))
        except Exception as exc:
            result.add_error("knowledge_documents", exc)

    def _delete_support_escalations(self, result: DeletionResult) -> None:
        try:
            response = (
                self.service_db.table("support_escalations")
                .delete()
                .eq("user_id", self.user_id)
                .execute()
            )
            result.record("support_escalations", len(response.data or []))
        except Exception as exc:
            result.add_error("support_escalations", exc)

    def _delete_ai_settings(self, result: DeletionResult) -> None:
        try:
            response = (
                self.service_db.table("ai_settings")
                .delete()
                .eq("user_id", self.user_id)
                .execute()
            )
            result.record("ai_settings", len(response.data or []))
        except Exception as exc:
            result.add_error("ai_settings", exc)

    def _delete_user_preferences(self, result: DeletionResult) -> None:
        try:
            response = (
                self.service_db.table("user_preferences")
                .delete()
                .eq("user_id", self.user_id)
                .execute()
            )
            result.record("user_preferences", len(response.data or []))
        except Exception as exc:
            result.add_error("user_preferences", exc)

    def _delete_user_record(self, result: DeletionResult) -> None:
        try:
            response = (
                self.service_db.table("users")
                .delete()
                .eq("id", self.user_id)
                .execute()
            )
            result.record("users", len(response.data or []))
        except Exception as exc:
            result.add_error("users", exc)