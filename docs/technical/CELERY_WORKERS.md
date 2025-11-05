# ⚙️ Celery Workers

Distributed task queue: DM polling, comment moderation, post publishing, analytics.

---

## Architecture

```
Celery Beat (scheduler)
  ↓ Schedule periodic tasks
Redis (broker)
  ↓ Task queue
Celery Workers (executors)
  ↓ Execute tasks
PostgreSQL / Instagram API
```

**Stack:**
- **Redis** - Broker + result backend
- **Celery Beat** - Scheduler (single instance)
- **Celery Workers** - Task executors (scalable)
- **Flower** - Monitoring UI (port 5555)

---

## Why Celery?

| Solution | Distributed | Retry | Monitoring | Complexity |
|----------|-------------|-------|------------|------------|
| Threading | ❌ | ❌ | ❌ | Low |
| AsyncIO | ❌ | ❌ | ❌ | Low |
| RQ | ✅ | ⚠️ | ⚠️ | Medium |
| **Celery** | ✅ | ✅ | ✅ | Medium |
| Airflow | ✅ | ✅ | ✅ | High (overkill) |

**Why Celery:**
- Battle-tested (14+ years)
- Exponential backoff retry
- Horizontal scaling
- Flower UI
- Priority queues

---

## Tasks

**File:** `backend/app/workers/celery_app.py`

### Periodic

```python
CELERYBEAT_SCHEDULE = {
    'poll-instagram-messages': {
        'task': 'app.workers.messages.poll_instagram_messages',
        'schedule': 0.5,  # 0.5s
        'options': {'queue': 'high'}
    },
    'poll-comments': {
        'task': 'app.workers.comments.poll_all_monitored_posts',
        'schedule': 300.0,  # 5 min
        'options': {'queue': 'default'}
    },
    'check-scheduled-posts': {
        'task': 'app.workers.scheduler.check_scheduled_posts',
        'schedule': 60.0,  # 1 min
        'options': {'queue': 'default'}
    },
    'generate-daily-analytics': {
        'task': 'app.workers.analytics.generate_daily_analytics',
        'schedule': crontab(hour=0, minute=0),
        'options': {'queue': 'low'}
    }
}
```

**Intervals:**
- DMs: 0.5s (near real-time)
- Comments: 5-30min (adaptive)
- Posts: 60s (±60s accuracy)
- Analytics: Daily (low priority)

### On-Demand

```python
@celery_app.task(bind=True, max_retries=3)
def process_instagram_message(self, message_id: str):
    pass

@celery_app.task(bind=True, max_retries=3)
def publish_scheduled_post(self, post_id: str):
    pass
```

---

## Configuration

**Worker:** `docker-compose.yml`
```yaml
celery:
  command: celery -A app.workers.celery_app worker --concurrency=4
  deploy:
    replicas: 1
```

**Concurrency:** 4 tasks/worker (each RAG task ~200MB)

**Scaling:**
```bash
docker-compose up -d --scale celery=3  # 3 workers × 4 = 12 concurrent
```

---

## Retry Logic

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(InstagramAPIError,),
    retry_backoff=True,       # Exponential
    retry_backoff_max=600,
    retry_jitter=True         # ±20%
)
```

**Schedule:**
```
Attempt 1: t=0s → Fail
Attempt 2: t=60s ±jitter → Fail
Attempt 3: t=180s ±jitter → Fail
Attempt 4: t=420s ±jitter → Fail
Give up (max_retries)
```

**Why exponential backoff?** Rate limits recover.
**Why jitter?** Prevent thundering herd.

---

## Priority Queues

```python
CELERY_TASK_ROUTES = {
    'app.workers.messages.*': {'queue': 'high'},
    'app.workers.comments.*': {'queue': 'default'},
    'app.workers.analytics.*': {'queue': 'low'}
}
```

**Worker:**
```bash
celery -A app.workers.celery_app worker --queues=high,default,low
```

---

## Monitoring (Flower)

**Docker:**
```yaml
flower:
  command: celery -A app.workers.celery_app flower --port=5555
  ports:
    - "5555:5555"
```

**Access:** http://localhost:5555

**Features:**
- Active tasks
- Task history
- Worker stats
- Task revoke

---

## Key Files

| File | Purpose |
|------|---------|
| `workers/celery_app.py` | Config + schedule |
| `workers/messages.py` | DM polling |
| `workers/comments.py` | Comment polling |
| `workers/scheduler.py` | Post publishing |

---

**Last Updated:** 2025-10-30
