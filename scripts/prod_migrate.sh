#!/bin/bash
# ============================================================================
# MarketGPS - Run Database Migrations
# ============================================================================
#
# This script applies pending SQLite migrations to the production database.
# Migrations are stored in storage/migrations/*.sql
#
# Usage:
#   ./scripts/prod_migrate.sh
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

DB_PATH="data/marketgps.db"
MIGRATIONS_DIR="storage/migrations"
APPLIED_FILE="data/.applied_migrations"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MarketGPS - Database Migrations"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    echo "ERROR: Database not found at $DB_PATH"
    echo "Please ensure the database is initialized first."
    exit 1
fi

# Check migrations directory
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "No migrations directory found at $MIGRATIONS_DIR"
    exit 0
fi

# Create applied migrations tracker if not exists
touch "$APPLIED_FILE"

# Apply migrations
APPLIED=0
SKIPPED=0

for migration in "$MIGRATIONS_DIR"/*.sql; do
    if [ -f "$migration" ]; then
        BASENAME=$(basename "$migration")
        
        # Check if already applied
        if grep -q "^$BASENAME$" "$APPLIED_FILE" 2>/dev/null; then
            echo "SKIP: $BASENAME (already applied)"
            ((SKIPPED++))
        else
            echo "APPLYING: $BASENAME"
            
            # Apply migration
            if sqlite3 "$DB_PATH" < "$migration"; then
                echo "$BASENAME" >> "$APPLIED_FILE"
                echo "  ✓ Applied successfully"
                ((APPLIED++))
            else
                echo "  ✗ Failed!"
                exit 1
            fi
        fi
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Migration complete: $APPLIED applied, $SKIPPED skipped"
echo "═══════════════════════════════════════════════════════════════════════════"
