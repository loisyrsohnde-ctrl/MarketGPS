#!/bin/bash
# MarketGPS Smoke Tests
# Run before and after each deploy to verify critical functionality

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-https://api.marketgps.online}"
APP_URL="${APP_URL:-https://app.marketgps.online}"
TIMEOUT=10

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_content="$3"
    
    response=$(curl -sf --max-time $TIMEOUT "$url" 2>/dev/null) || {
        fail "$name - Connection failed"
        return 1
    }
    
    if [ -n "$expected_content" ]; then
        echo "$response" | jq -e "$expected_content" > /dev/null 2>&1 && {
            pass "$name"
            return 0
        } || {
            fail "$name - Content validation failed"
            return 1
        }
    else
        pass "$name"
        return 0
    fi
}

test_http_status() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    status=$(curl -sf -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null) || status="000"
    
    if [ "$status" = "$expected_status" ]; then
        pass "$name (HTTP $status)"
        return 0
    else
        fail "$name (Expected $expected_status, got $status)"
        return 1
    fi
}

# Header
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 MarketGPS Smoke Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "API: $API_URL"
echo "APP: $APP_URL"
echo ""

# ========================================
# Backend Tests
# ========================================
echo "📡 BACKEND TESTS"
echo "────────────────────────────────────"

# Health check
test_endpoint "Health endpoint" "$API_URL/health" '.status == "healthy"'

# Assets endpoints
test_endpoint "Assets top-scored" "$API_URL/api/assets/top-scored" 'length > 0'
test_endpoint "Assets search" "$API_URL/api/assets/search?q=a" 'type == "array"'
test_endpoint "Assets explorer" "$API_URL/api/assets/explorer?page=1&page_size=10" '.data | length > 0'

# Metrics
test_endpoint "Metrics counts" "$API_URL/api/metrics/counts" '.total >= 0'
test_endpoint "Metrics landing" "$API_URL/api/metrics/landing" 'has("total_assets")'

# Strategies
test_endpoint "Strategies templates" "$API_URL/api/strategies/templates" 'length >= 0'
test_endpoint "Strategies health" "$API_URL/api/strategies/health" '.status'

# Barbell
test_endpoint "Barbell health" "$API_URL/api/barbell/health" '.status'
test_endpoint "Barbell core candidates" "$API_URL/api/barbell/candidates/core" 'type == "array"'

# Watchlist (may be empty for anonymous)
test_endpoint "Watchlist endpoint" "$API_URL/api/watchlist" 'type == "array"'

echo ""

# ========================================
# Frontend Tests
# ========================================
echo "🌐 FRONTEND TESTS"
echo "────────────────────────────────────"

# Main pages
test_http_status "Landing page" "$APP_URL/" "200"
test_http_status "Login page" "$APP_URL/login" "200"
test_http_status "Signup page" "$APP_URL/signup" "200"
test_http_status "Pricing page" "$APP_URL/pricing" "200"

# Dashboard (may redirect to login if protected)
dashboard_status=$(curl -sf -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$APP_URL/dashboard" 2>/dev/null) || dashboard_status="000"
if [ "$dashboard_status" = "200" ] || [ "$dashboard_status" = "307" ] || [ "$dashboard_status" = "302" ]; then
    pass "Dashboard (HTTP $dashboard_status)"
else
    warn "Dashboard unexpected status: $dashboard_status"
fi

echo ""

# ========================================
# News Tests (if implemented)
# ========================================
echo "📰 NEWS TESTS (Optional)"
echo "────────────────────────────────────"

news_response=$(curl -sf --max-time $TIMEOUT "$API_URL/api/news" 2>/dev/null) && {
    echo "$news_response" | jq -e 'type == "array"' > /dev/null 2>&1 && {
        pass "News endpoint implemented"
    } || {
        warn "News endpoint returns unexpected format"
    }
} || {
    warn "News endpoint not implemented yet"
}

echo ""

# ========================================
# Summary
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "  ${GREEN}✅ All critical tests passed!${NC}"
    exit 0
else
    echo -e "  ${RED}❌ Some tests failed. Check before deploy.${NC}"
    exit 1
fi
