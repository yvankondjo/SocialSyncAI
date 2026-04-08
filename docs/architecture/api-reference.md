# API Reference

Key public endpoints currently exposed by the FastAPI app:

- `GET /health`: liveness probe for the API process.
- `GET /api/health`: readiness summary for API, database, Redis, and workers.
- `GET /api/versions`: resolved external API versions from runtime config.
- `GET /docs`: Swagger UI.
- `GET /redoc`: ReDoc documentation.

Business routes are mounted under `/api` through the routers in `backend/app/routers/`.
