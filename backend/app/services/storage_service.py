from typing import Optional
from app.db.session import get_db, get_authenticated_db
from app.schemas.subscription import StorageUsage
from fastapi import Depends


# SERVICE FOR STORAGE that is not used yet work for paid version
class StorageService:
    def __init__(self, db):
        self.db = db

    async def get_storage_usage(self, user_id: str) -> StorageUsage:
        """Retrieve storage usage from user_subscriptions."""
        used_mb = 0
        quota_mb = 1000000000
        available_mb = max(0, quota_mb - used_mb)
        percentage = (used_mb / quota_mb * 100) if quota_mb > 0 else 0

        return StorageUsage(
            used_mb=round(used_mb, 2),
            quota_mb=quota_mb,
            available_mb=round(available_mb, 2),
            percentage_used=round(percentage, 1),
            is_full=used_mb >= quota_mb,
        )

    async def check_storage_available(
        self, user_id: str, file_size_bytes: int
    ) -> tuple[bool, StorageUsage]:
        """Check if the quota allows adding this file."""
        usage = await self.get_storage_usage(user_id)
        file_size_mb = file_size_bytes / (1024 * 1024)
        can_upload = usage.available_mb >= file_size_mb

        return can_upload, usage


async def get_storage_service(db=Depends(get_authenticated_db)) -> StorageService:
    """Dependency to get an instance of StorageService."""
    return StorageService(db)
