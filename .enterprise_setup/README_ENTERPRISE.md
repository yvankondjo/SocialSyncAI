# SocialSync AI - Enterprise Edition

> 🔐 **Commercial SaaS Version**
>
> For the open-source community edition, visit: [socialsync-ai](https://github.com/YOUR_USERNAME/socialsync-ai)

## Features

✨ **Full-Featured SaaS Platform:**
- 💳 **Stripe Integration** - Subscriptions, payments & billing
- 🔐 **Authentication** - Google OAuth + Supabase Auth
- 📊 **Credit System** - Usage-based billing with limits
- 💰 **Subscription Management** - Plans, trials, upgrades
- 📈 **Advanced Analytics** - Detailed insights & reports
- 🤖 **AI-Powered** - Multiple AI models (GPT-4, Claude, Gemini)
- 📱 **Social Integration** - WhatsApp & Instagram Business API
- 📅 **Content Scheduling** - Calendar-based post planning
- 💬 **Auto-Responses** - AI-powered comment & DM automation
- 🎨 **AI Studio** - Content creation assistant
- 📚 **Knowledge Base** - RAG with custom documents
- 🎯 **Smart Triage** - Automated comment filtering

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (20.10+)
- **Node.js** (18+ LTS)
- **Python** (3.12+)
- **Supabase Account** ([Production project](https://supabase.com))
- **Stripe Account** ([Dashboard access](https://stripe.com))
- **Meta Developer Account** ([App setup](https://developers.facebook.com))

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/socialsync-ai-enterprise
cd socialsync-ai-enterprise
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your production credentials
```

3. **Start services:**
```bash
docker-compose up -d
```

4. **Run database migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Create Stripe products:**
```bash
docker-compose exec backend python scripts/create_stripe_products.py
```

6. **Access the platform:**
- 🎨 Frontend: http://localhost:3000
- 🔧 Backend API: http://localhost:8000
- 📊 API Docs: http://localhost:8000/docs
- 🌸 Flower (Celery): http://localhost:5555

### Environment Variables

See `.env.example` for complete configuration guide.

**Required (Core):**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon/public key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret for auth
- `REDIS_URL` - Redis connection string
- `STRIPE_SECRET_KEY` - Stripe secret key (live mode)
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret

**Required (Social Features):**
- `META_APP_ID` - Meta/Facebook app ID
- `META_APP_SECRET` - Meta/Facebook app secret
- `META_CONFIG_ID` - WhatsApp Business config ID

**Optional (AI Features):**
- `OPENROUTER_API_KEY` - OpenRouter for AI models
- `GEMINI_API_KEY` - Google Gemini API
- `ANTHROPIC_API_KEY` - Claude API (alternative)

**Optional (Services):**
- `RESEND_API_KEY` - Email service for notifications
- `SENTRY_DSN` - Error tracking
- `LANGSMITH_API_KEY` - LLM observability

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│  Supabase   │
│  Frontend   │     │   Backend   │     │  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ├─────▶ Redis (Queue)
                           │
                           ├─────▶ Celery Workers
                           │       ├─ Comment polling
                           │       ├─ Message processing
                           │       ├─ Post scheduling
                           │       └─ Topic modeling
                           │
                           ├─────▶ Stripe API
                           │
                           └─────▶ Meta Graph API
                                   ├─ Instagram
                                   └─ WhatsApp
```

### Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn/ui
- TanStack Query
- Zustand

**Backend:**
- FastAPI
- Python 3.12
- Celery (async tasks)
- Redis (queue & cache)
- Supabase (PostgreSQL + Auth)
- pgvector (embeddings)

**AI/ML:**
- LangChain
- LangGraph
- OpenRouter (multi-model)
- BERTopic (topic modeling)
- Gemini embeddings

**Infrastructure:**
- Docker & Docker Compose
- Supabase Cloud
- Stripe
- Meta Business Platform

## Development

### Project Structure

```
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── workers/          # Celery tasks
│   │   ├── core/             # Config & auth
│   │   └── schemas/          # Pydantic models
│   ├── scripts/              # Utility scripts
│   └── tests/                # Test suite
├── frontend/
│   ├── app/                  # Next.js pages
│   │   ├── dashboard/        # Protected routes
│   │   ├── pricing/          # Public pricing
│   │   └── auth/             # Authentication
│   ├── components/           # React components
│   └── hooks/                # Custom hooks
├── supabase/
│   └── migrations/           # Database migrations
└── docker-compose.yml        # Services orchestration
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### Code Quality

```bash
# Python linting
cd backend
black app/
ruff check app/

# TypeScript linting
cd frontend
npm run lint
npm run type-check
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment guide.

### Quick Deploy Options

1. **Docker Compose** (Simple): `docker-compose -f docker-compose.prod.yml up -d`
2. **Kubernetes** (Scalable): See `infrastructure/kubernetes/`
3. **Managed Services**:
   - Frontend → Vercel
   - Backend → Railway/Render
   - Database → Supabase Cloud
   - Redis → Upstash

## Monitoring & Observability

- **Uptime**: UptimeRobot
- **Errors**: Sentry
- **Analytics**: PostHog
- **Logs**: Better Stack
- **APM**: LangSmith (AI calls)

## Support

- 📧 **Email**: support@socialsync.ai
- 💬 **Slack**: [Internal team workspace]
- 📚 **Docs**: [Internal documentation portal]
- 🐛 **Issues**: [Internal issue tracker]

## License

**Proprietary - All Rights Reserved**

This software is commercial and proprietary. Unauthorized copying, modification, or distribution is strictly prohibited.

© 2025 SocialSync AI. All rights reserved.

---

## Team Documentation

For internal team documentation, see:
- `docs/team/ONBOARDING.md` - Team onboarding guide
- `docs/team/WORKFLOWS.md` - Development workflows
- `docs/api/` - Internal API documentation
- `docs/deployment/` - Deployment runbooks

---

Built with ❤️ by the SocialSync AI team
