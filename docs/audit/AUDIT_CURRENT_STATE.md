# 🔍 Audit de l'État Actuel - MarketGPS

## 1. Inventaire Technique

### Frontend (Next.js 13+ App Router)
*   **Routes Clés** : `/`, `/dashboard`, `/dashboard/explorer`, `/dashboard/markets`, `/strategies`, `/barbell`, `/watchlist`, `/settings`.
*   **Variables d'env** : `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_API_BASE_URL` (Mismatch détecté sur les ports 8501 vs 8000).
*   **Services API** : Centralisés dans `frontend/lib/api.ts` et `frontend/lib/config.ts`.
*   **Hooks** : `useUserProfile`, `useQuery` (TanStack Query) utilisé pour le fetching.

### Backend (FastAPI)
*   **Routers** : `api_routes`, `strategies_routes`, `barbell_routes`, `user_routes`.
*   **Sécurité** : JWT + Intégration Supabase (via `security.py`).
*   **Middleware** : CORS configuré sur `CORS_ORIGINS`.
*   **Stockage** : SQLite (via `SQLiteStore`) + Parquet (via `ParquetStore`).

### Pipeline & Data
*   **Entrypoints** : `python -m pipeline.jobs`, `scripts/run_optimized_pipeline.py`.
*   **Scopes** : `US_EU`, `AFRICA`.
*   **Providers** : EODHD (Principal) avec fallback `yfinance` (SmartProvider).

### Déploiement (Docker/Dokploy)
*   **Frontend** : Port 3000. Healthcheck `wget` sur `/`.
*   **Backend** : Port 8000. Healthcheck `curl` sur `/health`.
*   **DB** : `/app/data/marketgps.db` (en cours de migration vers `/app/data/sqlite/marketgps.db` pour supporter le mode WAL).

## 2. Analyse des Mismatches (Gaps)

| Composant | Frontend appelle... | Backend expose... | Statut |
|-----------|-------------------|-------------------|--------|
| **Compteurs** | `/api/scope-counts` | `/api/metrics/counts` | ❌ Mismatch |
| **Barbell** | Port 8501 (parfois) | Port 8000 | ⚠️ Corrigé |
| **Stratégies** | `/api/strategies/templates` | `/api/strategies/templates` | ❌ Table manquante |
| **Explorer** | `/api/assets/explorer` | `/api/assets/explorer` | ✅ OK (0 data) |

## 3. Priorités de Correction

### P0 (Critique - Bloque l'App)
1.  **Données vides** : Exécuter le pipeline pour peupler `scores_latest` et `universe` (active=1).
2.  **Tables manquantes** : Créer les tables de stratégies via migration additive.
3.  **Routers Backend** : Vérifier que `main.py` inclut bien tous les modules.

### P1 (UX / Fonctionnel)
1.  **Compteurs dynamiques** : Aligner `/api/scope-counts` et `/api/metrics/counts`.
2.  **Backtest réel** : Remplacer les mocks de graphiques par les données Parquet.
3.  **Healthcheck** : Sécuriser le `start_period` et l'URL du healthcheck frontend.

### P2 (Dette technique)
1.  **userId** : Passer de 'default' au vrai UUID Supabase.
2.  **Migration Next.js 16** : (Phase 2).
