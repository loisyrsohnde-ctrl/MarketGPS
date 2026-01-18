# 📝 Changelog - MarketGPS

## 18 Janvier 2026

### 📊 Module Stratégies Institutionnelles Complet

#### 6 Templates de Stratégies Disponibles

| Slug | Nom | Catégorie | Risque | Horizon |
|------|-----|-----------|--------|---------|
| `barbell` | Barbell (Haltère) | Défensif | Modéré | 10 ans |
| `permanent` | Permanent Portfolio | Équilibré | Faible | 20 ans |
| `core_satellite` | Core-Satellite | Équilibré | Modéré | 10 ans |
| `risk_parity` | Risk Parity | Équilibré | Modéré | 15 ans |
| `dividend_growth` | Dividend Growth | Croissance | Modéré | 15 ans |
| `factor_investing` | Factor Investing | Croissance | Modéré | 10 ans |

#### Backend: `backend/strategies_routes.py`
- ✅ `GET /api/strategies/templates` - Liste tous les templates
- ✅ `GET /api/strategies/templates/{slug}` - Détail d'un template
- ✅ `GET /api/strategies/templates/{slug}/compositions` - Compositions par défaut
- ✅ `GET /api/strategies/eligible-instruments` - Instruments éligibles par bloc
- ✅ `POST /api/strategies/simulate` - Backtest simulation
- ✅ `GET /api/strategies/user` - Liste stratégies utilisateur
- ✅ `POST /api/strategies/user` - Créer stratégie
- ✅ `GET /api/strategies/user/{id}` - Détail stratégie
- ✅ `DELETE /api/strategies/user/{id}` - Supprimer stratégie

#### Strategy Fit Score
Score contextuel (0-100) calculé par bloc de stratégie:
- `ultra_safe` - Privilégie faible volatilité, faible drawdown
- `crisis_alpha` - Tolérance volatilité, convexité en crise
- `growth` - Score global + momentum + lt_score
- `inflation_hedge` - Volatilité modérée acceptable
- `core` - Équilibre tous les facteurs
- `satellite` - Momentum prioritaire

#### Frontend
- ✅ `/strategies` - Liste des templates avec filtres catégorie/risque
- ✅ `/strategies/[slug]` - Builder par stratégie:
  - Navigation par blocs
  - Instruments éligibles avec Fit Score
  - Composition éditable
  - Simulation avec métriques
  - Sauvegarde stratégie

#### SQL: `storage/migrations/add_strategy_tables.sql`
- `strategy_templates` - Templates prédéfinis
- `strategy_template_compositions` - Compositions par défaut
- `user_strategies` - Stratégies utilisateur
- `user_strategy_compositions` - Instruments par stratégie
- `strategy_simulations` - Cache des simulations
- `strategy_instrument_eligibility` - Cache d'éligibilité

#### Tests
- ✅ `tests/test_strategies_endpoints.py` - Tests complets

---

### 🏋️ Barbell Strategy Builder - Interactive Module

#### Nouveaux Fichiers Backend
- ✅ `backend/barbell_service.py` - Moteur de simulation avec données Parquet
- ✅ `storage/migrations/add_barbell_tables.sql` - Tables SQLite pour persistance

#### Endpoints Backend Ajoutés (ADDITIFS)
- ✅ `GET /api/barbell/candidates/core` - Candidats Core avec filtres & pagination
- ✅ `GET /api/barbell/candidates/satellite` - Candidats Satellite avec filtres
- ✅ `POST /api/barbell/simulate` - Backtest simulation (CAGR, Sharpe, etc.)
- ✅ `GET /api/barbell/portfolios` - Liste des portfolios sauvegardés
- ✅ `POST /api/barbell/portfolios` - Créer un portfolio
- ✅ `GET /api/barbell/portfolios/{id}` - Détail portfolio
- ✅ `PUT /api/barbell/portfolios/{id}` - Modifier portfolio
- ✅ `DELETE /api/barbell/portfolios/{id}` - Supprimer portfolio

#### Nouveaux Composants Frontend
- ✅ `components/barbell/asset-drawer.tsx` - Drawer détail actif avec breakdown
- ✅ `components/barbell/candidates-table.tsx` - Tables paginées avec filtres
- ✅ `components/barbell/barbell-builder.tsx` - Composition éditable + simulation
- ✅ `components/barbell/index.ts` - Index exports

#### Page Barbell Enrichie
- ✅ `app/barbell/page.tsx` - Refonte complète avec 3 onglets:
  - 💡 Suggestion - Portfolio suggéré par profil de risque
  - 📋 Candidats - Tables paginées Core/Satellite avec recherche
  - 🔧 Builder - Composition éditable + simulation backtest

#### Fonctionnalités Simulation
- ✅ Périodes: 5, 10, 20 ans
- ✅ Rebalancement: mensuel, trimestriel, annuel
- ✅ Métriques: CAGR, Volatilité, Sharpe, Max Drawdown
- ✅ Equity curve avec chart interactif
- ✅ Performance annuelle (meilleure/pire année)
- ✅ Warnings pour données insuffisantes

#### Documentation
- ✅ `docs/BARBELL_BUILDER.md` - Documentation complète du module

#### Tests
- ✅ `tests/test_barbell_endpoints.py` - Tests unitaires endpoints

#### 🛡️ Garantie Zero Breaking Change
- ✅ Aucun fichier existant modifié destructivement
- ✅ Aucune route existante renommée
- ✅ Aucune table existante altérée
- ✅ Module 100% additif

---

## 12 Janvier 2026

### 🧹 Nettoyage et Archivage

#### Supprimés/Archivés
- ✅ `app/` → Archivé dans `_archive/streamlit_old/app/`
  - Ancien interface Streamlit
  - Pages, composants, configuration Streamlit
  - À ne plus utiliser
  
- ✅ `download_logos.sh` → Archivé dans `_archive/streamlit_old/`
- ✅ `download_logos_robust.py` → Archivé dans `_archive/streamlit_old/`

#### Créés (Documentation & Configuration)
- ✅ `PROJECT_STRUCTURE.md` - Architecture du projet
- ✅ `CLEANUP_SUMMARY.md` - Résumé du nettoyage
- ✅ `QUICK_START.md` - Guide de démarrage rapide
- ✅ `CHANGELOG.md` - Ce fichier
- ✅ `_archive/streamlit_old/README.md` - Doc archivage
- ✅ `.gitignore` - Fichiers à ignorer
- ✅ `frontend/lib/config.ts` - Configuration centralisée API
- ✅ `frontend/lib/api-client.ts` - Client HTTP unifié

### 📋 Raison de l'Archivage

**Streamlit était utilisé pour :**
- Interface utilisateur prototype
- Dashboard initial

**Pourquoi Next.js ?**
- ✅ Meilleure performance
- ✅ UX moderne et responsive
- ✅ TypeScript natif
- ✅ Déploiement plus facile
- ✅ Écosystème React mature

---

## Structure Actuelle

### ✅ Frontend (Next.js)
- Exclusif et unique interface utilisateur
- Port : 3000
- Tech : React 18 + TypeScript + Tailwind

### ✅ Backend (FastAPI)
- API centralisée
- Port : 8501
- Tech : Python + FastAPI + Supabase

### ✅ Logique Partagée
- `core/` - Modèles et utilitaires
- `providers/` - Fournisseurs de données
- `auth/` - Authentification
- `storage/` - Persistance

### ❌ Streamlit (Archivé)
- Plus utilisé
- Conservé à titre historique
- Inaccessible depuis la racine pour éviter confusion

---

## Configuration Requise

### Frontend
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8501
```

### Backend
```bash
# .env
# Configuration Stripe, Supabase, etc.
```

---

## Points d'Attention

1. **Import Old Code**
   - ❌ Ne pas réimporter l'ancien code Streamlit
   - ✅ Utiliser exclusivement Next.js

2. **API Communication**
   - ✅ Utiliser `frontend/lib/api-client.ts`
   - ✅ Configurer endpoints dans `frontend/lib/config.ts`

3. **Port Conflicts**
   - ✅ Frontend : 3000
   - ✅ Backend : 8501

---

## Prochaines Étapes

- [ ] Vérifier tous les endpoints API
- [ ] Tester les boutons "Suivre"
- [ ] Tester l'authentification
- [ ] Vérifier CORS
- [ ] Documenter les endpoints manquants
- [ ] Commit et push des changements

---

**Archivé par :** AI Assistant (Claude)  
**Date :** 12 Janvier 2026  
**Status :** ✅ Complet
