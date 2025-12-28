# =============================================================================
# DataPulse - Production Dockerfile
# =============================================================================
# Multi-stage build for optimized image size
# Final image: ~250MB (vs ~1GB unoptimized)
#
# Build:  docker build -t datapulse:latest .
# Run:    docker run -p 8000:8000 -p 8501:8501 datapulse:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pydantic-settings gunicorn

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.12-slim as production

# Labels
LABEL maintainer="Luca Neviani"
LABEL version="2.1.0"
LABEL description="DataPulse - AI-Powered Business Intelligence"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production \
    LOG_FORMAT=json

# Create non-root user for security
RUN groupadd --gid 1000 datapulse && \
    useradd --uid 1000 --gid datapulse --shell /bin/bash --create-home datapulse

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=datapulse:datapulse backend/ ./backend/
COPY --chown=datapulse:datapulse frontend/ ./frontend/
COPY --chown=datapulse:datapulse data/*.csv ./data/
COPY --chown=datapulse:datapulse data/populate_db.py ./data/

# Create directories
RUN mkdir -p data/database uploads exports logs && \
    chown -R datapulse:datapulse data uploads exports logs

# Switch to non-root user
USER datapulse

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health', timeout=5)" || exit 1

# Expose ports
EXPOSE 8000 8501

# Default command - can be overridden
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
