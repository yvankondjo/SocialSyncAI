from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    scheduled_posts,
    comments,
    ai_studio,
    instagram_profiles,
    monitoring,
    analytics,
)
import logging
import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    logging.info("🚀 FastAPI startup...")

    # Batch scanning is now handled by Celery Beat worker
    logging.info("✅ DM/Chat batch scanning handled by Celery Beat (every 0.5s)")
    logging.info(
        "📝 Make sure Celery Beat is running: celery -A app.workers.celery_app beat"
    )

    # Async Supabase client will be initialized lazily on first use
    logging.info("✅ Async Supabase client configured (lazy initialization)")

    yield

    # Shutdown
    logging.info("🛑 FastAPI shutdown initiated...")

    # Close async Supabase client
    from app.db.session import close_async_db
    await close_async_db()
    logging.info("✅ Async Supabase client closed")

    logging.info("🛑 FastAPI shutdown complete")


app = FastAPI(
    title="SocialSyncAI API",
    description="API pour la gestion et synchronisation de contenus sur les réseaux sociaux avec IA",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


from app.routers import support

app.include_router(support.router, prefix="/api")

app.include_router(scheduled_posts.router, prefix="/api")
app.include_router(comments.router, prefix="/api")


app.include_router(ai_studio.router, prefix="/api")

app.include_router(instagram_profiles.router, prefix="/api")


app.include_router(monitoring.router, prefix="/api")

app.include_router(analytics.router, prefix="/api")


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
    from app.services.batch_scanner import batch_scanner

    return {
        "system": "healthy",
        "scanner": batch_scanner.get_health_status(),
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/metrics")
async def system_metrics():
    """Métriques détaillées du système"""
    from app.services.batch_scanner import batch_scanner

    metrics = batch_scanner.get_metrics()
    health = batch_scanner.get_health_status()

    return {
        "scanner_metrics": metrics,
        "health_status": health,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }
