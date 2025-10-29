# ==============================================================================
# MULTI-STAGE DOCKERFILE FOR FASTAPI BACKEND
# Optimized for: Security (non-root), Performance (cache layers), Size
# ==============================================================================

# ------------------------------------------------------------------------------
# STAGE 1: Builder - Install dependencies
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better Docker cache)
COPY requirements-dev.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
  pip install --no-cache-dir -r requirements-dev.txt && \
  pip install --no-cache-dir --no-deps bertopic


# ------------------------------------------------------------------------------
# STAGE 2: Runtime - Development (Devcontainer)
# ------------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Runtime + outils nécessaires à Supabase CLI & healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl unzip xz-utils ca-certificates gnupg lsb-release \
    postgresql-client socat iproute2 netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

# [RECOMMANDÉ] Docker CLI + Compose v2 (pour `supabase start`)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg \
      | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable" \
      > /etc/apt/sources.list.d/docker.list \
  && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
  && rm -rf /var/lib/apt/lists/* \
  && docker --version && docker compose version

# Supabase CLI (version épinglée) — paquets Linux via Releases officiels
ARG SUPABASE_VERSION=2.54.13
RUN curl -L -o /tmp/supabase.deb "https://github.com/supabase/cli/releases/download/v${SUPABASE_VERSION}/supabase_${SUPABASE_VERSION}_linux_amd64.deb" \
  && dpkg -i /tmp/supabase.deb || apt-get -f install -y \
  && rm -f /tmp/supabase.deb \
  && supabase --version

# Claude Code (installation native correcte : domaine .ai, pas .com)
# Le script met le binaire dans ~/.local/bin ; on crée un lien global.
RUN mkdir -p /root/.local/bin \
  && curl -fsSL https://claude.ai/install.sh | bash \
  && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
  && claude --version

# Venv depuis le builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Code app
COPY . .

RUN mkdir -p /app/logs && chmod -R 777 /app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
