#!/bin/bash
# ============================================================================
# MarketGPS - Stop Production Services
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MarketGPS - Stopping Production Services"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

docker compose -f docker-compose.prod.yml down

echo ""
echo "All services stopped."
echo ""
echo "To remove volumes (WARNING: deletes data): docker compose -f docker-compose.prod.yml down -v"
