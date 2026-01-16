# Quality & Liquidity Adjustments Patch (US_EU)

## Problème résolu

**Symptôme**: Des small caps / titres illiquides avec données faibles apparaissaient avec de très bonnes notes (80-100).

**Cause racine**: Le scoring était basé uniquement sur les indicateurs de prix (RSI, momentum, volatilité) sans pénaliser suffisamment :
- La faible liquidité (ADV_USD < 250K)
- La mauvaise couverture de données (< 85%)
- Les prix "stale" (non mis à jour)
- Les jours avec volume zéro

**Solution**: Patch minimal qui injecte des pénalités et caps basés sur les métriques d'investabilité, uniquement pour US_EU.

## Modifications apportées

### 1. Nouveau module: `pipeline/quality_adjustments.py`

**Fonctions ajoutées**:
- `compute_investability_metrics(df)`: Calcule ADV_USD, zero_volume_ratio, stale_ratio, coverage
- `compute_data_confidence(...)`: Calcule un score de confiance 0-100 basé sur la qualité des données
- `apply_quality_liquidity_adjustments(...)`: Applique les pénalités et caps au score brut

### 2. Modifications dans `pipeline/gating.py`

**Changements**:
- Pour US_EU uniquement: utilise `compute_investability_metrics()` au lieu des méthodes originales
- Calcule `data_confidence` avec la nouvelle formule (pénalités linéaires)
- Stocke ADV_USD dans `gating_status.liquidity` (réutilisation du champ existant)

**Lignes modifiées**: `_evaluate_asset()` méthode

### 3. Modifications dans `pipeline/rotation.py`

**Changements**:
- Juste avant d'écrire `scores_latest`: applique `apply_quality_liquidity_adjustments()`
- Met à jour `score_total` avec la valeur ajustée
- Met à jour `confidence` avec `min(existing, gating.data_confidence)`
- Merge les métriques de debug dans `json_breakdown`

**Lignes modifiées**: `_process_asset()` méthode, juste avant `upsert_score()`

## Formule d'ajustement

```
1. Multiplicateur de confiance:
   score_after_confidence = raw_score * (data_confidence/100)^1.6

2. Pénalité liquidité:
   liquidity_penalty = 0 si ADV >= 2M USD
                      sinon (2M - ADV) / 2M * 35
   score_after_penalty = score_after_confidence - liquidity_penalty

3. Caps durs:
   - Si ADV < 250K USD → cap à 60
   - Si coverage < 85% → cap à 65
   - Si stale_ratio > 10% → cap à 55
   - Si zero_volume_ratio > 5% → cap à 55

4. Score final = clamp(score_after_penalty, 0, 100) avec caps appliqués
```

## Data Confidence (0-100)

```
base = 100
- Pénalité coverage: -40 max (linéaire si < 85%)
- Pénalité ADV: -35 max (linéaire si < 2M USD)
- Pénalité stale: -25 max (linéaire si > 5%)
- Pénalité zero_vol: -20 max (linéaire si > 2%)
confidence = clamp(base - penalties, 5, 100)
```

## Exemple de json_breakdown généré

```json
{
  "version": "1.1",
  "weights": {"momentum": 0.4, "safety": 0.3, "value": 0.3},
  "features": {
    "rsi": 65.2,
    "vol_annual": 18.5,
    "raw_score_total": 87.5,
    "adv_usd": 150000.0,
    "coverage": 0.75,
    "stale_ratio": 0.12,
    "zero_volume_ratio": 0.08,
    "data_confidence": 28,
    "confidence_multiplier": 0.1234,
    "score_after_confidence": 10.8,
    "liquidity_penalty": 32.4,
    "score_after_penalty": -21.6,
    "caps_applied": [
      "ADV < 250,000 USD → cap at 60",
      "Coverage < 85% → cap at 65",
      "Stale ratio > 10% → cap at 55",
      "Zero volume ratio > 5% → cap at 55"
    ],
    "final_score_total": 55.0
  }
}
```

## Validation SQL

```sql
-- Vérifier que les illiquides ne dominent plus le Top 50
SELECT 
    u.symbol,
    u.name,
    s.score_total,
    s.confidence,
    g.liquidity as adv_usd,
    g.coverage,
    g.stale_ratio,
    g.eligible,
    g.reason
FROM scores_latest s
JOIN universe u ON s.asset_id = u.asset_id
JOIN gating_status g ON g.asset_id = s.asset_id
WHERE u.market_scope = 'US_EU'
ORDER BY s.score_total DESC
LIMIT 50;
```

**Résultat attendu**:
- Les assets avec ADV < 250K ne devraient plus avoir score > 60
- Les assets avec coverage < 85% ne devraient plus avoir score > 65
- Les assets avec stale_ratio > 10% ne devraient plus avoir score > 55

## Tests

Exécuter les tests:
```bash
python -m pytest tests/test_quality_adjustments.py -v
```

## Notes d'implémentation

1. **Scope**: Uniquement US_EU. AFRICA n'est pas affecté.

2. **Rétrocompatibilité**: 
   - Les champs DB existants sont réutilisés (`liquidity` pour ADV_USD)
   - Les scores AFRICA continuent de fonctionner normalement
   - Si gating n'est pas disponible, le score brut est utilisé (fallback)

3. **Robustesse**:
   - Si DataFrame vide → metrics = 0, confidence = 5, eligible = False
   - Si calcul échoue → fallback sur méthodes originales
   - Tous les calculs sont protégés par try/except

4. **Performance**:
   - Calculs effectués uniquement pour US_EU
   - Pas d'appels réseau supplémentaires
   - Utilise uniquement données Parquet déjà chargées

## Pourquoi ça fonctionnait avant (et plus maintenant)

**Avant**: Un small cap avec un bon momentum (RSI optimal, prix au-dessus SMA200) pouvait obtenir 85-90/100 même avec:
- ADV de 50K USD (illiquide)
- Coverage de 60% (données incomplètes)
- 20% de jours stale (prix non mis à jour)

**Maintenant**: Le même asset verra:
- `data_confidence` = ~25 (pénalités coverage + ADV + stale)
- `confidence_multiplier` = (25/100)^1.6 = 0.08
- `score_after_confidence` = 85 * 0.08 = 6.8
- `liquidity_penalty` = 32 points
- Caps appliqués → `final_score` = 55 (cap stale_ratio)

Le score reflète maintenant la **qualité investable** et pas seulement le momentum technique.
