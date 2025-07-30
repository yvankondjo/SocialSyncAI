from fastapi import FastAPI
from contextlib import asynccontextmanager
# from app.scheduler import start_scheduler, stop_scheduler
from app.routers import analytics, social_accounts, content
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

# Inclusion des routes
app.include_router(analytics.router, prefix="/api")
app.include_router(social_accounts.router, prefix="/api")
app.include_router(content.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "SocialSyncAI API is running test"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "socialsyncai-api"} 