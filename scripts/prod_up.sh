#!/bin/bash
# ============================================================================
# MarketGPS - Start Production Services
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MarketGPS - Starting Production Services"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Check for .env.prod
if [ ! -f ".env.prod" ]; then
    echo "ERROR: .env.prod file not found!"
    echo "Please copy .env.prod.example to .env.prod and fill in the values."
    exit 1
fi

# Check for required data files
if [ ! -f "data/marketgps.db" ]; then
    echo "WARNING: data/marketgps.db not found."
    echo "The pipeline may need to initialize the database."
fi

# Build and start services
echo "Building and starting services..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Services started!"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000"
echo "Health:    http://localhost:8000/health"
echo ""
echo "View logs: ./scripts/prod_logs.sh"
echo "Stop:      ./scripts/prod_down.sh"
echo ""

# Show status
docker compose -f docker-compose.prod.yml ps
