from pydantic import BaseModel, Field, validator
from typing import Optional, Any, Dict, List, Union
from enum import Enum

class Platform(str, Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"

class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    TEMPLATE = "template"
    POST = "post"
    STORY = "story"

# Schémas de requête unifiés
class UnifiedMessageRequest(BaseModel):
    platform: Platform = Field(..., description="Plateforme cible")
    message_type: MessageType = Field(..., description="Type de message")
    recipient: str = Field(..., description="Destinataire (numéro, email, ID, webhook URL)")
    content: str = Field(..., description="Contenu principal du message")
    
    # Paramètres optionnels spécifiques aux plateformes
    access_token: Optional[str] = Field(None, description="Token d'accès spécifique")
    phone_number_id: Optional[str] = Field(None, description="ID téléphone WhatsApp")
    page_id: Optional[str] = Field(None, description="ID page Instagram")
    
    # Paramètres pour différents types de messages
    subject: Optional[str] = Field(None, description="Sujet (email)")
    title: Optional[str] = Field(None, description="Titre (push notifications)")
    caption: Optional[str] = Field(None, description="Légende (média)")
    template_name: Optional[str] = Field(None, description="Nom du template")
    language_code: Optional[str] = Field(None, description="Code langue")
    media_type: Optional[str] = Field(None, description="Type de média")
    media_url: Optional[str] = Field(None, description="URL du média")
    image_url: Optional[str] = Field(None, description="URL de l'image")
    
    # Paramètres avancés
    is_html: Optional[bool] = Field(False, description="Email HTML")
    channel: Optional[str] = Field(None, description="Canal Slack")
    username: Optional[str] = Field("SocialSync", description="Nom d'utilisateur")
    extra_params: Optional[Dict[str, Any]] = Field({}, description="Paramètres supplémentaires")

class BulkMessageRequest(BaseModel):
    messages: List[UnifiedMessageRequest] = Field(..., max_items=100, description="Liste des messages")

class BroadcastRequest(BaseModel):
    platforms: List[Platform] = Field(..., description="Plateformes cibles")
    message_type: MessageType = Field(..., description="Type de message")
    content: str = Field(..., description="Contenu du message")
    recipients: Dict[Platform, List[str]] = Field(..., description="Destinataires par plateforme")
    
    # Paramètres communs optionnels
    subject: Optional[str] = None
    title: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = {}

# Schémas de réponse
class UnifiedMessageResponse(BaseModel):
    success: bool = True
    platform: str
    recipient: str
    message_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BulkMessageResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[UnifiedMessageResponse]

class BroadcastResponse(BaseModel):
    platforms: Dict[str, Dict[str, Any]]  # platform -> {total, successful, failed, results}
    summary: Dict[str, int]  # total_messages, total_successful, total_failed

class PlatformCapabilities(BaseModel):
    message_types: List[str]
    media_types: List[str]
    max_text_length: Optional[int]
    supports_markup: bool
    requires_credentials: bool

class CapabilitiesResponse(BaseModel):
    platform: Platform
    capabilities: PlatformCapabilities

# Schémas pour les différentes plateformes (utilisés par l'API unifiée)
class WhatsAppParams(BaseModel):
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    template_name: Optional[str] = "hello_world"
    language_code: Optional[str] = "en_US"
    media_type: Optional[str] = "image"

class InstagramParams(BaseModel):
    access_token: Optional[str] = None
    page_id: Optional[str] = None
    caption: Optional[str] = ""
    location_id: Optional[str] = None

class EmailParams(BaseModel):
    subject: str = "SocialSync Notification"
    is_html: bool = False
    attachments: List[str] = []

class PushParams(BaseModel):
    title: str = "SocialSync"
    provider: str = "firebase"  # firebase ou onesignal
    data: Optional[Dict[str, Any]] = None
    url: Optional[str] = None

class SlackParams(BaseModel):
    channel: Optional[str] = None
    username: str = "SocialSync"

class DiscordParams(BaseModel):
    username: str = "SocialSync"

class WebhookParams(BaseModel):
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

# Schéma pour la détection automatique de plateforme
class SmartMessageRequest(BaseModel):
    recipient: str = Field(..., description="Destinataire (auto-détection du type)")
    content: str = Field(..., description="Contenu du message")
    message_type: MessageType = Field(MessageType.TEXT, description="Type de message")
    
    # Paramètres optionnels
    subject: Optional[str] = None
    title: Optional[str] = None
    fallback_platforms: Optional[List[Platform]] = Field([], description="Plateformes de fallback")
    auto_detect: bool = Field(True, description="Activer la détection automatique")

class SmartMessageResponse(BaseModel):
    detected_platform: Platform
    confidence: float  # 0.0 to 1.0
    success: bool
    result: Optional[Dict[str, Any]] = None
    fallback_used: bool = False
    error: Optional[str] = None
