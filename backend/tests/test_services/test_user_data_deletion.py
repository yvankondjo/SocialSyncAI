import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, List

from app.services.user_data_deletion_service import UserDataDeletionService, DeletionResult


class TestUserDataDeletionService:
    """Tests for the UserDataDeletionService."""

    @pytest.fixture
    def mock_auth_db(self):
        """Mock authenticated database client."""
        return Mock()

    @pytest.fixture
    def mock_service_db(self):
        """Mock service database client."""
        return Mock()

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return "user_123"

    @pytest.fixture
    def deletion_service(self, mock_auth_db, mock_service_db, user_id):
        """Create a UserDataDeletionService instance."""
        return UserDataDeletionService(
            auth_db=mock_auth_db,
            service_db=mock_service_db,
            user_id=user_id
        )

    def test_init(self, mock_auth_db, mock_service_db, user_id):
        """Test service initialization."""
        service = UserDataDeletionService(mock_auth_db, mock_service_db, user_id)
        assert service.auth_db == mock_auth_db
        assert service.service_db == mock_service_db
        assert service.user_id == user_id
        assert service.storage_bucket_names == ["message", "knowledge"]

    @pytest.mark.asyncio
    async def test_delete_user_data_success(self, deletion_service, mock_auth_db, mock_service_db):
        """Test successful user data deletion."""
        # Setup mock responses
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "account_1"}, {"id": "account_2"}]
        }
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            {"data": [{"id": "conv_1"}, {"id": "conv_2"}]},  # conversations
            {"data": [{"id": "doc_1", "storage_object_name": "file.pdf"}]}  # documents
        ]

        # Mock deletion operations
        mock_service_db.table.return_value.delete.return_value.in_.return_value.execute.return_value = {
            "data": [{"id": "deleted_1"}]
        }
        mock_service_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "deleted_1"}]
        }

        # Mock storage operations
        mock_bucket = Mock()
        mock_service_db.storage.from_.return_value = mock_bucket

        # Execute deletion
        result = await deletion_service.delete_user_data()

        # Verify result
        assert isinstance(result, DeletionResult)
        assert result.user_id == deletion_service.user_id
        assert "social_accounts" in result.deleted_counts
        assert "conversations" in result.deleted_counts
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_delete_user_data_with_errors(self, deletion_service, mock_auth_db):
        """Test user data deletion with some errors."""
        # Setup to cause errors in some operations
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")

        result = await deletion_service.delete_user_data()

        # Should have errors recorded
        assert len(result.errors) > 0
        assert any("DB Error" in error for error in result.errors)

    def test_get_social_account_ids(self, deletion_service, mock_auth_db):
        """Test fetching social account IDs."""
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "account_1"}, {"id": "account_2"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        account_ids = deletion_service._get_social_account_ids(result)

        assert account_ids == ["account_1", "account_2"]
        assert len(result.errors) == 0

    def test_get_social_account_ids_error(self, deletion_service, mock_auth_db):
        """Test error handling when fetching social account IDs."""
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")

        result = DeletionResult(user_id=deletion_service.user_id)
        account_ids = deletion_service._get_social_account_ids(result)

        assert account_ids == []
        assert len(result.errors) == 1
        assert "social_accounts.fetch" in result.errors[0]

    def test_get_conversation_ids(self, deletion_service, mock_auth_db):
        """Test fetching conversation IDs."""
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "conv_1"}, {"id": "conv_2"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        conv_ids = deletion_service._get_conversation_ids(result)

        assert conv_ids == ["conv_1", "conv_2"]
        assert len(result.errors) == 0

    def test_get_document_entries(self, deletion_service, mock_auth_db):
        """Test fetching document entries."""
        mock_auth_db.table.return_value.select.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "doc_1", "storage_object_name": "file.pdf"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        docs = deletion_service._get_document_entries(result)

        assert len(docs) == 1
        assert docs[0]["id"] == "doc_1"
        assert docs[0]["storage_object_name"] == "file.pdf"

    @pytest.mark.asyncio
    async def test_delete_conversation_messages(self, deletion_service, mock_service_db):
        """Test deleting conversation messages."""
        mock_service_db.table.return_value.delete.return_value.in_.return_value.execute.return_value = {
            "data": [{"id": "msg_1"}, {"id": "msg_2"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        await deletion_service._delete_conversation_messages(["conv_1", "conv_2"], result)

        assert result.deleted_counts["conversation_messages"] == 2

    @pytest.mark.asyncio
    async def test_delete_conversation_messages_empty_list(self, deletion_service):
        """Test deleting conversation messages with empty list."""
        result = DeletionResult(user_id=deletion_service.user_id)
        await deletion_service._delete_conversation_messages([], result)

        # Should not have recorded anything
        assert "conversation_messages" not in result.deleted_counts

    def test_delete_conversations(self, deletion_service, mock_service_db):
        """Test deleting conversations."""
        mock_service_db.table.return_value.delete.return_value.in_.return_value.execute.return_value = {
            "data": [{"id": "conv_1"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_conversations(["conv_1"], result)

        assert result.deleted_counts["conversations"] == 1

    def test_delete_social_accounts(self, deletion_service, mock_service_db):
        """Test deleting social accounts."""
        mock_service_db.table.return_value.delete.return_value.in_.return_value.execute.return_value = {
            "data": [{"id": "account_1"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_social_accounts(["account_1"], result)

        assert result.deleted_counts["social_accounts"] == 1

    def test_delete_knowledge_chunks(self, deletion_service, mock_service_db):
        """Test deleting knowledge chunks."""
        mock_service_db.table.return_value.delete.return_value.in_.return_value.execute.return_value = {
            "data": [{"id": "chunk_1"}, {"id": "chunk_2"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_knowledge_chunks(["doc_1"], result)

        assert result.deleted_counts["knowledge_chunks"] == 2

    @pytest.mark.asyncio
    async def test_delete_document_storage_objects(self, deletion_service, mock_service_db):
        """Test deleting document storage objects."""
        mock_bucket = Mock()
        mock_service_db.storage.from_.return_value = mock_bucket

        document_entries = [{"id": "doc_1", "storage_object_name": "file.pdf"}]

        result = DeletionResult(user_id=deletion_service.user_id)
        await deletion_service._delete_document_storage_objects(document_entries, result)

        # Verify storage deletion was called
        mock_bucket.remove.assert_called_once_with("file.pdf")
        assert "file.pdf" in result.storage_deleted

    def test_delete_knowledge_documents(self, deletion_service, mock_service_db):
        """Test deleting knowledge documents."""
        mock_service_db.table.return_value.delete.return_value.in_.return_value.execute.return_value = {
            "data": [{"id": "doc_1"}]
        }

        document_entries = [{"id": "doc_1", "storage_object_name": "file.pdf"}]

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_knowledge_documents(document_entries, result)

        assert result.deleted_counts["knowledge_documents"] == 1

    def test_delete_support_escalations(self, deletion_service, mock_service_db):
        """Test deleting support escalations."""
        mock_service_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "esc_1"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_support_escalations(result)

        assert result.deleted_counts["support_escalations"] == 1

    def test_delete_ai_settings(self, deletion_service, mock_service_db):
        """Test deleting AI settings."""
        mock_service_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "ai_1"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_ai_settings(result)

        assert result.deleted_counts["ai_settings"] == 1

    def test_delete_user_preferences(self, deletion_service, mock_service_db):
        """Test deleting user preferences."""
        mock_service_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "pref_1"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_user_preferences(result)

        assert result.deleted_counts["user_preferences"] == 1

    def test_delete_user_record(self, deletion_service, mock_service_db):
        """Test deleting user record."""
        mock_service_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = {
            "data": [{"id": "user_123"}]
        }

        result = DeletionResult(user_id=deletion_service.user_id)
        deletion_service._delete_user_record(result)

        assert result.deleted_counts["users"] == 1

    def test_deletion_result_methods(self):
        """Test DeletionResult helper methods."""
        result = DeletionResult(user_id="user_123")

        # Test record method
        result.record("conversations", 5)
        result.record("messages", 10)
        result.record("conversations", 3)  # Should add to existing

        assert result.deleted_counts["conversations"] == 8
        assert result.deleted_counts["messages"] == 10

        # Test add_error method
        exc = Exception("Test error")
        result.add_error("storage", exc)

        assert len(result.errors) == 1
        assert "storage: Test error" in result.errors[0]





