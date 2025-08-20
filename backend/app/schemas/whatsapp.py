from pydantic import BaseModel, Field, validator
from typing import Optional, Any, Dict, List
from enum import Enum

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"

class MessageType(str, Enum):
    TEXT = "text"
    TEMPLATE = "template"
    MEDIA = "media"

# Schémas de requête
class WhatsAppCredentials(BaseModel):
    access_token: str = Field(..., description="Token d'accès WhatsApp Business")
    phone_number_id: str = Field(..., description="ID du numéro de téléphone WhatsApp")

class TextMessageRequest(BaseModel):
    to: str = Field(..., description="Numéro de téléphone destinataire (format: 33612345678)")
    text: str = Field(..., min_length=1, max_length=4096, description="Contenu du message")
    access_token: Optional[str] = Field(None, description="Token d'accès spécifique (optionnel)")
    phone_number_id: Optional[str] = Field(None, description="ID du numéro spécifique (optionnel)")
    
    @validator('to')
    def validate_phone_number(cls, v):
        # Retirer les espaces et caractères spéciaux
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Numéro de téléphone invalide')
        return cleaned

class TemplateMessageRequest(BaseModel):
    to: str = Field(..., description="Numéro de téléphone destinataire")
    template_name: str = Field("hello_world", description="Nom du template WhatsApp")
    language_code: str = Field("en_US", description="Code langue du template")
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    
    @validator('to')
    def validate_phone_number(cls, v):
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Numéro de téléphone invalide')
        return cleaned

class MediaMessageRequest(BaseModel):
    to: str = Field(..., description="Numéro de téléphone destinataire")
    media_type: MediaType = Field(..., description="Type de média")
    media_url: str = Field(..., description="URL du média à envoyer")
    caption: Optional[str] = Field("", description="Légende du média (optionnelle)")
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    
    @validator('to')
    def validate_phone_number(cls, v):
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Numéro de téléphone invalide')
        return cleaned
    
    @validator('media_url')
    def validate_media_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL du média invalide')
        return v

# Schémas de réponse
class PhoneInfo(BaseModel):
    display_phone_number: str
    verified_name: Optional[str]
    code_verification_status: Optional[str]
    quality_rating: Optional[str]

class WhatsAppCredentialsValidation(BaseModel):
    valid: bool
    phone_info: Optional[PhoneInfo] = None
    error: Optional[str] = None

class MessageContact(BaseModel):
    input: str
    wa_id: str

class MessageInfo(BaseModel):
    id: str
    message_status: Optional[str] = None

class WhatsAppMessageResponse(BaseModel):
    messaging_product: str
    contacts: List[MessageContact]
    messages: List[MessageInfo]
    success: bool = True
    message_type: str

class BusinessProfileData(BaseModel):
    messaging_product: str
    address: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    websites: Optional[List[str]] = None
    vertical: Optional[str] = None

class BusinessProfileResponse(BaseModel):
    data: List[BusinessProfileData]

class WhatsAppErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# Schémas pour les webhooks (à venir)
class WebhookMessageStatus(BaseModel):
    id: str
    status: str  # sent, delivered, read, failed
    timestamp: str
    recipient_id: str

class WebhookIncomingMessage(BaseModel):
    id: str
    from_: str = Field(..., alias="from")
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    video: Optional[Dict[str, str]] = None
    audio: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None

class WebhookEntry(BaseModel):
    id: str
    changes: List[Dict[str, Any]]

class WebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]

# Schémas utilitaires
class SendMessageBatch(BaseModel):
    messages: List[TextMessageRequest] = Field(..., max_items=100)
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None

class BatchResponse(BaseModel):
    total_messages: int
    successful_messages: int
    failed_messages: int
    results: List[Dict[str, Any]]
