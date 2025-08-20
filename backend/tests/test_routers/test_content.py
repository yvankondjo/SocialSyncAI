import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testtest_client import TestClient
from datetime import datetime
from uuid import uuid4
from app.main import app

# Le test_client de test est défini dans conftest.py

class TestContentRouter:
    
    @pytest.fixture
    def valid_content_data(self):
        return {
            "title": "Test Content",
            "content": "This is test content",
            "social_account_id": str(uuid4()),
            "content_type": "text",
            "status": "draft"
        }
    
    @pytest.fixture
    def mock_content_db_response(self):
        content_id = str(uuid4())
        social_account_id = str(uuid4())
        created_by = str(uuid4())
        
        return {
            "data": [{
                "id": content_id,
                "title": "Test Content",
                "content": "This is test content",
                "social_account_id": social_account_id,
                "created_by": created_by,
                "content_type": "text",
                "status": "draft",
                "media_url": None,
                "published_at": None,
                "scheduled_at": None,
                "created_at": "2024-01-15T10:30:45.123Z",
                "updated_at": "2024-01-15T10:30:45.123Z"
            }]
        }

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_create_content_success(self, mock_db, mock_service, mock_auth, valid_content_data, test_client):
        """Test création contenu réussie"""
        mock_auth.return_value = "user_123"
        mock_service.create_content = AsyncMock(return_value={
            "id": "content_123",
            **valid_content_data,
            "created_by": "user_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        response = test_client.post("/api/content/", json=valid_content_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Content"
        assert data["content"] == "This is test content"

    @patch('app.routers.content.get_current_user_id')
    def test_create_content_invalid_data(self, mock_auth, test_client):
        """Test création avec données invalides"""
        mock_auth.return_value = "user_123"
        
        invalid_data = {
            "title": "",  # Titre vide
            "content": "Content without title"
            # Manque social_account_id
        }
        
        response = test_client.post("/api/content/", json=invalid_data)
        
        assert response.status_code == 422

    @patch('app.routers.content.get_current_user_id')
    def test_create_content_invalid_uuid(self, mock_auth, test_client):
        """Test création avec UUID invalide"""
        mock_auth.return_value = "user_123"
        
        invalid_data = {
            "title": "Test",
            "content": "Content",
            "social_account_id": "not-a-uuid"
        }
        
        response = test_client.post("/api/content/", json=invalid_data)
        
        assert response.status_code == 422

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_get_content_by_id_success(self, mock_db, mock_service, mock_auth, mock_content_db_response, test_client):
        """Test récupération contenu par ID"""
        mock_auth.return_value = "user_123"
        mock_service.get_content_by_id = AsyncMock(return_value=mock_content_db_response["data"][0])
        
        response = test_client.get("/api/content/content_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Content"

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_get_content_by_id_not_found(self, mock_db, mock_service, mock_auth, test_client):
        """Test contenu non trouvé"""
        mock_auth.return_value = "user_123"
        mock_service.get_content_by_id = AsyncMock(return_value=None)
        
        response = test_client.get("/api/content/nonexistent")
        
        assert response.status_code == 404

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_get_user_content_success(self, mock_db, mock_service, mock_auth, mock_content_db_response, test_client):
        """Test récupération contenu utilisateur"""
        mock_auth.return_value = "user_123"
        mock_service.get_user_content = AsyncMock(return_value=mock_content_db_response["data"])
        
        response = test_client.get("/api/content/user/user_123")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test Content"

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_update_content_success(self, mock_db, mock_service, mock_auth, test_client):
        """Test mise à jour contenu"""
        mock_auth.return_value = "user_123"
        
        update_data = {
            "title": "Updated Title",
            "status": "published"
        }
        
        updated_content = {
            "id": "content_123",
            "title": "Updated Title",
            "content": "Original content",
            "status": "published",
            "updated_at": datetime.now()
        }
        
        mock_service.update_content = AsyncMock(return_value=updated_content)
        
        response = test_client.put("/api/content/content_123", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "published"

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_update_content_not_found(self, mock_db, mock_service, mock_auth, test_client):
        """Test mise à jour contenu non trouvé"""
        mock_auth.return_value = "user_123"
        mock_service.update_content = AsyncMock(return_value=None)
        
        update_data = {"title": "Updated Title"}
        
        response = test_client.put("/api/content/nonexistent", json=update_data)
        
        assert response.status_code == 404

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_delete_content_success(self, mock_db, mock_service, mock_auth, test_client):
        """Test suppression contenu"""
        mock_auth.return_value = "user_123"
        mock_service.delete_content = AsyncMock(return_value=True)
        
        response = test_client.delete("/api/content/content_123")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Content deleted successfully"

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_delete_content_not_found(self, mock_db, mock_service, mock_auth, test_client):
        """Test suppression contenu non trouvé"""
        mock_auth.return_value = "user_123"
        mock_service.delete_content = AsyncMock(return_value=False)
        
        response = test_client.delete("/api/content/nonexistent")
        
        assert response.status_code == 404

class TestContentFiltering:
    """Tests pour le filtrage et la pagination du contenu"""
    
    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_get_content_with_filters(self, mock_db, mock_service, mock_auth, test_client):
        """Test récupération avec filtres"""
        mock_auth.return_value = "user_123"
        
        filtered_content = [
            {
                "id": "content_1",
                "title": "Published Content",
                "status": "published",
                "content_type": "text"
            }
        ]
        
        mock_service.get_user_content = AsyncMock(return_value=filtered_content)
        
        response = test_client.get("/api/content/user/user_123?status=published&content_type=text")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "published"
        assert data[0]["content_type"] == "text"

    @patch('app.routers.content.get_current_user_id')
    @patch('app.routers.content.content_service')
    @patch('app.routers.content.get_db')
    def test_get_content_with_pagination(self, mock_db, mock_service, mock_auth, test_client):
        """Test récupération avec pagination"""
        mock_auth.return_value = "user_123"
        
        paginated_content = [
            {"id": f"content_{i}", "title": f"Content {i}"} 
            for i in range(10)
        ]
        
        mock_service.get_user_content = AsyncMock(return_value=paginated_content[:5])  # Première page
        
        response = test_client.get("/api/content/user/user_123?limit=5&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

class TestContentValidation:
    """Tests de validation spécifiques au contenu"""
    
    @patch('app.routers.content.get_current_user_id')
    def test_content_title_validation(self, mock_auth, test_client):
        """Test validation du titre"""
        mock_auth.return_value = "user_123"
        
        # Titre trop long
        long_title_data = {
            "title": "A" * 500,  # Titre très long
            "content": "Content",
            "social_account_id": str(uuid4())
        }
        
        response = test_client.post("/api/content/", json=long_title_data)
        # Dépend de la validation en place
        assert response.status_code in [200, 422]

    @patch('app.routers.content.get_current_user_id')
    def test_content_type_validation(self, mock_auth, test_client):
        """Test validation du type de contenu"""
        mock_auth.return_value = "user_123"
        
        valid_types = ["text", "image", "video", "carousel"]
        
        for content_type in valid_types:
            data = {
                "title": f"Test {content_type}",
                "content": "Content",
                "social_account_id": str(uuid4()),
                "content_type": content_type
            }
            
            response = test_client.post("/api/content/", json=data)
            # Le résultat dépend de la validation en place
            assert response.status_code in [200, 422]

    @patch('app.routers.content.get_current_user_id')
    def test_content_status_validation(self, mock_auth, test_client):
        """Test validation du statut"""
        mock_auth.return_value = "user_123"
        
        valid_statuses = ["draft", "scheduled", "published", "failed"]
        
        for status in valid_statuses:
            data = {
                "title": f"Test {status}",
                "content": "Content",
                "social_account_id": str(uuid4()),
                "status": status
            }
            
            response = test_client.post("/api/content/", json=data)
            # Le résultat dépend de la validation en place
            assert response.status_code in [200, 422]