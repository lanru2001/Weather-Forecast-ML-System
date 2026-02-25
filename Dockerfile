# ============================================================
# Weather ML API - Multi-stage Dockerfile
# ============================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim as production

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup model/ ./model/

# Create model directory
RUN mkdir -p /models && chown appuser:appgroup /models

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Run with uvicorn for production
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--log-level", "info"]
