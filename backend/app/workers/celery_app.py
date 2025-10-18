import os
from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "socialsyncAI",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery.conf.update(
    task_routes={
        "app.workers.ingest.*": {"queue": "ingest"},
        "app.workers.scheduler.*": {"queue": "scheduler"},
        "app.workers.comments.*": {"queue": "comments"},
    },
    task_time_limit=1800,              # 30 min max/ tâche
    worker_max_tasks_per_child=200,
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    "enqueue-due-posts-every-minute": {
        "task": "app.workers.scheduler.enqueue_due_posts",
        "schedule": 60.0,  # Every 60 seconds (1 minute)
        "options": {
            "expires": 55,  # Task expires after 55s to avoid overlap
        }
    },
    "poll-post-comments-every-5-minutes": {
        "task": "app.workers.comments.poll_post_comments",
        "schedule": 300.0,  # Every 5 minutes (300 seconds)
        "options": {
            "expires": 290,  # Task expires after 290s to avoid overlap
        }
    },
}


from app.workers import ingest
from app.workers import scheduler
from app.workers import comments
