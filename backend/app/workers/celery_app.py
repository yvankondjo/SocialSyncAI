import logging
import os
import ssl

from celery import Celery
from celery.schedules import crontab

from app.core.config import resolve_redis_url, canonicalize_redis_url

logger = logging.getLogger(__name__)

raw_broker_url = os.getenv("CELERY_BROKER_URL", "")
raw_backend_url = os.getenv("CELERY_RESULT_BACKEND", "")

# Resolve and canonicalize Redis URLs while preserving the rediss:// scheme
broker_url = resolve_redis_url(raw_broker_url, source="CELERY_BROKER_URL")
backend_url = resolve_redis_url(raw_backend_url or broker_url, source="CELERY_RESULT_BACKEND")

masked_broker_url = broker_url.split('@')[0] + '@***' if '@' in broker_url else broker_url
masked_backend_url = backend_url.split('@')[0] + '@***' if '@' in backend_url else backend_url
logger.info(f"[CELERY_REDIS] Canonical broker URL: {masked_broker_url}")
logger.info(f"[CELERY_REDIS] Canonical backend URL: {masked_backend_url}")

broker_transport_options = {
    'visibility_timeout': 3600,
    'retry_policy': {
        'timeout': 5.0
    },
    'max_connections': 10,
    'socket_keepalive': True,
    'health_check_interval': 30,
}

result_backend_transport_options = {
    'visibility_timeout': 3600,
    'retry_policy': {
        'timeout': 5.0
    },
    'max_connections': 5,
}

if broker_url.startswith('rediss://'):
    broker_transport_options['ssl_cert_reqs'] = ssl.CERT_NONE
    broker_transport_options['ssl_ca_certs'] = None
    broker_transport_options['ssl_certfile'] = None
    broker_transport_options['ssl_keyfile'] = None

if backend_url.startswith('rediss://'):
    result_backend_transport_options['ssl_cert_reqs'] = ssl.CERT_NONE
    result_backend_transport_options['ssl_ca_certs'] = None
    result_backend_transport_options['ssl_certfile'] = None
    result_backend_transport_options['ssl_keyfile'] = None

celery = Celery(
    "socialsyncAI",
    broker=broker_url,
    backend=backend_url,
)

# Explicit SSL configuration for Celery (compatible with redis-py 5.x)
# IMPORTANT: Only configure SSL if the URL uses rediss://
# If redis://, explicitly disable SSL to avoid "SSL parameters ... redis://" errors
if broker_url.startswith('rediss://'):
    celery.conf.broker_use_ssl = {'ssl_cert_reqs': ssl.CERT_NONE}
else:
    # If using a non-SSL URL, force-disable any SSL options
    # inherited from the environment to avoid conflicts.
    celery.conf.broker_use_ssl = None
if backend_url.startswith('rediss://'):
    celery.conf.redis_backend_use_ssl = {'ssl_cert_reqs': ssl.CERT_NONE}
else:
    # Prevent Celery from passing SSL options when the URL is redis://,
    # which would crash workers on startup.
    celery.conf.redis_backend_use_ssl = None

celery.conf.update(
    task_routes={
        "app.workers.ingest.process_document": {
            "queue": "ingest"
        },
        "app.workers.comments.*": {"queue": "comments"},
        "app.workers.topics.*": {"queue": "topics"},
    },
    task_time_limit=1800,
    worker_max_tasks_per_child=200,
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    result_backend_always_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=10,
    broker_pool_limit=1,
    broker_transport_options=broker_transport_options,
    result_backend_transport_options=result_backend_transport_options,
    task_ignore_result=True,
)

# Celery Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    "poll-post-comments-every-15-minutes": {
        "task": "app.workers.comments.poll_post_comments",
        "schedule": 900.0,  # Every 15 minutes (900 seconds)
        "options": {
            "expires": 890,  # Task expires after 890s to avoid overlap
        },
    },
    "topic-modeling-daily-fit-merge": {
        "task": "app.workers.topics.run_daily_fit_and_merge",
        "schedule": crontab(hour=0, minute=25),  # Every day at 00:25 AM UTC
        "options": {
            "expires": 7200,  # 2 hours timeout
        },
    },
}


from app.workers import ingest
from app.workers import comments
from app.workers import topics
