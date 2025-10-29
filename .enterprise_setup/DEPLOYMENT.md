# Deployment Guide - Enterprise Edition

This guide covers production deployment of SocialSync AI Enterprise Edition.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Options](#deployment-options)
4. [CI/CD Setup](#cicd-setup)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling](#scaling)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Infrastructure Requirements

**Minimum Specs (Small Team <100 users):**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- Bandwidth: 100 Mbps

**Recommended Specs (Growing <1000 users):**
- CPU: 8 cores
- RAM: 16 GB
- Storage: 200 GB SSD
- Bandwidth: 1 Gbps

**High Scale (1000+ users):**
- Multi-node cluster (Kubernetes)
- Auto-scaling enabled
- CDN for static assets
- Redis Cluster for high availability

### External Services

1. **Supabase** (Database + Auth)
   - Production project created
   - PostgreSQL with pgvector extension
   - RLS policies configured
   - Storage buckets created

2. **Stripe** (Payments)
   - Live mode configured
   - Webhooks endpoint configured
   - Products & prices created
   - Test mode for staging

3. **Meta Platform** (Social APIs)
   - App in production mode
   - WhatsApp Business API approved
   - Instagram Basic Display approved
   - Webhooks configured

4. **Domain & SSL**
   - Domain purchased (e.g., socialsync.ai)
   - SSL certificates (Let's Encrypt or Cloudflare)
   - DNS configured

5. **Email Service**
   - Resend account (or SendGrid/Postmark)
   - Domain verified
   - SPF/DKIM configured

---

## Pre-Deployment Checklist

### Security

- [ ] All secrets stored in secure vault (not in .env files)
- [ ] 2FA enabled for all admin accounts
- [ ] API keys rotated from development
- [ ] Database backups configured
- [ ] RLS policies tested and verified
- [ ] Rate limiting configured
- [ ] CORS configured for production domains only
- [ ] Webhook signatures verified
- [ ] SQL injection protection verified
- [ ] XSS protection enabled

### Configuration

- [ ] Production .env file complete
- [ ] Supabase project in production mode
- [ ] Stripe in live mode (not test mode)
- [ ] Meta app in production mode
- [ ] Redis persistence enabled
- [ ] Celery workers configured
- [ ] Docker images built and tagged
- [ ] Health checks configured
- [ ] Logging configured
- [ ] Monitoring dashboards setup

### Testing

- [ ] All tests passing (`pytest backend/tests/`)
- [ ] E2E tests passing
- [ ] Load tests completed
- [ ] Security scan completed
- [ ] Penetration testing done (if required)
- [ ] Stripe test transactions successful
- [ ] Social OAuth flows tested
- [ ] Email notifications tested

---

## Deployment Options

### Option 1: Docker Compose (Simplest)

**Best for**: Small teams, single-server deployments

**Steps:**

1. **Clone repository on server:**
```bash
ssh user@your-server.com
git clone https://github.com/YOUR_USERNAME/socialsync-ai-enterprise
cd socialsync-ai-enterprise
```

2. **Configure environment:**
```bash
cp .env.example .env
nano .env  # Edit with production values
```

3. **Setup SSL (using Caddy or nginx):**
```bash
# Install Caddy
curl https://getcaddy.com | bash -s personal

# Configure Caddy
cat > Caddyfile <<EOF
socialsync.ai {
    reverse_proxy localhost:3000
}

api.socialsync.ai {
    reverse_proxy localhost:8000
}
EOF

# Start Caddy
caddy start
```

4. **Start services:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

5. **Run migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

6. **Create Stripe products:**
```bash
docker-compose exec backend python scripts/create_stripe_products.py
```

7. **Verify deployment:**
```bash
curl https://api.socialsync.ai/health
curl https://socialsync.ai
```

**docker-compose.prod.yml example:**
```yaml
version: '3.8'

services:
  frontend:
    image: your-registry/socialsync-frontend:latest
    restart: always
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    ports:
      - "3000:3000"

  backend:
    image: your-registry/socialsync-backend:latest
    restart: always
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery_worker:
    image: your-registry/socialsync-backend:latest
    restart: always
    env_file: .env
    command: celery -A app.workers.celery_app worker -l info
    depends_on:
      - redis

  celery_beat:
    image: your-registry/socialsync-backend:latest
    restart: always
    env_file: .env
    command: celery -A app.workers.celery_app beat -l info
    depends_on:
      - redis

  flower:
    image: your-registry/socialsync-backend:latest
    restart: always
    env_file: .env
    command: celery -A app.workers.celery_app flower
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  redis_data:
```

---

### Option 2: Kubernetes (Scalable)

**Best for**: High availability, auto-scaling, multi-region

**Prerequisites:**
- Kubernetes cluster (GKE, EKS, AKS, or self-managed)
- kubectl configured
- Helm 3 installed

**Steps:**

1. **Create namespace:**
```bash
kubectl create namespace socialsync-prod
```

2. **Create secrets:**
```bash
kubectl create secret generic socialsync-secrets \
  --from-file=.env \
  --namespace=socialsync-prod
```

3. **Deploy with Helm:**
```bash
helm install socialsync ./infrastructure/helm/socialsync \
  --namespace socialsync-prod \
  --values ./infrastructure/helm/values.prod.yaml
```

4. **Verify deployment:**
```bash
kubectl get pods -n socialsync-prod
kubectl get services -n socialsync-prod
```

See `infrastructure/kubernetes/` for detailed manifests.

---

### Option 3: Managed Services (Easiest)

**Best for**: Quick deployment, minimal DevOps

**Architecture:**
- Frontend → **Vercel**
- Backend → **Railway** or **Render**
- Database → **Supabase Cloud**
- Redis → **Upstash**
- Storage → **Supabase Storage**

**Steps:**

1. **Deploy Frontend to Vercel:**
```bash
cd frontend
vercel --prod
```

Configure environment variables in Vercel dashboard.

2. **Deploy Backend to Railway:**
```bash
railway login
railway init
railway up
```

Add environment variables in Railway dashboard.

3. **Configure domains:**
- Frontend: `socialsync.ai` → Vercel
- Backend: `api.socialsync.ai` → Railway

---

## CI/CD Setup

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Production

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker build -t socialsync/backend:${{ github.ref_name }} ./backend
          docker build -t socialsync/frontend:${{ github.ref_name }} ./frontend

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push socialsync/backend:${{ github.ref_name }}
          docker push socialsync/frontend:${{ github.ref_name }}

      - name: Deploy to production
        run: |
          ssh ${{ secrets.PROD_SERVER }} "cd /app && docker-compose pull && docker-compose up -d"
```

**Required Secrets:**
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `PROD_SERVER` (SSH connection string)
- All production environment variables

---

## Monitoring & Alerts

### Health Checks

Configure uptime monitoring:
- **UptimeRobot**: https://uptimerobot.com
- **Pingdom**: https://www.pingdom.com

Monitor endpoints:
- `https://api.socialsync.ai/health` (every 5 min)
- `https://socialsync.ai` (every 5 min)

### Error Tracking

**Sentry Setup:**
```bash
# Add to .env
SENTRY_DSN=https://xxx@sentry.io/xxx

# Sentry will automatically capture:
# - Backend exceptions (FastAPI)
# - Frontend errors (Next.js)
# - Celery task failures
```

### Application Metrics

**LangSmith (AI Observability):**
```bash
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=socialsync-prod
```

Monitors:
- AI response times
- Model performance
- Token usage
- Error rates

### Infrastructure Metrics

**Prometheus + Grafana:**
```bash
# Deploy monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
```

Dashboards for:
- CPU/Memory usage
- Request rates
- Response times
- Queue sizes
- Database connections

---

## Backup & Recovery

### Database Backups

**Supabase** (automatic):
- Daily snapshots (retained 7 days)
- Point-in-time recovery (last 7 days)

**Manual backup:**
```bash
pg_dump postgresql://user:pass@db.project.supabase.co:5432/postgres > backup.sql
```

### Redis Backups

Configure persistence in `redis.conf`:
```
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
```

### File Storage

Supabase Storage is automatically backed up.

Manual backup:
```bash
# Export all files
supabase storage export bucket_name ./backup/
```

### Disaster Recovery Plan

1. **Database failure:**
   - Restore from latest Supabase snapshot
   - Verify data integrity
   - Reconfigure application

2. **Server failure:**
   - Spin up new server
   - Clone repository
   - Restore .env from vault
   - Start services

3. **Complete failure:**
   - Deploy to new infrastructure
   - Restore database backup
   - Restore Redis persistence
   - Verify all services

**Recovery Time Objective (RTO)**: < 1 hour
**Recovery Point Objective (RPO)**: < 1 day

---

## Scaling

### Horizontal Scaling

**Add more workers:**
```bash
docker-compose up -d --scale celery_worker=5
```

**Load balance backend:**
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Vertical Scaling

**Increase resources:**
```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### Database Scaling

**Supabase Pro:**
- Read replicas
- Connection pooling
- Larger instance types

### Caching Strategy

**Redis caching layers:**
1. API response cache (5 min TTL)
2. Database query cache (1 hour TTL)
3. AI model embeddings cache (24 hour TTL)

---

## Troubleshooting

### Common Issues

**1. 502 Bad Gateway**
- Check backend container: `docker logs backend`
- Verify backend is listening: `curl localhost:8000/health`
- Check reverse proxy config

**2. Stripe webhooks failing**
- Verify webhook secret matches
- Check HTTPS is configured
- Ensure POST endpoint is accessible

**3. Celery tasks not running**
- Check Redis connection: `redis-cli ping`
- Verify Celery workers: `docker logs celery_worker`
- Check Celery Beat: `docker logs celery_beat`

**4. Database connection errors**
- Verify Supabase credentials
- Check connection pool limits
- Ensure pgvector extension is enabled

**5. AI API rate limits**
- Check API key quotas
- Implement exponential backoff
- Use multiple API keys rotation

### Debug Commands

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Access backend shell
docker-compose exec backend bash

# Check database
docker-compose exec backend python
>>> from app.db.session import get_db
>>> db = get_db()
>>> db.table('users').select('*').execute()

# Test Stripe connection
docker-compose exec backend python scripts/test_stripe.py

# Test social API
docker-compose exec backend python scripts/test_instagram.py
```

---

## Support

For deployment assistance:
- 📧 devops@socialsync.ai
- 💬 #deployment Slack channel
- 📚 Internal wiki: https://wiki.socialsync.ai

---

## Appendix

### Environment Variables Reference

See `.env.example` for complete list.

### Firewall Rules

Required ports:
- `80` (HTTP)
- `443` (HTTPS)
- `22` (SSH - restrict to trusted IPs)

Internal:
- `6379` (Redis - internal only)
- `5432` (PostgreSQL - internal only)

### SSL Certificate Renewal

With Let's Encrypt (auto-renew):
```bash
certbot renew --dry-run
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```
