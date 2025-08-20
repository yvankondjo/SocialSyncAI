from pydantic import BaseModel, Field, validator
from typing import Optional, Any, Dict, List
from enum import Enum

class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class PositionType(str, Enum):
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"

class WidgetSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"

# Schémas de configuration
class WidgetSettings(BaseModel):
    # Apparence
    theme: ThemeType = ThemeType.LIGHT
    primary_color: str = Field("#007bff", regex=r"^#[0-9A-Fa-f]{6}$")
    position: PositionType = PositionType.BOTTOM_RIGHT
    widget_size: WidgetSize = WidgetSize.MEDIUM
    
    # Textes
    welcome_message: str = Field("Bonjour ! Comment puis-je vous aider ?", max_length=200)
    placeholder_text: str = Field("Tapez votre message...", max_length=100)
    offline_message: str = Field("Nous reviendrons vers vous bientôt !", max_length=200)
    company_name: str = Field("Support", max_length=50)
    
    # Comportement
    auto_open: bool = False
    auto_open_delay: int = Field(3000, ge=1000, le=30000)  # 1-30 secondes
    show_agent_typing: bool = True
    collect_email: bool = True
    collect_name: bool = False
    
    # IA
    ai_enabled: bool = True
    ai_provider: AIProvider = AIProvider.OPENAI
    ai_model: str = "gpt-3.5-turbo"
    ai_temperature: float = Field(0.7, ge=0.0, le=2.0)
    ai_max_tokens: int = Field(150, ge=50, le=500)
    ai_system_prompt: str = Field(
        "Vous êtes un assistant IA serviable pour le support client. Répondez de manière courtoise et professionnelle.",
        max_length=1000
    )
    
    # Sécurité
    allowed_domains: List[str] = []
    rate_limit: int = Field(10, ge=1, le=100)  # messages par minute
    max_conversation_length: int = Field(50, ge=10, le=200)

class CreateWidgetRequest(BaseModel):
    website_url: str = Field(..., description="URL du site web")
    widget_settings: WidgetSettings = Field(..., description="Configuration du widget")
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL du site web invalide')
        return v

class UpdateWidgetRequest(BaseModel):
    widget_settings: WidgetSettings = Field(..., description="Nouvelle configuration")

# Schémas de réponse
class WidgetConfig(BaseModel):
    widget_id: str
    api_key: str
    user_id: str
    website_url: str
    created_at: str
    status: str
    settings: WidgetSettings

class CreateWidgetResponse(BaseModel):
    success: bool = True
    widget_id: str
    api_key: str
    config: WidgetConfig
    embed_code: str
    setup_instructions: Dict[str, Any]

class WidgetPreviewResponse(BaseModel):
    html_preview: str
    css_variables: Dict[str, str]

class WidgetAnalytics(BaseModel):
    widget_id: str
    date_range: str
    total_conversations: int
    total_messages: int
    avg_response_time: float
    ai_resolution_rate: float
    user_satisfaction: float
    top_questions: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]
    response_times: Dict[str, float]

# Schémas pour le chat
class ChatMessage(BaseModel):
    widget_id: str = Field(..., description="ID du widget")
    message: str = Field(..., min_length=1, max_length=1000, description="Message de l'utilisateur")
    conversation_id: Optional[str] = Field(None, description="ID de conversation (optionnel)")
    user_info: Optional[Dict[str, str]] = Field({}, description="Infos utilisateur (email, nom, etc.)")

class ChatResponse(BaseModel):
    success: bool = True
    conversation_id: str
    user_message: str
    ai_response: str
    timestamp: str
    response_time: float
    error: Optional[str] = None
    fallback_response: Optional[str] = None

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    last_activity: str
    user_info: Dict[str, str]
    widget_id: str

# Schémas pour les analytics
class AnalyticsRequest(BaseModel):
    date_range: str = Field("7d", regex=r"^(1d|7d|30d|90d)$")

class DomainValidationRequest(BaseModel):
    widget_id: str
    domain: str

class WidgetStatusUpdate(BaseModel):
    status: str = Field(..., regex=r"^(active|inactive|suspended)$")

# Schémas pour l'administration
class WidgetListItem(BaseModel):
    widget_id: str
    website_url: str
    company_name: str
    status: str
    created_at: str
    total_conversations: int
    last_activity: str

class UserWidgetsResponse(BaseModel):
    widgets: List[WidgetListItem]
    total_count: int
    active_widgets: int
    total_conversations: int

# Schémas pour les templates de widget
class WidgetTemplate(BaseModel):
    template_id: str
    name: str
    description: str
    category: str
    settings: WidgetSettings
    preview_image: str

class TemplatesResponse(BaseModel):
    templates: List[WidgetTemplate]
    categories: List[str]
