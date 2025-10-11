import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.services.user_data_deletion_service import DeletionResult


class TestUserDataRouter:
    """Tests for the user data deletion router."""

    @pytest.fixture
    def test_client(self):
        """Test client for API calls."""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        return {"id": "user_123", "email": "test@example.com"}

    @pytest.fixture
    def mock_deletion_result(self):
        """Mock deletion result."""
        result = DeletionResult(user_id="user_123")
        result.record("conversations", 5)
        result.record("conversation_messages", 25)
        result.record("social_accounts", 2)
        result.storage_deleted = ["file1.pdf", "file2.jpg"]
        result.cache_keys_deleted = ["conv:whatsapp:123:456", "conv:instagram:789:012"]
        return result

    @patch('app.routers.user_data.get_current_user_id')
    @patch('app.routers.user_data.get_authenticated_db')
    @patch('app.routers.user_data.get_db')
    @patch('app.routers.user_data.UserDataDeletionService')
    def test_delete_user_data_success(
        self, mock_service_class, mock_service_db, mock_auth_db, mock_auth, test_client, mock_current_user, mock_deletion_result
    ):
        """Test successful user data deletion via DELETE endpoint."""
        # Setup mocks
        mock_auth.return_value = mock_current_user["id"]
        mock_auth_db.return_value = Mock()
        mock_service_db.return_value = Mock()

        # Mock the service
        mock_service_instance = Mock()
        mock_service_instance.delete_user_data = AsyncMock(return_value=mock_deletion_result)
        mock_service_class.return_value = mock_service_instance

        # Make request
        response = test_client.delete("/api/user-data/delete")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "user_123"
        assert data["deleted_counts"]["conversations"] == 5
        assert data["deleted_counts"]["conversation_messages"] == 25
        assert data["deleted_counts"]["social_accounts"] == 2
        assert len(data["storage_deleted"]) == 2
        assert len(data["cache_keys_deleted"]) == 2
        assert len(data["errors"]) == 0
        assert data["success"] is True

    @patch('app.routers.user_data.get_current_user_id')
    @patch('app.routers.user_data.get_authenticated_db')
    @patch('app.routers.user_data.get_db')
    @patch('app.routers.user_data.UserDataDeletionService')
    def test_delete_user_data_with_errors(
        self, mock_service_class, mock_service_db, mock_auth_db, mock_auth, test_client, mock_current_user
    ):
        """Test user data deletion with errors."""
        # Setup mocks
        mock_auth.return_value = mock_current_user["id"]
        mock_auth_db.return_value = Mock()
        mock_service_db.return_value = Mock()

        # Mock the service with errors
        mock_deletion_result = DeletionResult(user_id="user_123")
        mock_deletion_result.record("conversations", 3)
        mock_deletion_result.add_error("storage", Exception("Storage delete failed"))
        mock_deletion_result.add_error("cache", Exception("Cache clear failed"))

        mock_service_instance = Mock()
        mock_service_instance.delete_user_data = AsyncMock(return_value=mock_deletion_result)
        mock_service_class.return_value = mock_service_instance

        # Make request
        response = test_client.delete("/api/user-data/delete")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert len(data["errors"]) == 2
        assert "Storage delete failed" in data["errors"][0]
        assert "Cache clear failed" in data["errors"][1]

    @patch('app.routers.user_data.get_current_user_id')
    @patch('app.routers.user_data.get_authenticated_db')
    @patch('app.routers.user_data.get_db')
    @patch('app.routers.user_data.UserDataDeletionService')
    def test_delete_user_data_service_error(
        self, mock_service_class, mock_service_db, mock_auth_db, mock_auth, test_client, mock_current_user
    ):
        """Test handling of service-level errors."""
        # Setup mocks
        mock_auth.return_value = mock_current_user["id"]
        mock_auth_db.return_value = Mock()
        mock_service_db.return_value = Mock()

        # Mock service to raise exception
        mock_service_instance = Mock()
        mock_service_instance.delete_user_data = AsyncMock(side_effect=Exception("Service error"))
        mock_service_class.return_value = mock_service_instance

        # Make request
        response = test_client.delete("/api/user-data/delete")

        # Should return 500 error
        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]

    @patch('app.routers.user_data.get_current_user_id')
    @patch('app.routers.user_data.get_authenticated_db')
    @patch('app.routers.user_data.get_db')
    @patch('app.routers.user_data.UserDataDeletionService')
    def test_post_user_data_delete_success(
        self, mock_service_class, mock_service_db, mock_auth_db, mock_auth, test_client, mock_current_user, mock_deletion_result
    ):
        """Test successful user data deletion via POST endpoint (Meta compliance)."""
        # Setup mocks
        mock_auth.return_value = mock_current_user["id"]
        mock_auth_db.return_value = Mock()
        mock_service_db.return_value = Mock()

        # Mock the service
        mock_service_instance = Mock()
        mock_service_instance.delete_user_data = AsyncMock(return_value=mock_deletion_result)
        mock_service_class.return_value = mock_service_instance

        # Make request
        response = test_client.post("/api/user-data/delete")

        # Verify response (same as DELETE endpoint)
        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "user_123"
        assert data["success"] is True

    def test_delete_user_data_unauthorized(self, test_client):
        """Test deletion without authentication."""
        response = test_client.delete("/api/user-data/delete")

        # Should return 401 or 422 depending on auth setup
        assert response.status_code in [401, 422]

    def test_post_user_data_delete_unauthorized(self, test_client):
        """Test POST deletion without authentication."""
        response = test_client.post("/api/user-data/delete")

        # Should return 401 or 422 depending on auth setup
        assert response.status_code in [401, 422]


class TestUserDataDeletionResponse:
    """Tests for the UserDataDeletionResponse model."""

    def test_from_deletion_result_success(self, mock_deletion_result):
        """Test conversion from DeletionResult to response model."""
        from app.routers.user_data import UserDataDeletionResponse

        response = UserDataDeletionResponse.from_deletion_result(mock_deletion_result)

        assert response.user_id == "user_123"
        assert response.deleted_counts["conversations"] == 5
        assert response.deleted_counts["conversation_messages"] == 25
        assert response.deleted_counts["social_accounts"] == 2
        assert len(response.storage_deleted) == 2
        assert len(response.cache_keys_deleted) == 2
        assert len(response.errors) == 0
        assert response.success is True

    def test_from_deletion_result_with_errors(self):
        """Test conversion from DeletionResult with errors."""
        from app.routers.user_data import UserDataDeletionResponse

        result = DeletionResult(user_id="user_123")
        result.add_error("db", Exception("Database error"))
        result.add_error("storage", Exception("Storage error"))

        response = UserDataDeletionResponse.from_deletion_result(result)

        assert response.success is False
        assert len(response.errors) == 2
        assert "Database error" in response.errors[0]
        assert "Storage error" in response.errors[1]





