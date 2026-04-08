# Local Setup

## Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
uvicorn app.main:app --reload --app-dir backend
```

Fill `backend/.env` with real Supabase credentials before starting the API.

## Frontend

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

## Optional services

- Redis improves readiness and background processing.
- Celery workers can be started with `celery -A app.workers.celery_app.celery worker --workdir backend --loglevel=info`.
