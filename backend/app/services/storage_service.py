from typing import Optional
from app.db.session import get_db, get_authenticated_db
from app.services.credits_service import CreditsService, get_credits_service
from app.schemas.subscription import StorageUsage, StorageQuotaExceededError
from fastapi import HTTPException, Depends


class StorageService:
    def __init__(self, db):
        self.db = db

    async def get_storage_usage(self, user_id: str) -> StorageUsage:
        """Retrieve storage usage from user_subscriptions."""
        credits_service = CreditsService(self.db)
        subscription = await credits_service.get_user_subscription(user_id)

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        used_mb = subscription.storage_used_mb
        quota_mb = subscription.plan.storage_quota_mb
        available_mb = max(0, quota_mb - used_mb)
        percentage = (used_mb / quota_mb * 100) if quota_mb > 0 else 0

        return StorageUsage(
            used_mb=round(used_mb, 2),
            quota_mb=quota_mb,
            available_mb=round(available_mb, 2),
            percentage_used=round(percentage, 1),
            is_full=used_mb >= quota_mb
        )

    async def check_storage_available(self, user_id: str, file_size_bytes: int) -> tuple[bool, StorageUsage]:
        """Check if the quota allows adding this file."""
        usage = await self.get_storage_usage(user_id)
        file_size_mb = file_size_bytes / (1024 * 1024)
        can_upload = usage.available_mb >= file_size_mb

        return can_upload, usage


async def get_storage_service(db=Depends(get_authenticated_db)) -> StorageService:
    """Dependency to get a StorageService instance."""
    return StorageService(db)
