# ============================================================================
# MarketGPS Pipeline/Scheduler Dockerfile
# Production scheduler for US market open/close scoring runs
# ============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Copy root requirements (main project dependencies)
COPY requirements.txt ./requirements.txt

# Copy backend requirements (has additional deps like exchange-calendars)
COPY backend/requirements.txt ./backend_requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend_requirements.txt && \
    pip install --no-cache-dir apscheduler>=3.10.0

# Copy application code (full project needed for pipeline)
COPY core/ ./core/
COPY pipeline/ ./pipeline/
COPY storage/ ./storage/
COPY providers/ ./providers/
COPY backend/scripts/scheduler_guard.py ./backend/scripts/scheduler_guard.py

# Create directories for data and logs (will be mounted as volumes)
RUN mkdir -p /app/data /app/logs /app/backend/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=America/New_York

# No port exposed - scheduler is a background job
# Health can be checked via docker inspect or log monitoring

# Default command: run production scheduler
# Options:
#   - python -m pipeline.scheduler : APScheduler-based continuous scheduler
#   - python -m pipeline.prod_scheduler : New US open/close scheduler (recommended)
#   - python -m pipeline.jobs --full-pipeline --scope US_EU : One-time full run
CMD ["python", "-m", "pipeline.prod_scheduler"]
