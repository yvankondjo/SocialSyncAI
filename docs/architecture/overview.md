# System Overview

**High-level architecture and design decisions for SocialSync AI.**

This guide explains how SocialSync AI components work together to automate social media customer support.

---

## Table of Contents

- [Architecture diagram](#architecture-diagram)
- [Core components](#core-components)
- [Data flow](#data-flow)
- [Technology stack](#technology-stack)
- [Design principles](#design-principles)
- [Scalability](#scalability)

---

## Architecture diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Services                         │
├─────────────┬─────────────┬─────────────┬─────────────┬────────┤
│  Instagram  │  WhatsApp   │  Messenger  │   Stripe    │  AI    │
│   Webhook   │   Webhook   │   Webhook   │   Webhook   │  APIs  │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴───┬────┘
       │             │             │             │          │
       └─────────────┴─────────────┴─────────────┘          │
                     │                                      │
              ┌──────▼──────┐                              │
              │   FastAPI   │◄─────────────────────────────┘
              │   Backend   │
              │  (Port 8000)│
              └──────┬──────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼───┐   ┌───▼───┐   ┌───▼────┐
    │ Redis │   │Celery │   │Supabase│
    │Message│   │Workers│   │Postgres│
    │ Queue │   │  +    │   │   +    │
    │       │   │ Beat  │   │  Auth  │
    └───────┘   └───┬───┘   └────────┘
                    │
              ┌─────┴─────┐
              │           │
         ┌────▼────┐ ┌───▼────┐
         │  RAG    │ │Message │
         │ Agent   │ │Polling │
         │LangGraph│ │ Tasks  │
         └─────────┘ └────────┘
                     
         ┌───────────────┐
         │   Next.js     │
         │   Frontend    │
         │  (Port 3000)  │
         └───────────────┘
              │
         ┌────▼────┐
         │ Users   │
         │Browsers │
         └─────────┘
```

---

## Core components

### Frontend (Next.js 14)

**User interface for managing social media automation.**

**Technology:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS + shadcn/ui components
- Supabase Auth for authentication

**Key features:**
- Unified inbox for all platforms (Chat & Comments)
- Knowledge base management (Documents & FAQs)
- AI automation settings
- Analytics dashboard
- Connect social accounts

**Port:** 3000

### Backend (FastAPI)

**REST API server handling all business logic.**

**Technology:**
- FastAPI (Python async framework)
- Pydantic for request/response validation
- JWT authentication via Supabase
- CORS enabled for frontend communication

**Key responsibilities:**
- OAuth flows for Instagram, WhatsApp, Messenger
- Webhook verification and processing
- Database operations (CRUD)
- AI agent orchestration
- Stripe payment processing

**Port:** 8000

**API documentation:** Available at `/docs` (Swagger) and `/redoc`

### Database (Supabase / PostgreSQL)

**Primary data store for all application data.**

**Technology:**
- PostgreSQL 15+ via Supabase
- Row Level Security (RLS) for multi-tenancy
- pgvector extension for embeddings
- Real-time subscriptions (optional)

**Stores:**
- User accounts and profiles
- Social account connections
- Conversations and messages
- Knowledge base documents and embeddings
- FAQ questions and answers
- Monitored posts and comments
- AI decisions and settings
- User credits and subscriptions

See [Database Schema](database-schema.md) for complete table structure.

### Message Queue (Redis)

**Distributed task queue broker for asynchronous processing.**

**Technology:**
- Redis 7+
- Used by Celery for task distribution

**Purpose:**
- Queue background tasks
- Distribute work across multiple Celery workers
- Cache frequently accessed data
- Store temporary session data

**Port:** 6379

### Workers (Celery + Beat)

**Background task processors for long-running operations.**

**Technology:**
- Celery (distributed task queue)
- Celery Beat (task scheduler)
- Multiple queues for priority management

**Task types:**

**Periodic tasks (Celery Beat):**
- Poll comments on monitored posts (every 5 minutes)
- Update topic models (daily at 2 AM)
- Refresh Instagram tokens (as needed)

**On-demand tasks:**
- Process incoming messages with AI
- Send outgoing messages
- Monitor comments on posts
- Generate embeddings for knowledge base
- Send email notifications

**Queues:**
- `high` - Real-time message processing
- `default` - Standard background tasks
- `low` - Analytics and non-urgent work

### AI Layer (LangChain + LangGraph)

**AI agent orchestration for automated responses.**

**Technology:**
- LangChain for LLM interactions
- LangGraph for agentic workflows
- Multiple provider support (OpenAI, Anthropic, Google, OpenRouter)

**Components:**

**RAG Agent:**
- Retrieves relevant documents from knowledge base
- Generates context-aware responses
- Scores confidence for escalation decisions

**Vector Search:**
- PostgreSQL pgvector for similarity search
- Embeddings generated via Google Gemini or OpenAI
- Semantic search for FAQ and documents

**Workflow:**
1. Receive message from webhook
2. Search knowledge base for relevant context
3. Generate response with LLM
4. Calculate confidence score
5. If confidence < threshold → Escalate to human
6. If confidence ≥ threshold → Send automated response

---

## Data flow

### Message receipt flow

**When a user sends a message on Instagram, WhatsApp, or Messenger:**

```
1. User sends message
   ↓
2. Meta delivers webhook POST to /api/{platform}/webhook
   ↓
3. Backend verifies webhook signature
   ↓
4. Backend queues Celery task: process_message(message_id)
   ↓
5. Backend responds HTTP 200 to Meta (< 20 seconds required)
   ↓
6. Celery worker picks up task from queue
   ↓
7. Worker fetches message details from Meta API
   ↓
8. Worker saves message to database
   ↓
9. If AI mode enabled:
   ├─ Worker invokes RAG agent
   ├─ Agent searches knowledge base
   ├─ Agent generates response
   ├─ If confidence < 80%:
   │  └─ Create escalation → Email support team
   └─ If confidence ≥ 80%:
      └─ Send automated response via Meta API
   ↓
10. Worker updates message status in database
```

### Knowledge base ingestion flow

**When a user uploads a document:**

```
1. User uploads PDF/text via frontend
   ↓
2. Frontend sends file to backend
   ↓
3. Backend validates file (size, type)
   ↓
4. Backend extracts text content
   ↓
5. Backend splits text into chunks (500 tokens each)
   ↓
6. Backend queues Celery task: generate_embeddings(doc_id)
   ↓
7. Celery worker generates embeddings for each chunk
   ↓
8. Worker stores embeddings in PostgreSQL (pgvector)
   ↓
9. Document marked as processed
```

### Comment monitoring flow

**When monitoring Instagram comments:**

```
1. User imports post or enables monitoring
   ↓
2. Post saved to monitored_posts table
   ↓
3. Celery Beat polls comments every 5 minutes
   ↓
4. Worker fetches new comments via Instagram API
   ↓
5. For each comment:
   ├─ Comment triage service evaluates if AI should respond
   ├─ If respond: Generate AI reply
   ├─ If ignore: Skip (user-to-user conversation)
   └─ If escalate: Flag for human review
   ↓
6. Worker posts AI replies via Instagram API
```

---

## Technology stack

### Frontend

| Technology | Purpose | Version |
|------------|---------|---------|
| Next.js | React framework | 14 |
| TypeScript | Type safety | 5+ |
| Tailwind CSS | Styling | 3+ |
| shadcn/ui | Component library | Latest |
| Supabase JS | Database + Auth client | 2+ |
| Zustand | State management | 4+ |
| React Query | Server state | 5+ |

### Backend

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Programming language | 3.12+ |
| FastAPI | Web framework | 0.100+ |
| Pydantic | Data validation | 2+ |
| Celery | Task queue | 5+ |
| Redis | Message broker | 7+ |
| LangChain | LLM orchestration | Latest |
| LangGraph | Agent workflows | Latest |
| httpx | Async HTTP client | Latest |

### Database

| Technology | Purpose | Version |
|------------|---------|---------|
| PostgreSQL | Relational database | 15+ |
| pgvector | Vector similarity search | 0.5+ |
| Supabase | Database hosting + Auth | Latest |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| nginx | Reverse proxy (production) |

---

## Design principles

### 1. Separation of concerns

**Each component has a single responsibility:**
- Frontend: UI and user interactions only
- Backend: Business logic and API endpoints
- Workers: Background processing
- Database: Data persistence

**Benefits:**
- Easier to debug and test
- Can scale components independently
- Team members can work on different components simultaneously

### 2. Event-driven architecture

**Webhooks trigger asynchronous processing:**
- Webhooks return immediately (HTTP 200)
- Actual processing happens in background
- No blocking operations in request handlers

**Benefits:**
- Fast webhook responses (< 100ms)
- Can handle high webhook volume
- Retry failed operations automatically

### 3. Multi-tenancy

**Every user's data is isolated:**
- Row Level Security (RLS) in PostgreSQL
- User ID required for all database queries
- JWT tokens contain user ID for authentication

**Benefits:**
- Security by default
- Single database for all users
- Efficient resource utilization

### 4. AI-first design

**AI is integrated at every level:**
- Automated message responses
- Smart escalation decisions
- Content generation assistance
- Analytics insights

**Benefits:**
- Reduces manual workload
- Scales customer support
- Improves response quality

### 5. API-driven

**Everything accessible via REST API:**
- Frontend uses API for all operations
- Third-party integrations possible
- Mobile apps can use same API

**Benefits:**
- Consistent interface
- Easy to add new clients
- API documentation auto-generated

---

## Scalability

### Horizontal scaling

**Components that scale horizontally:**

**Celery Workers:**
- Add more worker processes to handle increased load
- Each worker processes tasks independently
- No coordination required between workers

**Command:**
```bash
docker-compose up --scale celery=5
```

**Backend API:**
- Deploy multiple FastAPI instances behind load balancer
- Each instance is stateless
- Share same database and Redis

**Redis:**
- Use Redis Cluster for distributed caching
- Sentinel for high availability
- Master-replica for read scaling

### Vertical scaling

**Database (PostgreSQL):**
- Increase CPU and RAM for better query performance
- Add read replicas for read-heavy workloads
- Use connection pooling (built into Supabase)

**Supabase Pro plan:**
- 8GB RAM, 4 CPU cores
- Connection pooling included
- Automatic backups

### Performance optimizations

**Database:**
- Indexes on frequently queried columns
- Partitioning for large tables (messages, analytics)
- Materialized views for complex aggregations

**Caching:**
- Redis cache for frequently accessed data
- Cache user sessions
- Cache AI model responses for common questions

**Background processing:**
- Priority queues (high, default, low)
- Rate limiting for external API calls
- Batch processing for bulk operations

**Monitoring:**
- LangSmith for AI agent tracing
- Celery Flower for worker monitoring
- PostgreSQL slow query log

---

**Next:** [Database Schema](database-schema.md) for complete table structure.
