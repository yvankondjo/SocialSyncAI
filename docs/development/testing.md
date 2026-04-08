# Testing

Use these commands from the repository root.

## Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
pytest
```

## Frontend

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
```

## What is covered

- Backend unit tests for checkpointer behavior.
- Frontend static checks via ESLint, TypeScript, and a smoke script.
- Production build validation for the Next.js app.
