from pydantic import BaseModel, Field, validator
from typing import Optional, Any, Dict, List
from enum import Enum

class MediaType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL_ALBUM = "CAROUSEL_ALBUM"
    STORIES = "STORIES"

class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    TEMPLATE = "template"

# Schémas de requête
class InstagramCredentials(BaseModel):
    access_token: str = Field(..., description="Token d'accès Instagram Business")
    page_id: str = Field(..., description="ID de la page Instagram Business")

class DirectMessageRequest(BaseModel):
    recipient_ig_id: str = Field(..., description="ID Instagram du destinataire")
    text: str = Field(..., min_length=1, max_length=1000, description="Contenu du message")
    access_token: Optional[str] = None
    page_id: Optional[str] = None

class FeedPostRequest(BaseModel):
    image_url: str = Field(..., description="URL de l'image à publier")
    caption: str = Field("", max_length=2200, description="Légende du post")
    location_id: Optional[str] = Field(None, description="ID du lieu")
    access_token: Optional[str] = None
    page_id: Optional[str] = None
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL de l\'image invalide')
        return v

class StoryRequest(BaseModel):
    image_url: str = Field(..., description="URL de l'image de la story")
    link_url: Optional[str] = Field(None, description="URL de lien (optionnel)")
    access_token: Optional[str] = None
    page_id: Optional[str] = None
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL de l\'image invalide')
        return v

class CommentReplyRequest(BaseModel):
    comment_id: str = Field(..., description="ID du commentaire")
    message: str = Field(..., min_length=1, max_length=8000, description="Réponse au commentaire")
    access_token: Optional[str] = None
    page_id: Optional[str] = None

class ScheduledPostRequest(BaseModel):
    image_url: str = Field(..., description="URL de l'image")
    caption: str = Field("", max_length=2200, description="Légende du post")
    publish_time: int = Field(..., description="Timestamp Unix de publication")
    access_token: Optional[str] = None
    page_id: Optional[str] = None

# Schémas de réponse
class AccountInfo(BaseModel):
    id: str
    username: Optional[str]
    name: Optional[str]
    followers_count: Optional[int]
    media_count: Optional[int]
    profile_picture_url: Optional[str]

class InstagramCredentialsValidation(BaseModel):
    valid: bool
    account_info: Optional[AccountInfo] = None
    error: Optional[str] = None

class InstagramMessageResponse(BaseModel):
    success: bool = True
    message_id: Optional[str] = None
    error: Optional[str] = None

class InstagramPostResponse(BaseModel):
    success: bool = True
    post_id: Optional[str] = None
    container_id: Optional[str] = None
    message: str = "Post publié avec succès"

class InstagramStoryResponse(BaseModel):
    success: bool = True
    story_id: Optional[str] = None
    container_id: Optional[str] = None
    message: str = "Story publiée avec succès"

class ConversationData(BaseModel):
    id: str
    updated_time: Optional[str]
    message_count: Optional[int]
    unread_count: Optional[int]

class ConversationsResponse(BaseModel):
    data: List[ConversationData]
    paging: Optional[Dict[str, Any]] = None

class MessageData(BaseModel):
    id: str
    created_time: Optional[str]
    message: Optional[str]
    from_: Optional[Dict[str, str]] = Field(None, alias="from")
    to: Optional[Dict[str, str]] = None

class MessagesResponse(BaseModel):
    data: List[MessageData]
    paging: Optional[Dict[str, Any]] = None

class MediaInsight(BaseModel):
    name: str
    period: str
    values: List[Dict[str, Any]]
    title: str
    description: str

class MediaInsightsResponse(BaseModel):
    data: List[MediaInsight]

class CommentReplyResponse(BaseModel):
    success: bool = True
    reply_id: Optional[str] = None
    message: str = "Réponse publiée avec succès"

class ScheduledPostResponse(BaseModel):
    success: bool = True
    container_id: str
    scheduled_time: int
    message: str = "Post programmé avec succès"

class InstagramErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# Schémas utilitaires
class BatchDirectMessageRequest(BaseModel):
    messages: List[DirectMessageRequest] = Field(..., max_items=50)
    access_token: Optional[str] = None
    page_id: Optional[str] = None

class BatchResponse(BaseModel):
    total_messages: int
    successful_messages: int
    failed_messages: int
    results: List[Dict[str, Any]]

class HashtagSearchRequest(BaseModel):
    hashtag: str = Field(..., min_length=1, description="Hashtag à rechercher (sans #)")
    access_token: Optional[str] = None
    page_id: Optional[str] = None

class UserSearchRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Nom d'utilisateur à rechercher (sans @)")
    access_token: Optional[str] = None
    page_id: Optional[str] = None
