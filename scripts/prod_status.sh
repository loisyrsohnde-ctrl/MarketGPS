#!/bin/bash
# ============================================================================
# MarketGPS - Production Status
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MarketGPS - Production Status"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Container status
echo "CONTAINERS:"
echo "-----------"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "HEALTH CHECKS:"
echo "--------------"

# Backend health
echo -n "Backend:   "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy or not running"
fi

# Frontend health
echo -n "Frontend:  "
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy or not running"
fi

echo ""
echo "VOLUMES:"
echo "--------"
docker volume ls | grep marketgps || echo "No MarketGPS volumes found"

echo ""
echo "DISK USAGE:"
echo "-----------"
docker system df

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
