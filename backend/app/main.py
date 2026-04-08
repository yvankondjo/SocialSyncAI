import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

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

from app.core.config import get_settings
from app.services.warmup import run_startup_warmup

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask_url(url: str) -> str:
    if "@" not in url:
        return url
    prefix, suffix = url.split("@", 1)
    if "://" not in prefix:
        return f"***@{suffix}"
    scheme, _ = prefix.split("://", 1)
    return f"{scheme}://***@{suffix}"


def _component_status(name: str, status: str, details: dict | None = None, error: str | None = None) -> dict:
    payload = {"name": name, "status": status}
    if details:
        payload["details"] = details
    if error:
        payload["error"] = error
    return payload


def _overall_status(components: dict[str, dict]) -> str:
    critical_components = ("api", "db")

    if any(components[name]["status"] == "unhealthy" for name in critical_components):
        return "unhealthy"

    if any(component["status"] == "unhealthy" for component in components.values()):
        return "degraded"

    if any(component["status"] == "degraded" for component in components.values()):
        return "degraded"

    return "healthy"


def _db_health_status() -> dict:
    try:
        from app.db.session import supabase

        if supabase is None:
            return _component_status("db", "unhealthy", error="Supabase client is not initialized")

        return _component_status(
            "db",
            "healthy",
            details={
                "provider": "supabase",
                "configured": True,
                "url": settings.SUPABASE_URL,
            },
        )
    except Exception as exc:  # pragma: no cover - depends on runtime configuration
        return _component_status("db", "unhealthy", error=str(exc))


async def _redis_health_status() -> dict:
    try:
        from app.core.redis_client import get_redis_client

        client = await get_redis_client()
        healthy = await asyncio.wait_for(client.health_check(), timeout=3.0)
        details = {"configured_url": settings.REDIS_URL or settings.CELERY_BROKER_URL}

        with suppress(Exception):
            metrics = await client.get_metrics()
            details["metrics"] = metrics

        return _component_status("redis", "healthy" if healthy else "degraded", details=details)
    except Exception as exc:  # pragma: no cover - depends on runtime configuration
        return _component_status("redis", "degraded", error=str(exc))


def _worker_health_status() -> dict:
    try:
        from app.workers.celery_app import celery, broker_url, backend_url

        beat_schedule = getattr(celery.conf, "beat_schedule", {}) or {}
        return _component_status(
            "workers",
            "healthy" if broker_url and backend_url else "degraded",
            details={
                "broker": _mask_url(broker_url),
                "result_backend": _mask_url(backend_url),
                "registered_tasks": len(celery.tasks),
                "beat_schedule_size": len(beat_schedule),
            },
        )
    except Exception as exc:  # pragma: no cover - depends on runtime configuration
        return _component_status("workers", "degraded", error=str(exc))


@app.get("/")
async def root():
    return {
        "message": "SocialSyncAI API is running",
        "service": "socialsyncai-api",
        "version": settings.PROJECT_VERSION,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "socialsyncai-api",
        "version": settings.PROJECT_VERSION,
    }


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
    """Expose resolved external API versions from runtime configuration."""

    graph_version = settings.META_GRAPH_VERSION

    return {
        "whatsapp": {
            "graph_api_version": graph_version,
            "base_url": f"https://graph.facebook.com/{graph_version}",
            "webhook_compatible": True,
            "config_source": "META_GRAPH_VERSION",
        },
        "instagram": {
            "graph_api_version": graph_version,
            "base_url": f"https://graph.instagram.com/{graph_version}",
            "webhook_compatible": True,
            "config_source": "META_GRAPH_VERSION",
        },
        "api_info": {
            "socialsync_version": settings.PROJECT_VERSION,
            "meta_graph_version": graph_version,
            "resolved_at": _utc_timestamp(),
        },
    }


@app.get("/api/health")
async def system_health():
    """Readiness endpoint with real component statuses."""

    components = {
        "api": _component_status(
            "api",
            "healthy",
            details={"service": "socialsyncai-api", "version": settings.PROJECT_VERSION},
        ),
        "db": _db_health_status(),
        "redis": await _redis_health_status(),
        "workers": _worker_health_status(),
    }

    return {
        "status": _overall_status(components),
        "service": "socialsyncai-api",
        "version": settings.PROJECT_VERSION,
        "timestamp": _utc_timestamp(),
        "components": components,
    }


@app.get("/api/metrics")
async def system_metrics():
    """Operational metrics for key runtime services."""

    redis_metrics = {}
    with suppress(Exception):  # pragma: no cover - depends on runtime configuration
        from app.core.redis_client import get_redis_client

        client = await get_redis_client()
        redis_metrics = await client.get_metrics()

    worker_metrics = {}
    with suppress(Exception):  # pragma: no cover - depends on runtime configuration
        from app.workers.celery_app import celery

        beat_schedule = getattr(celery.conf, "beat_schedule", {}) or {}
        worker_metrics = {
            "registered_tasks": len(celery.tasks),
            "beat_schedule_size": len(beat_schedule),
        }

    return {
        "service": "socialsyncai-api",
        "version": settings.PROJECT_VERSION,
        "timestamp": _utc_timestamp(),
        "redis": redis_metrics,
        "workers": worker_metrics,
    }
