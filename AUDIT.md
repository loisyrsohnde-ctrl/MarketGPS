# MarketGPS - Audit Report
**Date:** 2026-01-24  
**Auditor:** Full-Stack Senior Architect  
**Version:** 1.0

---

## Executive Summary

MarketGPS est une application de scoring d'actifs financiers fonctionnelle en production. L'audit révèle une architecture solide mais identifie des lacunes critiques pour l'expérience mobile et des fonctionnalités manquantes (News, Strategies améliorées).

### Verdict Global
| Domaine | État | Priorité Fix |
|---------|------|--------------|
| Mobile UX | ⚠️ Partiel | **CRITIQUE** |
| News Module | ❌ Absent | **HAUTE** |
| Strategies | ⚠️ Basique | **MOYENNE** |
| Backend API | ✅ Solide | - |
| Pipeline | ✅ Production-ready | - |
| Auth | ✅ Fonctionnel | - |

---

## 1. Frontend Audit

### 1.1 Routes Existantes

```
app/
├── page.tsx                      # Landing
├── login/page.tsx                # Auth
├── signup/page.tsx               # Auth
├── reset-password/page.tsx       # Auth
├── pricing/page.tsx              # Marketing
├── contact/page.tsx              # Marketing
├── legal/
│   ├── privacy/page.tsx
│   └── terms/page.tsx
├── dashboard/
│   ├── layout.tsx                # Sidebar + Topbar
│   ├── page.tsx                  # Dashboard home
│   ├── explorer/page.tsx         # Asset explorer
│   └── markets/page.tsx          # Markets overview
├── asset/
│   ├── layout.tsx
│   └── [ticker]/page.tsx         # Asset detail
├── watchlist/
│   ├── layout.tsx
│   └── page.tsx                  # User watchlist
├── strategies/
│   ├── layout.tsx
│   ├── page.tsx                  # Templates list
│   ├── [slug]/page.tsx           # Template detail
│   ├── new/page.tsx              # Create strategy
│   └── edit/[id]/page.tsx        # Edit strategy
├── barbell/
│   ├── layout.tsx
│   └── page.tsx                  # Barbell builder
├── settings/
│   ├── layout.tsx
│   ├── page.tsx                  # Settings
│   └── billing/page.tsx          # Subscription
└── api/health/route.ts           # Health check
```

### 1.2 Composants

| Fichier | Usage | État Mobile |
|---------|-------|-------------|
| `layout/sidebar.tsx` | Navigation desktop | ❌ Hidden mobile |
| `layout/topbar.tsx` | Header + search | ⚠️ Partiel |
| `AssetInspector.tsx` | Slide-over detail | ✅ Responsive |
| `barbell/*.tsx` | Builder complet | ⚠️ Tables cachées |
| `charts/price-chart.tsx` | Recharts | ⚠️ Axes non optimisés |
| `charts/score-gauge.tsx` | Gauge SVG | ✅ Responsive |
| `cards/asset-card.tsx` | Asset card | ✅ OK |
| `ui/*.tsx` | Design system | ✅ OK |

### 1.3 State Management

**Zustand Stores:**
- `useAssetInspector` - Global inspector state

**React Query:**
- Utilisé pour server state (assets, watchlist, etc.)
- Cache configuré dans `providers.tsx`

### 1.4 API Client

| Fichier | Usage |
|---------|-------|
| `lib/config.ts` | `getApiBaseUrl()` |
| `lib/api.ts` | Assets, watchlist, metrics |
| `lib/api-client.ts` | Generic client class |
| `lib/api-user.ts` | User profile/settings |

**Problème identifié:** ~15 fichiers utilisent `fetch()` directement au lieu du client centralisé.

### 1.5 Mobile Responsiveness

**Points positifs:**
- Tailwind breakpoints utilisés (`md:`, `lg:`)
- Grids responsive (`grid-cols-1 md:grid-cols-2`)
- Asset Inspector `w-full sm:w-[500px]`

**Lacunes critiques:**
1. ❌ **Pas de bottom tab bar** - Navigation impossible sur mobile
2. ❌ **Tables non converties en cards** - Colonnes cachées = perte info
3. ⚠️ **Sidebar desktop-only** - `hidden` sur mobile sans alternative
4. ⚠️ **Charts axes trop denses** - Illisibles < 400px
5. ⚠️ **Overflow horizontal** - Possible sur certaines pages

---

## 2. Backend Audit

### 2.1 API Routes

**Assets (14 endpoints):**
```
GET  /api/assets/top-scored
GET  /api/assets/top-scored-institutional
GET  /api/assets/search
GET  /api/assets/explorer
GET  /api/assets/{ticker}
GET  /api/assets/{ticker}/chart
POST /api/assets/{ticker}/score
```

**Watchlist (4 endpoints):**
```
GET    /api/watchlist
POST   /api/watchlist
DELETE /api/watchlist/{ticker}
GET    /api/watchlist/check/{ticker}
```

**Strategies (15 endpoints):**
```
GET  /api/strategies/templates
GET  /api/strategies/templates/{slug}
GET  /api/strategies/templates/{slug}/compositions
GET  /api/strategies/eligible-instruments
POST /api/strategies/simulate
GET  /api/strategies/user
POST /api/strategies/user
GET  /api/strategies/user/{strategy_id}
PUT  /api/strategies/user/{strategy_id}
DELETE /api/strategies/user/{strategy_id}
POST /api/strategies/user/{strategy_id}/add-instrument
POST /api/strategies/ai-suggest
POST /api/strategies/ai-generate
```

**Barbell (12 endpoints):**
```
GET  /api/barbell/health
GET  /api/barbell/suggest
GET  /api/barbell/allocation-ratios
GET  /api/barbell/core-candidates
GET  /api/barbell/satellite-candidates
GET  /api/barbell/candidates/core
GET  /api/barbell/candidates/satellite
POST /api/barbell/simulate
GET  /api/barbell/portfolios
POST /api/barbell/portfolios
GET  /api/barbell/portfolios/{id}
PUT  /api/barbell/portfolios/{id}
DELETE /api/barbell/portfolios/{id}
```

**Users (12 endpoints):**
```
GET  /users/profile
POST /users/profile/update
POST /users/avatar/upload
GET  /users/notifications
POST /users/notifications/update
GET  /users/notifications/messages
POST /users/notifications/read
GET  /users/notifications/unread-count
POST /users/security/change-password
POST /users/logout
POST /users/delete-account
GET  /users/entitlements
```

**News: ❌ ABSENT** (à créer)

### 2.2 Database Schema

**Tables existantes (25+):**

| Table | Colonnes clés | Usage |
|-------|---------------|-------|
| `universe` | asset_id, symbol, name, market_scope | Catalog |
| `scores_latest` | score_total, score_value, momentum, safety | Current scores |
| `gating_status` | coverage, liquidity, eligible | Data quality |
| `watchlist` | asset_id, user_id, notes | User watchlist |
| `users` | email, password_hash | Auth |
| `user_profiles` | display_name, avatar, preferences | Profile |
| `subscriptions_state` | plan, stripe_*, quota | Billing |
| `strategy_templates` | slug, name, structure_json | Templates |
| `user_strategies` | user_id, template_id, name | User strategies |
| `user_strategy_compositions` | ticker, weight, fit_score | Allocations |
| `barbell_portfolios` | name, core_ratio, satellite_ratio | Barbell |
| `barbell_portfolio_items` | asset_id, block, weight | Barbell items |
| `job_runs` | status, assets_processed | Pipeline tracking |

**Tables NEWS à créer:**
- `news_sources`
- `news_raw_items`
- `news_articles`
- `news_user_saves`

### 2.3 Authentication

- **Provider:** Supabase JWT
- **Fallback:** `user_id="default"` en dev
- **Extraction:** `get_user_id_from_request()` in `security.py`
- **Tables:** `users`, `sessions`, `user_sessions`

---

## 3. Pipeline Audit

### 3.1 Jobs Existants

| Module | Entry Point | Schedule |
|--------|-------------|----------|
| `universe.py` | `UniverseJob.run()` | Weekly |
| `gating.py` | `GatingJob.run()` | Every 6h |
| `rotation.py` | `RotationJob.run()` | Every 15min |
| `scoring.py` | `ScoringEngine.compute_score()` | On demand |
| `pool.py` | `PoolJob.run()` | Every 6h |
| `africa/rotation_africa.py` | `RotationAfricaJob.run()` | Africa-specific |

### 3.2 Data Sources

- **Primary:** EODHD (API key required)
- **Fallback:** yfinance (free, unlimited)
- **Bulk fetching:** `smart_bulk_fetcher.py` (99% reduction API calls)

### 3.3 News Pipeline: ❌ ABSENT

À créer:
```
pipeline/news/
├── sources_registry.json    # 100 sources Africa
├── ingest_rss.py           # RSS/Atom fetcher
├── ingest_html_playwright.py # Scraping fallback
├── extract_article.py      # Content extraction
├── rewrite_translate.py    # FR translation + TLDR
├── dedupe.py               # Deduplication
└── store.py                # SQLite storage
```

---

## 4. Problèmes Identifiés

### 4.1 Mobile (CRITIQUE)

| ID | Problème | Impact | Fix |
|----|----------|--------|-----|
| M1 | Pas de bottom tabs | Navigation impossible | Créer `MobileTabBar.tsx` |
| M2 | Sidebar hidden sans alternative | Menu inaccessible | AppShell responsive |
| M3 | Tables non converties | Info masquée | Cards sur mobile |
| M4 | Charts illisibles | UX dégradée | Axes simplifiés |
| M5 | Overflow horizontal | Scroll frustrant | `overflow-x-hidden` |

### 4.2 News (HAUTE)

| ID | Problème | Impact | Fix |
|----|----------|--------|-----|
| N1 | Aucune route /news | Feature absente | Créer pages + API |
| N2 | Pas de tables news | Data non stockable | Migrations additives |
| N3 | Pas de pipeline ingestion | Pas de contenu | Créer modules |

### 4.3 Strategies (MOYENNE)

| ID | Problème | Impact | Fix |
|----|----------|--------|-----|
| S1 | Simulation basique | Peu utile | Améliorer backtest |
| S2 | UI allocation complexe | UX confuse | Sliders visuels |
| S3 | Pas de validation weights | Erreurs user | Validation temps réel |

---

## 5. Décisions Architecture

### 5.1 Mobile Strategy

**Approche:** Progressive Enhancement
- Garder layout desktop intact
- Ajouter `AppShell` responsive qui compose:
  - Desktop: `sidebar.tsx` + `topbar.tsx` existants
  - Mobile: `topbar-compact.tsx` + `MobileTabBar.tsx`
- Transformer tables en cards via composant hybride
- Aucun breaking change sur routes existantes

### 5.2 News Module

**Approche:** Additive
- Nouvelles tables (pas d'ALTER sur existantes)
- Nouveaux endpoints `/api/news/*`
- Nouvelles pages `/news/*`
- Pipeline séparé dans `pipeline/news/`

### 5.3 Strategies Enhancement

**Approche:** Additive + Feature Flags
- Garder simulation existante
- Ajouter `enhanced_simulation` avec flag
- Améliorer UI sans casser comportement

---

## 6. Dépendances à Ajouter

### Frontend
```json
{
  "@radix-ui/react-sheet": "^1.0.0",    // Mobile drawers
  "vaul": "^0.9.0"                       // Bottom sheet (optionnel)
}
```

### Backend
```
playwright                               # HTML scraping
feedparser                               # RSS parsing
httpx                                    # Async HTTP
```

---

## 7. Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Regression routes | Basse | Haute | Smoke tests avant deploy |
| Performance news pipeline | Moyenne | Moyenne | Rate limiting + cache |
| Mobile layout break | Moyenne | Haute | Tests manuels 3 breakpoints |
| API overload | Basse | Haute | Pagination + cache headers |

---

## 8. Prochaines Étapes

1. ✅ Audit complet (ce document)
2. 🔲 TEST_PLAN.md avec checklists
3. 🔲 Mobile optimization (Phase 1)
4. 🔲 News module (Phase 2)
5. 🔲 Strategies redesign (Phase 3)
6. 🔲 Next.js 16 upgrade (Phase B)

---

*Fin du rapport d'audit*
