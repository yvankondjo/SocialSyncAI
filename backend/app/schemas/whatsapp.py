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

# Request schemas
class WhatsAppCredentials(BaseModel):
    access_token: str = Field(..., description="WhatsApp Business access token")
    phone_number_id: str = Field(..., description="WhatsApp phone number ID")

class TextMessageRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number (format: 33612345678)")
    text: str = Field(..., min_length=1, max_length=4096, description="Message content")
    access_token: Optional[str] = Field(None, description="Override access token (optional)")
    phone_number_id: Optional[str] = Field(None, description="Override phone number ID (optional)")
    
    @validator('to')
    def validate_phone_number(cls, v):
        # Remove spaces and special characters
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Invalid phone number')
        return cleaned

class TemplateMessageRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number")
    template_name: str = Field("hello_world", description="WhatsApp template name")
    language_code: str = Field("en_US", description="Template language code")
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    
    @validator('to')
    def validate_phone_number(cls, v):
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Invalid phone number')
        return cleaned

class MediaMessageRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number")
    media_type: MediaType = Field(..., description="Media type")
    media_url: str = Field(..., description="Media URL to send")
    caption: Optional[str] = Field("", description="Media caption (optional)")
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    
    @validator('to')
    def validate_phone_number(cls, v):
        cleaned = ''.join(filter(str.isdigit, v))
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Invalid phone number')
        return cleaned
    
    @validator('media_url')
    def validate_media_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid media URL')
        return v

# Response schemas
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

# Webhook schemas (future)
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

# Utility schemas
class SendMessageBatch(BaseModel):
    messages: List[TextMessageRequest] = Field(..., max_items=100)
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None

class BatchResponse(BaseModel):
    total_messages: int
    successful_messages: int
    failed_messages: int
    results: List[Dict[str, Any]]
