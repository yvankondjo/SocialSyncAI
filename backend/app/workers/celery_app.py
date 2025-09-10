import os
from celery import Celery

celery = Celery(
    "socialsyncAI",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery.conf.update(
    task_routes={"app.workers.ingest.*": {"queue": "ingest"}},
    task_time_limit=1800,              # 30 min max/ tâche
    worker_max_tasks_per_child=200,
)


from app.workers import ingest  
