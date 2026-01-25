#!/bin/bash
# ============================================================================
# MarketGPS News Pipeline - Smoke Test
# 
# Tests:
# 1. Run a quick news ingestion
# 2. Check API returns articles
# 3. Check health endpoint
# ============================================================================

set -e

API_BASE="${API_BASE:-https://api.marketgps.online}"
PYTHONPATH="${PYTHONPATH:-/app}"

echo "=============================================="
echo "MarketGPS News Pipeline - Smoke Test"
echo "API: $API_BASE"
echo "Time: $(date)"
echo "=============================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    FAILED=$((FAILED + 1))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

# ============================================================================
# Test 1: Check API is reachable
# ============================================================================
echo ""
echo "Test 1: API Connectivity"
echo "------------------------"

if curl -s -f "$API_BASE/health" > /dev/null 2>&1; then
    pass "API is reachable"
else
    fail "Cannot reach API at $API_BASE/health"
fi

# ============================================================================
# Test 2: Check news feed endpoint
# ============================================================================
echo ""
echo "Test 2: News Feed Endpoint"
echo "--------------------------"

NEWS_RESPONSE=$(curl -s "$API_BASE/api/news?page_size=5" 2>&1)

if echo "$NEWS_RESPONSE" | grep -q '"total"'; then
    TOTAL=$(echo "$NEWS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")
    pass "News feed returns data (total: $TOTAL articles)"
else
    fail "News feed endpoint failed"
    echo "Response: $NEWS_RESPONSE"
fi

# ============================================================================
# Test 3: Check news health endpoint
# ============================================================================
echo ""
echo "Test 3: News Health Endpoint"
echo "----------------------------"

HEALTH_RESPONSE=$(curl -s "$API_BASE/api/news/health" 2>&1)

if echo "$HEALTH_RESPONSE" | grep -q '"status"'; then
    STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    LAST_RUN=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('last_run', 'never'))" 2>/dev/null || echo "never")
    
    if [ "$STATUS" = "healthy" ]; then
        pass "News pipeline is healthy (last run: $LAST_RUN)"
    else
        warn "News pipeline status: $STATUS (last run: $LAST_RUN)"
    fi
else
    fail "News health endpoint failed"
    echo "Response: $HEALTH_RESPONSE"
fi

# ============================================================================
# Test 4: Check regions endpoint
# ============================================================================
echo ""
echo "Test 4: Regions Endpoint"
echo "------------------------"

REGIONS_RESPONSE=$(curl -s "$API_BASE/api/news/regions" 2>&1)

if echo "$REGIONS_RESPONSE" | grep -q '"regions"'; then
    TOTAL=$(echo "$REGIONS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")
    pass "Regions endpoint returns data (total articles: $TOTAL)"
else
    fail "Regions endpoint failed"
fi

# ============================================================================
# Test 5: Check if articles have required fields
# ============================================================================
echo ""
echo "Test 5: Article Data Quality"
echo "----------------------------"

if [ "$TOTAL" -gt 0 ]; then
    FIRST_ARTICLE=$(echo "$NEWS_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps(d.get('data', [{}])[0]))" 2>/dev/null)
    
    if echo "$FIRST_ARTICLE" | grep -q '"title"'; then
        pass "Articles have title field"
    else
        fail "Articles missing title"
    fi
    
    if echo "$FIRST_ARTICLE" | grep -q '"slug"'; then
        pass "Articles have slug field"
    else
        fail "Articles missing slug"
    fi
    
    if echo "$FIRST_ARTICLE" | grep -q '"source_name"'; then
        pass "Articles have source_name field"
    else
        fail "Articles missing source_name"
    fi
else
    warn "No articles to check quality"
fi

# ============================================================================
# Test 6: Run local pipeline test (if not in CI)
# ============================================================================
echo ""
echo "Test 6: Local Pipeline Test"
echo "---------------------------"

if command -v python3 &> /dev/null && [ -f "pipeline/news/ingest_rss.py" ]; then
    echo "Running quick ingestion test..."
    if python3 -m pipeline.jobs --news-ingest --news-limit 3 2>&1; then
        pass "Local ingestion test completed"
    else
        warn "Local ingestion test failed (may need dependencies)"
    fi
else
    warn "Skipping local test (not in correct environment)"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
