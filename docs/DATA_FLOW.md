# MarketGPS - DATA FLOW AUDIT

**Date**: 2026-01-26
**Version**: 1.0
**Auteur**: Audit automatisé

---

## 1. ARCHITECTURE DONNÉES

### 1.1 Tables Source de Vérité (SQLite)

| Table | Description | Colonnes Clés |
|-------|-------------|---------------|
| **universe** | Registre de tous les instruments | asset_id, symbol, name, asset_type, market_scope, market_code, exchange_code, currency, sector, industry, tier, active |
| **scores_latest** | Scores actuels | asset_id, market_scope, score_total, score_value, score_momentum, score_safety, score_fx_risk (Africa), score_liquidity_risk (Africa), confidence, state_label |
| **scores_history** | Historique des scores | asset_id, market_scope, score_total, confidence, created_at |
| **gating_status** | Éligibilité et qualité | asset_id, market_scope, eligible, coverage, liquidity, data_confidence |
| **calibration_params** | Poids par pilier par scope | market_scope, weight_momentum, weight_safety, weight_value, weight_fx_risk, weight_liquidity_risk |
| **watchlist** | Suivi utilisateur | asset_id, ticker, market_scope, user_id, notes |

### 1.2 Mapping Géographique

```
SCOPES:
├── US_EU
│   ├── Markets: US, EU, UK, FR, DE
│   └── Exchanges: NYSE, NASDAQ, LSE, EURONEXT, XETRA
│
└── AFRICA
    ├── Regions: North, West, Central, East, Southern
    ├── Countries: NG, ZA, KE, EG, MA, GH, CM, SN, CI, BW, MU, TZ, UG, RW
    └── Exchanges: JSE, NSE, EGX, BRVM, GSE, CSE, DSE
```

### 1.3 Mapping Pays → Région → Scope

```python
AFRICA_COUNTRY_EXCHANGES = {
    # East Africa
    "KE": ["NSE"],      # Kenya
    "TZ": ["DSE"],      # Tanzania
    "UG": ["USE"],      # Uganda
    "RW": ["RSE"],      # Rwanda

    # Southern Africa
    "ZA": ["JSE"],      # South Africa
    "BW": ["BSE"],      # Botswana
    "MU": ["SEM"],      # Mauritius

    # West Africa
    "NG": ["NGX"],      # Nigeria
    "GH": ["GSE"],      # Ghana
    "SN": ["BRVM"],     # Senegal (BRVM)
    "CI": ["BRVM"],     # Côte d'Ivoire (BRVM)

    # North Africa
    "EG": ["EGX"],      # Egypt
    "MA": ["CSE"],      # Morocco
    "TN": ["BVMT"],     # Tunisia

    # Central Africa
    "CM": ["BVMAC"],    # Cameroon
}

AFRICA_REGIONS = {
    "EAST": ["KE", "TZ", "UG", "RW"],
    "SOUTHERN": ["ZA", "BW", "MU", "ZM", "ZW"],
    "WEST": ["NG", "GH", "SN", "CI", "BF", "BJ", "ML", "NE", "TG"],
    "NORTH": ["EG", "MA", "TN", "DZ", "LY"],
    "CENTRAL": ["CM", "GA", "CG", "CD"],
}
```

---

## 2. ENDPOINTS API - CARTOGRAPHIE COMPLÈTE

### 2.1 Endpoints Assets

| Endpoint | Filtres | Defaults | Join Scores | Pagination |
|----------|---------|----------|-------------|------------|
| `GET /api/assets/top-scored` | market_scope, asset_type, market_filter, only_scored | scope=US_EU, only_scored=True*, limit=30 | LEFT JOIN | limit/offset |
| `GET /api/assets/explorer` | market_scope, asset_type, country, region, query, only_scored | scope=US_EU, page_size=50 | LEFT JOIN | page/page_size |
| `GET /api/assets/search` | q, market_scope, limit | limit=20 | LEFT JOIN | limit only |
| `GET /api/assets/{ticker}` | - | - | LEFT JOIN | - |
| `GET /api/assets/{ticker}/chart` | period | period=1y | Parquet files | - |

**⚠️ Note critique**: `/top-scored` désactive `only_scored` pour EU/AFRICA mais pas les autres endpoints.

### 2.2 Endpoints Métriques

| Endpoint | Description | Paramètres |
|----------|-------------|------------|
| `GET /api/metrics/counts` | Counts par scope | - |
| `GET /api/metrics/asset-type-counts` | Counts par type | market_scope (opt) |
| `GET /api/metrics/stats` | Stats complètes | market_scope (opt) |
| `GET /api/scope-counts` | Alias de /metrics/counts | - |

### 2.3 Endpoints Watchlist

| Endpoint | Auth | Scope-Aware |
|----------|------|-------------|
| `GET /api/watchlist` | Optional JWT | Oui (market_scope param) |
| `POST /api/watchlist` | Optional JWT | Oui (dans body) |
| `DELETE /api/watchlist/{ticker}` | Optional JWT | Non |
| `GET /api/watchlist/check/{ticker}` | Optional JWT | Non |

---

## 3. FRONTEND - APPELS API

### 3.1 React Query Keys

| Page | Query Key | Endpoint | Params |
|------|-----------|----------|--------|
| Dashboard | `['topScored', marketFilter, typeFilter, marketScope]` | `/api/assets/top-scored` | limit=50, filters... |
| Dashboard | `['assetTypeCounts', marketScope]` | `/api/metrics/asset-type-counts` | market_scope |
| Explorer | `['explorer', ...]` | `/api/assets/explorer` | page, filters... |
| Markets | `['scopeCounts']` | `/api/metrics/counts` | - |
| Markets | `['marketsTopAssets', market]` | `/api/assets/top-scored` | limit=10, market_filter |
| Watchlist | `['watchlist', userId]` | `/api/watchlist` | user_id |
| Asset Detail | `['asset', ticker]` | `/api/assets/{ticker}` | - |

### 3.2 Valeurs Hardcodées Frontend

```typescript
// Dashboard
topScored: limit = 50, mais affiche slice(0, 20) // ⚠️ INCOHÉRENCE

// Explorer
pageSize = 50 // Hardcodé

// Markets
topAssets: limit = 10 // Hardcodé

// Cache
assetTypeCounts: staleTime = 300000 (5 min)
topScored: staleTime = 60000 (1 min)
```

---

## 4. DIAGNOSTIC - CAUSES RACINES

### 🔴 CAUSE RACINE #1: Filtrage `only_scored` Incohérent

**Symptôme**: Un actif apparaît dans Dashboard mais pas dans Explorer (ou vice versa).

**Explication**:
```python
# /api/assets/top-scored (api_routes.py:165-167)
if market_filter in ("EU", "AFRICA"):
    show_only_scored = False  # ← Exception pour EU/AFRICA

# /api/assets/explorer (search_universe)
# Pas de cette exception → only_scored=True par défaut
```

**Impact**:
- Dashboard (top-scored) avec market_filter=AFRICA → montre actifs non-scorés
- Explorer avec market_scope=AFRICA → cache actifs non-scorés

**Fix recommandé**: Aligner le comportement, probablement `only_scored=False` partout ou bien partout respecter le paramètre utilisateur.

---

### 🔴 CAUSE RACINE #2: Paramètres Géographiques Non-Standardisés

**Symptôme**: Confusion entre market_scope, market_code, market_filter, country, region.

**Mapping actuel**:
```
/top-scored:   market_scope + market_filter (legacy mapping)
/explorer:     market_scope + country + region (Africa only)
/search:       market_scope only
/watchlist:    market_scope only
```

**Problème**:
- `market_filter="EU"` dans top-scored → filtre sur market_code EU
- `market_scope="US_EU"` dans explorer → PAS de filtre country/market_code

**Impact**: Impossible de filtrer "seulement actifs français" dans explorer vs possible dans top-scored.

**Fix recommandé**: Standardiser sur `market_scope` + `country` (optionnel) partout.

---

### 🔴 CAUSE RACINE #3: Counts Hardcodés / Mismatch

**Symptôme**: Menu "Marchés" affiche des nombres qui ne correspondent pas aux résultats réels.

**Explication**:
- Frontend: certains counts hardcodés ou calculés différemment
- Backend: `/api/metrics/counts` vs `/api/scope-counts` (alias) vs calcul inline

**Exemple de divergence**:
```python
# /api/metrics/counts retourne:
{"US_EU": count_where_active_and_scored, "AFRICA": count_where_active_and_scored}

# Mais /api/assets/top-scored?market_filter=AFRICA:
# Retourne aussi les non-scorés (si EU/AFRICA)!
```

**Fix recommandé**: Un seul endpoint `/api/metrics/counts` avec params `scope`, `only_scored`, `asset_type`.

---

## 5. INCOHÉRENCES DÉTAILLÉES

### 5.1 Tableau Comparatif des Filtres

| Endpoint | active | only_scored | market_scope | market_code | country | region |
|----------|--------|-------------|--------------|-------------|---------|--------|
| /top-scored | ✅ Implicit | ⚠️ Conditional | ✅ | ✅ (via filter) | ❌ | ❌ |
| /explorer | ✅ Implicit | ✅ Param | ✅ | ❌ | ✅ Africa | ✅ Africa |
| /search | ✅ Implicit | ❌ | ✅ Optional | ❌ | ❌ | ❌ |
| /watchlist | ✅ Implicit | ❌ | ✅ Optional | ❌ | ❌ | ❌ |

### 5.2 Problèmes de Pagination

| Endpoint | Style | Default | Max |
|----------|-------|---------|-----|
| /top-scored | limit+offset | 30 | 100 |
| /explorer | page+page_size | 50 | 100 |
| /search | limit only | 20 | 50 |
| /watchlist | none | all | all |

### 5.3 Champs Retournés

**Standard (tous endpoints)**:
```json
{
  "asset_id", "ticker", "symbol", "name", "asset_type",
  "market_scope", "market_code",
  "score_total", "score_value", "score_momentum", "score_safety",
  "confidence"
}
```

**Manquants selon endpoint**:
- `/search`: pas de `coverage`, `liquidity`
- `/watchlist`: pas de `sector`, `industry`
- `/explorer`: pas de `score_breakdown` détaillé

---

## 6. PLAN DE NORMALISATION (ADDITIF)

### Phase 1: Module asset_query.py ✅ IMPLÉMENTÉ (PR3)

Module centralisé créé:
```python
# backend/asset_query.py

from asset_query import AssetQueryBuilder, AssetFilters

# Usage simple
builder = AssetQueryBuilder(store)
filters = AssetFilters(
    market_scope="US_EU",
    only_scored=True,
    asset_type="EQUITY",
    limit=50,
)
results, total = builder.search(filters)

# Méthodes de commodité
top_scored = builder.get_top_scored(market_scope="US_EU", limit=20)
institutional = builder.get_institutional(market_scope="US_EU", min_liquidity_tier="B")
explorer_results, total = builder.get_explorer(market_scope="AFRICA", country="ZA")
```

**Fonctionnalités**:
- Validation des filtres géographiques (scope → region → country)
- Support institutional (score_institutional, lt_score, liquidity_tier)
- Pagination standardisée (limit/offset)
- 29 tests unitaires passés

### Phase 2: Migration Progressive

1. **Ajouter** le module sans casser l'existant
2. **Migrer** chaque endpoint un par un
3. **Tester** avec les mêmes résultats attendus
4. **Déprécier** les anciennes méthodes (pas supprimer)

### Phase 3: Tests

```python
# tests/test_asset_query.py

def test_scope_filtering():
    """US_EU scope ne retourne pas d'actifs AFRICA"""

def test_country_in_scope():
    """country=KE implique scope=AFRICA"""

def test_region_mapping():
    """region=EAST implique countries=[KE, TZ, UG, RW]"""

def test_no_cross_scope_leaks():
    """Aucun actif ne peut être dans deux scopes à la fois"""
```

---

## 7. MAPPING VALIDATION GÉO

### Règles de Validation

```python
GEO_VALIDATION_RULES = {
    # Scope → Regions autorisées
    "scope_regions": {
        "US_EU": [],  # Pas de régions, seulement market_code
        "AFRICA": ["NORTH", "WEST", "CENTRAL", "EAST", "SOUTHERN"],
    },

    # Region → Countries autorisés
    "region_countries": {
        "NORTH": ["EG", "MA", "TN", "DZ", "LY"],
        "WEST": ["NG", "GH", "SN", "CI", "BF", "BJ", "ML", "NE", "TG"],
        "CENTRAL": ["CM", "GA", "CG", "CD"],
        "EAST": ["KE", "TZ", "UG", "RW", "ET"],
        "SOUTHERN": ["ZA", "BW", "MU", "ZM", "ZW", "NA", "MW"],
    },

    # Country → Exchanges autorisés
    "country_exchanges": {
        "KE": ["NSE"],
        "NG": ["NGX"],
        "ZA": ["JSE"],
        "EG": ["EGX"],
        # ...
    },
}
```

### Validation Pipeline

```python
def validate_asset_geography(asset: dict) -> Tuple[bool, List[str]]:
    """
    Valide la cohérence géographique d'un actif.
    Retourne (is_valid, list_of_errors).
    """
    errors = []

    scope = asset.get("market_scope")
    country = asset.get("country_code")
    region = asset.get("region")
    exchange = asset.get("exchange_code")

    # Rule 1: Country implique scope
    if country and country in AFRICA_COUNTRIES:
        if scope != "AFRICA":
            errors.append(f"Country {country} requires scope=AFRICA, got {scope}")

    # Rule 2: Region implique scope
    if region and region in AFRICA_REGIONS:
        if scope != "AFRICA":
            errors.append(f"Region {region} requires scope=AFRICA")

    # Rule 3: Country doit être dans la bonne région
    if country and region:
        expected_region = get_region_for_country(country)
        if expected_region != region:
            errors.append(f"Country {country} should be in {expected_region}, not {region}")

    # Rule 4: Exchange doit correspondre au country
    if exchange and country:
        valid_exchanges = COUNTRY_EXCHANGES.get(country, [])
        if exchange not in valid_exchanges:
            errors.append(f"Exchange {exchange} not valid for country {country}")

    return len(errors) == 0, errors
```

---

## 8. RECOMMANDATIONS PRIORITAIRES

### Urgentes (Bloquantes)

1. **[P0]** Aligner `only_scored` default entre tous les endpoints
2. **[P0]** Créer `asset_query.py` avec règles centralisées
3. **[P0]** Ajouter validation géographique dans pipeline

### Importantes (Haute priorité)

4. **[P1]** Standardiser paramètres: `scope`, `country`, `region` partout
5. **[P1]** Endpoint unique `/api/metrics/counts` avec filtres
6. **[P1]** Frontend: remplacer hardcoded counts par API

### Recommandées (Moyenne priorité)

7. **[P2]** Unifier pagination: toujours `page`+`page_size`
8. **[P2]** Ajouter quarantine table pour assets invalides
9. **[P2]** Tests unitaires règles géo (10+ cas)

---

## 9. CHECKLIST VALIDATION

- [x] Module `asset_query.py` créé avec validation (PR3)
- [x] Tests unitaires asset_query (29 passed) (PR3)
- [x] Emails envoyés après subscription (PR2)
- [x] Counts dynamiques dans frontend (PR4) - endpoint `/api/metrics/counts/v2`
- [x] Page Markets utilise countsV2 avec breakdown scored/unscored (PR4)
- [x] Score affiché partout avec fallback "—" standardisé (PR5)
- [x] Dashboard: PillarBars utilisent `?? null` au lieu de `|| 0` (PR5)
- [x] Constants SCORE_FALLBACK_TEXT et UNSCORED_LABEL dans utils.ts (PR5)
- [x] Helpers formatScore() et isAssetScored() dans utils.ts (PR5)
- [x] DTO AssetResult standardisé dans asset_query.py (PR5)
- [x] Module geo_validation.py avec GeoValidator (PR6)
- [x] Table geo_quarantine pour assets invalides (PR6)
- [x] Endpoints validation: /validation/geo/run, /validation/quarantine (PR6)
- [x] 27 tests de validation géographique passés (PR6)
- [ ] Tous les endpoints migrent vers `asset_query.py`
- [ ] `only_scored` comportement identique partout

---

*Document généré automatiquement - PR1 Audit*
