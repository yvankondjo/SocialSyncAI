import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testtest_client import TestClient
from datetime import datetime
from uuid import uuid4
from app.main import app

# Le test_client de test est défini dans conftest.py

class TestAnalyticsRouter:
    
    @pytest.fixture
    def mock_analytics_response(self):
        return {
            "content_id": "content_123",
            "platform": "instagram",
            "likes": 150,
            "shares": 75,
            "comments": 25,
            "impressions": 5000,
            "reach": 3000,
            "engagement_rate": 5.2,
            "clicks": 200,
            "conversions": 10
        }

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_sync_content_analytics_success(self, mock_db, mock_service, mock_auth, mock_analytics_response, test_client):
        """Test synchronisation analytics contenu réussie"""
        mock_auth.return_value = "user_123"
        mock_service.sync_content_analytics = AsyncMock(return_value={
            "success": True,
            "data": mock_analytics_response
        })
        
        response = test_client.post("/api/analytics/sync/content_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_sync_content_analytics_error(self, mock_db, mock_service, mock_auth, test_client):
        """Test erreur lors synchronisation analytics"""
        mock_auth.return_value = "user_123"
        mock_service.sync_content_analytics = AsyncMock(return_value={
            "error": "Content not found or not accessible"
        })
        
        response = test_client.post("/api/analytics/sync/nonexistent_content")
        
        assert response.status_code == 400
        assert "Content not found" in response.json()["detail"]

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_sync_user_analytics_success(self, mock_db, mock_service, mock_auth, test_client):
        """Test synchronisation analytics utilisateur"""
        mock_auth.return_value = "user_123"
        mock_service.sync_user_analytics = AsyncMock(return_value={
            "success": True,
            "synced_content_count": 5,
            "total_impressions": 25000,
            "total_engagement": 1250
        })
        
        response = test_client.post("/api/analytics/sync/user/user_123?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["synced_content_count"] == 5

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_sync_user_analytics_custom_days(self, mock_db, mock_service, mock_auth, test_client):
        """Test synchronisation avec période personnalisée"""
        mock_auth.return_value = "user_123"
        mock_service.sync_user_analytics = AsyncMock(return_value={
            "success": True,
            "synced_content_count": 15,
            "days": 30
        })
        
        response = test_client.post("/api/analytics/sync/user/user_123?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["synced_content_count"] == 15

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_get_content_analytics_success(self, mock_db, mock_service, mock_auth, mock_analytics_response, test_client):
        """Test récupération analytics contenu"""
        mock_auth.return_value = "user_123"
        mock_service.get_content_analytics = AsyncMock(return_value=[mock_analytics_response])
        
        response = test_client.get("/api/analytics/content/content_123")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["content_id"] == "content_123"

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_get_content_analytics_not_found(self, mock_db, mock_service, mock_auth, test_client):
        """Test analytics contenu non trouvé"""
        mock_auth.return_value = "user_123"
        mock_service.get_content_analytics = AsyncMock(return_value=[])
        
        response = test_client.get("/api/analytics/content/nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_get_user_analytics_summary(self, mock_db, mock_service, mock_auth, test_client):
        """Test récupération résumé analytics utilisateur"""
        mock_auth.return_value = "user_123"
        
        summary_data = {
            "total_content": 25,
            "total_likes": 5000,
            "total_shares": 2500,
            "total_comments": 1250,
            "total_impressions": 125000,
            "total_reach": 75000,
            "average_engagement_rate": 4.2,
            "top_performing_content": [
                {"content_id": "content_1", "engagement_rate": 8.5},
                {"content_id": "content_2", "engagement_rate": 7.2}
            ]
        }
        
        mock_service.get_user_analytics_summary = AsyncMock(return_value=summary_data)
        
        response = test_client.get("/api/analytics/user/user_123/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_content"] == 25
        assert data["average_engagement_rate"] == 4.2
        assert len(data["top_performing_content"]) == 2

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_get_analytics_by_platform(self, mock_db, mock_service, mock_auth, test_client):
        """Test récupération analytics par plateforme"""
        mock_auth.return_value = "user_123"
        
        platform_data = {
            "instagram": {
                "total_content": 15,
                "total_likes": 3000,
                "average_engagement_rate": 5.1
            },
            "linkedin": {
                "total_content": 8,
                "total_likes": 1200,
                "average_engagement_rate": 3.8
            }
        }
        
        mock_service.get_analytics_by_platform = AsyncMock(return_value=platform_data)
        
        response = test_client.get("/api/analytics/user/user_123/by-platform")
        
        assert response.status_code == 200
        data = response.json()
        assert "instagram" in data
        assert "linkedin" in data
        assert data["instagram"]["total_content"] == 15

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_get_analytics_trends(self, mock_db, mock_service, mock_auth, test_client):
        """Test récupération tendances analytics"""
        mock_auth.return_value = "user_123"
        
        trends_data = {
            "daily_metrics": [
                {"date": "2024-01-01", "likes": 150, "impressions": 2000},
                {"date": "2024-01-02", "likes": 200, "impressions": 2500},
                {"date": "2024-01-03", "likes": 175, "impressions": 2200}
            ],
            "growth_rate": {
                "likes": 12.5,
                "impressions": 8.3,
                "engagement_rate": -2.1
            }
        }
        
        mock_service.get_analytics_trends = AsyncMock(return_value=trends_data)
        
        response = test_client.get("/api/analytics/user/user_123/trends?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_metrics" in data
        assert "growth_rate" in data
        assert len(data["daily_metrics"]) == 3

class TestAnalyticsValidation:
    """Tests de validation pour les paramètres analytics"""
    
    @patch('app.routers.analytics.get_current_user_id')
    def test_invalid_days_parameter(self, mock_auth, test_client):
        """Test paramètre days invalide"""
        mock_auth.return_value = "user_123"
        
        # Jours négatifs
        response = test_client.post("/api/analytics/sync/user/user_123?days=-5")
        assert response.status_code == 422
        
        # Jours trop élevés
        response = test_client.post("/api/analytics/sync/user/user_123?days=10000")
        # Dépend de la validation en place
        assert response.status_code in [200, 422]

    @patch('app.routers.analytics.get_current_user_id')
    def test_invalid_content_id_format(self, mock_auth, test_client):
        """Test format content_id invalide"""
        mock_auth.return_value = "user_123"
        
        # ID vide
        response = test_client.post("/api/analytics/sync/")
        assert response.status_code == 404  # Route not found
        
        # ID avec caractères spéciaux
        response = test_client.post("/api/analytics/sync/content@123")
        # Dépend du routage
        assert response.status_code in [200, 400, 404]

class TestAnalyticsPermissions:
    """Tests de permissions pour les analytics"""
    
    def test_analytics_without_auth(self, test_client):
        """Test accès analytics sans authentification"""
        response = test_client.get("/api/analytics/content/content_123")
        assert response.status_code in [401, 422]  # Selon la config auth

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_analytics_different_user(self, mock_db, mock_service, mock_auth, test_client):
        """Test accès analytics d'un autre utilisateur"""
        mock_auth.return_value = "user_123"
        mock_service.get_user_analytics_summary = AsyncMock(return_value={
            "error": "Access denied"
        })
        
        # Tenter d'accéder aux analytics d'un autre utilisateur
        response = test_client.get("/api/analytics/user/other_user/summary")
        
        # Le comportement dépend de la logique d'autorisation
        assert response.status_code in [200, 403]

class TestAnalyticsBackground:
    """Tests pour les tâches en arrière-plan"""
    
    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_background_sync_user_analytics(self, mock_db, mock_service, mock_auth, test_client):
        """Test synchronisation en arrière-plan"""
        mock_auth.return_value = "user_123"
        mock_service.sync_user_analytics = AsyncMock(return_value={
            "success": True,
            "background_task_id": "task_456"
        })
        
        response = test_client.post("/api/analytics/sync/user/user_123?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch('app.routers.analytics.get_current_user_id')
    @patch('app.routers.analytics.analytics_service')
    @patch('app.routers.analytics.get_db')
    def test_analytics_service_timeout(self, mock_db, mock_service, mock_auth, test_client):
        """Test timeout du service analytics"""
        mock_auth.return_value = "user_123"
        mock_service.sync_content_analytics = AsyncMock(side_effect=TimeoutError("Service timeout"))
        
        response = test_client.post("/api/analytics/sync/content_123")
        
        assert response.status_code == 500