# Google Cloud Run

Cloud Run deployment is supported conceptually by the repository structure, but the exact deployment manifests are environment-specific.

Use this repo as the application source of truth, then supply:

- backend and frontend image builds,
- Cloud Run service definitions,
- Redis and worker infrastructure,
- environment variables and secrets from your GCP project.
