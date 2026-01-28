# MarketGPS Mobile - API Endpoints Map

Ce document liste tous les endpoints backend consommés par l'application mobile.

## Base URL

```
Production: https://api.marketgps.online
Development: http://localhost:8501
```

## Authentification

Toutes les requêtes authentifiées incluent le header:
```
Authorization: Bearer <supabase_jwt_token>
```

---

## Endpoints Utilisés

### 1. Assets

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/assets/top-scored` | GET | Non | Top assets par score | Dashboard, Explorer |
| `/api/assets/search` | GET | Non | Recherche d'actifs | Explorer |
| `/api/assets/explorer` | GET | Non | Liste paginée avec filtres | Explorer |
| `/api/assets/{ticker}` | GET | Non | Détail d'un actif | Asset Detail |
| `/api/assets/{ticker}/chart` | GET | Non | Données de graphique | Asset Detail |

**Paramètres communs:**
- `market_scope`: `US_EU` | `AFRICA`
- `asset_type`: `EQUITY` | `ETF` | `BOND` | `FX` | `CRYPTO`
- `limit`, `offset` ou `page`, `page_size`

### 2. Watchlist

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/watchlist` | GET | Oui* | Liste watchlist | Watchlist |
| `/api/watchlist` | POST | Oui* | Ajouter à watchlist | Asset Detail |
| `/api/watchlist/{ticker}` | DELETE | Oui* | Retirer de watchlist | Watchlist, Asset Detail |
| `/api/watchlist/check/{ticker}` | GET | Oui* | Vérifier si dans watchlist | Asset Detail |

*Auth optionnelle - utilise `user_id=default` si non authentifié

### 3. Metrics

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/metrics/counts` | GET | Non | Compteurs par scope | Dashboard, Markets |
| `/api/metrics/landing` | GET | Non | Métriques landing | Dashboard |

### 4. News

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/news` | GET | Non | Feed paginé | News |
| `/api/news/{slug}` | GET | Non | Article détail | News Article |
| `/api/news/regions` | GET | Non | Liste régions | News |

**Paramètres:**
- `page`, `page_size`
- `country`: Code pays (NG, ZA, KE, etc.)
- `tag`: fintech, startup, vc, banking, crypto

### 5. Strategies

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/strategies/templates` | GET | Non | Liste templates | Strategies |
| `/api/strategies/templates/{slug}` | GET | Non | Détail template | Strategy Detail |
| `/api/strategies/eligible-instruments` | GET | Non | Instruments par bloc | Strategy Detail |
| `/api/strategies/simulate` | POST | Non | Simulation stratégie | Strategy Detail |

### 6. Barbell

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/barbell/suggest` | GET | Non | Suggestion portefeuille | Barbell Builder |
| `/api/barbell/candidates/core` | GET | Non | Candidats Core | Barbell Builder |
| `/api/barbell/candidates/satellite` | GET | Non | Candidats Satellite | Barbell Builder |

**Paramètres:**
- `risk_profile`: conservative | moderate | aggressive
- `market_scope`: US_EU | AFRICA
- `core_count`, `satellite_count`

### 7. Billing

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/api/billing/me` | GET | Oui | Statut abonnement | Settings, Billing |
| `/api/billing/checkout-session` | POST | Oui | Créer session Stripe | Checkout |
| `/api/billing/portal-session` | POST | Oui | Créer portail Stripe | Billing |

### 8. User

| Endpoint | Méthode | Auth | Description | Écran Mobile |
|----------|---------|------|-------------|--------------|
| `/users/profile` | GET | Oui | Profil utilisateur | Profile |
| `/users/profile/update` | POST | Oui | Mettre à jour profil | Profile |
| `/users/notifications` | GET | Oui | Préférences notifications | Notifications |
| `/users/notifications/update` | POST | Oui | MAJ notifications | Notifications |
| `/users/notifications/unread-count` | GET | Oui | Compteur non lus | Dashboard |

---

## Endpoints NON Utilisés (mais disponibles)

Ces endpoints existent dans le backend mais ne sont pas (encore) consommés par le mobile:

| Endpoint | Raison |
|----------|--------|
| `/api/assets/top-scored-institutional` | Feature avancée, phase 2 |
| `/api/assets/{ticker}/score` | Scoring on-demand, phase 2 |
| `/api/user/quota` | Affichage quota, phase 2 |
| `/api/strategies/user` | Stratégies sauvegardées, phase 2 |
| `/api/strategies/ai-suggest` | AI suggestions, phase 2 |
| `/api/strategies/ai-generate` | AI generation, phase 2 |
| `/api/barbell/portfolios` | Portefeuilles sauvegardés, phase 2 |
| `/api/barbell/simulate` | Simulation barbell, phase 2 |
| `/users/avatar/upload` | Upload avatar, phase 2 |
| `/users/security/change-password` | Géré via Supabase |
| `/users/delete-account` | Géré via portail |

---

## Endpoints Manquants (TODO Backend)

Ces endpoints seraient utiles mais n'existent pas encore:

| Endpoint Proposé | Description | Priorité |
|------------------|-------------|----------|
| `/api/news/featured` | Articles mis en avant | Moyenne |
| `/api/user/preferences` | Préférences app (langue, etc.) | Basse |
| `/api/assets/{ticker}/similar` | Actifs similaires | Basse |
| `/api/alerts` | Alertes prix/score | Moyenne |
| `/api/push/register` | Enregistrer token push | Haute |

---

## Codes de Réponse

| Code | Signification | Action Mobile |
|------|---------------|---------------|
| 200 | Succès | Afficher données |
| 201 | Créé | Succès + refresh |
| 400 | Mauvaise requête | Afficher erreur |
| 401 | Non authentifié | Rediriger login |
| 403 | Non autorisé | Afficher paywall |
| 404 | Non trouvé | Afficher état vide |
| 429 | Rate limit | Retry avec backoff |
| 500 | Erreur serveur | Afficher erreur générique |

---

## Schémas de Données Clés

### Asset
```typescript
interface Asset {
  asset_id: string;
  symbol: string;
  name: string;
  asset_type: 'EQUITY' | 'ETF' | 'BOND' | 'FX' | 'CRYPTO';
  market_scope: 'US_EU' | 'AFRICA';
  exchange?: string;
  country?: string;
  score_total: number | null;
  score_value?: number | null;
  score_momentum?: number | null;
  score_safety?: number | null;
  last_price?: number | null;
  pct_change_1d?: number | null;
  vol_annual?: number | null;
  rsi?: number | null;
  state_label?: string | null;
}
```

### SubscriptionStatus
```typescript
interface SubscriptionStatus {
  user_id: string;
  plan: 'free' | 'monthly' | 'annual';
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'inactive';
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  is_active: boolean;
}
```

### NewsArticle
```typescript
interface NewsArticle {
  id: number;
  slug: string;
  title: string;
  excerpt?: string;
  content_md?: string;
  tldr?: string[];
  tags?: string[];
  country?: string;
  image_url?: string;
  source_name: string;
  source_url?: string;
  published_at?: string;
  category?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
}
```

---

## Notes d'Intégration

1. **Pagination**: Le backend supporte `limit/offset` OU `page/page_size` selon l'endpoint.

2. **Market Scope**: Toujours inclure `market_scope` pour éviter les mélanges de données.

3. **Erreurs**: Le backend retourne `{ detail: string }` pour les erreurs.

4. **Auth Header**: Supabase JWT, validé côté backend via `SUPABASE_JWT_SECRET`.

5. **CORS**: Le backend doit autoriser l'origine mobile (ou `*` en dev).

6. **Timeout**: Recommandé 15s pour les requêtes standard, 30s pour les simulations.
