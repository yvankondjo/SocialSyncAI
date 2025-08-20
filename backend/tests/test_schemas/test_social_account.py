import pytest
from datetime import datetime
from pydantic import ValidationError, HttpUrl
from app.schemas.social_account import (
    SocialAccountBase,
    SocialAccountCreate, 
    SocialAccount,
    TokenData,
    AuthURL
)

class TestSocialAccountBase:
    """Tests pour le schéma de base SocialAccountBase"""
    
    def test_valid_social_account_base(self, valid_base_data):
        """Test création valide d'un SocialAccountBase"""
        account = SocialAccountBase(**valid_base_data)
        
        assert account.platform == "instagram"
        assert account.username == "test_user"
        assert account.account_id == "12345"
        assert account.access_token == "token123"
        assert account.user_id == "user456"
        assert account.is_active is True  # Valeur par défaut
        assert account.display_name is None  # Optionnel
        
    def test_social_account_base_with_optionals(self):
        """Test avec tous les champs optionnels"""
        data = {
            "platform": "linkedin",
            "username": "test_user", 
            "account_id": "67890",
            "display_name": "Test User",
            "profile_url": "https://example.com/profile",
            "access_token": "token123",
            "refresh_token": "refresh456",
            "token_expires_at": datetime.now(),
            "is_active": False,
            "user_id": "user789"
        }
        
        account = SocialAccountBase(**data)
        
        assert account.display_name == "Test User"
        assert str(account.profile_url) == "https://example.com/profile"
        assert account.refresh_token == "refresh456"
        assert account.is_active is False
        assert isinstance(account.token_expires_at, datetime)
        
    def test_missing_required_fields(self):
        """Test erreurs avec champs requis manquants"""
        invalid_data = {
            "platform": "instagram",
            # Manque username, account_id, access_token, user_id
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SocialAccountBase(**invalid_data)
            
        errors = exc_info.value.errors()
        missing_fields = {error['loc'][0] for error in errors}
        expected_missing = {'username', 'account_id', 'access_token', 'user_id'}
        
        assert missing_fields == expected_missing
        
    def test_invalid_url_validation(self):
        """Test validation URL invalide"""
        data = {
            "platform": "instagram",
            "username": "test_user",
            "account_id": "12345", 
            "profile_url": "not-a-valid-url",  # URL invalide
            "access_token": "token123",
            "user_id": "user456"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SocialAccountBase(**data)
            
        assert "profile_url" in str(exc_info.value)

class TestSocialAccountCreate:
    """Tests pour SocialAccountCreate (hérite de Base)"""
    
    def test_create_inherits_from_base(self, valid_base_data):
        """Test que Create hérite bien de Base"""
        create_account = SocialAccountCreate(**valid_base_data)
        base_account = SocialAccountBase(**valid_base_data)
        
        # Même comportement que Base
        assert create_account.platform == base_account.platform
        assert create_account.username == base_account.username

class TestSocialAccount:
    """Tests pour SocialAccount (lecture complète)"""
    
    def test_social_account_with_db_fields(self, complete_account_data):
        """Test avec tous les champs y compris DB"""
        account = SocialAccount(**complete_account_data)
        
        assert account.id == "account789"
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)
        
    def test_from_attributes_true(self):
        """Test que from_attributes fonctionne"""
        # Simulation d'un objet avec attributs (comme SQLAlchemy)
        class MockDBObject:
            def __init__(self):
                self.platform = "instagram"
                self.username = "test_user"
                self.account_id = "12345"
                self.access_token = "token123"
                self.user_id = "user456"
                self.id = "account789"
                self.created_at = datetime.now()
                self.updated_at = datetime.now()
                self.display_name = None
                self.profile_url = None
                self.refresh_token = None
                self.token_expires_at = None
                self.is_active = True
        
        db_obj = MockDBObject()
        
        # Doit marcher grâce à from_attributes = True
        account = SocialAccount.model_validate(db_obj)
        
        assert account.platform == "instagram"
        assert account.username == "test_user" 
        assert account.id == "account789"

class TestTokenData:
    """Tests pour TokenData"""
    
    def test_valid_token_data(self):
        """Test création valide TokenData"""
        data = {
            "access_token": "token123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user_id": 12345
        }
        
        token = TokenData(**data)
        
        assert token.access_token == "token123"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.user_id == 12345
        
    def test_token_data_missing_fields(self):
        """Test erreurs champs manquants"""
        data = {"access_token": "token123"}  # Manque les autres
        
        with pytest.raises(ValidationError):
            TokenData(**data)

class TestAuthURL:
    """Tests pour AuthURL"""
    
    def test_valid_auth_url(self):
        """Test URL d'autorisation valide"""
        data = {"authorization_url": "https://api.instagram.com/oauth/authorize"}
        
        auth_url = AuthURL(**data)
        
        assert str(auth_url.authorization_url) == "https://api.instagram.com/oauth/authorize"
        
    def test_invalid_auth_url(self):
        """Test URL invalide"""
        data = {"authorization_url": "not-a-url"}
        
        with pytest.raises(ValidationError):
            AuthURL(**data)

# Tests d'intégration avec des données réelles
class TestRealWorldScenarios:
    """Tests avec des scénarios réels"""
    
    @pytest.fixture
    def instagram_response_data(self):
        """Simulation réponse Instagram API"""
        return {
            "platform": "instagram",
            "username": "real_user",
            "account_id": "17841400455970028",
            "display_name": "Real User",
            "profile_url": "https://www.instagram.com/real_user/",
            "access_token": "IGQVJYWDJqSDJhTVRIdHJGT1NqRnVHdkRCQkFKbHZA...",
            "refresh_token": None,
            "token_expires_at": datetime(2024, 12, 31, 23, 59, 59),
            "is_active": True,
            "user_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    
    def test_instagram_data_flow(self, instagram_response_data):
        """Test flux complet Instagram"""
        # 1. Création depuis API
        create_data = SocialAccountCreate(**instagram_response_data)
        assert create_data.platform == "instagram"
        
        # 2. Ajout champs DB et lecture
        db_data = {
            **instagram_response_data,
            "id": "db_id_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        account = SocialAccount(**db_data)
        assert account.id == "db_id_123"
        assert isinstance(account.created_at, datetime)

    def test_supabase_integration_format(self):
        """Test format données Supabase"""
        # Simulation de ce que retourne Supabase
        supabase_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "platform": "linkedin", 
            "username": "john_doe",
            "account_id": "urn:li:person:ABC123",
            "display_name": "John Doe",
            "profile_url": "https://www.linkedin.com/in/johndoe/",
            "access_token": "AQV...",
            "refresh_token": "AQW...",
            "token_expires_at": "2024-12-31T23:59:59.000Z",
            "is_active": True,
            "user_id": "auth0|123456789",
            "created_at": "2024-01-15T10:30:45.123Z",
            "updated_at": "2024-01-15T10:30:45.123Z"
        }
        
        # Test conversion string datetime
        account = SocialAccount(**supabase_data)
        
        assert account.platform == "linkedin"
        assert isinstance(account.token_expires_at, datetime)
        assert isinstance(account.created_at, datetime)