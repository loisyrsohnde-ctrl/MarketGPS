# MarketGPS - Test Plan
**Date:** 2026-01-24  
**Version:** 1.0

---

## 1. Test Categories

| Category | Type | Priority |
|----------|------|----------|
| A. Frontend Manual | UI/UX | CRITIQUE |
| B. Backend API | Functional | HAUTE |
| C. Mobile Phone | Responsive | CRITIQUE |
| D. Pipeline | Integration | MOYENNE |
| E. Smoke Tests | Pre-deploy | CRITIQUE |

---

## 2. Category A: Frontend Manual Tests

### A1. Authentication Flow

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A1.1 | Visit /login | Page loads, form visible | 🔲 |
| A1.2 | Login with valid credentials | Redirect to /dashboard | 🔲 |
| A1.3 | Login with invalid credentials | Error message displayed | 🔲 |
| A1.4 | Visit /signup | Page loads, form visible | 🔲 |
| A1.5 | Register new user | Success message, redirect | 🔲 |
| A1.6 | Register existing email | Error "already exists" | 🔲 |
| A1.7 | Visit /reset-password | Page loads, form visible | 🔲 |
| A1.8 | Request password reset | Confirmation message | 🔲 |
| A1.9 | Logout from topbar | Redirect to / or /login | 🔲 |
| A1.10 | Access /dashboard unauthenticated | Redirect to /login | 🔲 |

### A2. Dashboard

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A2.1 | Load /dashboard | Page loads < 3s | 🔲 |
| A2.2 | Top scored cards visible | Min 5 cards displayed | 🔲 |
| A2.3 | Score badges colored correctly | Green > 60, Yellow > 40 | 🔲 |
| A2.4 | Click asset card | Opens inspector | 🔲 |
| A2.5 | Metrics counts visible | Shows scope counts | 🔲 |
| A2.6 | Charts render | No blank areas | 🔲 |
| A2.7 | Responsive grid | 1 col mobile, 3 cols desktop | 🔲 |

### A3. Explorer / Markets

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A3.1 | Load /dashboard/explorer | Table loads with data | 🔲 |
| A3.2 | Search for "AAPL" | Results contain Apple | 🔲 |
| A3.3 | Filter by scope US_EU | Only US/EU assets | 🔲 |
| A3.4 | Filter by scope AFRICA | Only Africa assets | 🔲 |
| A3.5 | Pagination next | New page loads | 🔲 |
| A3.6 | Pagination prev | Previous page loads | 🔲 |
| A3.7 | Click row | Opens inspector | 🔲 |
| A3.8 | Asset logos load | No broken images | 🔲 |
| A3.9 | Sort by score | Descending order | 🔲 |

### A4. Watchlist

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A4.1 | Load /watchlist | Page loads | 🔲 |
| A4.2 | Add asset from inspector | Toast "Added" | 🔲 |
| A4.3 | Refresh page | Asset still in list | 🔲 |
| A4.4 | Remove asset | Toast "Removed", disappears | 🔲 |
| A4.5 | Empty watchlist message | "No assets" displayed | 🔲 |

### A5. Settings

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A5.1 | Load /settings | Profile form visible | 🔲 |
| A5.2 | Update display name | Success toast | 🔲 |
| A5.3 | Upload avatar | Preview updates | 🔲 |
| A5.4 | Change password | Success message | 🔲 |
| A5.5 | Load /settings/billing | Subscription info visible | 🔲 |
| A5.6 | Upgrade button | Opens Stripe checkout | 🔲 |

### A6. Strategies

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A6.1 | Load /strategies | Templates list visible | 🔲 |
| A6.2 | Click template card | Opens /strategies/[slug] | 🔲 |
| A6.3 | View template detail | Name, description, risk visible | 🔲 |
| A6.4 | Run simulation | Results display (mocked or real) | 🔲 |
| A6.5 | Load /strategies/new | Creation form visible | 🔲 |
| A6.6 | Save user strategy | Success, appears in list | 🔲 |
| A6.7 | Edit user strategy | Form pre-filled | 🔲 |
| A6.8 | Delete user strategy | Removed from list | 🔲 |

### A7. Barbell

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A7.1 | Load /barbell | Builder interface visible | 🔲 |
| A7.2 | View core candidates | Table with assets | 🔲 |
| A7.3 | View satellite candidates | Table with assets | 🔲 |
| A7.4 | Add to portfolio | Asset added to selection | 🔲 |
| A7.5 | Adjust weights | Sliders functional | 🔲 |
| A7.6 | Run simulation | Results display | 🔲 |
| A7.7 | Save portfolio | Success message | 🔲 |

### A8. Asset Inspector

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| A8.1 | Open inspector | Slide-over animates in | 🔲 |
| A8.2 | View scores | Total + breakdown visible | 🔲 |
| A8.3 | View chart | Price chart renders | 🔲 |
| A8.4 | Add to watchlist | Button changes state | 🔲 |
| A8.5 | Close inspector | Slide-over closes | 🔲 |
| A8.6 | Deep link /asset/[ticker] | Full page loads | 🔲 |

---

## 3. Category B: Backend API Tests

### B1. Health & Core

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B1.1 | `/health` | GET | 200 + status | 🔲 |
| B1.2 | `/api/metrics/counts` | GET | 200 + counts | 🔲 |
| B1.3 | `/api/metrics/landing` | GET | 200 + metrics | 🔲 |

### B2. Assets

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B2.1 | `/api/assets/top-scored` | GET | 200 + array | 🔲 |
| B2.2 | `/api/assets/top-scored?scope=AFRICA` | GET | 200 + Africa assets | 🔲 |
| B2.3 | `/api/assets/search?q=apple` | GET | 200 + results | 🔲 |
| B2.4 | `/api/assets/explorer?page=1` | GET | 200 + paginated | 🔲 |
| B2.5 | `/api/assets/AAPL` | GET | 200 + asset detail | 🔲 |
| B2.6 | `/api/assets/AAPL.US` | GET | 200 + asset detail | 🔲 |
| B2.7 | `/api/assets/INVALID` | GET | 404 | 🔲 |
| B2.8 | `/api/assets/AAPL/chart` | GET | 200 + OHLCV data | 🔲 |

### B3. Watchlist

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B3.1 | `/api/watchlist` | GET | 200 + array | 🔲 |
| B3.2 | `/api/watchlist` | POST `{ticker}` | 200/201 | 🔲 |
| B3.3 | `/api/watchlist/AAPL` | DELETE | 200 | 🔲 |
| B3.4 | `/api/watchlist/check/AAPL` | GET | 200 + boolean | 🔲 |

### B4. Strategies

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B4.1 | `/api/strategies/health` | GET | 200 | 🔲 |
| B4.2 | `/api/strategies/templates` | GET | 200 + array | 🔲 |
| B4.3 | `/api/strategies/templates/balanced-global` | GET | 200 + template | 🔲 |
| B4.4 | `/api/strategies/templates/INVALID` | GET | 404 | 🔲 |
| B4.5 | `/api/strategies/user` | GET | 200 + array | 🔲 |
| B4.6 | `/api/strategies/simulate` | POST | 200 + results | 🔲 |

### B5. Barbell

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B5.1 | `/api/barbell/health` | GET | 200 | 🔲 |
| B5.2 | `/api/barbell/candidates/core` | GET | 200 + array | 🔲 |
| B5.3 | `/api/barbell/candidates/satellite` | GET | 200 + array | 🔲 |
| B5.4 | `/api/barbell/simulate` | POST | 200 + results | 🔲 |
| B5.5 | `/api/barbell/portfolios` | GET | 200 + array | 🔲 |

### B6. User

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B6.1 | `/users/profile` | GET | 200 + profile | 🔲 |
| B6.2 | `/users/entitlements` | GET | 200 + plan | 🔲 |
| B6.3 | `/users/notifications` | GET | 200 + settings | 🔲 |

### B7. News (À créer)

| ID | Endpoint | Method | Expected | Status |
|----|----------|--------|----------|--------|
| B7.1 | `/api/news` | GET | 200 + array | 🔲 |
| B7.2 | `/api/news?tags=fintech` | GET | 200 + filtered | 🔲 |
| B7.3 | `/api/news/{slug}` | GET | 200 + article | 🔲 |
| B7.4 | `/api/news/{id}/save` | POST | 201 | 🔲 |
| B7.5 | `/api/news/saved` | GET | 200 + array | 🔲 |

---

## 4. Category C: Mobile Phone Tests

### C1. Breakpoint Verification

| ID | Device | Width | Test | Status |
|----|--------|-------|------|--------|
| C1.1 | iPhone SE | 375px | All pages load | 🔲 |
| C1.2 | iPhone 14 | 390px | All pages load | 🔲 |
| C1.3 | Android small | 360px | All pages load | 🔲 |
| C1.4 | Tablet | 768px | Hybrid layout | 🔲 |

### C2. Navigation

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| C2.1 | Bottom tabs visible | 5 tabs at bottom | 🔲 |
| C2.2 | Tab "Dashboard" | Navigates to /dashboard | 🔲 |
| C2.3 | Tab "Marchés" | Navigates to /dashboard/explorer | 🔲 |
| C2.4 | Tab "Watchlist" | Navigates to /watchlist | 🔲 |
| C2.5 | Tab "News" | Navigates to /news | 🔲 |
| C2.6 | Tab "Settings" | Navigates to /settings | 🔲 |
| C2.7 | Active tab highlighted | Visual indicator | 🔲 |
| C2.8 | Sidebar hidden | Not visible < 768px | 🔲 |

### C3. Touch Targets

| ID | Element | Min Size | Status |
|----|---------|----------|--------|
| C3.1 | Tab bar icons | 44x44px | 🔲 |
| C3.2 | Asset cards | 44px height min | 🔲 |
| C3.3 | Buttons | 44px height | 🔲 |
| C3.4 | Filter chips | 36px height | 🔲 |
| C3.5 | Close buttons | 44x44px | 🔲 |

### C4. Layout

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| C4.1 | No horizontal scroll | Content fits viewport | 🔲 |
| C4.2 | Tables -> Cards | Cards view on mobile | 🔲 |
| C4.3 | Filter sheet | Opens as bottom sheet | 🔲 |
| C4.4 | Charts readable | Axes simplified | 🔲 |
| C4.5 | Safe area iOS | Bottom tabs above home bar | 🔲 |
| C4.6 | Keyboard doesn't overlap | Input stays visible | 🔲 |

### C5. Performance

| ID | Test Case | Expected | Status |
|----|-----------|----------|--------|
| C5.1 | Dashboard FCP | < 2.5s on 4G | 🔲 |
| C5.2 | Explorer load | < 3s on 4G | 🔲 |
| C5.3 | Image lazy load | Offscreen logos deferred | 🔲 |
| C5.4 | Scroll smoothness | 60 FPS | 🔲 |

---

## 5. Category D: Pipeline Tests

### D1. Jobs

| ID | Command | Expected | Status |
|----|---------|----------|--------|
| D1.1 | `python -m pipeline.jobs --status` | Shows job status | 🔲 |
| D1.2 | `python -m pipeline.jobs --run-gating --scope US_EU` | Completes | 🔲 |
| D1.3 | `python -m pipeline.jobs --run-rotation --scope US_EU` | Completes | 🔲 |

### D2. News Pipeline (À créer)

| ID | Command | Expected | Status |
|----|---------|----------|--------|
| D2.1 | `python -m pipeline.jobs --news-ingest` | Fetches sources | 🔲 |
| D2.2 | `python -m pipeline.jobs --news-rewrite` | Translates/TLDR | 🔲 |
| D2.3 | `python -m pipeline.jobs --news-full` | Full pipeline | 🔲 |

---

## 6. Category E: Smoke Tests

### E1. Pre-Deploy Checklist

```bash
#!/bin/bash
# scripts/smoke_test.sh

set -e

API_URL="${API_URL:-https://api.marketgps.online}"
APP_URL="${APP_URL:-https://app.marketgps.online}"

echo "🔍 MarketGPS Smoke Tests"
echo "========================"

# Backend health
echo -n "✓ Backend health: "
curl -sf "$API_URL/health" > /dev/null && echo "OK" || echo "FAIL"

# Assets endpoint
echo -n "✓ Assets top-scored: "
curl -sf "$API_URL/api/assets/top-scored" | jq -e 'length > 0' > /dev/null && echo "OK" || echo "FAIL"

# Metrics
echo -n "✓ Metrics counts: "
curl -sf "$API_URL/api/metrics/counts" | jq -e '.total > 0' > /dev/null && echo "OK" || echo "FAIL"

# Strategies templates
echo -n "✓ Strategy templates: "
curl -sf "$API_URL/api/strategies/templates" | jq -e 'length > 0' > /dev/null && echo "OK" || echo "FAIL"

# Frontend health (check 200 status)
echo -n "✓ Frontend /dashboard: "
curl -sf -o /dev/null -w "%{http_code}" "$APP_URL/dashboard" | grep -q "200" && echo "OK" || echo "FAIL"

echo ""
echo "✅ Smoke tests complete"
```

### E2. Post-Deploy Verification

| ID | Check | Method | Status |
|----|-------|--------|--------|
| E2.1 | Backend accessible | curl /health | 🔲 |
| E2.2 | Frontend accessible | curl / | 🔲 |
| E2.3 | Auth working | Manual login | 🔲 |
| E2.4 | Data visible | Check dashboard | 🔲 |
| E2.5 | Mobile working | Phone test | 🔲 |

---

## 7. Test Execution Schedule

| Phase | Tests | When |
|-------|-------|------|
| Pre-Implementation | A1-A8, B1-B6 | Before any changes |
| Mobile Phase | C1-C5 | After mobile implementation |
| News Phase | A.News, B7, D2 | After news implementation |
| Pre-Deploy | E1, E2 | Before each deploy |

---

## 8. Bug Tracking

| ID | Description | Severity | Fix Status |
|----|-------------|----------|------------|
| | | | |

---

## 9. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | | | |
| Dev Lead | | | |
| Product | | | |

---

*Fin du plan de tests*
