# 📅 Scheduled Posts

Automated Instagram post publishing with recurring posts (RRULE) and retry logic.

---

## Flow

```
User creates scheduled post in calendar
  ↓
Stored in DB: scheduled_posts (status=queued)
  ↓
Celery Beat checks every 1 min: check_scheduled_posts()
  ↓
For posts where publish_at <= NOW():
  1. Status: queued → publishing
  2. Upload media to Instagram
  3. Publish post
  4. Status: published (or failed + retry)
  ↓
If recurring (RRULE): generate next occurrence
```

---

## Celery Beat vs Cron

**Why Celery Beat?**
- Distributed (works in Docker/K8s)
- Dynamic scheduling (no restart needed)
- Built-in retry logic
- Monitored via Flower UI

**Why not Cron?**
- Container-dependent
- No distributed locking
- No retry logic

---

## Retry Logic

**Config:** `backend/app/workers/scheduler.py`
```python
@celery_app.task(
    max_retries=3,
    default_retry_delay=60,  # 1 min
    retry_backoff=True,      # Exponential
    retry_jitter=True        # ±20% random
)
```

**Schedule:**
```
Attempt 1: t=0s
  ↓ Fails
Attempt 2: t=60s + jitter
  ↓ Fails
Attempt 3: t=180s + jitter
  ↓ Fails
Attempt 4: t=420s + jitter
  ↓ Fails
Give up (max_retries=3)
```

**Why exponential backoff?** Rate limits recover after waiting.

---

## Recurring Posts (RRULE)

**RFC 5545** format:
```python
# Daily at 10 AM
"FREQ=DAILY;BYHOUR=10;BYMINUTE=0"

# Weekly on Monday
"FREQ=WEEKLY;BYDAY=MO"

# Monthly on 1st
"FREQ=MONTHLY;BYMONTHDAY=1"
```

**Table:** `scheduled_posts`
```sql
recurrence_rule text  -- RRULE string
parent_post_id uuid   -- Link to original
```

**Logic:**
```python
if post.recurrence_rule:
    rrule = dateutil.rrule.rrulestr(post.recurrence_rule, dtstart=post.publish_at)
    next_occurrence = rrule.after(datetime.now())
    # Create new scheduled_posts entry
```

---

## State Machine

**Table:** `scheduled_posts`
```sql
status text CHECK (status IN ('queued', 'publishing', 'published', 'failed'))
```

```
queued
  ↓
publishing (API call in progress)
  ↓
published (success) OR failed (max retries)
```

**Track:** `post_runs` table stores each publish attempt.

---

## Components

**Worker:** `backend/app/workers/scheduler.py`
```python
@celery_app.task
def check_scheduled_posts():
    # Celery Beat: every 1 min
    # Find posts where publish_at <= NOW()
    # Enqueue publish_scheduled_post()

@celery_app.task(max_retries=3)
def publish_scheduled_post(post_id: str):
    # 1. Upload media to Instagram
    # 2. Publish post
    # 3. Update status
    # 4. If recurring: generate next
```

---

## Configuration

**Celery Beat Schedule:**
```python
# backend/app/workers/celery_app.py
CELERYBEAT_SCHEDULE = {
    'check-scheduled-posts': {
        'task': 'app.workers.scheduler.check_scheduled_posts',
        'schedule': 60.0,  # Every 1 minute
        'options': {'queue': 'default'}
    }
}
```

**Tables:**
```sql
CREATE TABLE scheduled_posts (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    social_account_id uuid,
    publish_at timestamptz NOT NULL,
    status text DEFAULT 'queued',
    recurrence_rule text,  -- RRULE
    retry_count int DEFAULT 0,
    media_url text,
    caption text
);

CREATE TABLE post_runs (
    id uuid PRIMARY KEY,
    scheduled_post_id uuid,
    attempt_number int,
    status text,
    error_message text,
    created_at timestamptz DEFAULT now()
);
```

---

## Key Files

| File | Purpose |
|------|---------|
| `workers/scheduler.py` | Check + publish posts |
| `routers/scheduled_posts.py` | CRUD API |
| `services/instagram_service.py` | Instagram API |

---

**Last Updated:** 2025-10-30
