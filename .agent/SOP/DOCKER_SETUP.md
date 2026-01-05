# Docker Setup - SocialSync AI

**Date:** 2025-10-20
**Version:** 2.0
**Environnement:** Dev Container (VSCode)

---

## 📋 Table des Matières

1. [Architecture Docker](#architecture-docker)
2. [Services](#services)
3. [Démarrage](#démarrage)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Production](#production)

---

## Architecture Docker

### Vue d'Ensemble

```
┌──────────────────────────────────────────────────────────┐
│              DOCKER COMPOSE ARCHITECTURE                  │
└──────────────────────────────────────────────────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│     dev     │  │   backend   │  │  frontend   │
│ (VSCode)    │  │  (FastAPI)  │  │ (Next.js)   │
│  :8001      │  │    :8000    │  │   :3000     │
└─────────────┘  └─────────────┘  └─────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                    ┌────▼────┐
                    │  redis  │
                    │  :6380  │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┬────────────────┐
        │                │                │                │
┌───────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐ ┌──────▼──────┐
│celery-worker-│ │celery-worker-│ │celery-worker-│ │celery-beat  │
│   ingest     │ │  scheduler   │ │  comments    │ │(scheduler)  │
└──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘
        │                │                │                │
        └────────────────┼────────────────┴────────────────┘
                         │
                    ┌────▼────┐
                    │ flower  │
                    │  :5555  │
                    └─────────┘
```

---

## Services

### 1. dev (VSCode Dev Container)

**Rôle:** Environnement de développement VSCode

**Image:** Custom (Python 3.12 + Node 20 + Docker CLI)

**Commande:**
```yaml
command: sleep infinity  # Reste actif pour VSCode
```

**Ports:**
- 8001 → 8000 (backend)
- 3001 → 3000 (frontend)

**Utilisation:**
- Ouvrir VSCode
- "Reopen in Container"
- Terminal VSCode = Inside container

---

### 2. backend (FastAPI)

**Rôle:** API REST + Webhooks

**Image:** `backend/Dockerfile` (Python 3.12)

**Commande:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Ports:**
- 8000:8000

**Volumes:**
```yaml
- ../backend:/app  # Hot reload
```

**Depends on:**
- redis

**Env File:**
- `backend/.env`

---

### 3. frontend (Next.js)

**Rôle:** Interface utilisateur React

**Image:** `frontend/Dockerfile` (Node 20)

**Commande:**
```bash
npm run dev
```

**Ports:**
- 3000:3000

**Volumes:**
```yaml
- ../frontend:/app
- /app/node_modules  # Avoid overwrite
```

**Environment:**
```yaml
- WATCHPACK_POLLING=true       # Hot reload in Docker
- CHOKIDAR_USEPOLLING=true
- CHOKIDAR_INTERVAL=1000
```

**Depends on:**
- backend

**Env File:**
- `frontend/.env.local`

---

### 4. redis (Broker)

**Rôle:** Message broker + Result backend + Batching

**Image:** `redis:8.2.1-alpine`

**Ports:**
- 6380:6379 (externe:interne)

**Restart:** `unless-stopped`

**Pas de volume** = Données volatiles (OK pour queues)

---

### 5. celery-worker-ingest

**Rôle:** Worker pour queue "ingest" (DMs, documents)

**Image:** Même que backend

**Commande:**
```bash
celery -A app.workers.celery_app worker \
  -Q ingest \
  -E \            # Events enabled (pour Flower)
  -l info \       # Log level
  -n ingest@%h    # Nom unique
```

**Volumes:**
```yaml
- ../backend:/app  # Code partagé avec backend
```

**Environment:**
```yaml
- CELERY_BROKER_URL=${CELERY_BROKER_URL}
- CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
```

**Depends on:**
- redis

**Env File:**
- `backend/.env`

**Restart:** `unless-stopped`

---

### 6. celery-worker-scheduler

**Rôle:** Worker pour queue "scheduler" (posts planifiés)

**Image:** Même que backend

**Commande:**
```bash
celery -A app.workers.celery_app worker \
  -Q scheduler \
  -E \
  -l info \
  -n scheduler@%h
```

**Config:** Identique à celery-worker-ingest

---

### 7. celery-worker-comments

**Rôle:** Worker pour queue "comments" (polling commentaires)

**Image:** Même que backend

**Commande:**
```bash
celery -A app.workers.celery_app worker \
  -Q comments \
  -E \
  -l info \
  -n comments@%h
```

**Config:** Identique à celery-worker-ingest

---

### 8. celery-beat

**Rôle:** Scheduler de tâches périodiques

**Image:** Même que backend

**Commande:**
```bash
celery -A app.workers.celery_app beat -l info
```

**⚠️ CRITIQUE:** Un seul Beat par système !

**Tâches schedulées:**
- 0.5s: `scan_redis_batches` (DMs)
- 1min: `enqueue_due_posts` (posts)
- 5min: `poll_post_comments` (commentaires)

**Depends on:**
- redis

**Env File:**
- `backend/.env`

**Restart:** `unless-stopped`

---

### 9. flower (Monitoring)

**Rôle:** Dashboard web pour Celery

**Image:** Même que backend

**Commande:**
```bash
celery -A app.workers.celery_app flower \
  --port=5555 \
  --broker=${CELERY_BROKER_URL} \
  --result-backend=${CELERY_RESULT_BACKEND} \
  --persistent \                       # Persist data
  --db=/data/flower.db \               # SQLite DB
  --basic_auth=${FLOWER_BASIC_AUTH}    # admin:password
```

**Ports:**
- 5555:5555

**Volumes:**
```yaml
- ../backend:/app
- ./data/flower:/data  # Persist Flower DB
```

**Depends on:**
- redis

**Accès:**
```
http://localhost:5555
Username: admin
Password: (from FLOWER_BASIC_AUTH)
```

---

## Démarrage

### Prérequis

**Fichiers .env requis:**

1. **`backend/.env`**
```bash
# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
SUPABASE_ANON_KEY=xxx
SUPABASE_JWT_SECRET=xxx

# Meta API
META_GRAPH_VERSION=v24.0
META_APP_SECRET=xxx
META_APP_ID=xxx

# Flower
FLOWER_BASIC_AUTH=admin:password
```

2. **`frontend/.env.local`**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### Option 1: Tous les Services

```bash
cd /workspace
docker-compose -f .devcontainer/docker-compose.yml up -d
```

**Services démarrés:**
- ✅ backend (FastAPI) - http://localhost:8000
- ✅ frontend (Next.js) - http://localhost:3000
- ✅ redis (broker)
- ✅ celery-worker-ingest
- ✅ celery-worker-scheduler
- ✅ celery-worker-comments
- ✅ celery-beat ⏰
- ✅ flower - http://localhost:5555

**Vérifier:**
```bash
docker-compose -f .devcontainer/docker-compose.yml ps

# Doit afficher tous les services "Up"
```

---

### Option 2: Services Essentiels Uniquement

```bash
# Backend + Workers + Beat + Redis
docker-compose -f .devcontainer/docker-compose.yml up -d \
  backend redis \
  celery-worker-ingest \
  celery-worker-scheduler \
  celery-worker-comments \
  celery-beat

# Frontend séparément (si besoin)
docker-compose -f .devcontainer/docker-compose.yml up -d frontend
```

---

### Option 3: Dev Mode (VSCode)

**1. Ouvrir dans Dev Container:**
```
VSCode → Command Palette (Ctrl+Shift+P)
→ "Dev Containers: Reopen in Container"
```

**2. Lancer services depuis VSCode terminal:**
```bash
# Terminal 1: Backend (dans le container dev)
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend (dans le container dev)
cd frontend
npm run dev

# Terminal 3: Celery Workers (dans le container dev)
cd backend
celery -A app.workers.celery_app worker --beat -l info -Q ingest,scheduler,comments
```

**Avantage:** Debugging direct dans VSCode

---

## Configuration

### docker-compose.yml

**Fichier:** `.devcontainer/docker-compose.yml`

```yaml
version: "3.9"

services:
  # Dev container (VSCode)
  dev:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    command: sleep infinity
    ports:
      - "8001:8000"
      - "3001:3000"
    depends_on:
      - redis

  # Backend (FastAPI)
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    volumes:
      - ../backend:/app
    env_file:
      - ../backend/.env
    ports:
      - "8000:8000"
    depends_on:
      - redis

  # Frontend (Next.js)
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    volumes:
      - ../frontend:/app
      - /app/node_modules
    env_file:
      - ../frontend/.env.local
    environment:
      - WATCHPACK_POLLING=true
      - CHOKIDAR_USEPOLLING=true
      - CHOKIDAR_INTERVAL=1000
    ports:
      - "3000:3000"
    depends_on:
      - backend

  # Celery Workers (3 queues)
  celery-worker-ingest:
    build:
      context: ../backend
      dockerfile: Dockerfile
    command: >
      sh -c "celery -A app.workers.celery_app worker -Q ingest -E -l info -n ingest@%h"
    volumes:
      - ../backend:/app
    env_file:
      - ../backend/.env
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    depends_on:
      - redis
    restart: unless-stopped

  celery-worker-scheduler:
    build:
      context: ../backend
      dockerfile: Dockerfile
    command: >
      sh -c "celery -A app.workers.celery_app worker -Q scheduler -E -l info -n scheduler@%h"
    volumes:
      - ../backend:/app
    env_file:
      - ../backend/.env
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    depends_on:
      - redis
    restart: unless-stopped

  celery-worker-comments:
    build:
      context: ../backend
      dockerfile: Dockerfile
    command: >
      sh -c "celery -A app.workers.celery_app worker -Q comments -E -l info -n comments@%h"
    volumes:
      - ../backend:/app
    env_file:
      - ../backend/.env
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    depends_on:
      - redis
    restart: unless-stopped

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: ../backend
      dockerfile: Dockerfile
    command: >
      sh -c "celery -A app.workers.celery_app beat -l info"
    volumes:
      - ../backend:/app
    env_file:
      - ../backend/.env
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    depends_on:
      - redis
    restart: unless-stopped

  # Flower (Monitoring)
  flower:
    build:
      context: ../backend
      dockerfile: Dockerfile
    command: >
      sh -c "celery -A app.workers.celery_app flower
      --port=5555
      --broker=${CELERY_BROKER_URL}
      --result-backend=${CELERY_RESULT_BACKEND}
      --persistent
      --db=/data/flower.db
      --basic_auth=${FLOWER_BASIC_AUTH}"
    volumes:
      - ../backend:/app
      - ./data/flower:/data
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
      - FLOWER_BASIC_AUTH=${FLOWER_BASIC_AUTH}
    ports:
      - "5555:5555"
    depends_on:
      - redis

  # Redis (Broker)
  redis:
    image: redis:8.2.1-alpine
    ports:
      - "6380:6379"
    restart: unless-stopped
```

---

### Dockerfiles

#### Backend Dockerfile

**Fichier:** `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### Dev Container Dockerfile

**Fichier:** `.devcontainer/Dockerfile`

```dockerfile
FROM python:3.12-slim

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl git jq tree wget sudo locales libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest && corepack enable

# Docker CLI (pour Docker-in-Docker)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | \
    gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce-cli

# User non-root
ARG USERNAME=dev
ARG USER_UID=1000
RUN useradd -ms /bin/bash -u $USER_UID $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
USER $USERNAME
WORKDIR /workspace

# Python dependencies
COPY --chown=$USERNAME backend/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

CMD ["bash"]
```

---

## Troubleshooting

### Problème: Container ne démarre pas

**Diagnostic:**
```bash
# Voir les logs
docker-compose -f .devcontainer/docker-compose.yml logs backend

# Voir tous les logs
docker-compose -f .devcontainer/docker-compose.yml logs
```

**Solutions courantes:**
1. **Port déjà utilisé:**
```bash
# Trouver qui utilise le port 8000
lsof -i :8000

# Changer le port dans docker-compose.yml
ports:
  - "8001:8000"  # Externe:Interne
```

2. **Fichier .env manquant:**
```bash
# Vérifier
ls backend/.env
ls frontend/.env.local

# Copier template
cp backend/.env.example backend/.env
```

3. **Build failed:**
```bash
# Rebuild
docker-compose -f .devcontainer/docker-compose.yml build --no-cache backend
```

---

### Problème: Celery Beat ne schedule pas

**Diagnostic:**
```bash
# Beat tourne ?
docker-compose -f .devcontainer/docker-compose.yml ps celery-beat

# Logs Beat
docker-compose -f .devcontainer/docker-compose.yml logs -f celery-beat
```

**Solution:**
```bash
# Restart Beat
docker-compose -f .devcontainer/docker-compose.yml restart celery-beat

# Si ça ne marche pas, supprimer lock
docker-compose -f .devcontainer/docker-compose.yml exec celery-beat rm -f /app/celerybeat-schedule.db
docker-compose -f .devcontainer/docker-compose.yml restart celery-beat
```

---

### Problème: Workers ne traitent pas les tâches

**Diagnostic:**
```bash
# Workers actifs ?
docker-compose -f .devcontainer/docker-compose.yml ps | grep celery-worker

# Logs workers
docker-compose -f .devcontainer/docker-compose.yml logs -f celery-worker-ingest

# Vérifier queues Redis
docker-compose -f .devcontainer/docker-compose.yml exec redis redis-cli
> LLEN celery:ingest
> LLEN celery:scheduler
> LLEN celery:comments
```

**Solution:**
```bash
# Restart workers
docker-compose -f .devcontainer/docker-compose.yml restart celery-worker-ingest
docker-compose -f .devcontainer/docker-compose.yml restart celery-worker-scheduler
docker-compose -f .devcontainer/docker-compose.yml restart celery-worker-comments
```

---

### Problème: Hot reload ne fonctionne pas

**Frontend:**
```yaml
# Vérifier dans docker-compose.yml
environment:
  - WATCHPACK_POLLING=true
  - CHOKIDAR_USEPOLLING=true
```

**Backend:**
```bash
# Vérifier commande
CMD ["uvicorn", "app.main:app", "--reload"]  # --reload REQUIS
```

---

### Problème: Redis connection refused

**Diagnostic:**
```bash
# Redis tourne ?
docker-compose -f .devcontainer/docker-compose.yml ps redis

# Tester connexion
docker-compose -f .devcontainer/docker-compose.yml exec redis redis-cli ping
# Doit retourner: PONG
```

**Solution:**
```bash
# Restart Redis
docker-compose -f .devcontainer/docker-compose.yml restart redis

# Vérifier CELERY_BROKER_URL dans .env
# Doit être: redis://redis:6379/0 (pas localhost!)
```

---

## Commandes Utiles

### Gestion des Containers

```bash
# Démarrer tous les services
docker-compose -f .devcontainer/docker-compose.yml up -d

# Démarrer service spécifique
docker-compose -f .devcontainer/docker-compose.yml up -d backend

# Arrêter tous les services
docker-compose -f .devcontainer/docker-compose.yml down

# Restart un service
docker-compose -f .devcontainer/docker-compose.yml restart backend

# Rebuild un service
docker-compose -f .devcontainer/docker-compose.yml build --no-cache backend
docker-compose -f .devcontainer/docker-compose.yml up -d backend

# Voir les services actifs
docker-compose -f .devcontainer/docker-compose.yml ps

# Voir les logs
docker-compose -f .devcontainer/docker-compose.yml logs -f backend
docker-compose -f .devcontainer/docker-compose.yml logs -f celery-beat
docker-compose -f .devcontainer/docker-compose.yml logs -f  # Tous

# Entrer dans un container
docker-compose -f .devcontainer/docker-compose.yml exec backend bash
docker-compose -f .devcontainer/docker-compose.yml exec redis redis-cli
```

### Nettoyage

```bash
# Supprimer tous les containers
docker-compose -f .devcontainer/docker-compose.yml down

# Supprimer + volumes
docker-compose -f .devcontainer/docker-compose.yml down -v

# Rebuild complet (clean)
docker-compose -f .devcontainer/docker-compose.yml down
docker-compose -f .devcontainer/docker-compose.yml build --no-cache
docker-compose -f .devcontainer/docker-compose.yml up -d
```

---

## Production

### Différences Dev vs Prod

| Dev | Production |
|-----|------------|
| Hot reload (volumes) | Build fixe (COPY) |
| `--reload` | Pas de reload |
| 1 worker par queue | Multiple workers |
| Logs console | Logs fichier/Sentry |
| SQLite Flower | PostgreSQL Flower |

### Docker Compose Production

**Fichier:** `docker-compose.prod.yml` (à créer)

```yaml
version: "3.9"

services:
  backend:
    image: socialsyncai/backend:latest
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
    ports:
      - "8000:8000"
    env_file:
      - .env.prod
    restart: always

  celery-worker-ingest:
    image: socialsyncai/backend:latest
    command: celery -A app.workers.celery_app worker -Q ingest -n ingest@%h --autoscale=10,3
    env_file:
      - .env.prod
    restart: always

  celery-worker-scheduler:
    image: socialsyncai/backend:latest
    command: celery -A app.workers.celery_app worker -Q scheduler -n scheduler@%h --autoscale=5,2
    env_file:
      - .env.prod
    restart: always

  celery-worker-comments:
    image: socialsyncai/backend:latest
    command: celery -A app.workers.celery_app worker -Q comments -n comments@%h --autoscale=3,1
    env_file:
      - .env.prod
    restart: always

  celery-beat:
    image: socialsyncai/backend:latest
    command: celery -A app.workers.celery_app beat -l info
    env_file:
      - .env.prod
    restart: always
    deploy:
      replicas: 1  # UN SEUL

  redis:
    image: redis:8.2.1-alpine
    command: redis-server --appendonly yes --maxmemory 1gb
    volumes:
      - redis-data:/data
    restart: always

volumes:
  redis-data:
```

---

## Related Documentation

- **Celery Architecture:** `.agent/System/CELERY_ARCHITECTURE.md`
- **Cours Celery/Redis:** `/workspace/CELERY_REDIS_COURS_COMPLET.md`
- **Architecture globale:** `.agent/System/ARCHITECTURE.md`
- **Deploy guide:** `.agent/SOP/DEPLOY.md`

---

**Version:** 2.0
**Dernière mise à jour:** 2025-10-20
**Status:** ✅ Production Ready
