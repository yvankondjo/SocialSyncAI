# Environment Variables

**Complete reference for all configuration variables in SocialSync AI.**

This page documents every environment variable used by the backend and frontend.

---

## Table of Contents

- [How to use this guide](#how-to-use-this-guide)
- [Backend variables](#backend-variables)
  - [Supabase (Required)](#supabase-required)
  - [Meta Platforms (Required for social features)](#meta-platforms-required-for-social-features)
  - [Redis (Required)](#redis-required)
  - [AI Providers (At least one required)](#ai-providers-at-least-one-required)
  - [Stripe (Optional)](#stripe-optional)
  - [Email (Optional)](#email-optional)
  - [Observability (Optional)](#observability-optional)
  - [Application settings](#application-settings)
- [Frontend variables](#frontend-variables)
- [Required vs Optional](#required-vs-optional)
- [Getting credentials](#getting-credentials)

---

## How to use this guide

**Each variable includes:**
- **Description** - What it does
- **Required/Optional** - Whether you must set it
- **Example value** - How to format it
- **Where to get it** - Link to configuration guide

**Variables are grouped by service** to make it easier to configure one service at a time.

**Set variables in these files:**
- Backend: `backend/.env` (copy from `backend/.env.example`)
- Frontend: `frontend/.env` (copy from `frontend/.env.example`)

---

## Backend variables

### Supabase (Required)

**Supabase provides PostgreSQL database and JWT authentication.**

All four variables are required for the application to start.

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | **Your Supabase project URL.** Found in Project Settings → API. | `https://abcdefgh.supabase.co` |
| `SUPABASE_ANON_KEY` | **Public anonymous key for client-side requests.** Found in Project Settings → API. | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_SERVICE_ROLE_KEY` | **Server-side key with admin privileges.** **Keep secret.** Found in Project Settings → API. | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_JWT_SECRET` | **Secret used to verify JWT tokens.** Found in Project Settings → API → JWT Settings. | `your-super-secret-jwt-token-with-at-least-32-characters-long` |

**Optional database connection variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_DB_URL` | Direct PostgreSQL connection string. Only needed for migrations. | `postgresql://postgres.abc:pass@host.supabase.com:5432/postgres` |
| `SUPABASE_DB_HOST` | Database hostname. | `db.abcdefgh.supabase.co` |
| `SUPABASE_DB_PORT` | Database port. | `5432` |
| `SUPABASE_DB_NAME` | Database name. | `postgres` |
| `SUPABASE_DB_USER` | Database user. | `postgres.abcdefgh` |
| `SUPABASE_DB_PASSWORD` | Database password. | `your_database_password` |

**Setup guide:** [Supabase Configuration](../configuration/supabase.md)

---

### Meta Platforms (Required for social features)

**Meta Developer App credentials enable Instagram, WhatsApp, and Messenger integrations.**

#### Meta App (Required for all Meta integrations)

| Variable | Description | Example |
|----------|-------------|---------|
| `META_APP_ID` | **Your Meta app ID.** Found in Meta Developer Dashboard → App Settings → Basic. | `1234567890123456` |
| `META_APP_SECRET` | **Your Meta app secret.** **Keep secret.** Found in App Settings → Basic → Show button. | `abcdef1234567890abcdef1234567890` |
| `META_GRAPH_VERSION` | Meta Graph API version to use. | `v21.0` |
| `META_CONFIG_ID` | WhatsApp configuration ID for Embedded Signup. Only needed for WhatsApp. | `1234567890` |

#### Instagram

| Variable | Description | Example |
|----------|-------------|---------|
| `INSTAGRAM_CLIENT_ID` | Instagram app client ID. Usually same as `META_APP_ID`. | `1234567890123456` |
| `INSTAGRAM_CLIENT_SECRET` | Instagram app secret. Usually same as `META_APP_SECRET`. | `abcdef1234567890abcdef1234567890` |
| `INSTAGRAM_REDIRECT_URI` | OAuth callback URL. Must match exactly in Meta Developer settings. | `https://yourdomain.com/api/social-accounts/connect/instagram/callback` |
| `INSTAGRAM_VERIFY_TOKEN` | **Random string you create** for webhook verification. Choose any secure random string. | `my_secure_verify_token_12345` |

#### WhatsApp

| Variable | Description | Example |
|----------|-------------|---------|
| `WHATSAPP_REDIRECT_URI` | OAuth callback URL for WhatsApp. Must match in Meta Developer settings. | `https://yourdomain.com/api/social-accounts/connect/whatsapp/callback` |
| `WHATSAPP_VERIFY_TOKEN` | **Random string you create** for webhook verification. | `my_whatsapp_verify_token_67890` |
| `WHATSAPP_WEBHOOK_SECRET` | **Optional.** Webhook signature verification secret. | `your_webhook_secret` |

#### Messenger

| Variable | Description | Example |
|----------|-------------|---------|
| `MESSENGER_VERIFY_TOKEN` | **Random string you create** for webhook verification. | `my_messenger_verify_token_abcde` |

**Setup guide:** [Meta Platforms Configuration](../configuration/meta-platforms.md)

---

### Redis (Required)

**Redis provides message queuing for Celery background workers.**

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | **Redis connection URL.** Uses `redis:6379` when running in Docker. | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery message broker URL. Usually same as `REDIS_URL`. | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result storage URL. Usually same as `REDIS_URL`. | `redis://redis:6379/0` |

**For local development without Docker:**
- Change `redis://redis:6379/0` to `redis://localhost:6379/0`
- Ensure Redis server is running on your machine

---

### AI Providers (At least one required)

**Choose at least one AI provider for automated responses.**

#### OpenRouter (Recommended)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | **OpenRouter API key.** Get from [openrouter.ai/keys](https://openrouter.ai/keys). Provides access to 100+ models. | `sk-or-v1-abc123...` |

#### OpenAI

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | **OpenAI API key.** Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys). | `sk-proj-abc123...` |

#### Anthropic

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | **Anthropic API key.** Get from [console.anthropic.com](https://console.anthropic.com). | `sk-ant-abc123...` |

#### Google Gemini

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | **Google AI API key.** Get from [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey). | `AIzaSyAbc123...` |
| `GEMINI_BASE_URL` | Gemini API base URL. Leave as default. | `https://generativelanguage.googleapis.com/v1beta/openai/` |

**Setup guide:** [AI Providers Configuration](../configuration/ai-providers.md)

---

### Stripe (Optional)

**Stripe enables payment processing and user billing.**

Only needed if you plan to charge users for your service.

| Variable | Description | Example |
|----------|-------------|---------|
| `STRIPE_SECRET_KEY` | **Server-side Stripe secret key.** **Keep secret.** Get from Stripe Dashboard → Developers → API keys. Use `sk_test_` for testing. | `sk_test_abc123...` |
| `STRIPE_PUBLISHABLE_KEY` | Client-side publishable key. Get from Stripe Dashboard → Developers → API keys. | `pk_test_abc123...` |
| `STRIPE_WEBHOOK_SECRET` | **Webhook signature secret.** Get from Stripe Dashboard → Developers → Webhooks after adding endpoint. | `whsec_abc123...` |

**Setup guide:** [Stripe Configuration](../configuration/stripe.md)

---

### Email (Optional)

**Email service for sending notifications and escalation alerts.**

| Variable | Description | Example |
|----------|-------------|---------|
| `RESEND_API_KEY` | **Resend API key.** Get from [resend.com/api-keys](https://resend.com/api-keys). | `re_abc123...` |
| `FROM_EMAIL` | Email address that appears as sender. Must be verified in Resend. | `noreply@yourdomain.com` |

---

### Observability (Optional)

**LangSmith provides tracing and debugging for AI agent interactions.**

| Variable | Description | Example |
|----------|-------------|---------|
| `LANGSMITH_TRACING` | Enable/disable LangSmith tracing. | `true` or `false` |
| `LANGSMITH_ENDPOINT` | LangSmith API endpoint. Leave as default. | `https://api.smith.langchain.com` |
| `LANGSMITH_API_KEY` | **LangSmith API key.** Get from [smith.langchain.com/settings](https://smith.langchain.com/settings). | `ls__abc123...` |
| `LANGSMITH_PROJECT` | Project name for organizing traces. | `socialsync-production` |

---

### Application settings

| Variable | Description | Example |
|----------|-------------|---------|
| `BACKEND_URL` | **Backend API URL.** Used for OAuth callbacks. Set to your production domain or `http://localhost:8000` for local. | `https://api.yourdomain.com` |
| `FRONTEND_URL` | **Frontend URL.** Used for redirects after OAuth. | `https://yourdomain.com` |
| `FLOWER_BASIC_AUTH` | **Username:password for Celery Flower monitoring UI.** Format: `username:password`. | `admin:securepass123` |

---

## Frontend variables

**Frontend uses fewer variables than backend.**

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | **Supabase project URL.** Must match backend `SUPABASE_URL`. | `https://abcdefgh.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **Supabase anonymous key.** Must match backend `SUPABASE_ANON_KEY`. | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `NEXT_PUBLIC_API_URL` | **Backend API URL.** Points to FastAPI server. | `http://localhost:8000` (local) or `https://api.yourdomain.com` (production) |
| `NEXT_PUBLIC_FRONTEND_URL` | **Frontend URL.** Used for OAuth redirects. | `http://localhost:3000` (local) or `https://yourdomain.com` (production) |
| `NEXT_PUBLIC_USE_DEMO` | **Enable demo mode.** Shows fake data without real API calls. | `false` (default) or `true` |

**Note:** Variables starting with `NEXT_PUBLIC_` are exposed to the browser. Never put secrets in these variables.

---

## Required vs Optional

**Minimum required variables to start the application:**

### Backend (8 required)
1. ✅ `SUPABASE_URL`
2. ✅ `SUPABASE_ANON_KEY`
3. ✅ `SUPABASE_SERVICE_ROLE_KEY`
4. ✅ `SUPABASE_JWT_SECRET`
5. ✅ `REDIS_URL`
6. ✅ `CELERY_BROKER_URL`
7. ✅ `META_APP_ID`
8. ✅ `META_APP_SECRET`

**Plus at least one AI provider:**
- ✅ `OPENROUTER_API_KEY` **OR**
- ✅ `OPENAI_API_KEY` **OR**
- ✅ `ANTHROPIC_API_KEY` **OR**
- ✅ `GEMINI_API_KEY`

### Frontend (3 required)
1. ✅ `NEXT_PUBLIC_SUPABASE_URL`
2. ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. ✅ `NEXT_PUBLIC_API_URL`

**Everything else is optional** and enables specific features.

---

## Getting credentials

**Where to find each credential:**

| Service | Get Credentials From | Setup Time |
|---------|---------------------|------------|
| Supabase | [Supabase Configuration](../configuration/supabase.md) | 5 minutes |
| Meta Platforms | [Meta Platforms Configuration](../configuration/meta-platforms.md) | 15 minutes |
| OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | 2 minutes |
| OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | 2 minutes |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | 2 minutes |
| Google Gemini | [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey) | 2 minutes |
| Stripe | [Stripe Configuration](../configuration/stripe.md) | 10 minutes |

---

**Next:** Follow the configuration guides to obtain each credential.
