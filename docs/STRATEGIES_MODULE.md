# Strategies Module - Documentation

## Vue d'Ensemble

Le module Stratégies offre des templates institutionnels prédéfinis que les utilisateurs peuvent personnaliser et simuler.

## Stratégies Disponibles

### 1. Barbell (Haltère)
**Catégorie:** Défensif | **Risque:** Modéré | **Horizon:** 10 ans

Stratégie de Nassim Taleb combinant:
- **Ultra-Safe (85%)**: T-Bills, obligations court terme, money market
- **Crisis Alpha (15%)**: Convexité, tail-risk hedges, managed futures

### 2. Permanent Portfolio
**Catégorie:** Équilibré | **Risque:** Faible | **Horizon:** 20 ans

Harry Browne's All-Weather:
- **Croissance (25%)**: Actions pour la prospérité
- **Déflation (25%)**: Obligations long terme
- **Inflation (25%)**: Or comme hedge inflation
- **Liquidité (25%)**: Cash/T-bills pour les récessions

### 3. Core-Satellite
**Catégorie:** Équilibré | **Risque:** Modéré | **Horizon:** 10 ans

- **Core Equity (50%)**: ETFs diversifiés globaux
- **Core Bond (25%)**: Obligations agrégées
- **Satellites (25%)**: Thématiques, facteurs, picks tactiques

### 4. Risk Parity
**Catégorie:** Équilibré | **Risque:** Modéré | **Horizon:** 15 ans

Allocation par contribution au risque égale:
- **Actions (30%)**
- **Obligations (40%)**
- **Matières Premières (20%)**
- **Alternatifs (10%)**

### 5. Dividend Growth
**Catégorie:** Croissance | **Risque:** Modéré | **Horizon:** 15 ans

Focus sur les dividendes:
- **Dividend Core (70%)**: Aristocrates du dividende
- **High Growth Dividend (20%)**: Croissance rapide des dividendes
- **Yield Boost (10%)**: Rendement élevé

### 6. Factor Investing
**Catégorie:** Croissance | **Risque:** Modéré | **Horizon:** 10 ans

Exposition multi-factorielle:
- **Value (25%)**
- **Momentum (25%)**
- **Quality (25%)**
- **Low Volatility (25%)**

## API Endpoints

### Templates

```
GET /api/strategies/templates
GET /api/strategies/templates?category=balanced
GET /api/strategies/templates?risk_level=low
GET /api/strategies/templates/{slug}
GET /api/strategies/templates/{slug}/compositions
```

### Instruments Éligibles

```
GET /api/strategies/eligible-instruments?block_type=growth
GET /api/strategies/eligible-instruments?block_type=ultra_safe&strategy_slug=barbell
```

Query params:
- `block_type` (requis): Type de bloc (growth, ultra_safe, core, satellite, etc.)
- `strategy_slug` (optionnel): Slug de la stratégie pour contexte
- `limit` (optionnel, min 5): Nombre de résultats

### Simulation

```
POST /api/strategies/simulate
```

Body:
```json
{
  "compositions": [
    {"ticker": "AAPL", "block_name": "growth", "weight": 0.3},
    {"ticker": "MSFT", "block_name": "growth", "weight": 0.2},
    {"ticker": "BND", "block_name": "core_bond", "weight": 0.5}
  ],
  "period_years": 10,
  "initial_value": 10000,
  "rebalance_frequency": "annual"
}
```

Response:
```json
{
  "cagr": 8.5,
  "volatility": 12.3,
  "sharpe": 0.69,
  "max_drawdown": -25.4,
  "final_value": 22500,
  "total_return": 125.0,
  "series": [{"date": "2014-01-31", "value": 10234}],
  "data_quality_score": 85.2,
  "warnings": ["Missing data for XYZ"]
}
```

### Stratégies Utilisateur

```
GET /api/strategies/user?user_id=default
POST /api/strategies/user?user_id=default
GET /api/strategies/user/{strategy_id}?user_id=default
DELETE /api/strategies/user/{strategy_id}?user_id=default
```

Create body:
```json
{
  "name": "Mon Portfolio Growth",
  "description": "Focus croissance US tech",
  "template_id": 3,
  "compositions": [
    {"ticker": "AAPL", "block_name": "satellite", "weight": 0.25},
    {"ticker": "GOOGL", "block_name": "satellite", "weight": 0.25},
    {"ticker": "VOO", "block_name": "core_equity", "weight": 0.50}
  ]
}
```

## Strategy Fit Score

Le **Fit Score** est différent du score global. Il est contextuel au bloc de stratégie:

| Block Type | Critères Prioritaires |
|------------|----------------------|
| `ultra_safe` | Faible vol, faible drawdown, haute liquidité |
| `crisis_alpha` | Tolérance vol, momentum en période de crise |
| `growth` | Score global, momentum, lt_score |
| `inflation_hedge` | Volatilité modérée, safety |
| `core` | Équilibre tous les facteurs |
| `satellite` | Momentum prioritaire, score global |

## Base de Données

### strategy_templates
```sql
CREATE TABLE strategy_templates (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'balanced',
    risk_level TEXT DEFAULT 'moderate',
    horizon_years INTEGER DEFAULT 10,
    rebalance_frequency TEXT DEFAULT 'annual',
    structure_json TEXT NOT NULL,
    scope TEXT DEFAULT 'US_EU'
);
```

### user_strategies
```sql
CREATE TABLE user_strategies (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    template_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    is_template_copy INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
```

## Frontend

### Routes

| Route | Description |
|-------|-------------|
| `/strategies` | Liste des templates avec filtres |
| `/strategies/{slug}` | Builder pour une stratégie |
| `/barbell` | Page dédiée Barbell (accès direct) |

### Composants

- `StrategiesPage` - Liste avec cards et filtres
- `StrategyBuilderPage` - Builder par template
- `CandidatesTable` - Instruments éligibles paginés
- `BarbellBuilder` - Builder spécialisé Barbell

## Usage

### 1. Choisir un Template
Accédez à `/strategies` et sélectionnez un template.

### 2. Personnaliser
Sur la page du template:
- Parcourez les blocs
- Ajoutez des instruments depuis la liste des éligibles
- Ajustez les poids (total = 100%)

### 3. Simuler
- Sélectionnez la période (5, 10, 20 ans)
- Définissez le capital initial
- Lancez la simulation

### 4. Analyser
Consultez les métriques:
- CAGR
- Volatilité annualisée
- Ratio de Sharpe
- Max Drawdown
- Valeur finale
- Rendement total

### 5. Sauvegarder (optionnel)
Sauvegardez votre stratégie personnalisée pour y revenir plus tard.

## Tests

```bash
# Tests backend
pytest tests/test_strategies_endpoints.py -v
pytest tests/test_barbell_endpoints.py -v
```

## Notes Techniques

- **Données**: Utilise les fichiers Parquet OHLCV pour les backtests
- **Scope**: US_EU uniquement (Africa support futur)
- **Rebalancing**: Annuel par défaut (monthly/quarterly disponibles)
- **Risk-Free Rate**: 0% pour le calcul du Sharpe
- **Cache**: Les simulations peuvent être cachées via `composition_hash`
