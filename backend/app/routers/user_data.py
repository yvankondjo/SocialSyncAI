from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

from app.db.session import get_authenticated_db, get_db
from app.core.security import get_current_user_id
from app.services.user_data_deletion_service import UserDataDeletionService, DeletionResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-data", tags=["user-data"])


class UserDataDeletionResponse(BaseModel):
    """Response model for user data deletion operations."""
    user_id: str
    deleted_counts: Dict[str, int]
    storage_deleted: List[str]
    cache_keys_deleted: List[str]
    errors: List[str]
    success: bool

    @classmethod
    def from_deletion_result(cls, result: DeletionResult) -> "UserDataDeletionResponse":
        return cls(
            user_id=result.user_id,
            deleted_counts=result.deleted_counts,
            storage_deleted=result.storage_deleted,
            cache_keys_deleted=result.cache_keys_deleted,
            errors=result.errors,
            success=len(result.errors) == 0
        )


@router.delete("/delete", response_model=UserDataDeletionResponse)
async def delete_user_data(
    current_user_id: str = Depends(get_current_user_id),
    auth_db = Depends(get_authenticated_db),
    service_db = Depends(get_db)
):
    """
    Permanently delete all user data for the authenticated user.

    This endpoint complies with GDPR and Meta data deletion requirements.
    All conversations, messages, social accounts, knowledge documents, and user settings
    will be permanently deleted. This action cannot be undone.

    Returns a detailed report of what was deleted and any errors encountered.
    """
    try:
        logger.info(f"Starting user data deletion for user: {current_user_id}")

        # Initialize the deletion service
        deletion_service = UserDataDeletionService(
            auth_db=auth_db,
            service_db=service_db,
            user_id=current_user_id
        )

        # Execute the deletion
        result = await deletion_service.delete_user_data()

        # Log the results
        total_deleted = sum(result.deleted_counts.values())
        logger.info(f"User data deletion completed for {current_user_id}: "
                   f"{total_deleted} records deleted, "
                   f"{len(result.errors)} errors, "
                   f"{len(result.storage_deleted)} storage objects removed, "
                   f"{len(result.cache_keys_deleted)} cache keys cleared")

        # Return the result
        return UserDataDeletionResponse.from_deletion_result(result)

    except Exception as e:
        logger.error(f"Critical error during user data deletion for {current_user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Critical error during data deletion: {str(e)}"
        )


@router.post("/delete", response_model=UserDataDeletionResponse)
async def delete_user_data_post(
    current_user_id: str = Depends(get_current_user_id),
    auth_db = Depends(get_authenticated_db),
    service_db = Depends(get_db)
):
    """
    Alias for DELETE /user-data/delete - provided for Meta compliance requirements.

    Same functionality as the DELETE endpoint, but accessible via POST method.
    """
    # Reuse the same logic as the DELETE endpoint
    return await delete_user_data(current_user_id, auth_db, service_db)




