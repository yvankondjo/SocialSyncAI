# Architecture Système - SocialSync AI

## Vue d'ensemble

SocialSync AI utilise une **architecture microservices async** avec:
- Backend FastAPI (Python 3.12)
- Frontend Next.js 14 (React, TypeScript)
- Base de données Supabase (PostgreSQL + pgvector)
- Queue system: Celery + Redis
- Storage: Supabase Storage

## Flux de données principal

```
┌─────────────┐
│  Plateforme │ (WhatsApp, Instagram)
└──────┬──────┘
       │ Webhook
       ▼
┌─────────────────┐
│  FastAPI Router │ (validation HMAC)
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│  ResponseManager     │ (extraction, validation crédits)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Supabase DB         │ (save_unified_message)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  MessageBatcher      │ (Redis, 2s window)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  BatchScanner        │ (background loop, 0.5s)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  RAG Agent           │ (LangGraph + OpenAI)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Platform Service    │ (WhatsAppService, InstagramService)
└──────────┬───────────┘
           │
           ▼
┌─────────────┐
│  Utilisateur│
└─────────────┘
```

## Composants clés

### 1. API Layer (FastAPI)

**Fichier**: `backend/app/main.py`

**Routers**:
- `/api/social-accounts` - Connexion OAuth des comptes
- `/api/whatsapp` - Webhooks et messages WhatsApp
- `/api/instagram` - Webhooks et messages Instagram
- `/api/conversations` - Gestion des conversations
- `/api/knowledge-documents` - Upload et ingestion de documents
- `/api/faq-qa` - Gestion des Q&A
- `/api/ai-settings` - Configuration de l'agent IA
- `/api/subscriptions` - Gestion des abonnements
- `/api/stripe` - Webhooks Stripe
- `/api/support` - Escalations support

### 2. Message Processing Pipeline

#### MessageBatcher
**Fichier**: `backend/app/services/message_batcher.py`

**Responsabilités**:
- Grouper les messages par conversation (fenêtre de 2s)
- Stockage temporaire dans Redis avec TTL 30 min
- Gestion des deadlines via sorted sets Redis
- Structure de clé: `conv:{platform}:{account_id}:{contact_id}`

**Redis Keys**:
```
conv:whatsapp:{phone_id}:{wa_id}        # Batch data (hash)
conv:deadlines                           # Sorted set (timestamp scores)
conversation:{social_account_id}:{customer_id}  # Conversation cache
credentials:{platform}:{account_id}      # Credentials cache
```

#### BatchScanner
**Fichier**: `backend/app/services/batch_scanner.py`

**Responsabilités**:
- Scanner continu des conversations échues (loop 0.5s)
- Orchestration du traitement async
- Métriques temps réel (succès, timeouts, erreurs)
- Timeout: 30s max par conversation

**Métriques trackées**:
- `conversations_processed`
- `conversations_failed`
- `conversations_timed_out`
- `responses_generated`
- `processing_times[]`

#### ResponseManager
**Fichier**: `backend/app/services/response_manager.py`

**Responsabilités**:
- Extraction unifiée des messages par plateforme
- Validation des crédits et features (images/audio)
- Cache Redis des profils et credentials
- Envoi des réponses via platform services

**Fonctions clés**:
- `extract_{platform}_message_content()` - Extraction normalisée
- `generate_smart_response()` - Appel RAG agent
- `send_response()` - Envoi via platform service
- `send_typing_indicator_and_mark_read()` - UX indicators

### 3. RAG Agent (LangGraph)

**Fichier**: `backend/app/services/rag_agent.py`

**Architecture**:
- **Graph LangGraph** avec noeuds:
  - `retrieve` - Recherche vectorielle (pgvector)
  - `check_faq` - Vérification Q&A exactes
  - `generate` - Génération LLM
  - `validate` - Validation et post-processing

**Retrieval**:
- Embedding: OpenAI `text-embedding-3-small`
- Similarité cosinus sur `knowledge_chunks.embedding`
- Top-k chunks pertinents
- Reranking par pertinence

### 4. Platform Services

**Structure commune**:
```python
class PlatformService:
    def __init__(self, credentials)
    def validate_credentials() -> bool
    def send_message(contact_id, text, media=None)
    def _send_with_retry() -> response
    def send_typing_indicator()
    def mark_as_read()
```

**Implémentations**:
- `WhatsAppService` - API Graph Meta v23.0
- `InstagramService` - API Graph Meta

### 5. Celery Workers

**Fichier**: `backend/app/workers/celery_app.py`

**Configuration**:
- Broker: Redis (redis://redis:6379/0)
- Backend: Redis
- Queue: `ingest` pour documents knowledge

**Tasks**:
- `process_document_task` - Ingestion et embedding de documents

**Settings**:
- `task_time_limit`: 30 min
- `worker_max_tasks_per_child`: 200

### 6. Frontend (Next.js 14)

**Structure**:
```
app/
├── auth/                  # Pages d'authentification
├── dashboard/
│   ├── activity/          # Inbox et conversations
│   ├── analytics/         # Métriques et graphes
│   ├── playground/        # Test de l'agent
│   ├── settings/          # Config AI, billing
│   └── sources/           # Documents et FAQ
└── pricing/               # Plans et tarifs

components/
├── ui/                    # Composants shadcn/ui
├── inbox-page.tsx         # Interface conversations
├── ai-studio/             # Composants config IA
└── sidebar-new.tsx        # Navigation
```

**State Management**:
- React Query pour API calls
- Zustand pour state global (sidebar, auth)

## Sécurité

### Webhooks
- Validation HMAC SHA256 obligatoire
- Secrets en variables d'environnement
- Vérification signatures Meta

### API
- JWT auth via Supabase
- Row Level Security (RLS) sur toutes les tables
- CORS configuré (localhost + production)

### Retry & Rate Limiting
- Backoff exponentiel: 0.5s → 1s → 2s
- Max 3 tentatives
- Gestion 429 (rate limit)
- Timeouts: connect 5s, read 10s, write 5s

## Observabilité

### Logs
- Format structuré avec contexte
- Niveaux: INFO, WARNING, ERROR
- Pattern: `[{PLATFORM}] {action} - {context}`

### Health Checks
- `GET /health` - Service status
- `GET /api/health` - Système complet + scanner metrics
- `GET /api/metrics` - Métriques détaillées batch scanner

## Performance

### Cache Strategy (Redis)
- **Conversations**: TTL 1h
- **Credentials**: TTL 1h
- **Profiles**: TTL 1h
- **Batches**: TTL 30 min

### Database
- Indexes sur colonnes fréquentes (user_id, social_account_id, created_at)
- pgvector pour embeddings (HNSW index)
- Partitioning planifié pour analytics_history

### Scalabilité
- Workers Celery horizontalement scalables
- Redis cluster-ready
- Supabase auto-scaling

## Limitations actuelles

1. **Pas de publication planifiée** (scheduler posts)
2. **Pas de polling commentaires** (seulement DMs)
3. **Analytics limitées** (pas d'agrégation 2h)
4. **Pas de clustering** de topics
5. **Triage basique** (pas de IGNORE/ESCALATE/AUTO_REPLY structuré)
6. **Plateformes**: WhatsApp + Instagram uniquement

---
*Architecture mise à jour: 2025-10-18*
