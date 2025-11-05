# 🚀 Installation Guide

Complete setup guide for SocialSync AI (30-45 minutes)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Clone Repository](#step-1-clone-repository)
3. [Step 2: Environment Configuration](#step-2-environment-configuration)
4. [Step 3: Supabase Setup](#step-3-supabase-setup)
5. [Step 4: Meta Developer Setup](#step-4-meta-developer-setup)
6. [Step 5: Docker Setup](#step-5-docker-setup)
7. [Step 6: Database Migrations](#step-6-database-migrations)
8. [Step 7: Verification](#step-7-verification)

---

## Prerequisites

Before starting, ensure you have:

### Required Accounts
- ✅ **Supabase Account** - [Sign up free](https://supabase.com/)
- ✅ **OpenRouter Account** - [Get API key](https://openrouter.ai/keys) OR **OpenAI Account**
- ✅ **Meta Developer Account** - [Create account](https://developers.facebook.com/)
- ✅ **Resend Account** (for emails) - [Sign up](https://resend.com/)

### Required Software
- ✅ **Docker** 20.10+ - [Install Docker](https://docs.docker.com/get-docker/)
- ✅ **Docker Compose** 2.0+ - [Install Compose](https://docs.docker.com/compose/install/)
- ✅ **Git** - [Install Git](https://git-scm.com/downloads)

### Optional (for development)
- ⚪ **Node.js** 18+ (for local frontend dev)
- ⚪ **Python** 3.10+ (for local backend dev)
- ⚪ **PostgreSQL Client** (for database access)

---

## Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yvankondjo/socialsync-ai.git
cd socialsync-ai

# Verify structure
ls -la
# You should see: backend/, frontend/, docs/, docker-compose.yml
```

---

## Step 2: Environment Configuration

### 2.1 Copy Environment Template

```bash
# Copy the example environment file
cp backend/.env.example backend/.env
```

### 2.2 Configure Environment Variables

Open `backend/.env` and configure the following variables:

#### **A. Supabase Configuration (5 variables)**

```bash
# Get these from: https://supabase.com/dashboard/project/_/settings/api

# 1. Project URL
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co

# 2. Anonymous Key (public key)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4eHh4eHh4eHh4eHh4eHh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTk5OTk5OTksImV4cCI6MjAxNTU3OTk5OX0.xxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Service Role Key (admin key - keep secret!)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4eHh4eHh4eHh4eHh4eHh4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY5OTk5OTk5OSwiZXhwIjoyMDE1NTc5OTk5fQ.xxxxxxxxxxxxxxxxxxxxxxxxxxx

# 4. JWT Secret
# Get from: https://supabase.com/dashboard/project/_/settings/api > JWT Settings
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters

# 5. Database URL
# Get from: https://supabase.com/dashboard/project/_/settings/database > Connection string > URI
SUPABASE_DB_URL=postgresql://postgres.xxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

**Where to find these values:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Settings → API → Copy the values

---

#### **B. AI/LLM Configuration (Choose ONE)**

**Option 1: OpenRouter (Recommended - Access to 100+ models)**

```bash
# Get your key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Leave OpenAI key empty if using OpenRouter
OPENAI_API_KEY=
```

**Option 2: OpenAI**

```bash
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Leave OpenRouter key empty if using OpenAI
OPENROUTER_API_KEY=
```

**Model Configuration:**

```bash
# Default model to use (options: gpt-4o, claude-3.5-sonnet, gemini-pro, etc.)
DEFAULT_AI_MODEL=gpt-4o

# Temperature (0.0 = deterministic, 1.0 = creative)
DEFAULT_AI_TEMPERATURE=0.7
```

---

#### **C. Meta Platform Configuration (Instagram + WhatsApp)**

**Get these from Meta Developer Portal (detailed steps in section 4)**

```bash
# Instagram Graph API
INSTAGRAM_CLIENT_ID=1234567890123456
INSTAGRAM_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
INSTAGRAM_WEBHOOK_SECRET=your-webhook-verification-token

# WhatsApp Business API
WHATSAPP_VERIFY_TOKEN=your-custom-verify-token
WHATSAPP_ACCESS_TOKEN=EAAG... (long token from Meta)
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789012345
```

---

#### **D. Redis Configuration**

```bash
# Redis URL (default for Docker Compose)
REDIS_URL=redis://redis:6379/0

# If using external Redis (e.g., Upstash):
# REDIS_URL=rediss://:password@redis-xxxxx.upstash.io:6379
```

---

#### **E. Email Configuration (Resend)**

```bash
# Get API key from: https://resend.com/api-keys
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Sender email (must be verified domain or use onboarding@resend.dev for testing)
FROM_EMAIL=noreply@yourdomain.com

# For development, use:
# FROM_EMAIL=onboarding@resend.dev
```

**Important:** For production, verify your domain on Resend:
1. Go to https://resend.com/domains
2. Add your domain
3. Configure DNS records (MX, TXT, DKIM)
4. Wait for verification
5. Update `FROM_EMAIL=noreply@yourdomain.com`

---

#### **F. Application Configuration**

```bash
# Environment
ENVIRONMENT=development  # or production

# Backend URL (for webhooks)
BACKEND_URL=http://localhost:8000

# Frontend URL
FRONTEND_URL=http://localhost:3000

# API Keys (generate random strings)
API_SECRET_KEY=generate-a-random-32-character-secret-key-here
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate secure secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

#### **G. Celery Worker Configuration**

```bash
# Celery broker (same as Redis)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Worker settings
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600
```

---

#### **H. Feature Toggles**

```bash
# Enable/disable features
ENABLE_INSTAGRAM_DM=true
ENABLE_WHATSAPP=true
ENABLE_COMMENT_MODERATION=true
ENABLE_SCHEDULED_POSTS=true
ENABLE_AI_STUDIO=true

# Polling intervals (seconds)
COMMENT_POLLING_INTERVAL=300  # 5 minutes
DM_POLLING_INTERVAL=0.5       # 0.5 seconds (real-time)
```

---

### 2.3 Verify Environment File

```bash
# Check all required variables are set
grep -E "^[A-Z_]+=" backend/.env | wc -l
# Should show ~30+ configured variables

# Verify no empty critical values
grep -E "^(SUPABASE_URL|SUPABASE_ANON_KEY|OPENROUTER_API_KEY|INSTAGRAM_CLIENT_ID)=$" backend/.env
# Should return nothing (all values filled)
```

---

## Step 3: Supabase Setup

### 3.1 Create Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click **New Project**
3. Fill in:
   - **Name:** SocialSync AI
   - **Database Password:** Generate a strong password (save it!)
   - **Region:** Choose closest to your users
4. Click **Create Project** (takes 1-2 minutes)

### 3.2 Enable Required Extensions

Run these SQL commands in Supabase SQL Editor:

```sql
-- Enable vector extension (for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_cron (for scheduled tasks)
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

**How to run:**
1. Dashboard → SQL Editor → New Query
2. Paste the SQL above
3. Click **Run** (or press Cmd/Ctrl + Enter)

### 3.3 Configure Storage

1. Go to **Storage** in sidebar
2. Create bucket: `social-media-uploads`
3. Bucket settings:
   - **Public:** Yes (for public post images)
   - **File size limit:** 50 MB
   - **Allowed MIME types:** `image/*`, `video/*`

### 3.4 Setup Row Level Security (RLS)

We'll apply RLS policies via migrations in Step 6. For now, verify RLS is enabled:

```sql
-- Check RLS status for main tables (run after migrations)
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

All tables should have `rowsecurity = true`.

---

## Step 4: Meta Developer Setup

### 4.1 Create Meta App

1. Go to [Meta Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** type
4. Fill in:
   - **App Name:** SocialSync AI
   - **Contact Email:** your@email.com
5. Click **Create App**

### 4.2 Add Instagram Graph API

1. In App Dashboard, click **Add Products**
2. Find **Instagram** → Click **Set Up**
3. Settings → Basic:
   - Copy **App ID** → `INSTAGRAM_CLIENT_ID`
   - Copy **App Secret** → `INSTAGRAM_CLIENT_SECRET`
4. Settings → Instagram Basic Display:
   - **Valid OAuth Redirect URIs:**
     ```
     http://localhost:3000/api/auth/instagram/callback
     https://yourdomain.com/api/auth/instagram/callback
     ```
   - **Deauthorize Callback URL:** `https://yourdomain.com/api/auth/instagram/deauthorize`
   - **Data Deletion Request URL:** `https://yourdomain.com/api/auth/instagram/delete`

### 4.3 Configure Instagram Webhooks

1. Products → Webhooks → Instagram
2. Click **Subscribe to this object**
3. **Callback URL:** `https://yourdomain.com/api/webhooks/instagram`
4. **Verify Token:** Generate random string → `INSTAGRAM_WEBHOOK_SECRET`
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Subscribe to fields:
   - ✅ `comments`
   - ✅ `messages`
   - ✅ `message_reactions`

**Important:** Webhooks require HTTPS. For local development, use [ngrok](https://ngrok.com/):
```bash
ngrok http 8000
# Use the HTTPS URL: https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

### 4.4 Add WhatsApp Business API

1. Products → Add Product → **WhatsApp**
2. Set Up → Select **Business Account**
3. Settings → WhatsApp → API Setup:
   - Copy **Phone Number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - Copy **Business Account ID** → `WHATSAPP_BUSINESS_ACCOUNT_ID`
   - Generate **Access Token** (permanent) → `WHATSAPP_ACCESS_TOKEN`

### 4.5 Configure WhatsApp Webhooks

1. Products → Webhooks → WhatsApp
2. **Callback URL:** `https://yourdomain.com/api/webhooks/whatsapp`
3. **Verify Token:** Same as Instagram or new random string → `WHATSAPP_VERIFY_TOKEN`
4. Subscribe to fields:
   - ✅ `messages`
   - ✅ `message_status`

### 4.6 Request Permissions (Production)

For production, request these permissions:
- **Instagram:** `instagram_basic`, `instagram_manage_messages`, `instagram_manage_comments`
- **WhatsApp:** `whatsapp_business_messaging`, `whatsapp_business_management`

**App Review Process:**
1. Test Mode → Development → Production
2. Submit for review with screencast demo
3. Approval takes 5-10 business days

---

## Step 5: Docker Setup

### 5.1 Verify Docker Installation

```bash
# Check Docker version
docker --version
# Should show: Docker version 20.10.0 or higher

# Check Docker Compose version
docker-compose --version
# Should show: Docker Compose version 2.0.0 or higher
```

### 5.2 Start Services

```bash
# Start all services (backend, frontend, Redis, Celery workers)
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
socialsync-backend      Up 30 seconds       0.0.0.0:8000->8000/tcp
socialsync-frontend     Up 30 seconds       0.0.0.0:3000->3000/tcp
socialsync-redis        Up 30 seconds       6379/tcp
socialsync-celery       Up 30 seconds
socialsync-celery-beat  Up 30 seconds
```

### 5.3 View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery

# Stop following logs: Ctrl+C
```

---

## Step 6: Database Migrations

### 6.1 Access Backend Container

```bash
# Enter backend container
docker-compose exec backend bash
```

### 6.2 Run Migrations

```bash
# Inside container, run migrations
python -m app.db.migrate

# You should see:
# ✅ Running migration: 001_initial_schema.sql
# ✅ Running migration: 002_add_ai_decisions.sql
# ✅ Running migration: 003_add_support_escalations.sql
# ... (25 total migrations)
# ✅ All migrations completed successfully
```

### 6.3 Verify Database Schema

```bash
# Still inside container
python -m app.db.verify

# Or manually check tables in Supabase SQL Editor:
```

```sql
-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- You should see 25 tables:
-- ai_decisions, ai_settings, analytics_daily, comments,
-- conversations, files, messages, monitoring_rules, posts,
-- scheduled_posts, social_accounts, support_escalations,
-- users, and more...
```

### 6.4 Seed Initial Data (Optional)

```bash
# Create admin user
python -m app.db.seed_admin

# Seed demo data (for testing)
python -m app.db.seed_demo
```

Exit container:
```bash
exit
```

---

## Step 7: Verification

### 7.1 Backend Health Check

```bash
# Check if backend is responding
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","redis":"connected"}
```

### 7.2 Frontend Access

Open browser and navigate to:
- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs

You should see:
- ✅ Login page (frontend)
- ✅ Interactive API documentation (Swagger UI)

### 7.3 Test Authentication

```bash
# Create a test user via API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securePassword123",
    "full_name": "Test User"
  }'

# Expected response:
# {"user_id":"uuid-here","email":"test@example.com","message":"User created"}
```

Login at http://localhost:3000 with:
- **Email:** test@example.com
- **Password:** securePassword123

### 7.4 Test Celery Workers

```bash
# Check Celery worker status
docker-compose exec celery celery -A app.workers.celery_app inspect active

# Should show:
# celery@hostname: OK
# - empty list (no active tasks yet)
```

### 7.5 Test AI Connection

Navigate to: http://localhost:3000/dashboard/settings/ai

1. Click **Test AI Connection**
2. Enter a test message: "Hello, how are you?"
3. Expected: AI response appears with confidence score

If successful:
- ✅ OpenRouter/OpenAI API key is valid
- ✅ LLM model is accessible
- ✅ RAG agent is working

---

## Next Steps

After successful installation:

1. **Connect Social Accounts**
   - Go to Dashboard → Settings → Social Accounts
   - Connect Instagram and WhatsApp
   - Authorize OAuth permissions

2. **Upload Knowledge Base**
   - Go to Dashboard → Knowledge Base
   - Upload PDFs, TXT files with FAQs
   - Wait for embeddings to process

3. **Configure AI Settings**
   - Go to Dashboard → Settings → AI
   - Set default model (gpt-4o, claude-3.5-sonnet)
   - Configure temperature (0.7 recommended)
   - Add blocked keywords/phrases

4. **Schedule Your First Post**
   - Go to Dashboard → Calendar
   - Click **Create Post**
   - Upload image, write caption
   - Select date/time
   - Click **Schedule**

5. **Test DM Automation**
   - Send a DM to your connected Instagram account
   - Check Dashboard → Inbox
   - Verify AI responds automatically

6. **Read Feature Documentation**
   - [DM Automation Guide](./features/DM_AUTOMATION.md)
   - [Comment Moderation Guide](./features/COMMENT_MODERATION.md)
   - [Scheduled Posts Guide](./features/SCHEDULED_POSTS.md)

---

## Production Deployment

**Production deployment checklist:**
- ✅ Use HTTPS (SSL certificates)
- ✅ Set `ENVIRONMENT=production`
- ✅ Use strong `API_SECRET_KEY`
- ✅ Enable database backups
- ✅ Configure monitoring (Sentry, LogRocket)
- ✅ Set up CDN for media files
- ✅ Use production Redis (Upstash, Redis Cloud)
- ✅ Verify email domain (Resend)

---

## Support

If you encounter issues not covered here:

1. **Check Logs:**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f celery
   ```

2. **Search GitHub Issues:**
   https://github.com/yvankondjo/socialsync-ai/issues

3. **Ask in Discussions:**
   https://github.com/yvankondjo/socialsync-ai/discussions

4. **Read API Documentation:**
   http://localhost:8000/docs

---

**Installation complete!** 🎉

You now have a fully functional AI-powered social media management platform running locally.
