# 📊 Stratégie de Sources de Données - MarketGPS

## Vue d'ensemble

Ce document décrit comment connecter les différentes sources de données pour alimenter tous les types d'instruments financiers dans MarketGPS.

---

## 1. Sources Recommandées par Instrument

### 🏢 Actions (EQUITY)

| Région | Source Primaire | Source Backup | Coût |
|--------|-----------------|---------------|------|
| **USA** | EODHD | yfinance | $20/mois |
| **Europe** | EODHD (.PA, .DE, .AS, .MI) | yfinance | Inclus |
| **Afrique** | EODHD (.JSE) + CSV manuel | - | Inclus |

**Configuration EODHD :**
```bash
# Dans .env
EODHD_API_KEY=your_api_key_here
```

**Suffixes par exchange :**
- USA: `.US` (AAPL.US)
- France: `.PA` (BNP.PA)
- Allemagne: `.DE` (BMW.DE)
- Pays-Bas: `.AS` (ASML.AS)
- Italie: `.MI` (ENI.MI)
- UK: `.LSE` (BARC.LSE)
- Afrique du Sud: `.JSE` (AGL.JSE)
- Nigeria: `.NSE`

---

### 📈 ETF

| Source | Couverture | Coût |
|--------|-----------|------|
| **EODHD** | USA, Europe | Inclus avec Actions |
| **yfinance** | Backup | Gratuit |

---

### 💱 Forex (FX)

| Source | Paires | Coût |
|--------|--------|------|
| **yfinance** | Majeures (EURUSD, GBPUSD...) | Gratuit |
| **OANDA** | Toutes + historique tick | $$ |
| **Polygon.io** | Toutes | $29/mois |

**Format yfinance :** `EURUSD=X`, `GBPJPY=X`

**Paires recommandées pour démarrer :**
```
EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD,
EURGBP, EURJPY, GBPJPY, XAUUSD (Or)
```

---

### 📜 Obligations (BOND)

| Source | Couverture | Coût |
|--------|-----------|------|
| **FRED** | Treasuries US, taux | Gratuit (API key) |
| **yfinance** | Indices obligataires | Gratuit |

**Symboles clés :**
```
^TNX  - US 10-Year Treasury Yield
^IRX  - US 13-Week Treasury Bill
^TYX  - US 30-Year Treasury Yield
^FVX  - US 5-Year Treasury Yield
```

**FRED API Key :** https://fred.stlouisfed.org/docs/api/api_key.html

---

### ₿ Crypto

| Source | Couverture | Coût |
|--------|-----------|------|
| **CoinGecko** | Top 500+ coins | Gratuit (30 req/min) |
| **yfinance** | Top 20 | Gratuit |
| **Binance API** | Toutes | Gratuit |

**Top cryptos à intégrer :**
```
BTC, ETH, BNB, XRP, ADA, SOL, DOGE, DOT, MATIC, LTC,
AVAX, LINK, UNI, ATOM, XLM
```

---

### ⏳ Futures

| Source | Couverture | Coût |
|--------|-----------|------|
| **yfinance** | Indices, commodités | Gratuit |
| **Quandl** | Historique long | Gratuit/Payant |

**Symboles yfinance :**
```
ES=F   - S&P 500 E-mini
NQ=F   - Nasdaq 100 E-mini
YM=F   - Dow Jones E-mini
CL=F   - Crude Oil
GC=F   - Gold
SI=F   - Silver
NG=F   - Natural Gas
```

---

### 📊 Options

**⚠️ Complexité élevée** - Nécessite un provider spécialisé

| Source | Fonctionnalités | Coût |
|--------|----------------|------|
| **Tradier** | Chaînes d'options, Greeks | $$ |
| **IBKR API** | Complet | Compte broker |
| **CBOE** | Données officielles | $$$ |

**Recommandation :** Commencer par Tradier pour les options US.

---

### 🌾 Matières Premières (COMMODITY)

Même sources que Futures :
```
GC=F   - Or
SI=F   - Argent
CL=F   - Pétrole brut
NG=F   - Gaz naturel
ZW=F   - Blé
ZC=F   - Maïs
ZS=F   - Soja
KC=F   - Café
CT=F   - Coton
```

---

## 2. Plan d'Implémentation

### Phase 1 : Compléter les données actuelles (1 semaine)
- [ ] Exécuter le pipeline de scoring pour US_EU
- [ ] Télécharger les données de prix européennes via EODHD
- [ ] Importer les données africaines depuis CSV externe

### Phase 2 : Ajouter Forex & Crypto (1 semaine)
- [ ] Intégrer CoinGecko pour crypto
- [ ] Ajouter les paires Forex via yfinance
- [ ] Créer les assets dans universe

### Phase 3 : Obligations & Futures (1 semaine)
- [ ] Configurer FRED API pour bonds US
- [ ] Ajouter les futures majeurs
- [ ] Adapter le scoring pour ces asset types

### Phase 4 : Options (optionnel)
- [ ] Évaluer Tradier API
- [ ] Implémenter le provider d'options
- [ ] Créer un scoring spécifique

---

## 3. Commandes Utiles

### Calculer les scores pour tous les actifs US/EU :
```bash
cd /Users/cyrilsohnde/Documents/MarketGPS
python -m pipeline.jobs rotation --scope US_EU --limit 500
```

### Calculer les scores pour l'Afrique :
```bash
python -m pipeline.jobs rotation --scope AFRICA
```

### Importer un univers depuis CSV :
```bash
python -m pipeline.jobs init-universe --scope AFRICA --from-csv data/universe/africa_stocks.csv
```

### Mettre à jour le gating (couverture, liquidité) :
```bash
python -m pipeline.jobs gating --scope US_EU
```

---

## 4. Configuration Recommandée (.env)

```bash
# Data Providers
EODHD_API_KEY=your_eodhd_key
FRED_API_KEY=your_fred_key

# Optionnel
POLYGON_API_KEY=your_polygon_key
TRADIER_API_KEY=your_tradier_key
COINGECKO_API_KEY=optional_pro_key

# Database
SQLITE_PATH=data/sqlite/marketgps.db

# Supabase (Auth)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
```

---

## 5. Coûts Estimés

| Configuration | Sources | Coût/mois |
|---------------|---------|-----------|
| **Minimal** | yfinance + CoinGecko + FRED | **Gratuit** |
| **Standard** | + EODHD | **~$20** |
| **Complet** | + Polygon + Tradier | **~$80** |

---

## 6. Priorités pour votre cas

1. **Immédiat** : Lancer le scoring sur les 3552 actifs US_EU existants
2. **Court terme** : Ajouter les suffixes européens corrects (.PA, .DE, etc.)
3. **Moyen terme** : Intégrer Forex et Crypto (marchés très demandés)
4. **Long terme** : Options et instruments complexes

---

## Questions fréquentes

**Q: Pourquoi mes actifs européens n'ont pas de score ?**
A: Le pipeline n'a pas encore téléchargé les données de prix. Lancez :
```bash
python -m pipeline.jobs rotation --scope US_EU
```

**Q: Comment ajouter un nouvel actif ?**
A: Ajoutez-le dans la table `universe` puis lancez le scoring :
```sql
INSERT INTO universe (asset_id, symbol, name, asset_type, market_scope, market_code, active)
VALUES ('BNP.PA', 'BNP', 'BNP Paribas', 'EQUITY', 'US_EU', 'FR', 1);
```

**Q: Les données Afrique viennent d'où ?**
A: Pipeline séparé (`scoring_africa.py`) qui utilise des sources locales ou CSV.
