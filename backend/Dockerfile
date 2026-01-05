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
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-deps bertopic

# ------------------------------------------------------------------------------
# STAGE 2: Runtime - Minimal production image
# ------------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose the port used by Cloud Run
EXPOSE 8080

# Health check (curl is installed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c "curl -f http://localhost:\${PORT:-8080}/health || exit 1"

# Use a shell CMD so $PORT is expanded correctly
# Cloud Run manages scaling, so use single worker
# Add error handling and logging for better debugging
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info --access-log"]
