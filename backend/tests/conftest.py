import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def valid_base_data():
    """Données valides pour SocialAccountBase"""
    return {
        "platform": "instagram",
        "username": "test_user", 
        "account_id": "12345",
        "access_token": "token123",
        "user_id": "user456"
    }

@pytest.fixture
def complete_account_data(valid_base_data):
    """Données complètes avec champs DB"""
    return {
        **valid_base_data,
        "id": "account789",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@pytest.fixture
def valid_user_data():
    """Données utilisateur valides"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }

@pytest.fixture
def valid_content_data():
    """Données contenu valides"""
    return {
        "title": "Test Content",
        "content": "This is test content",
        "content_type": "text",
        "status": "draft"
    }

@pytest.fixture
def mock_supabase_client():
    """Mock client Supabase"""
    mock = Mock()
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = [{"id": "123"}]
    mock.table.return_value.update.return_value.execute.return_value.data = [{"id": "123"}]
    mock.table.return_value.upsert.return_value.execute.return_value.data = [{"id": "123"}]
    return mock

@pytest.fixture
def mock_current_user():
    """Mock utilisateur authentifié"""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "sub": "user_123"
    }

@pytest.fixture
def sample_analytics_data():
    """Données analytics d'exemple"""
    return {
        "content_id": uuid4(),
        "platform": "instagram",
        "likes": 100,
        "shares": 50,
        "comments": 25,
        "impressions": 5000,
        "reach": 3000,
        "engagement_rate": 5.5
    }

@pytest.fixture
def mock_db_response():
    """Mock réponse base de données standard"""
    return {
        "data": [{
            "id": "test_id_123",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }]
    }

@pytest.fixture(scope="session")
def test_client():
    """Fixture globale pour le client de test"""
    return TestClient(app)

# Auto-use fixtures pour les tests d'intégration
@pytest.fixture(autouse=True)
def mock_external_apis():
    """Mock toutes les APIs externes"""
    with patch('app.services.social_auth_service.social_auth_service') as mock_service:
        # Mock Instagram
        mock_service.get_instagram_auth_url.return_value = "https://api.instagram.com/oauth/authorize"
        mock_service.handle_instagram_callback.return_value = {"access_token": "token", "expires_in": 3600}
        mock_service.get_instagram_business_account.return_value = {"id": "123", "username": "test"}
        
        # Mock LinkedIn
        mock_service.get_linkedin_auth_url.return_value = "https://api.linkedin.com/oauth/authorize"
        mock_service.handle_linkedin_callback.return_value = {"access_token": "token", "expires_in": 3600}
        mock_service.get_linkedin_business_profile.return_value = {"id": "123", "username": "test"}
        
        # Mock Twitter
        mock_service.get_twitter_auth_url.return_value = "https://api.twitter.com/oauth/authorize"
        mock_service.handle_twitter_callback.return_value = {"access_token": "token", "expires_in": 3600}
        mock_service.get_twitter_profile.return_value = {"id": "123", "username": "test"}
        
        # Mock TikTok
        mock_service.get_tiktok_auth_url.return_value = "https://api.tiktok.com/oauth/authorize"
        mock_service.handle_tiktok_callback.return_value = {"access_token": "token", "expires_in": 3600}
        mock_service.get_tiktok_profile.return_value = {"id": "123", "username": "test"}
        
        yield mock_service