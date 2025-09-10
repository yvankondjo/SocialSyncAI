from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
# from app.scheduler import start_scheduler, stop_scheduler
from app.routers import analytics, social_accounts, content, whatsapp, instagram, messaging, web_widget, scheduler
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Démarrage
    from app.services.batch_scanner import batch_scanner
    await batch_scanner.start()
    yield
    # Arrêt
    await batch_scanner.stop()

app = FastAPI(
    title="SocialSyncAI API",
    description="API pour la gestion et synchronisation de contenus sur les réseaux sociaux avec IA",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(analytics.router, prefix="/api")
app.include_router(social_accounts.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(instagram.router, prefix="/api")
app.include_router(messaging.router, prefix="/api")
app.include_router(web_widget.router, prefix="/api")
app.include_router(scheduler.router, prefix="/api")

# Servir les fichiers statiques du widget
# TODO: Décommenter quand on implémentera le widget web intégrable
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "SocialSyncAI API is running test"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "socialsyncai-api"}

@app.get("/api/versions")
async def api_versions():
    """Vérifier les versions des APIs externes utilisées"""
    return {
        "whatsapp": {
            "graph_api_version": "v23.0",
            "base_url": "https://graph.facebook.com/v23.0",
            "webhook_compatible": True,
            "notes": "Cohérent avec les webhooks Meta"
        },
        "instagram": {
            "graph_api_version": "v23.0", 
            "base_url": "https://graph.instagram.com/v23.0",
            "webhook_compatible": True,
            "notes": "Cohérent avec les webhooks Meta"
        },
        "api_info": {
            "socialsync_version": "1.0.0",
            "last_updated": "2024-12-19",
            "compatibility": "Toutes les APIs utilisent la même version v23.0 pour la cohérence"
        }
    } 