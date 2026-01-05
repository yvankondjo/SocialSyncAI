# Tech Stack - SocialSync AI

## Backend

### Core Framework
- **FastAPI** 0.104+ (Python 3.12)
  - Async/await native
  - OpenAPI auto-documentation
  - Pydantic validation
  - Dependency injection

### Database
- **Supabase** (PostgreSQL 15+)
  - **Extensions**:
    - `pgvector` - Embeddings vectoriels
    - `pg_trgm` - Recherche trigram
    - `unaccent` - Normalisation texte
  - **Features**:
    - Row Level Security (RLS)
    - Realtime subscriptions
    - Storage (S3-compatible)
    - Auth JWT

### Queue & Cache
- **Redis** 7+
  - Message batching (hashes + sorted sets)
  - Cache credentials/profiles (TTL 1h)
  - Celery broker + result backend
  - Pub/Sub pour webhooks

- **Celery** 5+
  - Workers background (ingest, publish, polling)
  - Beat scheduler (cron jobs)
  - Retry avec backoff exponentiel
  - Monitoring via Flower (optionnel)

### AI & Embeddings
- **LangChain** 0.1+
  - LangGraph pour agent workflows
  - Retrievers pour RAG
  - Memory management

- **OpenAI**
  - GPT-4o / GPT-4o-mini (génération)
  - `text-embedding-3-small` (embeddings 1536d)
  - tiktoken pour token counting

### HTTP & API Calls
- **httpx** 0.25+
  - Async HTTP client
  - Retry automatique
  - Timeouts configurables

### Data Validation
- **Pydantic** 2+
  - Schemas typés
  - Validation automatique
  - Serialization JSON

### Testing
- **pytest** 7+
- **pytest-asyncio**
- **httpx** test client

---

## Frontend

### Core Framework
- **Next.js** 14.2+
  - App Router (React Server Components)
  - TypeScript strict mode
  - Server Actions

### UI Components
- **shadcn/ui**
  - Radix UI primitives
  - Tailwind CSS
  - Accessible components

- **Tailwind CSS** 3+
  - Utility-first
  - Dark mode support
  - Custom design tokens

### State Management
- **React Query** (TanStack Query) v5
  - Server state management
  - Cache automatique
  - Optimistic updates
  - Infinite queries

- **Zustand** 4+
  - Global state (sidebar, auth)
  - Minimal boilerplate
  - Middleware (persist)

### Forms & Validation
- **React Hook Form** 7+
- **Zod** pour validation schemas

### Data Visualization
- **Recharts** 2+
  - Charts React natifs
  - Responsive
  - Customizable

### HTTP Client
- **Axios** / Fetch API
  - Interceptors pour auth
  - Retry logic

---

## Infrastructure

### Container & Orchestration
- **Docker** 24+
  - Multi-stage builds
  - Docker Compose pour dev
  - Health checks

### Environnement
- **Dev Container**
  - VSCode Remote Containers
  - Standardisation env dev

### CI/CD
- À définir (GitHub Actions / GitLab CI)

### Monitoring (Futur)
- **Sentry** - Error tracking
- **Prometheus** + **Grafana** - Métriques

---

## Plateformes Externes

### Social Media APIs
- **Meta Graph API** v23.0
  - WhatsApp Business API
  - Instagram Graph API
  - Webhooks avec HMAC SHA256

### Payment
- **Stripe**
  - Subscriptions
  - Webhooks
  - Customer Portal

---

## Versions & Compatibilité

```yaml
Backend:
  python: "3.12"
  fastapi: "^0.104"
  supabase: "^2.0"
  celery: "^5.3"
  redis: "^7.0"
  langchain: "^0.1"
  openai: "^1.0"

Frontend:
  node: "20 LTS"
  next: "14.2"
  react: "18"
  typescript: "5"
  tailwind: "3"

Database:
  postgresql: "15+"
  pgvector: "0.5+"

Infrastructure:
  docker: "24+"
  redis: "7+"
```

---

## Variables d'environnement

### Backend (.env)
```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# OpenAI
OPENAI_API_KEY=sk-xxx

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=xxx
WHATSAPP_ACCESS_TOKEN=xxx
WHATSAPP_VERIFY_TOKEN=xxx
WHATSAPP_APP_SECRET=xxx

# Instagram
INSTAGRAM_APP_ID=xxx
INSTAGRAM_APP_SECRET=xxx
INSTAGRAM_ACCESS_TOKEN=xxx

# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx

# Meta OAuth
META_CLIENT_ID=xxx
META_CLIENT_SECRET=xxx
META_REDIRECT_URI=https://yourapp.com/api/social-accounts/connect/whatsapp/callback
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_xxx
```

---

## Dépendances Critiques

### Backend (requirements.txt - extract)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
supabase==2.0.3
celery==5.3.4
redis==5.0.1
langchain==0.1.0
langchain-openai==0.0.2
openai==1.3.0
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
stripe==7.8.0
```

### Frontend (package.json - extract)
```json
{
  "dependencies": {
    "next": "14.2.3",
    "react": "^18",
    "react-dom": "^18",
    "@supabase/supabase-js": "^2.39.0",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.4.7",
    "react-hook-form": "^7.49.0",
    "zod": "^3.22.0",
    "recharts": "^2.10.0",
    "tailwindcss": "^3.4.0",
    "shadcn-ui": "latest"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "eslint": "^8",
    "prettier": "^3"
  }
}
```

---

## Performance Benchmarks

### Backend
- **Latency** API: < 50ms (p50), < 200ms (p95)
- **Throughput**: 1000 req/s (vertical scaling 4 vCPU)
- **Worker**: 50-100 messages/s par worker

### Database
- **Queries**: < 10ms (indexed), < 100ms (vector search)
- **Connections**: 100 pool size (pgbouncer recommandé prod)

### Cache
- **Redis**: < 1ms (get), < 5ms (pipeline)
- **Hit rate**: > 80% (credentials, profiles)

---

*Tech stack documenté: 2025-10-18*
