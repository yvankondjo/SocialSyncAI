import pytest
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import ValidationError
from app.schemas.content import ContentBase, ContentCreate, ContentUpdate, Content

class TestContentBase:
    def test_valid_content_base(self):
        """Test création valide ContentBase"""
        data = {
            "title": "Test Post",
            "content": "This is a test post content"
        }
        
        content = ContentBase(**data)
        
        assert content.title == "Test Post"
        assert content.content == "This is a test post content"
        assert content.content_type == "text"  # Valeur par défaut
        assert content.status == "draft"  # Valeur par défaut
        assert content.media_url is None
        
    def test_content_base_with_optionals(self):
        """Test avec tous les champs optionnels"""
        data = {
            "title": "Video Post",
            "content": "Check out this video!",
            "content_type": "video",
            "status": "published",
            "media_url": "https://example.com/video.mp4"
        }
        
        content = ContentBase(**data)
        
        assert content.content_type == "video"
        assert content.status == "published"
        assert content.media_url == "https://example.com/video.mp4"
        
    def test_missing_required_fields(self):
        """Test erreurs avec champs requis manquants"""
        data = {"title": "Only title"}  # Manque content
        
        with pytest.raises(ValidationError):
            ContentBase(**data)

class TestContentCreate:
    def test_valid_content_create(self):
        """Test création valide ContentCreate"""
        data = {
            "title": "Test Post",
            "content": "Content here",
            "social_account_id": uuid4()
        }
        
        content = ContentCreate(**data)
        
        assert content.title == "Test Post"
        assert isinstance(content.social_account_id, UUID)
        
    def test_invalid_uuid(self):
        """Test UUID invalide"""
        data = {
            "title": "Test Post",
            "content": "Content here",
            "social_account_id": "not-a-uuid"
        }
        
        with pytest.raises(ValidationError):
            ContentCreate(**data)

class TestContentUpdate:
    def test_all_fields_optional(self):
        """Test que tous les champs sont optionnels"""
        content = ContentUpdate()
        
        assert content.title is None
        assert content.content is None
        assert content.status is None
        assert content.scheduled_at is None
        
    def test_partial_update(self):
        """Test mise à jour partielle"""
        data = {
            "title": "Updated Title",
            "status": "published"
        }
        
        content = ContentUpdate(**data)
        
        assert content.title == "Updated Title"
        assert content.status == "published"
        assert content.content is None  # Reste None

class TestContent:
    def test_complete_content(self):
        """Test contenu complet avec tous les champs"""
        data = {
            "title": "Full Content",
            "content": "Complete content",
            "id": "content_123",
            "social_account_id": uuid4(),
            "created_by": uuid4(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        content = Content(**data)
        
        assert content.id == "content_123"
        assert isinstance(content.social_account_id, UUID)
        assert isinstance(content.created_by, UUID)
        assert isinstance(content.created_at, datetime)
        assert content.published_at is None
        assert content.scheduled_at is None
        
    def test_from_attributes_config(self):
        """Test configuration from_attributes"""
        # Simuler un objet avec attributs
        class MockDBContent:
            def __init__(self):
                self.title = "Mock Title"
                self.content = "Mock content"
                self.id = "mock_123"
                self.social_account_id = uuid4()
                self.created_by = uuid4()
                self.created_at = datetime.now()
                self.updated_at = datetime.now()
                self.content_type = "text"
                self.status = "draft"
                self.media_url = None
                self.published_at = None
                self.scheduled_at = None
        
        mock_obj = MockDBContent()
        content = Content.model_validate(mock_obj)
        
        assert content.title == "Mock Title"
        assert content.content == "Mock content"
        assert content.id == "mock_123"