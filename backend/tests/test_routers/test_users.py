import pytest
from unittest.mock import Mock, patch
from fastapi.testtest_client import TestClient
from datetime import datetime
from app.main import app

# Le test_client de test est défini dans conftest.py

class TestUsersRouter:
    
    @pytest.fixture
    def valid_user_data(self):
        return {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "securepassword123"
        }
    
    @pytest.fixture
    def mock_user_db_response(self):
        return {
            "data": [{
                "id": "user_123",
                "email": "test@example.com",
                "full_name": "Test User",
                "is_active": True,
                "created_at": "2024-01-15T10:30:45.123Z",
                "updated_at": "2024-01-15T10:30:45.123Z"
            }]
        }

    @patch('app.routers.users.get_db')
    def test_create_user_success(self, mock_db, valid_user_data, mock_user_db_response, test_client):
        """Test création utilisateur réussie"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.insert.return_value.execute.return_value = mock_user_db_response
        
        response = test_client.post("/api/users/", json=valid_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data
        assert "password" not in data  # Mot de passe ne doit pas être retourné

    @patch('app.routers.users.get_db')
    def test_create_user_invalid_email(self, mock_db, test_client):
        """Test création avec email invalide"""
        invalid_data = {
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "password123"
        }
        
        response = test_client.post("/api/users/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
        assert "email" in response.json()["detail"][0]["loc"]

    @patch('app.routers.users.get_db')
    def test_create_user_missing_password(self, mock_db, test_client):
        """Test création sans mot de passe"""
        invalid_data = {
            "email": "test@example.com",
            "full_name": "Test User"
            # Manque password
        }
        
        response = test_client.post("/api/users/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    @patch('app.routers.users.get_db')
    def test_create_user_missing_email(self, mock_db, test_client):
        """Test création sans email"""
        invalid_data = {
            "full_name": "Test User",
            "password": "password123"
            # Manque email
        }
        
        response = test_client.post("/api/users/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    @patch('app.routers.users.get_db')
    def test_create_user_db_error(self, mock_db, valid_user_data, test_client):
        """Test erreur base de données lors création"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
        
        response = test_client.post("/api/users/", json=valid_user_data)
        
        assert response.status_code == 500

    @patch('app.routers.users.get_db')
    def test_create_user_empty_response(self, mock_db, valid_user_data, test_client):
        """Test réponse vide de la base de données"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.insert.return_value.execute.return_value = {"data": []}
        
        response = test_client.post("/api/users/", json=valid_user_data)
        
        assert response.status_code == 500

    @patch('app.routers.users.get_db')
    def test_get_users_success(self, mock_db, mock_user_db_response, test_client):
        """Test récupération liste utilisateurs"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.execute.return_value = mock_user_db_response
        
        response = test_client.get("/api/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["email"] == "test@example.com"

    @patch('app.routers.users.get_db')
    def test_get_users_empty_list(self, mock_db, test_client):
        """Test récupération avec liste vide"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.execute.return_value = {"data": []}
        
        response = test_client.get("/api/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('app.routers.users.get_db')
    def test_get_users_db_error(self, mock_db, test_client):
        """Test erreur base de données lors récupération"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.execute.side_effect = Exception("DB Error")
        
        response = test_client.get("/api/users/")
        
        assert response.status_code == 500

    @patch('app.routers.users.get_db')
    def test_get_user_by_id_success(self, mock_db, mock_user_db_response, test_client):
        """Test récupération utilisateur par ID"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user_db_response
        
        response = test_client.get("/api/users/user_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user_123"
        assert data["email"] == "test@example.com"

    @patch('app.routers.users.get_db')
    def test_get_user_by_id_not_found(self, mock_db, test_client):
        """Test utilisateur non trouvé"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = {"data": []}
        
        response = test_client.get("/api/users/nonexistent_user")
        
        assert response.status_code == 404

    @patch('app.routers.users.get_db')
    def test_update_user_success(self, mock_db, mock_user_db_response, test_client):
        """Test mise à jour utilisateur"""
        update_data = {
            "full_name": "Updated User",
            "is_active": False
        }
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = {
            "data": [{
                **mock_user_db_response["data"][0],
                "full_name": "Updated User",
                "is_active": False
            }]
        }
        
        response = test_client.put("/api/users/user_123", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated User"
        assert data["is_active"] is False

    @patch('app.routers.users.get_db')
    def test_update_user_not_found(self, mock_db, test_client):
        """Test mise à jour utilisateur non trouvé"""
        update_data = {"full_name": "Updated User"}
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = {"data": []}
        
        response = test_client.put("/api/users/nonexistent_user", json=update_data)
        
        assert response.status_code == 404

    @patch('app.routers.users.get_db')
    def test_delete_user_success(self, mock_db, mock_user_db_response, test_client):
        """Test suppression utilisateur"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_user_db_response
        
        response = test_client.delete("/api/users/user_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user_123"

    @patch('app.routers.users.get_db')
    def test_delete_user_not_found(self, mock_db, test_client):
        """Test suppression utilisateur non trouvé"""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.delete.return_value.eq.return_value.execute.return_value = {"data": []}
        
        response = test_client.delete("/api/users/nonexistent_user")
        
        assert response.status_code == 404

class TestUsersValidation:
    """Tests spécifiques pour la validation des données utilisateur"""
    
    def test_create_user_edge_cases(self, test_client):
        """Test cas limites pour création utilisateur"""
        # Email vide
        response = test_client.post("/api/users/", json={
            "email": "",
            "password": "password"
        })
        assert response.status_code == 422
        
        # Mot de passe vide
        response = test_client.post("/api/users/", json={
            "email": "test@example.com",
            "password": ""
        })
        assert response.status_code == 422
        
        # Full name très long (si limitation)
        response = test_client.post("/api/users/", json={
            "email": "test@example.com",
            "password": "password",
            "full_name": "A" * 1000  # Nom très long
        })
        # Dépend de la validation en place
        assert response.status_code in [200, 422]

    @patch('app.routers.users.get_db')
    def test_user_creation_with_minimal_data(self, mock_db, test_client):
        """Test création avec données minimales"""
        minimal_data = {
            "email": "minimal@example.com",
            "password": "password123"
            # Pas de full_name
        }
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.insert.return_value.execute.return_value = {
            "data": [{
                "id": "user_456",
                "email": "minimal@example.com",
                "full_name": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }]
        }
        
        response = test_client.post("/api/users/", json=minimal_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "minimal@example.com"
        assert data["full_name"] is None