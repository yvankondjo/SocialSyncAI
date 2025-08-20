from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from typing import List, Optional
import logging

from app.schemas.web_widget import (
    CreateWidgetRequest, UpdateWidgetRequest, CreateWidgetResponse,
    WidgetPreviewResponse, WidgetAnalytics, ChatMessage, ChatResponse,
    AnalyticsRequest, DomainValidationRequest, WidgetStatusUpdate,
    UserWidgetsResponse, TemplatesResponse
)
from app.services.web_service import get_web_widget_service

router = APIRouter(prefix="/widget", tags=["Web Widget"])
logger = logging.getLogger(__name__)

@router.post("/create", response_model=CreateWidgetResponse)
async def create_widget(request: CreateWidgetRequest, user_id: str = "user_123"):
    """
    🎨 Créer un nouveau widget de chat IA pour un site web
    
    Génère automatiquement :
    - Configuration du widget
    - Code embed JavaScript
    - Clé API sécurisée
    - Instructions d'installation
    """
    try:
        service = await get_web_widget_service()
        
        result = await service.create_widget_config(
            user_id=user_id,
            website_url=request.website_url,
            widget_settings=request.widget_settings.dict()
        )
        
        return CreateWidgetResponse(**result)
        
    except Exception as e:
        logger.error(f"Erreur création widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création widget: {str(e)}"
        )

@router.get("/preview/{widget_id}", response_class=HTMLResponse)
async def get_widget_preview(widget_id: str):
    """
    👀 Générer un aperçu HTML du widget
    """
    try:
        service = await get_web_widget_service()
        
        # TODO: Récupérer la vraie config depuis la BDD
        mock_config = {
            "settings": {
                "primary_color": "#007bff",
                "company_name": "Support",
                "welcome_message": "Bonjour ! Comment puis-je vous aider ?",
                "placeholder_text": "Tapez votre message..."
            }
        }
        
        html_preview = await service.generate_widget_preview(mock_config)
        return HTMLResponse(content=html_preview)
        
    except Exception as e:
        logger.error(f"Erreur aperçu widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur aperçu: {str(e)}"
        )

@router.put("/update/{widget_id}")
async def update_widget(widget_id: str, request: UpdateWidgetRequest):
    """
    ⚙️ Mettre à jour la configuration d'un widget
    """
    try:
        service = await get_web_widget_service()
        
        result = await service.update_widget_settings(
            widget_id=widget_id,
            new_settings=request.widget_settings.dict()
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur mise à jour widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur mise à jour: {str(e)}"
        )

@router.get("/analytics/{widget_id}", response_model=WidgetAnalytics)
async def get_widget_analytics(widget_id: str, date_range: str = Query("7d", regex="^(1d|7d|30d|90d)$")):
    """
    📊 Récupérer les analytics d'un widget
    """
    try:
        service = await get_web_widget_service()
        
        analytics = await service.get_widget_analytics(widget_id, date_range)
        return WidgetAnalytics(**analytics)
        
    except Exception as e:
        logger.error(f"Erreur analytics widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur analytics: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(request: ChatMessage):
    """
    💬 Traiter un message de chat et générer une réponse IA
    
    Endpoint utilisé par le widget JavaScript pour envoyer les messages
    """
    try:
        service = await get_web_widget_service()
        
        result = await service.process_chat_message(
            widget_id=request.widget_id,
            message=request.message,
            conversation_id=request.conversation_id,
            user_info=request.user_info
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Erreur traitement message: {e}")
        return ChatResponse(
            success=False,
            conversation_id=request.conversation_id or "error",
            user_message=request.message,
            ai_response="",
            timestamp="",
            response_time=0.0,
            error=str(e),
            fallback_response="Désolé, je rencontre des difficultés techniques. Un agent humain vous contactera bientôt."
        )

@router.post("/validate-domain")
async def validate_domain(request: DomainValidationRequest):
    """
    🔒 Valider qu'un domaine est autorisé pour un widget
    """
    try:
        service = await get_web_widget_service()
        
        is_valid = await service.validate_widget_domain(
            widget_id=request.widget_id,
            domain=request.domain
        )
        
        return {
            "widget_id": request.widget_id,
            "domain": request.domain,
            "is_valid": is_valid,
            "message": "Domaine autorisé" if is_valid else "Domaine non autorisé"
        }
        
    except Exception as e:
        logger.error(f"Erreur validation domaine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur validation: {str(e)}"
        )

@router.get("/user-widgets", response_model=UserWidgetsResponse)
async def get_user_widgets(user_id: str = "user_123"):
    """
    📋 Récupérer tous les widgets d'un utilisateur
    """
    try:
        # TODO: Implémenter la récupération depuis la BDD
        
        # Mock data
        mock_widgets = [
            {
                "widget_id": "widget_1",
                "website_url": "https://example.com",
                "company_name": "Example Corp",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "total_conversations": 245,
                "last_activity": "2024-01-15T14:30:00Z"
            },
            {
                "widget_id": "widget_2", 
                "website_url": "https://mystore.shop",
                "company_name": "My Store",
                "status": "active",
                "created_at": "2024-01-05T00:00:00Z",
                "total_conversations": 89,
                "last_activity": "2024-01-15T12:15:00Z"
            }
        ]
        
        return UserWidgetsResponse(
            widgets=mock_widgets,
            total_count=len(mock_widgets),
            active_widgets=len([w for w in mock_widgets if w["status"] == "active"]),
            total_conversations=sum(w["total_conversations"] for w in mock_widgets)
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération widgets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération: {str(e)}"
        )

@router.get("/templates", response_model=TemplatesResponse)
async def get_widget_templates():
    """
    🎨 Récupérer les templates de widgets disponibles
    """
    try:
        from app.schemas.web_widget import WidgetTemplate, WidgetSettings, ThemeType, PositionType
        
        templates = [
            WidgetTemplate(
                template_id="minimal",
                name="Minimal",
                description="Widget simple et épuré",
                category="Basic",
                settings=WidgetSettings(
                    theme=ThemeType.LIGHT,
                    primary_color="#6c757d",
                    position=PositionType.BOTTOM_RIGHT,
                    welcome_message="Bonjour, comment puis-je vous aider ?",
                    company_name="Support"
                ),
                preview_image="/static/templates/minimal.jpg"
            ),
            WidgetTemplate(
                template_id="modern",
                name="Modern",
                description="Design moderne avec couleurs vives",
                category="Modern",
                settings=WidgetSettings(
                    theme=ThemeType.LIGHT,
                    primary_color="#007bff",
                    position=PositionType.BOTTOM_RIGHT,
                    welcome_message="👋 Salut ! En quoi puis-je vous aider aujourd'hui ?",
                    company_name="Support IA"
                ),
                preview_image="/static/templates/modern.jpg"
            ),
            WidgetTemplate(
                template_id="dark",
                name="Dark Mode",
                description="Thème sombre élégant",
                category="Dark",
                settings=WidgetSettings(
                    theme=ThemeType.DARK,
                    primary_color="#28a745",
                    position=PositionType.BOTTOM_RIGHT,
                    welcome_message="Bonsoir ! Comment pouvons-nous vous assister ?",
                    company_name="Support Nuit"
                ),
                preview_image="/static/templates/dark.jpg"
            )
        ]
        
        return TemplatesResponse(
            templates=templates,
            categories=["Basic", "Modern", "Dark", "E-commerce", "SaaS"]
        )
        
    except Exception as e:
        logger.error(f"Erreur templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur templates: {str(e)}"
        )

@router.get("/embed-code/{widget_id}", response_class=PlainTextResponse)
async def get_embed_code(widget_id: str):
    """
    📋 Récupérer le code embed d'un widget
    """
    try:
        service = await get_web_widget_service()
        
        # TODO: Récupérer l'API key depuis la BDD
        api_key = f"wgt_{widget_id}_key"
        
        embed_code = service._generate_embed_code(widget_id, api_key)
        return PlainTextResponse(content=embed_code)
        
    except Exception as e:
        logger.error(f"Erreur code embed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur code embed: {str(e)}"
        )

@router.put("/status/{widget_id}")
async def update_widget_status(widget_id: str, request: WidgetStatusUpdate):
    """
    🔄 Mettre à jour le statut d'un widget (actif/inactif/suspendu)
    """
    try:
        # TODO: Mettre à jour le statut en BDD
        
        logger.info(f"Widget {widget_id} statut changé vers {request.status}")
        
        return {
            "success": True,
            "widget_id": widget_id,
            "new_status": request.status,
            "message": f"Statut mis à jour vers '{request.status}'"
        }
        
    except Exception as e:
        logger.error(f"Erreur mise à jour statut: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur statut: {str(e)}"
        )

@router.delete("/delete/{widget_id}")
async def delete_widget(widget_id: str):
    """
    🗑️ Supprimer un widget
    """
    try:
        # TODO: Supprimer de la BDD avec toutes les conversations associées
        
        logger.info(f"Widget {widget_id} supprimé")
        
        return {
            "success": True,
            "widget_id": widget_id,
            "message": "Widget supprimé avec succès"
        }
        
    except Exception as e:
        logger.error(f"Erreur suppression widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur suppression: {str(e)}"
        )

@router.get("/health")
async def widget_health_check():
    """
    ❤️ Vérifier la santé du service de widgets
    """
    try:
        service = await get_web_widget_service()
        
        # Tests de base
        test_results = {
            "service_available": True,
            "ai_providers": {
                "openai": bool(service.openai_api_key),
                "anthropic": bool(service.anthropic_api_key)
            },
            "api_endpoints": [
                "/widget/create",
                "/widget/chat", 
                "/widget/preview/{id}",
                "/widget/analytics/{id}"
            ]
        }
        
        return {
            "service": "web_widget",
            "status": "healthy",
            "tests": test_results,
            "message": "Service de widgets opérationnel"
        }
        
    except Exception as e:
        logger.error(f"Erreur health check widget: {e}")
        return {
            "service": "web_widget",
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/setup-guide")
async def get_setup_guide():
    """
    📖 Guide d'installation et configuration des widgets
    """
    return {
        "title": "Guide d'installation du Widget SocialSync",
        "overview": "Intégrez facilement un chat IA sur votre site web en quelques minutes",
        "steps": {
            "1_create": {
                "title": "Créer votre widget",
                "description": "Utilisez l'endpoint /widget/create pour générer votre widget",
                "example_request": {
                    "website_url": "https://votre-site.com",
                    "widget_settings": {
                        "theme": "light",
                        "primary_color": "#007bff",
                        "welcome_message": "Bonjour ! Comment puis-je vous aider ?",
                        "ai_enabled": True
                    }
                }
            },
            "2_install": {
                "title": "Installer le code",
                "description": "Copiez le code embed fourni et collez-le avant </body>",
                "platforms": [
                    "WordPress - Dans le fichier footer.php",
                    "Shopify - Dans theme.liquid",
                    "React - Composant avec useEffect",
                    "HTML - Directement dans le code"
                ]
            },
            "3_customize": {
                "title": "Personnaliser",
                "description": "Ajustez l'apparence et le comportement via l'API",
                "options": [
                    "Couleurs et thème",
                    "Position du widget", 
                    "Messages d'accueil",
                    "Configuration IA"
                ]
            },
            "4_monitor": {
                "title": "Monitorer",
                "description": "Suivez les performances via /widget/analytics/{id}",
                "metrics": [
                    "Nombre de conversations",
                    "Temps de réponse IA",
                    "Taux de résolution",
                    "Satisfaction utilisateur"
                ]
            }
        },
        "best_practices": [
            "Personnalisez le message d'accueil selon votre secteur",
            "Configurez les domaines autorisés pour la sécurité",
            "Monitorer régulièrement les analytics",
            "Ajustez la température IA selon vos besoins"
        ],
        "troubleshooting": {
            "widget_not_appearing": "Vérifiez que le code est bien avant </body>",
            "ai_not_responding": "Vérifiez votre configuration IA et les clés API",
            "cors_errors": "Ajoutez votre domaine dans allowed_domains"
        }
    }
