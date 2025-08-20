import pytest
from app.schemas.common import SocialPlatform

class TestSocialPlatform:
    def test_all_platforms_available(self):
        """Test que toutes les plateformes attendues sont disponibles"""
        expected_platforms = {
            "facebook", "twitter", "instagram", 
            "linkedin", "youtube", "tiktok", "whatsapp"
        }
        
        actual_platforms = {platform.value for platform in SocialPlatform}
        
        assert actual_platforms == expected_platforms
        
    def test_platform_values(self):
        """Test les valeurs spécifiques des plateformes"""
        assert SocialPlatform.instagram.value == "instagram"
        assert SocialPlatform.linkedin.value == "linkedin"
        assert SocialPlatform.twitter.value == "twitter"
        assert SocialPlatform.facebook.value == "facebook"
        assert SocialPlatform.youtube.value == "youtube"
        assert SocialPlatform.tiktok.value == "tiktok"
        assert SocialPlatform.whatsapp.value == "whatsapp"
        
    def test_platform_comparison_with_string(self):
        """Test comparaison des plateformes avec des strings"""
        assert SocialPlatform.instagram == "instagram"
        assert SocialPlatform.linkedin == "linkedin"
        assert SocialPlatform.twitter == "twitter"
        
        # Tests négatifs
        assert SocialPlatform.instagram != "linkedin"
        assert SocialPlatform.twitter != "instagram"
        
    def test_platform_enum_membership(self):
        """Test appartenance à l'enum"""
        assert "instagram" in [p.value for p in SocialPlatform]
        assert "linkedin" in [p.value for p in SocialPlatform]
        assert "invalid_platform" not in [p.value for p in SocialPlatform]
        
    def test_platform_iteration(self):
        """Test itération sur les plateformes"""
        platforms = []
        for platform in SocialPlatform:
            platforms.append(platform.value)
            
        assert len(platforms) == 7
        assert "instagram" in platforms
        assert "linkedin" in platforms
        
    def test_platform_from_value(self):
        """Test création de plateforme depuis valeur"""
        instagram = SocialPlatform("instagram")
        linkedin = SocialPlatform("linkedin")
        
        assert instagram == SocialPlatform.instagram
        assert linkedin == SocialPlatform.linkedin
        
    def test_invalid_platform_raises_error(self):
        """Test qu'une plateforme invalide lève une erreur"""
        with pytest.raises(ValueError):
            SocialPlatform("invalid_platform")
            
    def test_platform_string_representation(self):
        """Test représentation string des plateformes"""
        assert SocialPlatform.instagram.value == "instagram"
        assert SocialPlatform.linkedin.value == "linkedin"
        assert SocialPlatform.twitter.value == "twitter"
        
    def test_platform_repr(self):
        """Test représentation repr des plateformes"""
        instagram_repr = repr(SocialPlatform.instagram)
        assert "instagram" in instagram_repr
        assert "SocialPlatform" in instagram_repr