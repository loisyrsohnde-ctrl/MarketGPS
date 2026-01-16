# MarketGPS - Contrat Fonctionnel Frontend

> Ce document définit le contrat entre le frontend Next.js et le backend existant.
> **AUCUNE LOGIQUE MÉTIER NE DOIT ÊTRE MODIFIÉE** - Le frontend consomme les données existantes.

---

## 📄 Pages de l'Application

| Route | Description | Auth Required |
|-------|-------------|---------------|
| `/` | Landing page publique | ❌ |
| `/pricing` | Plans et tarification | ❌ |
| `/login` | Connexion utilisateur | ❌ |
| `/signup` | Création de compte | ❌ |
| `/reset-password` | Réinitialisation mot de passe | ❌ |
| `/dashboard` | Tableau de bord principal | ✅ |
| `/dashboard/explorer` | Explorer tous les actifs (3000+) | ✅ |
| `/asset/[ticker]` | Détail d'un actif | ✅ |
| `/watchlist` | Liste de suivi utilisateur | ✅ |
| `/settings` | Paramètres compte | ✅ |
| `/settings/billing` | Gestion abonnement Stripe | ✅ |

---

## 🎯 Actions Utilisateur

### Navigation
- [ ] Ouvrir/fermer sidebar
- [ ] Naviguer entre les sections (Dashboard, Watchlist, Markets, Settings)
- [ ] Rechercher un actif (barre de recherche globale)

### Dashboard
- [ ] Voir les top scorés (liste paginée)
- [ ] Filtrer par marché (US, Europe, Afrique)
- [ ] Filtrer par type (ETF, Actions, FX, Obligations)
- [ ] Sélectionner un actif pour voir les détails
- [ ] Changer la période du graphique (30j, 1y, 5y, 10y)
- [ ] Cliquer "Voir plus" pour accéder à l'explorer complet

### Watchlist
- [ ] Ajouter un actif à la watchlist
- [ ] Retirer un actif de la watchlist
- [ ] Voir tous les actifs suivis

### Asset Detail
- [ ] Voir le score total et les piliers (Valeur, Momentum, Sécurité)
- [ ] Voir les KPIs (Couverture, Liquidité, Risque FX)
- [ ] Voir le graphique de prix
- [ ] Accéder aux liens externes (Yahoo Finance, Google Finance)

### Auth
- [ ] S'inscrire avec email/password
- [ ] Se connecter
- [ ] Réinitialiser le mot de passe
- [ ] Se déconnecter

### Billing
- [ ] Voir le plan actuel
- [ ] Souscrire à un plan (Stripe Checkout)
- [ ] Gérer l'abonnement

---

## 🔌 Endpoints API

> Base URL: `NEXT_PUBLIC_API_BASE_URL` (env variable)
> Auth Header: `Authorization: Bearer {access_token}`

### Assets

```typescript
// GET /api/assets/top-scored
// Récupère les actifs les mieux scorés
interface TopScoredParams {
  limit?: number;        // default: 30
  offset?: number;       // default: 0
  market_scope?: 'US_EU' | 'AFRICA';
  asset_type?: 'ETF' | 'EQUITY' | 'FX' | 'BOND' | null;
  market_filter?: 'US' | 'EU' | 'ALL';
}

interface TopScoredResponse {
  assets: Asset[];
  total: number;
  page: number;
  limit: number;
}

// GET /api/assets/search?q={query}
// Recherche d'actifs
interface SearchParams {
  q: string;
  market_scope?: string;
  limit?: number;
}

// GET /api/assets/{ticker}
// Détail d'un actif
interface AssetDetailResponse {
  asset_id: string;
  ticker: string;
  symbol: string;
  name: string;
  asset_type: string;
  market_scope: string;
  market_code: string;
  score_total: number | null;
  score_value: number | null;
  score_momentum: number | null;
  score_safety: number | null;
  coverage: number | null;
  liquidity: number | null;
  fx_risk: number | null;
  updated_at: string;
}

// GET /api/assets/{ticker}/chart?period={period}
// Données graphique
interface ChartParams {
  period: '30d' | '1y' | '5y' | '10y';
}

interface ChartResponse {
  data: {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
  }[];
}
```

### Watchlist

```typescript
// GET /api/watchlist
// Liste des actifs suivis
interface WatchlistResponse {
  items: Asset[];
}

// POST /api/watchlist
// Ajouter à la watchlist
interface AddWatchlistBody {
  asset_id: string;
  ticker: string;
  market_code?: string;
}

// DELETE /api/watchlist/{asset_id}
// Retirer de la watchlist
```

### Metrics

```typescript
// GET /api/metrics/counts
// Compteurs par scope
interface CountsResponse {
  US_EU: number;
  AFRICA: number;
}

// GET /api/metrics/landing
// Métriques pour landing page
interface LandingMetricsResponse {
  total_assets: number;
  avg_score: number;
  top_performer: Asset;
}
```

### Auth (Supabase)

```typescript
// Utilise le SDK Supabase directement
// - supabase.auth.signUp({ email, password })
// - supabase.auth.signInWithPassword({ email, password })
// - supabase.auth.resetPasswordForEmail(email)
// - supabase.auth.updateUser({ password })
// - supabase.auth.signOut()
```

### Billing (Stripe)

```typescript
// POST /api/billing/checkout-session
// Crée une session Stripe Checkout
interface CheckoutBody {
  plan: 'monthly' | 'yearly';
  success_url: string;
  cancel_url: string;
}

interface CheckoutResponse {
  checkout_url: string;
}

// GET /api/billing/subscription
// Récupère l'abonnement actuel
interface SubscriptionResponse {
  plan: 'free' | 'monthly' | 'yearly';
  status: 'active' | 'canceled' | 'past_due';
  current_period_end?: string;
}
```

---

## 📊 Modèles de Données

### Asset
```typescript
interface Asset {
  asset_id: string;          // ex: "AAPL.US"
  ticker: string;            // ex: "AAPL"
  symbol: string;            // ex: "AAPL"
  name: string;              // ex: "Apple Inc."
  asset_type: 'ETF' | 'EQUITY' | 'FX' | 'BOND';
  market_scope: 'US_EU' | 'AFRICA';
  market_code: string;       // ex: "US", "XETRA", "PA"
  score_total: number | null;      // 0-100
  score_value: number | null;      // 0-100
  score_momentum: number | null;   // 0-100
  score_safety: number | null;     // 0-100
  coverage: number | null;         // 0-100 (%)
  liquidity: number | null;        // 0-1
  fx_risk: number | null;          // 0-1
  updated_at: string;
}
```

### User
```typescript
interface User {
  id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  plan: 'free' | 'monthly' | 'yearly';
  daily_quota_used: number;
  daily_quota_limit: number;
}
```

---

## 🎨 Score Color Mapping

| Range | Couleur | Label |
|-------|---------|-------|
| 0-30 | `#EF4444` (rouge) | Faible |
| 31-60 | `#F59E0B` (jaune/orange) | Stable |
| 61-75 | `#4ADE80` (vert clair) | Élevée |
| 76-100 | `#22C55E` (vert) | Dynamique |

---

## ⚙️ Variables d'Environnement

```env
# API Backend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_xxx

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## ✅ Checklist de Validation

### Visuel
- [ ] Glassmorphism cohérent sur toutes les cartes
- [ ] Couleurs fidèles au design system
- [ ] Contrastes suffisants (WCAG AA)
- [ ] Animations subtiles et performantes
- [ ] Responsive (desktop → tablette → mobile)

### Fonctionnel
- [ ] Recherche d'actifs fonctionne
- [ ] Filtres (marché, type) fonctionnent
- [ ] Pagination/scroll infini sur explorer
- [ ] Watchlist add/remove fonctionne
- [ ] Graphique change selon période
- [ ] Auth flow complet (signup → confirm → login → logout)
- [ ] Stripe checkout redirige correctement

### Performance
- [ ] Skeleton loaders pendant chargement
- [ ] Virtualisation pour listes > 100 items
- [ ] Images lazy-loaded
- [ ] Bundle < 200kb (gzipped)

---

*Ce contrat est la source de vérité pour le développement frontend.*
