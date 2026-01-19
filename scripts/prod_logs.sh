#!/bin/bash
# ============================================================================
# MarketGPS - View Production Logs
# ============================================================================
#
# Usage:
#   ./scripts/prod_logs.sh           # All services
#   ./scripts/prod_logs.sh backend   # Backend only
#   ./scripts/prod_logs.sh frontend  # Frontend only
#   ./scripts/prod_logs.sh scheduler # Scheduler only
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

SERVICE="${1:-}"

if [ -n "$SERVICE" ]; then
    echo "Showing logs for: $SERVICE"
    docker compose -f docker-compose.prod.yml logs -f "$SERVICE"
else
    echo "Showing logs for all services (Ctrl+C to exit)"
    docker compose -f docker-compose.prod.yml logs -f
fi
