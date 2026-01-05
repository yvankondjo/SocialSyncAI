# Quick Start Guide

**Get SocialSync AI running in 15 minutes.**

This guide walks you through installing and running SocialSync AI on your local machine using Docker.

---

## Table of Contents

- [What you'll accomplish](#what-youll-accomplish)
- [Prerequisites](#prerequisites)
- [Step 1: Clone the repository](#step-1-clone-the-repository)
- [Step 2: Configure environment variables](#step-2-configure-environment-variables)
- [Step 3: Start services with Docker](#step-3-start-services-with-docker)
- [Step 4: Access the application](#step-4-access-the-application)
- [Next steps](#next-steps)
- [Troubleshooting](#troubleshooting)

---

## What you'll accomplish

After completing this guide, you'll have:
- ✅ SocialSync AI running locally on your machine
- ✅ Frontend accessible at `http://localhost:3000`
- ✅ Backend API running at `http://localhost:8000`
- ✅ Celery workers processing background tasks
- ✅ Redis handling message queuing

**Note:** This quick start uses minimal configuration. You'll need to configure external services (Supabase, Meta platforms) separately to enable full features.

---

## Prerequisites

**Required software installed on your machine:**

| Software | Minimum Version | Download |
|----------|----------------|----------|
| Docker | 20.10+ | [docker.com](https://www.docker.com/get-started) |
| Docker Compose | 2.0+ | Included with Docker Desktop |
| Git | Any recent version | [git-scm.com](https://git-scm.com/) |

**Check if installed:**
```bash
docker --version
docker-compose --version
git --version
```

**Don't have these?** See [Prerequisites Guide](prerequisites.md) for installation instructions.

---

## Step 1: Clone the repository

Open your terminal and run:

```bash
git clone https://github.com/YOUR_USERNAME/SocialSyncAI.git
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
# Copy the example environment file
cp frontend/.env.example frontend/.env
```

**What these files contain:**

The `.env.example` files have placeholder values for all required configuration. The application will start with these defaults, but many features won't work until you add real credentials.

**Required for basic functionality:**
- `SUPABASE_URL` - Database connection
- `SUPABASE_SERVICE_ROLE_KEY` - Database admin access
- `REDIS_URL` - Message queue connection

See [Environment Variables Guide](environment-variables.md) for complete configuration reference.

---

## Step 3: Start services with Docker

**Start all services:**

```bash
docker-compose up --build
```

**What this command does:**
1. Builds Docker images for backend, frontend, and workers
2. Starts PostgreSQL, Redis, and all application services
3. Connects everything together on a shared network

**First run takes 5-10 minutes** to download images and install dependencies.

**You'll see logs from multiple services:**
- `backend_1` - FastAPI server logs
- `frontend_1` - Next.js build and server logs
- `celery_1` - Celery worker logs
- `redis_1` - Redis server logs

**Run in background (detached mode):**

```bash
docker-compose up -d
```

**View logs:**

```bash
docker-compose logs -f
```

---

## Step 4: Access the application

**Wait for startup:** Look for these messages in logs:
- ✅ `frontend_1` - "Ready on http://localhost:3000"
- ✅ `backend_1` - "Application startup complete"
- ✅ `celery_1` - "celery@worker ready"

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

Expected response: `{"status":"healthy"}`

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

### Port conflicts

**Error:** `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:** Another service is using port 3000, 8000, or 6379.

Stop the conflicting service or change ports in `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "3001:3000"  # Changed from 3000:3000
```

### Docker daemon not running

**Error:** `Cannot connect to the Docker daemon`

**Solution:** Start Docker Desktop or Docker service:

**macOS/Windows:** Open Docker Desktop application

**Linux:**
```bash
sudo systemctl start docker
```

### Build failures

**Error:** `failed to solve with frontend dockerfile.v0`

**Solution:** Ensure Docker has enough resources:

1. Open Docker Desktop → Settings → Resources
2. Increase Memory to at least 4GB
3. Increase Disk to at least 20GB
4. Click "Apply & Restart"

### Missing dependencies

**Error:** `Module not found: Can't resolve 'package-name'`

**Solution:** Rebuild with no cache:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Check service status

**List running containers:**

```bash
docker-compose ps
```

**View logs for specific service:**

```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery
```

**Restart a specific service:**

```bash
docker-compose restart backend
```

---

## Stopping the application

**Stop all services:**

```bash
docker-compose down
```

**Stop and remove volumes (warning: deletes data):**

```bash
docker-compose down -v
```

---

**Next:** [Configure Supabase](../configuration/supabase.md) to enable database and authentication.
