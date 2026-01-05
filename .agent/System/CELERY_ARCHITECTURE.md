# Celery Architecture - SocialSync AI

**Date:** 2025-10-20
**Version:** 2.0 (Post-Migration)
**Status:** ✅ Production

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture Complète](#architecture-complète)
3. [Composants](#composants)
4. [Queues & Workers](#queues--workers)
5. [Tâches Périodiques (Beat)](#tâches-périodiques-beat)
6. [Flux de Données](#flux-de-données)
7. [Configuration](#configuration)
8. [Monitoring](#monitoring)

---

## Vue d'Ensemble

### Problème Résolu

**Avant Celery:**
- Tâches longues bloquent FastAPI (timeout webhooks)
- Si FastAPI crash → tâches perdues
- Pas de retry automatique
- Impossible de scaler

**Avec Celery:**
- ✅ FastAPI répond < 200ms (envoie tâche à Redis)
- ✅ Workers exécutent en arrière-plan
- ✅ Retry automatique configurable
- ✅ Scalabilité horizontale (multiple workers)
- ✅ Tâches périodiques (Celery Beat)

### Architecture 3-Tiers

```
┌─────────────────────────────────────────────────────────┐
│                  CELERY ARCHITECTURE                     │
└─────────────────────────────────────────────────────────┘

📱 PRODUCTEURS (Envoient des tâches)
├─ FastAPI (webhooks, API calls)
└─ Celery Beat (tâches périodiques)

📬 BROKER (File d'attente)
└─ Redis (queues: ingest, scheduler, comments)

👷 CONSOMMATEURS (Exécutent les tâches)
├─ Worker Ingest (DMs/chats)
├─ Worker Scheduler (posts planifiés)
└─ Worker Comments (commentaires)

⏰ SCHEDULER (Horloge distribuée)
└─ Celery Beat (envoie tâches périodiques)

📊 MONITORING
└─ Flower (dashboard web)
```

---

## Architecture Complète

```
┌──────────────────────────────────────────────────────────────┐
│                      FASTAPI (API LAYER)                      │
│  Webhooks, REST API, OAuth                                    │
└────────────┬────────────────────────────────────┬────────────┘
             │ Envoie tâches                      │ Envoie tâches
             │                                    │
             ▼                                    ▼
┌──────────────────┐                  ┌──────────────────┐
│  CELERY BEAT     │                  │      REDIS       │
│  (Scheduler)     │─────────────────▶│    (Broker)      │
│                  │  Envoie tâches   │                  │
│  Schedules:      │  périodiques     │  Queues:         │
│  - 0.5s: scan    │                  │  - ingest        │
│  - 1min: posts   │                  │  - scheduler     │
│  - 5min: comments│                  │  - comments      │
└──────────────────┘                  └─────────┬────────┘
                                                 │
                              ┌──────────────────┼──────────────────┐
                              │                  │                  │
                              ▼                  ▼                  ▼
                    ┌─────────────────┐ ┌────────────────┐ ┌────────────────┐
                    │ Worker Ingest   │ │Worker Scheduler│ │Worker Comments │
                    │ Queue: ingest   │ │Queue: scheduler│ │Queue: comments │
                    │                 │ │                │ │                │
                    │ Traite:         │ │ Traite:        │ │ Traite:        │
                    │ - DMs WhatsApp  │ │ - Posts planif.│ │ - Polling      │
                    │ - DMs Instagram │ │ - Publishing   │ │ - Processing   │
                    │ - Documents     │ │ - Retry failed │ │ - AI responses │
                    └─────────────────┘ └────────────────┘ └────────────────┘
                              │                  │                  │
                              └──────────────────┼──────────────────┘
                                                 ▼
                                      ┌──────────────────┐
                                      │   SUPABASE PG    │
                                      │  (Persistence)   │
                                      └──────────────────┘
```

---

## Composants

### 1. Redis (Broker & Backend)

**Rôle:** Messagerie ultra-rapide

**Utilisation:**
- **Broker:** File d'attente des tâches
- **Result Backend:** Stockage des résultats
- **Message Batching:** Batches DMs/chats (2s window)

**Configuration:**
```python
# backend/app/workers/celery_app.py
celery = Celery(
    "socialsyncAI",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)
```

**Clés Redis:**
```redis
# Queues Celery
celery:ingest    → [Task1, Task2, Task3]
celery:scheduler → [Task4, Task5]
celery:comments  → [Task6]

# Résultats
celery-task-result:abc-123 → {"status": "SUCCESS", "result": {...}}

# Batching DMs (notre système)
conv:whatsapp:+33612345678:+33698765432:msgs → [Msg1, Msg2]
conv:deadlines → {conversation_id: timestamp}
```

---

### 2. Celery Worker

**Rôle:** Exécute les tâches en arrière-plan

**Process Python qui:**
1. Se connecte à Redis
2. Écoute une ou plusieurs queues
3. Prend les tâches dès qu'elles arrivent
4. Exécute le code Python
5. Stocke le résultat dans Redis

**Commande:**
```bash
celery -A app.workers.celery_app worker \
  -Q ingest \              # Queue à écouter
  -n ingest@%h \           # Nom du worker
  --autoscale=10,3 \       # Min 3, max 10 process
  -l info                  # Log level
```

**Scalabilité:**
```bash
# Multiple workers pour la même queue
celery -A app.workers.celery_app worker -Q ingest -n worker1@%h
celery -A app.workers.celery_app worker -Q ingest -n worker2@%h
celery -A app.workers.celery_app worker -Q ingest -n worker3@%h

# Redis distribue automatiquement les tâches
Queue: [Task1, Task2, Task3, Task4]
        ↓      ↓      ↓      ↓
     Worker1 Worker2 Worker3 Worker1
```

---

### 3. Celery Beat

**Rôle:** Horloge distribuée (Cron job)

**Différence Worker vs Beat:**
| Celery Worker | Celery Beat |
|---------------|-------------|
| **Exécute** les tâches | **Planifie** les tâches |
| Écoute Redis | Envoie vers Redis |
| Peut y en avoir plusieurs | **UN SEUL** (master) |
| Obligatoire | Optionnel* |

*Optionnel sauf pour tâches périodiques

**Commande:**
```bash
celery -A app.workers.celery_app beat -l info
```

**⚠️ IMPORTANT: Un seul Beat par système !**

Plusieurs Beat = Tâches dupliquées (danger)

---

### 4. Flower (Monitoring)

**Rôle:** Dashboard web pour Celery

**Features:**
- 📊 Workers actifs/inactifs
- 📈 Graphiques de performance
- 📋 Liste des tâches (en cours, succès, échecs)
- ⏱️ Temps d'exécution moyen
- 🔄 Retry logs
- 📊 Task routing

**Accès:**
```bash
celery -A app.workers.celery_app flower --port=5555
# http://localhost:5555
```

---

## Queues & Workers

### Queue Ingest (DMs/Chats)

**Responsabilité:** Messages directs et documents

**Tâches:**
```python
# backend/app/workers/ingest.py

@celery.task(name="app.workers.ingest.scan_redis_batches")
def scan_redis_batches_task(self):
    """
    Scan Redis pour batches de messages dus (toutes les 0.5s)
    Appelé par Celery Beat
    """
    batches = message_batcher.get_due_conversations()
    for batch in batches:
        process_batch(batch)

@celery.task(name="app.workers.ingest.process_document")
def process_document_task(self, document_id: str):
    """
    Parse et indexe un document dans la knowledge base
    Appelé manuellement (FastAPI)
    """
    doc = download_document(document_id)
    chunks = split_text(doc)
    embed_and_store(chunks)
```

**Worker:**
```bash
celery -A app.workers.celery_app worker -Q ingest -n ingest@%h
```

---

### Queue Scheduler (Posts Planifiés)

**Responsabilité:** Publication de posts planifiés

**Tâches:**
```python
# backend/app/workers/scheduler.py

@celery.task(name="app.workers.scheduler.enqueue_due_posts")
def enqueue_due_posts():
    """
    Trouve les posts dont scheduled_at est passé (toutes les 1 min)
    Appelé par Celery Beat
    """
    due_posts = get_due_posts()
    for post in due_posts:
        publish_post.delay(post.id)

@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min
)
def publish_post(self, post_id: str):
    """
    Publie un post sur la plateforme (Instagram, Facebook, etc.)
    Appelé par enqueue_due_posts
    """
    try:
        post = get_post(post_id)
        platform_api.publish(post)
        update_status(post_id, "published")
    except Exception as e:
        # Retry automatique
        raise self.retry(exc=e)
```

**Worker:**
```bash
celery -A app.workers.celery_app worker -Q scheduler -n scheduler@%h
```

---

### Queue Comments (Commentaires)

**Responsabilité:** Polling et traitement commentaires

**Tâches:**
```python
# backend/app/workers/comments.py

@celery.task(name="app.workers.comments.poll_post_comments")
def poll_post_comments():
    """
    Poll les commentaires de tous les posts monitorés (toutes les 5 min)
    Appelé par Celery Beat
    """
    monitored_posts = get_monitored_posts()
    for post in monitored_posts:
        fetch_new_comments.delay(post.id)

@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def fetch_new_comments(self, post_id: str):
    """
    Fetch nouveaux commentaires d'un post
    Déclenche process_comment pour chaque nouveau commentaire
    """
    try:
        comments = platform_api.get_comments(post_id)
        for comment in comments:
            process_comment.delay(comment.id)
    except Exception as e:
        raise self.retry(exc=e)

@celery.task
def process_comment(comment_id: str):
    """
    Traite un commentaire (détection, AI, réponse)
    """
    comment = get_comment(comment_id)

    # Détection conversation (ignore @mentions, user-to-user)
    if is_conversation(comment):
        return

    # Génère réponse AI (avec Vision AI)
    response = generate_ai_response(comment)

    # Envoie réponse
    platform_api.reply(comment_id, response)
```

**Worker:**
```bash
celery -A app.workers.celery_app worker -Q comments -n comments@%h
```

---

## Tâches Périodiques (Beat)

### Configuration Schedule

**Fichier:** `backend/app/workers/celery_app.py`

```python
celery.conf.beat_schedule = {
    # DMs/Chats - Scan toutes les 0.5s
    "scan-redis-batches-every-500ms": {
        "task": "app.workers.ingest.scan_redis_batches",
        "schedule": 0.5,
        "options": {
            "expires": 0.4,  # Expire si pas exécutée en 400ms
        }
    },

    # Posts Planifiés - Check toutes les 1 min
    "enqueue-due-posts-every-minute": {
        "task": "app.workers.scheduler.enqueue_due_posts",
        "schedule": 60.0,
        "options": {
            "expires": 55,
        }
    },

    # Commentaires - Poll toutes les 5 min
    "poll-post-comments-every-5-minutes": {
        "task": "app.workers.comments.poll_post_comments",
        "schedule": 300.0,
        "options": {
            "expires": 290,
        }
    },
}
```

### Timeline Beat

```
T=0s    → Beat: Envoie scan_redis_batches → Redis queue "ingest"
T=0s    → Beat: Envoie enqueue_due_posts → Redis queue "scheduler"
T=0s    → Beat: Envoie poll_post_comments → Redis queue "comments"

T=0.5s  → Beat: Envoie scan_redis_batches → Redis queue "ingest"
T=1s    → Beat: Envoie scan_redis_batches → Redis queue "ingest"
T=1.5s  → Beat: Envoie scan_redis_batches → Redis queue "ingest"

T=60s   → Beat: Envoie enqueue_due_posts → Redis queue "scheduler"
T=60.5s → Beat: Envoie scan_redis_batches → Redis queue "ingest"

T=300s  → Beat: Envoie poll_post_comments → Redis queue "comments"

... (boucle infinie)
```

---

## Flux de Données

### Flux 1: DM WhatsApp (Tâche Périodique)

```
1. User envoie "Hello" via WhatsApp
   ↓
2. Meta webhook → FastAPI POST /api/whatsapp/webhook
   ↓
3. FastAPI:
   - Sauvegarde message en BDD (100ms)
   - Ajoute à Redis batch (10ms)
   - Répond "OK" à Meta (< 200ms total) ✅
   ↓
4. [2 secondes plus tard - Deadline atteinte]
   ↓
5. Celery Beat (toutes les 0.5s):
   - Envoie task scan_redis_batches → Redis queue "ingest"
   ↓
6. Worker Ingest:
   - Prend task scan_redis_batches
   - Exécute: batch_scanner._process_due_conversations()
   - Trouve le batch (deadline passée)
   - Lock Redis (évite doublons)
   ↓
7. Worker Ingest (suite):
   - Récupère messages du batch
   - Appel AI (10 secondes, pas grave)
   - Génère réponse AI
   - Envoie via WhatsApp API
   - Sauvegarde réponse en BDD
   ↓
8. User reçoit réponse AI ✅
```

**Timeline:**
```
0ms     │ Webhook arrive
100ms   │ Message saved in DB
110ms   │ Added to Redis batch
200ms   │ FastAPI responds "OK" ✅
        │
2000ms  │ Batch deadline reached
2500ms  │ Beat tick (next 0.5s scan)
2510ms  │ Task sent to Redis
2550ms  │ Worker picks task
2600ms  │ Batch found, lock acquired
5000ms  │ AI processing...
10000ms │ AI response ready
10500ms │ WhatsApp message sent ✅
```

---

### Flux 2: Post Planifié (Tâche Périodique)

```
1. User schedule un post pour 14h00
   ↓
2. FastAPI:
   - INSERT scheduled_posts (status=queued, scheduled_at=14h00)
   - Répond "OK"
   ↓
3. [14h00 arrive]
   ↓
4. Celery Beat (toutes les 1 min):
   - 13h59 → enqueue_due_posts → Pas encore
   - 14h00 → enqueue_due_posts → Post trouvé !
   - Envoie task publish_post(post_id) → Redis queue "scheduler"
   ↓
5. Worker Scheduler:
   - Prend task publish_post
   - UPDATE status="publishing"
   - Appel Instagram API (3 secondes)
   - UPDATE status="published"
   ↓
6. Post publié sur Instagram ✅

Si erreur:
   - Worker: raise self.retry(exc=e)
   - Celery: Attend 5 min (default_retry_delay)
   - Retry automatique (max 3 fois)
```

---

### Flux 3: Document Upload (Tâche Manuelle)

```
1. User upload PDF dans knowledge base
   ↓
2. FastAPI:
   - Upload fichier → Supabase Storage
   - INSERT knowledge_documents (status=pending)
   - Envoie task process_document.delay(doc_id) → Redis queue "ingest"
   - Répond "OK" (< 500ms)
   ↓
3. Worker Ingest:
   - Prend task process_document
   - Download PDF (5s)
   - Parse texte (10s)
   - Split en chunks (2s)
   - Generate embeddings (30s)
   - INSERT knowledge_chunks (5s)
   - UPDATE status="indexed"
   ↓
4. Document indexé ✅ (52 secondes total, en arrière-plan)
```

---

## Configuration

### Celery App

**Fichier:** `backend/app/workers/celery_app.py`

```python
import os
from celery import Celery

celery = Celery(
    "socialsyncAI",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery.conf.update(
    # Routing des tâches par queue
    task_routes={
        "app.workers.ingest.*": {"queue": "ingest"},
        "app.workers.scheduler.*": {"queue": "scheduler"},
        "app.workers.comments.*": {"queue": "comments"},
    },

    # Timeouts
    task_time_limit=1800,  # 30 min max/task (hard kill)
    task_soft_time_limit=1700,  # 28 min (SoftTimeLimitExceeded)

    # Worker lifecycle
    worker_max_tasks_per_child=200,  # Restart après 200 tasks (évite memory leaks)

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Result backend
    result_expires=3600,  # Résultats expirés après 1h (économise Redis)
)

# Beat schedule (tâches périodiques)
celery.conf.beat_schedule = {
    "scan-redis-batches-every-500ms": {
        "task": "app.workers.ingest.scan_redis_batches",
        "schedule": 0.5,
    },
    "enqueue-due-posts-every-minute": {
        "task": "app.workers.scheduler.enqueue_due_posts",
        "schedule": 60.0,
    },
    "poll-post-comments-every-5-minutes": {
        "task": "app.workers.comments.poll_post_comments",
        "schedule": 300.0,
    },
}

# Import des modules workers (nécessaire pour découverte des tasks)
from app.workers import ingest
from app.workers import scheduler
from app.workers import comments
```

### Variables d'Environnement

**Fichier:** `backend/.env`

```bash
# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Flower (monitoring)
FLOWER_BASIC_AUTH=admin:password

# Supabase (pour workers)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
SUPABASE_ANON_KEY=xxx

# Meta API (pour workers)
META_GRAPH_VERSION=v24.0
META_APP_SECRET=xxx
```

---

## Monitoring

### Commandes Celery

```bash
# Lister workers actifs
celery -A app.workers.celery_app inspect active_queues

# Stats détaillées
celery -A app.workers.celery_app inspect stats

# Tâches en cours
celery -A app.workers.celery_app inspect active

# Schedule Beat actif
celery -A app.workers.celery_app inspect scheduled

# Ping workers
celery -A app.workers.celery_app inspect ping

# Arrêt propre
celery -A app.workers.celery_app control shutdown
```

### Flower Dashboard

```bash
# Démarrer Flower
celery -A app.workers.celery_app flower --port=5555

# Accès
http://localhost:5555
```

**Metrics disponibles:**
- Workers actifs/inactifs
- Queues (taille, débit)
- Tasks (succès, échecs, retry)
- Graphiques temps réel
- Logs détaillés par task

### Redis Monitoring

```bash
# Connexion Redis
redis-cli

# Voir queues Celery
LLEN celery:ingest
LLEN celery:scheduler
LLEN celery:comments

# Voir résultats
KEYS celery-task-result:*

# Mémoire utilisée
INFO memory

# Voir batches DMs
KEYS conv:*
ZRANGE conv:deadlines 0 -1 WITHSCORES
```

---

## Best Practices

### 1. Un Seul Beat

**❌ Jamais ça:**
```bash
# Terminal 1
celery -A app.workers.celery_app beat

# Terminal 2
celery -A app.workers.celery_app beat  # ❌ DANGER: Tâches dupliquées !
```

**✅ Toujours ça:**
```bash
# Beat en daemon (production)
celery -A app.workers.celery_app beat -d --pidfile=/var/run/celery/beat.pid

# Vérifier qu'un seul tourne
ps aux | grep "celery.*beat" | wc -l  # Doit retourner: 1
```

### 2. Workers Dédiés par Queue

**❌ Pas optimal:**
```bash
# Un seul worker pour tout
celery -A app.workers.celery_app worker -Q ingest,scheduler,comments
```

**✅ Optimal (scalabilité):**
```bash
# Workers spécialisés
celery -A app.workers.celery_app worker -Q ingest -n ingest@%h --autoscale=10,3
celery -A app.workers.celery_app worker -Q scheduler -n scheduler@%h --autoscale=5,2
celery -A app.workers.celery_app worker -Q comments -n comments@%h --autoscale=3,1
```

### 3. Retry Strategy

```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 min entre retries
    autoretry_for=(httpx.TimeoutException, redis.ConnectionError),
)
def my_task(self, ...):
    try:
        # Code
        pass
    except Exception as e:
        # Retry avec backoff exponentiel
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### 4. Idempotence

**Les tâches doivent être idempotentes** (même résultat si exécutées 2x)

```python
# ❌ Pas idempotent
@celery.task
def increment_counter(user_id):
    user.counter += 1  # Si retry → +2 au lieu de +1

# ✅ Idempotent
@celery.task
def set_status(user_id, status):
    user.status = status  # Si retry → même résultat
```

### 5. Timeouts

```python
celery.conf.update(
    task_time_limit=1800,        # 30 min (hard kill)
    task_soft_time_limit=1700,   # 28 min (exception)
)

@celery.task
def long_task():
    try:
        # Traitement long
        process()
    except SoftTimeLimitExceeded:
        # Cleanup avant hard kill
        cleanup()
        raise
```

---

## Troubleshooting

### Problème: Tâches non exécutées

**Diagnostic:**
```bash
# Workers tournent ?
ps aux | grep celery

# Queues ont des tâches ?
redis-cli LLEN celery:ingest

# Workers écoutent les bonnes queues ?
celery -A app.workers.celery_app inspect active_queues
```

**Solution:**
```bash
# Restart workers
pkill -f "celery.*worker"
celery -A app.workers.celery_app worker -Q ingest -l info
```

### Problème: Beat ne schedule pas

**Diagnostic:**
```bash
# Beat tourne ?
ps aux | grep "celery.*beat"

# Lock file coincé ?
ls -la celerybeat-schedule*
```

**Solution:**
```bash
# Supprimer lock
rm -f celerybeat-schedule.db

# Restart Beat
celery -A app.workers.celery_app beat -l info
```

### Problème: Redis OOM

**Diagnostic:**
```bash
redis-cli INFO memory
# used_memory: 250mb / maxmemory: 256mb ⚠️
```

**Solution:**
```bash
# Augmenter mémoire (redis.conf)
maxmemory 1gb

# Ou purger anciens résultats
redis-cli KEYS celery-task-result:* | xargs redis-cli DEL

# Ou configurer TTL auto
celery.conf.result_expires = 3600  # 1h
```

---

## Migration History

### V1.0 (Avant - Legacy)

```
FastAPI (Batch Scanner asyncio loop)
└─ DMs traités dans le process FastAPI
└─ ❌ Single point of failure
```

### V2.0 (Actuel - Celery)

```
Celery Beat (0.5s schedule)
└─ Envoie task scan_redis_batches
    └─ Worker Ingest exécute
        ✅ Robuste
        ✅ Scalable
        ✅ Architecture cohérente
```

**Voir:** `/workspace/BATCH_SCANNER_MIGRATION.md`

---

## Related Documentation

- **Cours complet:** `/workspace/CELERY_REDIS_COURS_COMPLET.md`
- **Migration:** `/workspace/BATCH_SCANNER_MIGRATION.md`
- **Docker Setup:** `.agent/SOP/DOCKER_SETUP.md`
- **Architecture globale:** `.agent/System/ARCHITECTURE.md`
- **Workers config:** Voir ce fichier

---

**Version:** 2.0
**Dernière mise à jour:** 2025-10-20
**Status:** ✅ Production Ready
