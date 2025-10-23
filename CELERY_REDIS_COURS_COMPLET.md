# Cours Complet: Celery, Redis & Architecture Distribuée

**Date:** 2025-10-20
**Niveau:** Débutant → Intermédiaire
**Durée lecture:** 15-20 min

---

## 📚 Table des Matières

1. [Le Problème à Résoudre](#le-problème-à-résoudre)
2. [Redis: La Messagerie](#redis-la-messagerie)
3. [Celery Worker: Le Travailleur](#celery-worker-le-travailleur)
4. [Celery Beat: L'Horloge](#celery-beat-lhorloge)
5. [Architecture Complète](#architecture-complète)
6. [Cas Pratique: SocialSync AI](#cas-pratique-socialsync-ai)
7. [Commandes Essentielles](#commandes-essentielles)
8. [Troubleshooting](#troubleshooting)

---

## 1. Le Problème à Résoudre

### Sans Celery (Approche Naïve)

Imagine une API FastAPI qui doit:
- Recevoir un webhook WhatsApp
- Traiter le message avec l'IA (10 secondes)
- Envoyer la réponse

**Code naïf:**
```python
@app.post("/webhook")
async def webhook(message: dict):
    # ⏰ 10 secondes d'attente ici
    response = await process_with_ai(message)
    await send_response(response)
    return {"status": "ok"}
```

**Problèmes:**
1. ⏰ **Timeout**: Meta attend une réponse en < 5s, sinon il retry
2. 🔒 **Blocage**: Pendant 10s, l'API ne peut rien faire d'autre
3. 💥 **Crash**: Si FastAPI crash → tâche perdue
4. 📈 **Scalabilité**: Impossible de paralléliser

### Solution: Architecture Distribuée

**Principe:**
1. API reçoit webhook → Envoie tâche à une **queue** → Répond immédiatement "OK"
2. **Worker** prend la tâche dans la queue → Traite avec AI → Envoie réponse
3. Si API crash → Worker continue de travailler ✅

**C'est exactement ce que fait Celery + Redis !**

---

## 2. Redis: La Messagerie 📬

### Qu'est-ce que Redis ?

**Redis = Base de données en mémoire ultra-rapide**

Imagine Redis comme un **tableau d'affichage** dans une entreprise:
- Quelqu'un écrit un post-it et le colle
- Quelqu'un d'autre lit le post-it et le prend
- Tout le monde peut lire/écrire en même temps

### Rôle 1: Broker (File d'attente de messages)

**Analogie:** Redis = La boîte aux lettres

```
FastAPI (producteur) → Redis Queue → Celery Worker (consommateur)
   📮 "Task: Process message"  →  📬  →  👷 "Je prends!"
```

**En pratique:**
```python
# FastAPI envoie une tâche
task = process_message.delay(message_id="123")
# ↓ Redis stocke ça:
# Queue "ingest": [{"task": "process_message", "args": ["123"]}]

# Worker lit la queue
# ↓ Redis retire la tâche de la queue
# Worker exécute: process_message("123")
```

### Rôle 2: Result Backend (Stockage des résultats)

**Analogie:** Redis = Le casier de résultats

```python
# Worker termine la tâche
result = {"status": "success", "response": "Hello"}

# Stocke dans Redis
task_id = "abc-123-def"
redis.set(f"celery-task-result:{task_id}", result)

# FastAPI peut récupérer le résultat plus tard
result = task.get()
```

### Structure Redis pour Celery

```redis
# Queues (listes Redis)
LPUSH celery:ingest '{"task": "process_message", "id": "123"}'
RPOP celery:ingest  # Worker prend la tâche

# Résultats (hash Redis)
SET celery-task-result:abc-123 '{"status": "SUCCESS", "result": {...}}'

# Métadonnées
SET celery-task-meta:abc-123 '{"state": "PENDING", "retries": 0}'
```

**Pourquoi Redis et pas une BDD ?**

| Redis | PostgreSQL |
|-------|------------|
| ⚡ En RAM (ultra rapide) | 💾 Sur disque (lent) |
| 📊 100k ops/sec | 📊 1k ops/sec |
| ❌ Données volatiles (TTL) | ✅ Données persistantes |
| ✅ Parfait pour queues | ❌ Overhead pour queues |

---

## 3. Celery Worker: Le Travailleur 👷

### Qu'est-ce qu'un Worker ?

**Worker = Process Python qui écoute Redis et exécute des tâches**

**Analogie:** Imagine un restaurant

- **Redis Queue** = Le passe-plat (commandes en attente)
- **Celery Worker** = Le cuisinier qui prend les commandes et cuisine
- **Plusieurs Workers** = Plusieurs cuisiniers en parallèle

### Démarrage d'un Worker

```bash
celery -A app.workers.celery_app worker --loglevel=info -Q ingest
#       │                        │                         │
#       │                        │                         └─ Queue(s) à écouter
#       │                        └─ Commande: "worker"
#       └─ App Celery (configuration)
```

**Ce qu'il fait:**
1. Se connecte à Redis
2. Écoute la queue `ingest`
3. Prend une tâche dès qu'elle arrive
4. Exécute le code Python
5. Stocke le résultat dans Redis
6. Recommence (boucle infinie)

### Exemple: Notre Worker

**Fichier:** `backend/app/workers/ingest.py`

```python
@celery.task(bind=True, name="app.workers.ingest.process_document")
def process_document_task(self, document_id: str):
    # 1. Worker prend cette tâche dans la queue "ingest"
    # 2. Exécute ce code
    db = get_db()
    doc = db.table("knowledge_documents").select(...).execute()

    # 3. Traitement long (10s, 1 min, peu importe)
    process_pdf(doc)

    # 4. Résultat stocké dans Redis automatiquement
    return {"status": "success", "doc_id": document_id}
```

**Envoyer la tâche:**
```python
# Depuis FastAPI
from app.workers.ingest import process_document_task

@app.post("/documents")
async def upload_document(doc_id: str):
    # Envoie la tâche à Redis
    task = process_document_task.delay(doc_id)

    # Répond IMMÉDIATEMENT (< 100ms)
    return {"task_id": task.id, "status": "processing"}
```

### Concurrence: Multiple Workers

**Tu peux lancer PLUSIEURS workers:**

```bash
# Terminal 1: Worker 1
celery -A app.workers.celery_app worker -Q ingest -n worker1@%h

# Terminal 2: Worker 2
celery -A app.workers.celery_app worker -Q ingest -n worker2@%h

# Terminal 3: Worker 3
celery -A app.workers.celery_app worker -Q ingest -n worker3@%h
```

**Redis distribue les tâches:**
```
Redis Queue: [Task1, Task2, Task3, Task4, Task5]
              ↓      ↓      ↓      ↓      ↓
           Worker1 Worker2 Worker3 Worker1 Worker2
```

**Résultat:** 5x plus rapide ! 🚀

---

## 4. Celery Beat: L'Horloge ⏰

### Qu'est-ce que Celery Beat ?

**Celery Beat = Cron job distribué (scheduler de tâches périodiques)**

**Analogie:** Imagine un réveil qui sonne

- **Celery Beat** = Le réveil (envoie des tâches à intervalles réguliers)
- **Redis Queue** = La sonnerie retentit
- **Worker** = Tu te réveilles et tu fais l'action

### Différence Worker vs Beat

| Celery Worker | Celery Beat |
|---------------|-------------|
| **Exécute** les tâches | **Planifie** les tâches |
| Écoute Redis | Envoie vers Redis |
| Peut y en avoir plusieurs | **UN SEUL** (master) |
| Obligatoire | Optionnel |

**Important:**
- ✅ Worker sans Beat = OK (tâches manuelles uniquement)
- ❌ Beat sans Worker = Inutile (envoie des tâches, mais personne pour les faire)

### Configuration Beat

**Fichier:** `backend/app/workers/celery_app.py`

```python
celery.conf.beat_schedule = {
    "scan-redis-batches-every-500ms": {
        "task": "app.workers.ingest.scan_redis_batches",  # Quelle tâche
        "schedule": 0.5,  # Quand (0.5s = toutes les 500ms)
        "options": {
            "expires": 0.4,  # Expire si pas exécutée en 400ms
        }
    },
    "poll-comments-every-5-minutes": {
        "task": "app.workers.comments.poll_post_comments",
        "schedule": 300.0,  # Toutes les 5 minutes
    },
}
```

### Démarrage de Beat

```bash
celery -A app.workers.celery_app beat --loglevel=info
#                                │
#                                └─ Commande: "beat" (pas "worker")
```

**Ce qu'il fait:**
```
T=0s   → Beat: "Envoi task scan_redis_batches vers Redis queue 'ingest'"
T=0.5s → Beat: "Envoi task scan_redis_batches vers Redis queue 'ingest'"
T=1s   → Beat: "Envoi task scan_redis_batches vers Redis queue 'ingest'"
...

En parallèle:
Worker: "Je prends task scan_redis_batches" → Exécute → Termine
Worker: "Je prends task scan_redis_batches" → Exécute → Termine
```

### Types de Schedules

```python
from celery.schedules import crontab

celery.conf.beat_schedule = {
    # Toutes les 30 secondes
    "simple": {
        "task": "my_task",
        "schedule": 30.0,
    },

    # Tous les jours à 8h du matin
    "daily": {
        "task": "send_daily_report",
        "schedule": crontab(hour=8, minute=0),
    },

    # Tous les lundis à 9h
    "weekly": {
        "task": "weekly_cleanup",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),
    },

    # Toutes les heures
    "hourly": {
        "task": "check_status",
        "schedule": crontab(minute=0),
    },
}
```

---

## 5. Architecture Complète

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTÈME COMPLET                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   FastAPI    │────▶│    Redis     │◀────│Celery Worker │
│  (Producteur)│     │   (Broker)   │     │(Consommateur)│
└──────────────┘     └──────────────┘     └──────────────┘
      │                      ▲                     │
      │                      │                     │
      │              ┌───────┴───────┐             │
      │              │  Celery Beat  │             │
      │              │  (Scheduler)  │             │
      │              └───────────────┘             │
      │                                            │
      └────────────── PostgreSQL ─────────────────┘
                    (Données métier)
```

### Flux de Données

#### Scénario 1: Tâche Manuelle (DM WhatsApp)

```
1. WhatsApp → Webhook → FastAPI
   User envoie "Hello" → Meta webhook → POST /api/whatsapp/webhook

2. FastAPI → Redis
   @app.post("/webhook")
   async def webhook(data):
       # Sauvegarde message en BDD
       db.insert(message)

       # Envoie tâche à Redis (< 10ms)
       process_message.delay(message_id)

       # Répond IMMÉDIATEMENT à Meta
       return {"status": "ok"}  # ⚡ < 100ms total

3. Redis → Worker
   Worker écoute queue "ingest"
   Worker prend task "process_message"

4. Worker → Traitement
   # Appel IA (10 secondes, pas grave)
   response = await rag_agent.generate(message)

   # Envoie réponse WhatsApp
   await whatsapp_api.send(response)

5. Worker → Redis (résultat)
   task.update_state(state="SUCCESS", result={"sent": true})
```

**Timeline:**
```
0ms    │ Webhook arrive
10ms   │ Message saved in DB
20ms   │ Task sent to Redis
100ms  │ FastAPI responds "OK" ✅
       │
1000ms │ Worker picks task
3000ms │ AI processing...
8000ms │ AI processing...
10000ms│ Response generated
10500ms│ WhatsApp message sent ✅
```

#### Scénario 2: Tâche Planifiée (Batch Scanner)

```
1. Celery Beat → Redis
   Beat (horloge): "C'est l'heure ! Toutes les 0.5s"
   Beat envoie: scan_redis_batches.delay()

2. Redis → Worker
   Worker prend task "scan_redis_batches"

3. Worker → Exécution
   def scan_redis_batches():
       # Scan Redis pour batches dus
       batches = redis.get_due_batches()

       # Traite chaque batch
       for batch in batches:
           process_batch(batch)

       return {"processed": len(batches)}

4. Worker → Redis (résultat)
   task.update_state(state="SUCCESS")

5. Repeat (toutes les 0.5s)
   Beat: "Encore l'heure !"
   Beat envoie: scan_redis_batches.delay()
```

**Timeline:**
```
0ms     │ Beat schedule tick
10ms    │ Task sent to Redis
50ms    │ Worker picks task
100ms   │ Scan Redis for batches
200ms   │ Process batches (if any)
400ms   │ Task complete
500ms   │ Beat schedule tick (again) ♻️
510ms   │ Task sent to Redis
...
```

---

## 6. Cas Pratique: SocialSync AI

### Notre Architecture Actuelle

**3 Queues:**
1. `ingest` - Messages DMs/Chats (WhatsApp, Instagram)
2. `scheduler` - Posts planifiés
3. `comments` - Commentaires Instagram

**2 Types de Tâches:**
1. **Manuelles** (déclenchées par événements)
   - `process_message` - Traite un DM
   - `process_document` - Indexe un document
   - `publish_post` - Publie un post planifié

2. **Périodiques** (déclenchées par Celery Beat)
   - `scan_redis_batches` - Toutes les 0.5s
   - `poll_post_comments` - Toutes les 5 min
   - `enqueue_due_posts` - Toutes les 1 min

### Commandes de Démarrage

**Production complète:**
```bash
# Terminal 1: FastAPI (API)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Worker ingest (DMs/documents)
celery -A app.workers.celery_app worker -l info -Q ingest -n ingest@%h

# Terminal 3: Worker scheduler (posts planifiés)
celery -A app.workers.celery_app worker -l info -Q scheduler -n scheduler@%h

# Terminal 4: Worker comments (commentaires)
celery -A app.workers.celery_app worker -l info -Q comments -n comments@%h

# Terminal 5: Celery Beat (tâches périodiques) ⚠️ REQUIS
celery -A app.workers.celery_app beat -l info

# Terminal 6: Redis (si pas déjà lancé)
redis-server
```

**Dev simplifié (1 worker pour tout):**
```bash
# Terminal 1: FastAPI
uvicorn app.main:app --reload

# Terminal 2: Worker + Beat combiné
celery -A app.workers.celery_app worker --beat -l info -Q ingest,scheduler,comments

# Terminal 3: Redis
redis-server
```

### Que se passe-t-il SANS Celery Beat ?

**Avec Beat:**
```
✅ DMs traités (scan_redis_batches toutes les 0.5s)
✅ Comments pollés (toutes les 5 min)
✅ Posts publiés (toutes les 1 min)
```

**Sans Beat:**
```
❌ DMs NON traités (aucun scan de Redis)
❌ Comments NON pollés (pas de polling)
❌ Posts NON publiés (pas de trigger)

Mais:
✅ Tâches manuelles OK (si envoyées par FastAPI)
```

**Exemple concret:**
```bash
# Scenario: Beat arrêté
pkill -f "celery.*beat"

# Utilisateur envoie DM WhatsApp
# → FastAPI reçoit webhook
# → Message stocké dans Redis batch
# → ❌ JAMAIS traité (Beat ne scan pas Redis)
# → ❌ Utilisateur n'aura jamais de réponse

# Solution: Redémarrer Beat
celery -A app.workers.celery_app beat -l info
# → scan_redis_batches exécuté toutes les 0.5s
# → ✅ Batch traité, réponse envoyée
```

---

## 7. Commandes Essentielles

### Gestion des Workers

```bash
# Lister les workers actifs
celery -A app.workers.celery_app inspect active_queues

# Voir les stats
celery -A app.workers.celery_app inspect stats

# Voir les tâches en cours
celery -A app.workers.celery_app inspect active

# Arrêter proprement un worker
celery -A app.workers.celery_app control shutdown

# Purger une queue (vider)
celery -A app.workers.celery_app purge -Q ingest
```

### Monitoring Beat

```bash
# Voir le schedule actif
celery -A app.workers.celery_app inspect scheduled

# Vérifier si Beat tourne
ps aux | grep "celery.*beat"

# Logs Beat
celery -A app.workers.celery_app beat -l debug
```

### Debug Redis

```bash
# Se connecter à Redis
redis-cli

# Voir toutes les clés Celery
KEYS celery*

# Voir la queue "ingest"
LRANGE celery 0 -1

# Voir les résultats de tâches
KEYS celery-task-result:*

# Compter les tâches en attente
LLEN celery

# Vider Redis (⚠️ ATTENTION)
FLUSHDB
```

### Monitoring Production

**Flower (Interface Web pour Celery):**
```bash
# Installation
pip install flower

# Démarrage
celery -A app.workers.celery_app flower --port=5555

# Accès
http://localhost:5555
```

**Dashboard Flower:**
- 📊 Workers actifs
- 📈 Graphiques de performance
- 📋 Liste des tâches (en cours, succès, échecs)
- ⏱️ Temps d'exécution moyen
- 🔄 Retry logs

---

## 8. Troubleshooting

### Problème 1: Tâches non exécutées

**Symptômes:**
- Task envoyée à Redis
- Jamais exécutée
- Timeout côté utilisateur

**Diagnostic:**
```bash
# 1. Worker tourne ?
ps aux | grep "celery.*worker"

# 2. Worker écoute la bonne queue ?
celery -A app.workers.celery_app inspect active_queues
# Doit afficher: "ingest", "scheduler", "comments"

# 3. Redis contient des tâches ?
redis-cli
LLEN celery  # Nombre de tâches

# 4. Erreurs dans les logs ?
celery -A app.workers.celery_app worker -l debug -Q ingest
```

**Solutions:**
```bash
# Redémarrer le worker
pkill -f "celery.*worker"
celery -A app.workers.celery_app worker -l info -Q ingest

# Si trop de tâches bloquées, purger
celery -A app.workers.celery_app purge -Q ingest
```

---

### Problème 2: Beat ne schedule pas

**Symptômes:**
- `scan_redis_batches` pas exécuté toutes les 0.5s
- DMs non traités

**Diagnostic:**
```bash
# 1. Beat tourne ?
ps aux | grep "celery.*beat"

# 2. Schedule configuré ?
celery -A app.workers.celery_app inspect scheduled

# 3. Logs Beat
celery -A app.workers.celery_app beat -l debug
```

**Solutions:**
```bash
# Beat utilise un fichier de lock
# Si Beat crash, le lock reste
rm -f celerybeat-schedule.db

# Redémarrer Beat
celery -A app.workers.celery_app beat -l info
```

---

### Problème 3: Tâches dupliquées

**Symptômes:**
- Même tâche exécutée 2x, 3x
- Utilisateur reçoit plusieurs réponses

**Causes:**
1. Plusieurs Beat lancés (interdit !)
2. Pas de lock Redis (nos batches ont un lock ✅)

**Diagnostic:**
```bash
# Combien de Beat actifs ?
ps aux | grep "celery.*beat" | wc -l
# Doit retourner: 1 (UN SEUL)

# Si > 1, kill tous sauf 1
pkill -f "celery.*beat"
celery -A app.workers.celery_app beat -l info
```

---

### Problème 4: Redis plein

**Symptômes:**
- Redis erreur "OOM (Out Of Memory)"
- Tâches rejetées

**Diagnostic:**
```bash
redis-cli
INFO memory
# maxmemory: 256mb
# used_memory: 255mb ⚠️

# Voir les clés qui prennent de la place
MEMORY USAGE celery-task-result:abc-123
```

**Solutions:**
```bash
# Augmenter mémoire Redis
# Dans redis.conf
maxmemory 1gb

# Ou purger les anciens résultats
redis-cli
KEYS celery-task-result:* | xargs DEL

# Configurer TTL automatique (Celery)
celery.conf.result_expires = 3600  # 1 heure
```

---

## 9. Best Practices

### Production Checklist

✅ **1. Un seul Beat**
```bash
# Process manager (Supervisor, systemd)
[program:celery-beat]
command=celery -A app.workers.celery_app beat
numprocs=1  # UN SEUL
```

✅ **2. Workers par queue**
```bash
# Worker dédié par type de tâche
celery -A ... worker -Q ingest -n ingest@%h --autoscale=10,3
celery -A ... worker -Q scheduler -n scheduler@%h --autoscale=5,2
celery -A ... worker -Q comments -n comments@%h --autoscale=3,1
```

✅ **3. Monitoring**
- Flower (UI web)
- Sentry (erreurs)
- Prometheus + Grafana (métriques)

✅ **4. Retry Strategy**
```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 min entre retries
)
def my_task(self, ...):
    try:
        # Code
    except Exception as e:
        raise self.retry(exc=e)
```

✅ **5. Redis Persistence**
```bash
# redis.conf
save 900 1     # Snapshot toutes les 15 min si 1 key modifiée
save 300 10    # Snapshot toutes les 5 min si 10 keys modifiées
save 60 10000  # Snapshot toutes les 1 min si 10k keys modifiées
```

---

## 10. Comparaison Finale

### Avant Celery (Naïf)

```python
# FastAPI bloque pendant le traitement
@app.post("/webhook")
async def webhook(data):
    message = save_message(data)  # 100ms

    # ⏰ 10 secondes d'attente
    response = await process_with_ai(message)  # 10s

    await send_response(response)  # 500ms

    return {"status": "ok"}  # ⚠️ Timeout Meta (> 5s)
```

**Problèmes:**
- ❌ Timeout Meta
- ❌ API bloquée
- ❌ Si crash, tâche perdue
- ❌ Pas de retry
- ❌ Pas de scalabilité

---

### Avec Celery (Production)

```python
# FastAPI répond immédiatement
@app.post("/webhook")
async def webhook(data):
    message = save_message(data)  # 100ms

    # Envoie à Celery (10ms)
    process_message.delay(message.id)

    return {"status": "ok"}  # ✅ < 200ms

# Worker traite en arrière-plan
@celery.task(bind=True, max_retries=3)
def process_message(self, message_id):
    try:
        message = get_message(message_id)
        response = process_with_ai(message)  # 10s, pas grave
        send_response(response)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
```

**Avantages:**
- ✅ FastAPI répond < 200ms
- ✅ Pas de timeout
- ✅ Si crash, task reste dans Redis
- ✅ Retry automatique
- ✅ Scalable (multiple workers)

---

## Résumé en 1 Image

```
┌─────────────────────────────────────────────────────────────┐
│                    CELERY + REDIS                            │
└─────────────────────────────────────────────────────────────┘

🏭 REDIS (La Poste)
├─ 📬 Queue "ingest"     → [Task1, Task2, Task3]
├─ 📬 Queue "scheduler"  → [Task4, Task5]
└─ 📬 Queue "comments"   → [Task6]

👷 CELERY WORKER (Les Facteurs)
├─ Worker 1 → Écoute "ingest"     → Prend Task1 → Exécute
├─ Worker 2 → Écoute "scheduler"  → Prend Task4 → Exécute
└─ Worker 3 → Écoute "comments"   → Prend Task6 → Exécute

⏰ CELERY BEAT (L'Horloge)
├─ Toutes les 0.5s  → Envoie scan_redis_batches → Queue "ingest"
├─ Toutes les 5 min → Envoie poll_comments      → Queue "comments"
└─ Toutes les 1 min → Envoie enqueue_posts      → Queue "scheduler"

📱 FASTAPI (Le Client)
└─ Webhook arrive → Envoie task → Queue "ingest" → Répond "OK"
```

---

## Commandes de Démarrage (Copier-Coller)

**Production:**
```bash
# Terminal 1: FastAPI
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Worker Ingest
celery -A app.workers.celery_app worker -l info -Q ingest -n ingest@%h --autoscale=10,3

# Terminal 3: Worker Scheduler
celery -A app.workers.celery_app worker -l info -Q scheduler -n scheduler@%h --autoscale=5,2

# Terminal 4: Worker Comments
celery -A app.workers.celery_app worker -l info -Q comments -n comments@%h --autoscale=3,1

# Terminal 5: Beat (UN SEUL) ⚠️
celery -A app.workers.celery_app beat -l info

# Terminal 6 (optionnel): Monitoring
celery -A app.workers.celery_app flower --port=5555
```

**Dev:**
```bash
# Terminal 1: FastAPI
uvicorn app.main:app --reload

# Terminal 2: All-in-one
celery -A app.workers.celery_app worker --beat -l info -Q ingest,scheduler,comments
```

---

## Conclusion

**Redis:**
- 📬 File d'attente de messages (broker)
- 💾 Stockage des résultats (backend)
- ⚡ Ultra-rapide (en mémoire)

**Celery Worker:**
- 👷 Exécute les tâches
- 🔄 Peut y en avoir plusieurs
- 📊 Scalable horizontalement

**Celery Beat:**
- ⏰ Planifie les tâches périodiques
- 📅 Comme un cron distribué
- ⚠️ **UN SEUL** par système

**Sans Beat → Tâches périodiques ne s'exécutent PAS !**

---

*Dernière mise à jour: 2025-10-20*
*Questions ? Ping @claude*
