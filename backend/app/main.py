from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from app.routers import (
    social_accounts,
    whatsapp,
    instagram,
    messenger,
    conversations,
    automation,
    process,
    knowledge_documents,
    faq_qa,
    ai_settings,
    media,
    subscriptions,
    stripe,
    comments,
    instagram_profiles,
    monitoring,
    analytics,
)
import logging
from datetime import datetime
import os

from app.core.config import get_settings
from app.services.warmup import run_startup_warmup

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    logging.info("✅ Application starting")
    await run_startup_warmup()

    yield

    logging.info("🛑 FastAPI shutdown complete")


app = FastAPI(
    title="SocialSyncAI API",
    description="API pour la gestion et synchronisation de contenus sur les réseaux sociaux avec IA",
    version="1.0.0",
    lifespan=lifespan,
)

try:
    settings = get_settings()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to load settings: {e}")
    logger.error("Application cannot start without valid configuration")
    raise
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if settings.FRONTEND_URL:
    cors_origins.append(settings.FRONTEND_URL)
    if settings.FRONTEND_URL.startswith("https://"):
        cors_origins.append(settings.FRONTEND_URL.replace("https://", "http://"))
    elif settings.FRONTEND_URL.startswith("http://"):
        cors_origins.append(settings.FRONTEND_URL.replace("http://", "https://"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Inclusion des routes
app.include_router(social_accounts.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(instagram.router, prefix="/api")
app.include_router(messenger.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(automation.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(knowledge_documents.router, prefix="/api")
app.include_router(faq_qa.router, prefix="/api")
app.include_router(ai_settings.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(subscriptions.router, prefix="/api")
app.include_router(stripe.router, prefix="/api")

# Nouvelles routes PRD2
from app.routers import support

app.include_router(support.router, prefix="/api")

# Comments polling feature
app.include_router(comments.router, prefix="/api")

# Instagram profile refresh (avatar URLs)
app.include_router(instagram_profiles.router, prefix="/api")

# Comment monitoring system (import posts, toggle monitoring, auto-rules)
app.include_router(monitoring.router, prefix="/api")

# Analytics router (real data)
app.include_router(analytics.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "SocialSyncAI API is running test"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "socialsyncai-api"}


@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        },
    )


@app.get("/api/versions")
async def api_versions():
    """Vérifier les versions des APIs externes utilisées"""
    return {
        "whatsapp": {
            "graph_api_version": "v23.0",
            "base_url": "https://graph.facebook.com/v23.0",
            "webhook_compatible": True,
            "notes": "Cohérent avec les webhooks Meta",
        },
        "instagram": {
            "graph_api_version": "v23.0",
            "base_url": "https://graph.instagram.com/v23.0",
            "webhook_compatible": True,
            "notes": "Cohérent avec les webhooks Meta",
        },
        "api_info": {
            "socialsync_version": "1.0.0",
            "last_updated": "2024-12-19",
            "compatibility": "Toutes les APIs utilisent la même version v23.0 pour la cohérence",
        },
    }


@app.get("/api/health")
async def system_health():
    """Statut de santé complet du système"""
    scanner_status = {
        "status": "disabled",
        "mode": "in-memory",
        "notes": "Batching handled inline via message_timer_batcher",
    }

    return {
        "system": "healthy",
        "scanner": scanner_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/metrics")
async def system_metrics():
    """Métriques détaillées du système"""
    metrics = {
        "scanner_metrics": {},
        "notes": "Batching handled inline via message_timer_batcher",
    }
    health = {
        "status": "disabled",
        "mode": "in-memory",
    }

    return {
        "scanner_metrics": metrics,
        "health_status": health,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }
