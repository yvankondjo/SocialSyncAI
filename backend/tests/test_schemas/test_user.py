import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.user import UserBase, UserCreate, UserUpdate, User

class TestUserBase:
    def test_valid_user_base(self):
        """Test création valide UserBase"""
        data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        user = UserBase(**data)
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True  # Valeur par défaut
        
    def test_user_base_minimal(self):
        """Test avec seulement l'email (champ requis)"""
        data = {"email": "minimal@example.com"}
        
        user = UserBase(**data)
        
        assert user.email == "minimal@example.com"
        assert user.full_name is None
        assert user.is_active is True
        
    def test_invalid_email(self):
        """Test validation email invalide"""
        data = {
            "email": "not-an-email",
            "full_name": "Test User"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserBase(**data)
            
        assert "email" in str(exc_info.value)
        
    def test_missing_email(self):
        """Test email manquant (requis)"""
        data = {"full_name": "Test User"}
        
        with pytest.raises(ValidationError):
            UserBase(**data)

class TestUserCreate:
    def test_valid_user_create(self):
        """Test création valide UserCreate"""
        data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "securepassword123"
        }
        
        user = UserCreate(**data)
        
        assert user.email == "test@example.com"
        assert user.password == "securepassword123"
        assert user.full_name == "Test User"
        
    def test_user_create_inherits_base(self):
        """Test que UserCreate hérite de UserBase"""
        data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        user = UserCreate(**data)
        
        assert user.is_active is True  # Hérité de UserBase
        assert user.full_name is None  # Hérité de UserBase
        
    def test_missing_password(self):
        """Test mot de passe manquant"""
        data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)

class TestUserUpdate:
    def test_all_fields_optional(self):
        """Test que tous les champs sont optionnels dans UserUpdate"""
        user = UserUpdate()
        
        assert user.email is None
        assert user.full_name is None
        assert user.is_active is None
        
    def test_partial_update(self):
        """Test mise à jour partielle"""
        data = {"email": "new@example.com"}
        
        user = UserUpdate(**data)
        
        assert user.email == "new@example.com"
        assert user.full_name is None
        assert user.is_active is None
        
    def test_full_update(self):
        """Test mise à jour complète"""
        data = {
            "email": "updated@example.com",
            "full_name": "Updated User",
            "is_active": False
        }
        
        user = UserUpdate(**data)
        
        assert user.email == "updated@example.com"
        assert user.full_name == "Updated User"
        assert user.is_active is False

class TestUser:
    def test_complete_user(self):
        """Test utilisateur complet avec tous les champs"""
        data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "id": "user_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        user = User(**data)
        
        assert user.id == "user_123"
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.email == "test@example.com"
        
    def test_from_attributes_config(self):
        """Test configuration from_attributes"""
        class MockDBUser:
            def __init__(self):
                self.email = "mock@example.com"
                self.full_name = "Mock User"
                self.is_active = True
                self.id = "mock_123"
                self.created_at = datetime.now()
                self.updated_at = datetime.now()
        
        mock_obj = MockDBUser()
        user = User.model_validate(mock_obj)
        
        assert user.email == "mock@example.com"
        assert user.full_name == "Mock User"
        assert user.id == "mock_123"