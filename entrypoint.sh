#!/bin/bash
set -e

# ============================================================================
# MarketGPS Backend Entrypoint
# Fixes permissions on bind-mounted volumes before dropping to appuser
# ============================================================================

# Fix ownership on bind-mounted SQLite directory (may be owned by root from host)
if [ -d "/app/data/sqlite" ]; then
    chown -R appuser:appuser /app/data/sqlite 2>/dev/null || true
fi

# Fix ownership on logs directory
if [ -d "/app/logs" ]; then
    chown -R appuser:appuser /app/logs 2>/dev/null || true
fi

# Fix ownership on article-videos directory
if [ -d "/app/data/article-videos" ]; then
    chown -R appuser:appuser /app/data/article-videos 2>/dev/null || true
fi

# Drop privileges and run the command as appuser
exec gosu appuser "$@"
