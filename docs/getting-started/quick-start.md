# Quick Start Guide

**Get SocialSync AI running in 15 minutes.**

This guide walks you through installing and running SocialSync AI locally from the current repository contents.

---

## Table of Contents

- [What you'll accomplish](#what-youll-accomplish)
- [Prerequisites](#prerequisites)
- [Step 1: Clone the repository](#step-1-clone-the-repository)
- [Step 2: Configure environment variables](#step-2-configure-environment-variables)
- [Step 3: Install dependencies](#step-3-install-dependencies)
- [Step 4: Access the application](#step-4-access-the-application)
- [Next steps](#next-steps)
- [Troubleshooting](#troubleshooting)

---

## What you'll accomplish

After completing this guide, you'll have:
- ✅ SocialSync AI running locally on your machine
- ✅ Frontend accessible at `http://localhost:3000`
- ✅ Backend API running at `http://localhost:8000`
- ✅ A reproducible backend and frontend setup
- ✅ A clear path to start optional Redis and Celery services

**Important:** the repository does not currently ship a root `docker-compose.yml`. This guide reflects the actual, repo-backed local workflow.

---

## Prerequisites

**Required software installed on your machine:**

| Software | Minimum Version | Download |
|----------|----------------|----------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| npm | 9+ | Included with Node.js |
| Git | Any recent version | [git-scm.com](https://git-scm.com/) |

**Check if installed:**
```bash
python --version
node --version
npm --version
git --version
```

**Don't have these?** See [Prerequisites Guide](prerequisites.md) for installation instructions.

---

## Step 1: Clone the repository

Open your terminal and run:

```bash
git clone https://github.com/yvankondjo/SocialSyncAI.git
cd SocialSyncAI
```

This downloads the code and enters the project directory.

---

## Step 2: Configure environment variables

**Backend configuration:**

```bash
# Copy the example environment file
cp backend/.env.example backend/.env
```

**Frontend configuration:**

```bash
cp frontend/.env.example frontend/.env.local
```

**What these files contain:**

The `.env.example` files have placeholder values for all required configuration. The application will start with these defaults, but many features won't work until you add real credentials.

**Required for a successful backend startup:**
- `SUPABASE_URL` - Database connection
- `SUPABASE_SERVICE_ROLE_KEY` - Database admin access
- `SUPABASE_ANON_KEY` - User-scoped access
- `SUPABASE_JWT_SECRET` - Token validation

See [Environment Variables Guide](environment-variables.md) for complete configuration reference.

---

## Step 3: Install dependencies

Install backend dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
```

Install frontend dependencies:

```bash
cd frontend
npm ci
cd ..
```

Start the backend:

```bash
uvicorn app.main:app --reload --app-dir backend
```

Start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Optional local quality checks:

```bash
pytest
cd frontend && npm run lint && npm run typecheck && npm run test
```

Optional worker stack after Redis is available:

```bash
celery -A app.workers.celery_app.celery worker --workdir backend --loglevel=info
```

## Step 4: Access the application

**Open in your browser:**

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main web interface |
| **Backend API** | http://localhost:8000 | REST API server |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation (Swagger) |
| **Redoc** | http://localhost:8000/redoc | Alternative API documentation |

**Test the backend:**

```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"ok","service":"socialsyncai-api",...}`

---

## Next steps

**Your local installation is running, but needs configuration to enable features.**

### Set up the database

**1. Create a Supabase project:**

Visit [supabase.com](https://supabase.com) and create a free project. Save your credentials:
- Project URL (e.g., `https://xxxxx.supabase.co`)
- Service Role Key (Settings → API)

**2. Link your local project:**

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Link to your project
npx supabase link --project-ref <your-project-id>
```

**3. Apply database migrations:**

```bash
# Push all migrations to your Supabase project
npx supabase db push
```

This creates all required tables, indexes, and functions automatically.

**4. Update environment variables:**

Add your Supabase credentials to `backend/.env`:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

See [Configure Supabase](../configuration/supabase.md) for detailed instructions.

### Connect external services

**Required for full functionality:**

1. **[Configure Meta Platforms](../configuration/meta-platforms.md)** - Instagram, WhatsApp, Messenger
   - Create Meta Developer app
   - Set up OAuth flows
   - Configure webhooks

2. **[Configure AI Provider](../configuration/ai-providers.md)** - AI responses
   - Choose provider (OpenAI, Anthropic, Google, OpenRouter)
   - Add API key to `backend/.env`

### Test features

**Once configured, you can:**
- Connect Instagram business accounts
- Receive and respond to messages automatically
- Upload knowledge base documents
- Monitor and respond to Instagram comments
- View analytics dashboard

---

## Troubleshooting

### Missing environment variables

**Error:** `Missing required environment variables`

**Solution:** complete `backend/.env` with real Supabase values before starting FastAPI.

### Frontend lint asks to initialize ESLint

**Solution:** use the committed ESLint CLI config and run:

```bash
cd frontend
npm run lint
```

### Missing Redis

Some features degrade without Redis. You can still boot the API, but readiness will report Redis as degraded until it is reachable.

---

**Next:** [Configure Supabase](../configuration/supabase.md) to enable database and authentication.
