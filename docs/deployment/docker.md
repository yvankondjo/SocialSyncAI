# Docker Deployment

The repository includes `backend/Dockerfile` and `frontend/Dockerfile`.

What is not currently committed:

- No root `docker-compose.yml`.
- No single-command multi-service orchestration manifest.

Recommended use today:

1. Build backend and frontend images independently from their Dockerfiles.
2. Provide environment variables externally.
3. Run Redis and worker processes through your own platform orchestration.
