import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testtest_client import TestClient
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from app.main import app
from app.schemas.social_account import SocialAccount, AuthURL

# Le test_client de test est défini dans conftest.py

class TestSocialAccountsRouter:
    
    @pytest.fixture
    def mock_current_user(self):
        return {"id": "user_123", "email": "test@example.com"}
    
    @pytest.fixture
    def mock_settings(self):
        mock = Mock()
        mock.SUPABASE_JWT_SECRET = "test_secret"
        mock.SUPABASE_JWT_ALGORITHM = "HS256"
        return mock
    
    @pytest.fixture
    def mock_db_response(self):
        return {
            "data": [{
                "id": "account_123",
                "platform": "instagram",
                "username": "test_user",
                "account_id": "12345",
                "access_token": "token123",
                "user_id": "user_123",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "display_name": "Test User",
                "profile_url": "https://instagram.com/test_user",
                "is_active": True,
                "refresh_token": None,
                "token_expires_at": None
            }]
        }

    def test_supported_platforms(self):
        """Test que toutes les plateformes sont supportées"""
        from app.routers.social_accounts import PLATFORMS
        
        expected_platforms = ["instagram", "linkedin", "twitter", "tiktok"]
        
        for platform in expected_platforms:
            assert platform in PLATFORMS
            assert "get_auth_url" in PLATFORMS[platform]
            assert "handle_callback" in PLATFORMS[platform]
            assert "get_profile" in PLATFORMS[platform]

    @patch('app.routers.social_accounts.get_current_user_id')
    @patch('app.routers.social_accounts.get_settings')
    @patch('app.routers.social_accounts.social_auth_service')
    def test_get_authorization_url_success(self, mock_service, mock_settings, mock_auth, test_test_client):
        """Test génération URL d'autorisation réussie"""
        # Setup
        mock_auth.return_value = {"id": "user_123"}
        mock_settings.return_value.SUPABASE_JWT_SECRET = "secret"
        mock_settings.return_value.SUPABASE_JWT_ALGORITHM = "HS256"
        mock_service.get_instagram_auth_url.return_value = "https://api.instagram.com/oauth/authorize?state=jwt_token"
        
        response = test_test_client.get("/api/social-accounts/connect/instagram")
        
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "instagram.com" in data["authorization_url"]

    @patch('app.routers.social_accounts.get_current_user_id')
    def test_get_authorization_url_invalid_platform(self, mock_auth, test_client):
        """Test plateforme non supportée"""
        mock_auth.return_value = {"id": "user_123"}
        
        response = test_client.get("/api/social-accounts/connect/invalid_platform")
        
        assert response.status_code == 404
        assert "Platform not supported" in response.json()["detail"]

    @patch('app.routers.social_accounts.get_db')
    @patch('app.routers.social_accounts.get_settings')
    @patch('app.routers.social_accounts.social_auth_service')
    @patch('app.routers.social_accounts.jwt')
    def test_oauth_callback_success(self, mock_jwt, mock_service, mock_settings, mock_db, test_client):
        """Test callback OAuth réussi"""
        # Setup
        mock_jwt.decode.return_value = {"user_id": "user_123"}
        mock_service.handle_instagram_callback.return_value = {
            "access_token": "token123",
            "expires_in": 3600
        }
        mock_service.get_instagram_business_account.return_value = {
            "id": "12345",
            "username": "test_user",
            "profile_picture_url": "https://example.com/pic.jpg"
        }
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.upsert.return_value.execute.return_value.data = [
            {"id": "account_123", "platform": "instagram"}
        ]
        
        response = test_client.get("/api/social-accounts/connect/instagram/callback?code=auth_code&state=jwt_token")
        
        assert response.status_code == 200
        assert response.json()["platform"] == "instagram"

    @patch('app.routers.social_accounts.jwt')
    def test_oauth_callback_invalid_state(self, mock_jwt, test_client):
        """Test callback avec state JWT invalide"""
        from jose import JWTError
        mock_jwt.decode.side_effect = JWTError("Invalid JWT")
        
        response = test_client.get("/api/social-accounts/connect/instagram/callback?code=auth_code&state=invalid_jwt")
        
        assert response.status_code == 401
        assert "Invalid state parameter" in response.json()["detail"]

    @patch('app.routers.social_accounts.get_db')
    @patch('app.routers.social_accounts.get_current_user_id')
    def test_get_social_accounts_success(self, mock_auth, mock_db, mock_db_response, test_client):
        """Test récupération des comptes sociaux"""
        # Setup
        mock_auth.return_value = {"id": "user_123"}
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_db_response
        
        response = test_client.get("/api/social-accounts/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["platform"] == "instagram"

    @patch('app.routers.social_accounts.get_db')
    @patch('app.routers.social_accounts.get_current_user_id')
    def test_get_social_accounts_empty_result(self, mock_auth, mock_db, test_client):
        """Test récupération avec résultat vide"""
        mock_auth.return_value = {"id": "user_123"}
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = {"data": []}
        
        response = test_client.get("/api/social-accounts/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('app.routers.social_accounts.get_db')
    @patch('app.routers.social_accounts.get_current_user_id')
    def test_get_social_accounts_db_error(self, mock_auth, mock_db, test_client):
        """Test erreur base de données"""
        mock_auth.return_value = {"id": "user_123"}
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
        
        response = test_client.get("/api/social-accounts/")
        
        assert response.status_code == 500
        assert "Could not get social accounts" in response.json()["detail"]

    def test_platforms_configuration(self):
        """Test configuration des plateformes"""
        from app.routers.social_accounts import PLATFORMS
        
        for platform_name, config in PLATFORMS.items():
            assert callable(config["get_auth_url"])
            assert callable(config["handle_callback"])
            assert callable(config["get_profile"])

class TestSocialAccountsIntegration:
    """Tests d'intégration pour les scénarios complets"""
    
    @pytest.fixture
    def complete_oauth_flow_mocks(self):
        return {
            "auth_response": {"authorization_url": "https://api.instagram.com/oauth/authorize"},
            "token_response": {"access_token": "token123", "expires_in": 3600},
            "profile_response": {"id": "12345", "username": "test_user"},
            "db_response": [{"id": "account_123", "platform": "instagram"}]
        }
    
    @patch('app.routers.social_accounts.get_current_user_id')
    @patch('app.routers.social_accounts.get_settings')
    @patch('app.routers.social_accounts.social_auth_service')
    def test_auth_url_generation_all_platforms(self, mock_service, mock_settings, mock_auth, test_client):
        """Test génération URL pour toutes les plateformes"""
        mock_auth.return_value = {"id": "user_123"}
        mock_settings.return_value.SUPABASE_JWT_SECRET = "secret"
        mock_settings.return_value.SUPABASE_JWT_ALGORITHM = "HS256"
        
        # Mock des différentes plateformes
        mock_service.get_instagram_auth_url.return_value = "https://api.instagram.com/oauth/authorize"
        mock_service.get_linkedin_auth_url.return_value = "https://api.linkedin.com/oauth/authorize"
        mock_service.get_twitter_auth_url.return_value = "https://api.twitter.com/oauth/authorize"
        mock_service.get_tiktok_auth_url.return_value = "https://api.tiktok.com/oauth/authorize"
        
        platforms = ["instagram", "linkedin", "twitter", "tiktok"]
        
        for platform in platforms:
            response = test_client.get(f"/api/social-accounts/connect/{platform}")
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert platform in data["authorization_url"] or "oauth/authorize" in data["authorization_url"]

    def test_error_handling_chain(self, test_client):
        """Test chaîne de gestion d'erreurs"""
        # Test sans auth
        response = test_client.get("/api/social-accounts/")
        assert response.status_code in [401, 422]  # Selon la config auth
        
        # Test plateforme invalide
        response = test_client.get("/api/social-accounts/connect/nonexistent")
        assert response.status_code == 404