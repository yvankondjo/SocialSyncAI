from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
# from app.scheduler import start_scheduler, stop_scheduler
from app.routers import analytics, social_accounts, content, whatsapp, instagram, messaging, web_widget
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Gestion du cycle de vie de l'application"""
#     # Démarrage
#     await start_scheduler()
#     yield
#     # Arrêt
#     await stop_scheduler()

app = FastAPI(
    title="SocialSyncAI API",
    description="API pour la gestion et synchronisation de contenus sur les réseaux sociaux avec IA",
    version="1.0.0",
    # lifespan=lifespan
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

# Servir les fichiers statiques du widget
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.get("/")
async def root():
    return {"message": "SocialSyncAI API is running test"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "socialsyncai-api"} 