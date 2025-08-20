import pytest
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import ValidationError
from app.schemas.insights import AnalyticsBase, AnalyticsCreate, Analytics, AnalyticsHistory
from app.schemas.common import SocialPlatform

class TestAnalyticsBase:
    def test_default_values(self):
        """Test valeurs par défaut d'AnalyticsBase"""
        analytics = AnalyticsBase()
        
        assert analytics.likes == 0
        assert analytics.shares == 0
        assert analytics.comments == 0
        assert analytics.impressions == 0
        assert analytics.reach == 0
        assert analytics.engagement_rate == 0.0
        assert analytics.clicks == 0
        assert analytics.conversions == 0
        assert analytics.raw_metrics is None
        
    def test_with_custom_values(self):
        """Test avec valeurs personnalisées"""
        data = {
            "likes": 100,
            "shares": 50,
            "comments": 25,
            "impressions": 5000,
            "reach": 3000,
            "engagement_rate": 5.5,
            "clicks": 200,
            "conversions": 10,
            "raw_metrics": {"additional_data": "value", "custom_metric": 42}
        }
        
        analytics = AnalyticsBase(**data)
        
        assert analytics.likes == 100
        assert analytics.shares == 50
        assert analytics.engagement_rate == 5.5
        assert analytics.raw_metrics == {"additional_data": "value", "custom_metric": 42}
        
    def test_negative_values_allowed(self):
        """Test que les valeurs négatives sont autorisées"""
        data = {
            "likes": -1,  # Peut être utile pour delta
            "engagement_rate": -2.5
        }
        
        analytics = AnalyticsBase(**data)
        
        assert analytics.likes == -1
        assert analytics.engagement_rate == -2.5

class TestAnalyticsCreate:
    def test_valid_analytics_create(self):
        """Test création valide AnalyticsCreate"""
        data = {
            "content_id": uuid4(),
            "platform": SocialPlatform.instagram,
            "likes": 100,
            "shares": 50
        }
        
        analytics = AnalyticsCreate(**data)
        
        assert isinstance(analytics.content_id, UUID)
        assert analytics.platform == SocialPlatform.instagram
        assert analytics.likes == 100
        assert analytics.shares == 50
        
    def test_all_platforms_supported(self):
        """Test que toutes les plateformes sont supportées"""
        content_id = uuid4()
        
        for platform in SocialPlatform:
            data = {
                "content_id": content_id,
                "platform": platform,
                "likes": 10
            }
            
            analytics = AnalyticsCreate(**data)
            assert analytics.platform == platform
        
    def test_invalid_platform(self):
        """Test plateforme invalide"""
        data = {
            "content_id": uuid4(),
            "platform": "invalid_platform",
            "likes": 100
        }
        
        with pytest.raises(ValidationError):
            AnalyticsCreate(**data)
            
    def test_invalid_content_id(self):
        """Test content_id invalide"""
        data = {
            "content_id": "not-a-uuid",
            "platform": SocialPlatform.instagram,
            "likes": 100
        }
        
        with pytest.raises(ValidationError):
            AnalyticsCreate(**data)

class TestAnalytics:
    def test_complete_analytics(self):
        """Test Analytics complet"""
        data = {
            "content_id": uuid4(),
            "platform": SocialPlatform.linkedin,
            "id": uuid4(),
            "recorded_at": datetime.now(),
            "created_at": datetime.now(),
            "likes": 200,
            "shares": 100,
            "engagement_rate": 7.5
        }
        
        analytics = Analytics(**data)
        
        assert isinstance(analytics.id, UUID)
        assert isinstance(analytics.content_id, UUID)
        assert isinstance(analytics.recorded_at, datetime)
        assert isinstance(analytics.created_at, datetime)
        assert analytics.platform == SocialPlatform.linkedin
        assert analytics.likes == 200
        assert analytics.engagement_rate == 7.5
        
    def test_inherits_from_analytics_create(self):
        """Test que Analytics hérite d'AnalyticsCreate"""
        base_data = {
            "content_id": uuid4(),
            "platform": SocialPlatform.twitter,
            "likes": 50
        }
        
        create_analytics = AnalyticsCreate(**base_data)
        
        full_data = {
            **base_data,
            "id": uuid4(),
            "recorded_at": datetime.now(),
            "created_at": datetime.now()
        }
        
        analytics = Analytics(**full_data)
        
        # Même valeurs héritées
        assert analytics.content_id == create_analytics.content_id
        assert analytics.platform == create_analytics.platform
        assert analytics.likes == create_analytics.likes

class TestAnalyticsHistory:
    def test_analytics_history(self):
        """Test AnalyticsHistory"""
        data = {
            "id": uuid4(),
            "recorded_at": datetime.now(),
            "created_at": datetime.now(),
            "user_id": uuid4(),
            "likes": 300,
            "shares": 150,
            "comments": 75
        }
        
        analytics = AnalyticsHistory(**data)
        
        assert isinstance(analytics.id, UUID)
        assert isinstance(analytics.user_id, UUID)
        assert isinstance(analytics.recorded_at, datetime)
        assert isinstance(analytics.created_at, datetime)
        assert analytics.likes == 300
        assert analytics.shares == 150
        assert analytics.comments == 75
        
    def test_from_attributes_config(self):
        """Test configuration from_attributes"""
        class MockDBAnalytics:
            def __init__(self):
                self.id = uuid4()
                self.recorded_at = datetime.now()
                self.created_at = datetime.now()
                self.user_id = uuid4()
                self.likes = 500
                self.shares = 250
                self.comments = 125
                self.impressions = 10000
                self.reach = 7500
                self.engagement_rate = 12.5
                self.clicks = 400
                self.conversions = 25
                self.raw_metrics = {"source": "instagram_api"}
        
        mock_obj = MockDBAnalytics()
        analytics = AnalyticsHistory.model_validate(mock_obj)
        
        assert analytics.likes == 500
        assert analytics.engagement_rate == 12.5
        assert analytics.raw_metrics == {"source": "instagram_api"}

class TestAnalyticsIntegration:
    """Tests d'intégration pour différents scénarios"""
    
    def test_instagram_analytics_flow(self):
        """Test flux complet analytics Instagram"""
        content_id = uuid4()
        
        # 1. Création analytics
        create_data = {
            "content_id": content_id,
            "platform": SocialPlatform.instagram,
            "likes": 250,
            "comments": 45,
            "shares": 12,
            "impressions": 8500,
            "reach": 5200,
            "engagement_rate": 3.6
        }
        
        analytics_create = AnalyticsCreate(**create_data)
        
        # 2. Analytics complet après sauvegarde
        full_data = {
            **create_data,
            "id": uuid4(),
            "recorded_at": datetime.now(),
            "created_at": datetime.now()
        }
        
        analytics = Analytics(**full_data)
        
        assert analytics.content_id == content_id
        assert analytics.platform == SocialPlatform.instagram
        assert analytics.likes == 250
        assert analytics.engagement_rate == 3.6
        
    def test_zero_engagement_scenario(self):
        """Test scénario avec engagement zéro"""
        data = {
            "content_id": uuid4(),
            "platform": SocialPlatform.linkedin,
            "impressions": 1000,
            "reach": 800
            # Tous les autres à 0 par défaut
        }
        
        analytics = AnalyticsCreate(**data)
        
        assert analytics.likes == 0
        assert analytics.shares == 0
        assert analytics.comments == 0
        assert analytics.engagement_rate == 0.0
        assert analytics.impressions == 1000
        assert analytics.reach == 800