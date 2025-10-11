from pydantic import BaseModel, Field, validator
from typing import Optional, Any, Dict, List, Union
from enum import Enum

class Platform(str, Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"

class UnifiedMessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    UNSUPPORTED = "unsupported"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MessageContentType(str, Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"

class TextContent(BaseModel):
    type: str = Field("text", description="Type de contenu")
    text: str = Field(..., description="Contenu texte")

class ImageUrlContent(BaseModel):
    type: str = Field("image_url", description="Type de contenu")
    image_url: Dict[str, str] = Field(..., description="Informations de l'image URL")

class UnifiedMessageContent(BaseModel):
    """Schéma unifié pour le contenu des messages entrants"""
    content: Union[str, List[Union[TextContent, ImageUrlContent]]] = Field(
        ..., description="Contenu du message (texte ou structure complexe)"
    )
    token_count: int = Field(..., description="Nombre de tokens du message")
    message_type: UnifiedMessageType = Field(..., description="Type du message")
    message_id: str = Field(..., description="ID externe du message")
    message_from: str = Field(..., description="Expéditeur du message")
    platform: Platform = Field(..., description="Plateforme d'origine")

    # Informations de contact
    customer_name: Optional[str] = Field(None, description="Nom du client/contact")

    storage_object_name: Optional[str] = Field(None, description="Nom de l'objet dans le stockage")
    media_type: Optional[MediaType] = Field(None, description="Type de média")
    caption: Optional[str] = Field(None, description="Légende du média")
    media_url: Optional[str] = Field(None, description="URL du média")
    media_id: Optional[str] = Field(None, description="ID du média externe")

    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées supplémentaires")

    @validator('content')
    def validate_content(cls, v):
        """Valider le format du contenu"""
        if isinstance(v, str):
            return v
        elif isinstance(v, list):
            for item in v:
                # Accepter les objets Pydantic ou les dict
                item_type = getattr(item, 'type', None) or (item.get('type') if isinstance(item, dict) else None)
                if not item_type:
                    raise ValueError("Chaque élément de contenu doit avoir un champ 'type'")
                if item_type not in ['text', 'image_url']:
                    raise ValueError("Type de contenu non supporté")
            return v
        else:
            raise ValueError("Le contenu doit être une chaîne ou une liste")

class MessageExtractionRequest(BaseModel):
    """Requête pour l'extraction de contenu de message"""
    platform: Platform = Field(..., description="Plateforme du message")
    raw_message: Dict[str, Any] = Field(..., description="Message brut de la plateforme")
    user_credentials: Optional[Dict[str, Any]] = Field(None, description="Credentials utilisateur")

class MessageSaveRequest(BaseModel):
    """Requête pour sauvegarder un message extrait"""
    platform: Platform = Field(..., description="Plateforme du message")
    extracted_message: UnifiedMessageContent = Field(..., description="Contenu extrait")
    user_info: Dict[str, Any] = Field(..., description="Informations utilisateur")
    conversation_id: Optional[str] = Field(None, description="ID de conversation existant")
    customer_name: Optional[str] = Field(None, description="Nom du client/contact")
    customer_identifier: Optional[str] = Field(None, description="Identifiant du client (phone, ig id)")

class MessageSaveResponse(BaseModel):
    """Réponse de sauvegarde de message"""
    success: bool = Field(..., description="Succès de la sauvegarde")
    conversation_message_id: Optional[str] = Field(None, description="ID du message de conversation")
    conversation_id: Optional[str] = Field(None, description="ID de conversation")
    error: Optional[str] = Field(None, description="Message d'erreur")

class BatchMessageRequest(BaseModel):
    """Requête pour ajouter un message au batch de traitement"""
    platform: Platform = Field(..., description="Plateforme du message")
    account_id: str = Field(..., description="ID du compte plateforme")
    contact_id: str = Field(..., description="ID du contact")
    message_data: Dict[str, Any] = Field(..., description="Données du message")
    conversation_message_id: str = Field(..., description="ID du message de conversation")
