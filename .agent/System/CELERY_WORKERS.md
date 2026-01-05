# Celery Workers Configuration - SocialSync AI

## Vue d'ensemble

SocialSync AI utilise **Celery** pour le traitement asynchrone et les tâches planifiées.

**Broker**: Redis (`redis://redis:6379/0`)  
**Backend**: Redis (`redis://redis:6379/0`)  
**Configuration**: `/workspace/backend/app/workers/celery_app.py`

---

## Queues

### 1. `ingest` Queue
Traitement des documents de la base de connaissance (RAG).

**Workers**: `app.workers.ingest`

**Tasks**:
- `process_document_task` - Ingestion et indexation de documents
  - Découpe en chunks
  - Génération d'embeddings (OpenAI text-embedding-3-small)
  - Stockage dans `knowledge_chunks` avec vecteurs
  - Support multi-langue (fr, en, es, etc.)

**Configuration**:
- `task_time_limit`: 1800s (30 min)
- `worker_max_tasks_per_child`: 200

**Démarrage**:
```bash
celery -A app.workers.celery_app worker --loglevel=info -Q ingest
```

---

### 2. `scheduler` Queue ✅ (2025-10-18)
Publication automatique de posts programmés.

**Workers**: `app.workers.scheduler`

**Tasks**:

#### `enqueue_due_posts` (Periodic Task)
- **Schedule**: Toutes les 60 secondes (Celery Beat)
- **Description**: Trouve les posts prêts à publier et les enqueue
- **Logic**:
  1. Query: `status='queued' AND publish_at <= NOW()`
  2. Pour chaque post → Update `status='publishing'`
  3. Enqueue `publish_post.delay(post_id)`
- **Returns**: `{enqueued: int, total_due: int, timestamp: str}`

#### `publish_post(post_id)` (Async Task)
- **Max Retries**: 3 (avec exponential backoff)
- **Description**: Publie un post sur la plateforme sociale
- **Logic**:
  1. Fetch post + channel data
  2. Create `post_run` record (started_at)
  3. Call platform service:
     - WhatsApp: `publish_to_whatsapp()`
     - Instagram: `publish_to_instagram()`
  4. Si succès:
     - Update post: `status='published'`, `platform_post_id`
     - Update run: `status='success'`, `finished_at`
  5. Si échec:
     - Retry logic (max 3 attempts)
     - Exponential backoff: 5min → 10min → 20min
     - After max retries: `status='failed'`

**Configuration**:
- `task_time_limit`: 1800s (30 min)
- `worker_max_tasks_per_child`: 200

**Démarrage**:
```bash
celery -A app.workers.celery_app worker --loglevel=info -Q scheduler
```

---

### 3. `comments` Queue ✅ (NEW - 2025-10-18)
Polling adaptatif des commentaires publics avec modération IA.

**Workers**: `app.workers.comments`

**Tasks**:

#### `poll_post_comments` (Periodic Task)
- **Schedule**: Toutes les 300 secondes (5 min) via Celery Beat
- **Description**: Poll les posts publiés pour nouveaux commentaires
- **Logic**:
  1. Query posts: `status='published' AND stop_at > NOW()`
  2. Pour chaque post:
     - Skip si `next_check_at > NOW()`
     - Calculate interval adaptatif (5/15/30 min selon âge)
     - Fetch via PlatformConnector (Instagram)
     - Save comments en DB
     - Enqueue `process_comment.delay(comment_id)`
     - Update checkpoint + next_check_at
- **Returns**: `{posts_checked: int, comments_found: int, errors: int}`
- **Polling Adaptatif**:
  - J+0 à J+2: 5 min (engagement élevé)
  - J+2 à J+5: 15 min (engagement moyen)
  - J+5 à J+7: 30 min (engagement faible)
  - J+7+: Stop (stop_at dépassé)

#### `process_comment(comment_id)` (Async Task)
- **Max Retries**: 3 (backoff 5 min)
- **Description**: Traite un commentaire avec guardrails IA
- **Logic**:
  1. Fetch comment + post + user
  2. AIDecisionService.check_message(text, **context_type="comment"**)
  3. Log decision dans ai_decisions
  4. Switch on decision:
     - **ESCALATE**: Generate + send email to user
     - **RESPOND**: RAG agent → reply_to_comment()
     - **IGNORE**: No action
  5. Update comment: triage + ai_decision_id
- **Context Type**: Utilise `context_type="comment"` pour contrôle granulaire
  - Permet AI ON pour chats mais OFF pour comments (indépendant)

**Configuration**:
- `task_time_limit`: 1800s (30 min)
- `worker_max_tasks_per_child`: 200

**Démarrage**:
```bash
celery -A app.workers.celery_app worker --loglevel=info -Q comments
```

---

## Celery Beat (Periodic Tasks)

**Schedule Configuration**: `celery.conf.beat_schedule` in `celery_app.py`

### Active Schedules

#### `enqueue-due-posts-every-minute`
- **Task**: `app.workers.scheduler.enqueue_due_posts`
- **Schedule**: Every 60 seconds
- **Expires**: 55 seconds (avoid overlap)
- **Purpose**: Automatic post publishing

#### `poll-post-comments-every-5-minutes` ✅ (NEW - 2025-10-18)
- **Task**: `app.workers.comments.poll_post_comments`
- **Schedule**: Every 300 seconds (5 minutes)
- **Expires**: 290 seconds (avoid overlap)
- **Purpose**: Poll published posts for new comments

**Démarrage**:
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

---

## Task Routing

Routes définies dans `celery.conf.update()`:

```python
task_routes = {
    "app.workers.ingest.*": {"queue": "ingest"},
    "app.workers.scheduler.*": {"queue": "scheduler"},
    "app.workers.comments.*": {"queue": "comments"},  # NEW - 2025-10-18
}
```

---

## Configuration Complète

### celery_app.py

```python
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
    },
    task_time_limit=1800,
    worker_max_tasks_per_child=200,
    timezone="UTC",
    enable_utc=True,
)

celery.conf.beat_schedule = {
    "enqueue-due-posts-every-minute": {
        "task": "app.workers.scheduler.enqueue_due_posts",
        "schedule": 60.0,
        "options": {"expires": 55}
    },
}

from app.workers import ingest
from app.workers import scheduler
```

---

## Déploiement

### Option 1: Workers Séparés (Recommandé Production)

**Worker Ingest**:
```bash
celery -A app.workers.celery_app worker --loglevel=info -Q ingest --concurrency=4
```

**Worker Scheduler**:
```bash
celery -A app.workers.celery_app worker --loglevel=info -Q scheduler --concurrency=2
```

**Celery Beat**:
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

### Option 2: Worker Combiné (Dev/Test)

```bash
celery -A app.workers.celery_app worker --beat --loglevel=info -Q ingest,scheduler
```

**Note**: En production, **toujours séparer Beat** des workers pour éviter des schedules multiples.

---

## Monitoring

### Commandes Utiles

**Inspecter les workers actifs**:
```bash
celery -A app.workers.celery_app inspect active
```

**Voir les tasks enregistrées**:
```bash
celery -A app.workers.celery_app inspect registered
```

**Voir le schedule Beat**:
```bash
celery -A app.workers.celery_app inspect scheduled
```

**Statistiques**:
```bash
celery -A app.workers.celery_app inspect stats
```

**Purger une queue**:
```bash
celery -A app.workers.celery_app purge -Q scheduler
```

### Logs

**Format de log structuré**:
- `[ENQUEUE]` - Messages du task `enqueue_due_posts`
- `[PUBLISH]` - Messages du task `publish_post`

**Exemples**:
```
[ENQUEUE] Checking for due posts at 2025-10-18T14:30:00Z
[ENQUEUE] Found 3 due posts
[ENQUEUE] Enqueued post 550e8400-e29b-41d4-a716-446655440001 for publishing
[PUBLISH] Starting publish task for post 550e8400-e29b-41d4-a716-446655440001
[PUBLISH] Successfully published post 550e8400-e29b-41d4-a716-446655440001 to whatsapp
```

---

## Troubleshooting

### Worker ne traite pas les tasks

**Symptômes**:
- Tasks enqueued mais pas exécutées
- Queue depth augmente

**Solutions**:
1. Vérifier que le worker écoute la bonne queue:
   ```bash
   celery -A app.workers.celery_app inspect active_queues
   ```
2. Vérifier les erreurs de task:
   ```bash
   docker logs backend -f | grep ERROR
   ```
3. Redémarrer le worker:
   ```bash
   docker compose restart backend
   ```

### Celery Beat ne schedule pas

**Symptômes**:
- `enqueue_due_posts` ne s'exécute pas toutes les minutes
- Aucun log `[ENQUEUE]`

**Solutions**:
1. Vérifier que Beat est running:
   ```bash
   ps aux | grep celery | grep beat
   ```
2. Vérifier le schedule:
   ```bash
   celery -A app.workers.celery_app inspect scheduled
   ```
3. Vérifier les logs Beat:
   ```bash
   docker logs backend -f | grep beat
   ```

### Tasks bloquées

**Symptômes**:
- Task reste en `started` indéfiniment
- Post reste en `status='publishing'`

**Solutions**:
1. Vérifier le timeout de task (1800s):
   ```python
   task_time_limit=1800
   ```
2. Révoquer la task bloquée:
   ```bash
   celery -A app.workers.celery_app revoke <task_id> --terminate
   ```
3. Reset le status du post manuellement dans Supabase

### Redis connection errors

**Symptômes**:
- `ConnectionError: Error connecting to Redis`
- Tasks ne s'enqueued pas

**Solutions**:
1. Vérifier que Redis est running:
   ```bash
   docker ps | grep redis
   ```
2. Vérifier la connexion:
   ```bash
   redis-cli -h redis -p 6379 ping
   # Should return: PONG
   ```
3. Vérifier les variables d'environnement:
   ```bash
   echo $CELERY_BROKER_URL
   echo $CELERY_RESULT_BACKEND
   ```

---

## Métriques de Performance

### Métriques à Suivre

1. **Task Success Rate**:
   ```python
   success_rate = successful_tasks / total_tasks * 100
   ```

2. **Average Task Duration**:
   - `process_document_task`: ~30-60s par document
   - `publish_post`: ~2-5s par post

3. **Queue Depth**:
   - Idéal: < 100 tasks en attente
   - Alerte: > 500 tasks (augmenter concurrency)

4. **Worker Utilization**:
   - Idéal: 70-80%
   - Sur-utilisé: > 95% (ajouter workers)

### Redis Memory

**Monitor**:
```bash
redis-cli info memory
```

**Eviction Policy**: `maxmemory-policy allkeys-lru`

---

## Best Practices

### ✅ DO

1. **Idempotence**: Tasks doivent être rejouables sans effet de bord
2. **Timeouts**: Toujours définir `task_time_limit`
3. **Retries**: Utiliser `max_retries` et `retry_backoff`
4. **Logging**: Logger début, succès, et erreurs
5. **Monitoring**: Tracker métriques (Sentry, Datadog, etc.)

### ❌ DON'T

1. **Ne pas** lancer Beat multiple fois (duplicate schedules)
2. **Ne pas** bloquer le worker avec I/O synchrone
3. **Ne pas** passer de gros objets en arguments (use IDs)
4. **Ne pas** ignorer les erreurs de retry
5. **Ne pas** oublier de purger les résultats expirés

---

## Scalabilité

### Vertical Scaling

Augmenter la concurrency:
```bash
celery -A app.workers.celery_app worker -Q scheduler --concurrency=10
```

### Horizontal Scaling

Lancer plusieurs workers:
```bash
# Worker 1
celery -A app.workers.celery_app worker -Q scheduler --hostname=scheduler1@%h

# Worker 2
celery -A app.workers.celery_app worker -Q scheduler --hostname=scheduler2@%h
```

**Note**: Un seul Beat process doit tourner (pas de duplication).

---

## Ressources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices)
- [Redis Configuration](https://redis.io/docs/manual/config/)

---

*Documentation mise à jour: 2025-10-18*
