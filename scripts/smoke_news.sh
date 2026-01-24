#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MarketGPS News Module - Smoke Test
# Verifies that the news pipeline and API are working correctly
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
NEWS_LIMIT="${NEWS_LIMIT:-10}"

echo "═══════════════════════════════════════════════════════════════════"
echo "MarketGPS News Module - Smoke Test"
echo "═══════════════════════════════════════════════════════════════════"
echo "API Base: $API_BASE"
echo "News Limit: $NEWS_LIMIT"
echo ""

# Track failures
FAILURES=0

# Helper function
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        FAILURES=$((FAILURES + 1))
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test 1: API Health Check
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "── Test 1: API Health Check ──"

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE/api/news/health" 2>/dev/null || echo "FAILED")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    check_result 0 "News API health endpoint responding"
else
    check_result 1 "News API health endpoint responding (HTTP $HTTP_CODE)"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Test 2: Run News Ingestion (limited)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "── Test 2: Run News Ingestion ──"

cd "$(dirname "$0")/.."

python -m pipeline.jobs --news-ingest --news-limit "$NEWS_LIMIT" 2>/dev/null
INGEST_RESULT=$?

check_result $INGEST_RESULT "News ingestion job completed"

# ═══════════════════════════════════════════════════════════════════════════════
# Test 3: Run News Publishing (limited)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "── Test 3: Run News Publishing ──"

python -m pipeline.jobs --news-rewrite --news-limit "$NEWS_LIMIT" 2>/dev/null
PUBLISH_RESULT=$?

check_result $PUBLISH_RESULT "News publishing job completed"

# ═══════════════════════════════════════════════════════════════════════════════
# Test 4: Check News API Returns Data
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "── Test 4: Check News API ──"

NEWS_RESPONSE=$(curl -s "$API_BASE/api/news?page_size=5" 2>/dev/null || echo '{"total": 0}')
TOTAL=$(echo "$NEWS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")

if [ "$TOTAL" -gt 0 ]; then
    check_result 0 "News API returns $TOTAL articles"
else
    # Not a failure if no articles yet (first run)
    echo -e "${YELLOW}⚠ News API returns 0 articles (may be first run)${NC}"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Test 5: Check Tags/Countries endpoints
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "── Test 5: Check Tags/Countries Endpoints ──"

TAGS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/news/tags" 2>/dev/null || echo "0")
check_result $([ "$TAGS_CODE" = "200" ] && echo 0 || echo 1) "Tags endpoint responding"

COUNTRIES_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/news/countries" 2>/dev/null || echo "0")
check_result $([ "$COUNTRIES_CODE" = "200" ] && echo 0 || echo 1) "Countries endpoint responding"

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════════"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES test(s) failed${NC}"
    exit 1
fi
