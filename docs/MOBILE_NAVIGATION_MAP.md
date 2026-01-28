# MARKETGPS MOBILE - CARTE DE NAVIGATION

**Date**: 27 Janvier 2026
**Version**: 1.0

---

## STRUCTURE DE NAVIGATION

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ROOT LAYOUT                                  │
│                        (_layout.tsx)                                 │
│  - QueryClientProvider                                               │
│  - GestureHandlerRootView                                            │
│  - Auth initialization                                               │
│  - Splash screen management                                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
┌───────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│    (auth) GROUP       │ │  (tabs) GROUP   │ │   MODAL SCREENS     │
│    Stack Navigator    │ │ Tab Navigator   │ │   Stack Navigator   │
├───────────────────────┤ ├─────────────────┤ ├─────────────────────┤
│ /login                │ │ /               │ │ /checkout           │
│ /signup               │ │ /explorer       │ │ /asset/[ticker]     │
│ /forgot-password      │ │ /watchlist      │ │ /news/[slug]        │
└───────────────────────┘ │ /news           │ │ /strategy/[slug]    │
                          │ /settings       │ │ /strategy/barbell   │
                          └─────────────────┘ └─────────────────────┘
```

---

## ROUTES DÉTAILLÉES

### 1. GROUP: (auth) - Authentification

| Route | Fichier | Description | Params |
|-------|---------|-------------|--------|
| `/login` | `(auth)/login.tsx` | Connexion email/password | - |
| `/signup` | `(auth)/signup.tsx` | Inscription nouvel utilisateur | - |
| `/forgot-password` | `(auth)/forgot-password.tsx` | Réinitialisation mot de passe | - |

**Navigation:**
- Login → Signup (lien)
- Login → Forgot Password (lien)
- Success → Tabs (replace)

---

### 2. GROUP: (tabs) - Navigation Principale

| Route | Fichier | Tab Icon | Description |
|-------|---------|----------|-------------|
| `/` (index) | `(tabs)/index.tsx` | `home` | Dashboard principal |
| `/explorer` | `(tabs)/explorer.tsx` | `search` | Explorer les actifs |
| `/watchlist` | `(tabs)/watchlist.tsx` | `bookmark` | Liste de suivi |
| `/news` | `(tabs)/news.tsx` | `newspaper` | Actualités |
| `/settings` | `(tabs)/settings.tsx` | `settings` | Paramètres |

**Tab Bar Config:**
```typescript
{
  tabBarActiveTintColor: '#19D38C',  // Accent green
  tabBarInactiveTintColor: '#6B7280',
  tabBarStyle: {
    backgroundColor: '#0A0F1C',
    borderTopColor: '#1E293B',
  }
}
```

---

### 3. SETTINGS SUB-ROUTES

| Route | Fichier | Description | Auth Required |
|-------|---------|-------------|---------------|
| `/settings/profile` | `settings/profile.tsx` | Profil utilisateur | ✅ |
| `/settings/billing` | `settings/billing.tsx` | Abonnement & facturation | ✅ |
| `/settings/notifications` | `settings/notifications.tsx` | Préférences notifications | ✅ |
| `/settings/security` | `settings/security.tsx` | Sécurité & mot de passe | ✅ |
| `/settings/strategies` | `settings/strategies.tsx` | Templates de stratégies | ❌ |
| `/settings/markets` | `settings/markets.tsx` | Préférences marchés | ❌ |
| `/settings/help` | `settings/help.tsx` | Aide & support | ❌ |
| `/settings/terms` | `settings/terms.tsx` | Conditions d'utilisation | ❌ |
| `/settings/privacy` | `settings/privacy.tsx` | Politique de confidentialité | ❌ |

---

### 4. ROUTES DYNAMIQUES

| Route | Fichier | Description | Params |
|-------|---------|-------------|--------|
| `/asset/[ticker]` | `asset/[ticker].tsx` | Détail d'un actif | `ticker: string` |
| `/news/[slug]` | `news/[slug].tsx` | Article complet | `slug: string` |
| `/strategy/[slug]` | `strategy/[slug].tsx` | Détail template stratégie | `slug: string` |

**Exemples d'URLs:**
- `/asset/AAPL` → Détail Apple Inc
- `/asset/NPN.JSE` → Détail Naspers (Afrique du Sud)
- `/news/fintech-africa-2026` → Article actualité
- `/strategy/permanent-portfolio` → Template stratégie

---

### 5. ROUTES MODALES

| Route | Fichier | Presentation | Description |
|-------|---------|--------------|-------------|
| `/checkout` | `checkout.tsx` | `modal` | Sélection plan & paiement |
| `/strategy/barbell` | `strategy/barbell.tsx` | `card` | Builder Barbell |

---

## FLUX DE NAVIGATION

### A. Flux Authentification

```
App Launch
    │
    ▼
┌─────────────────┐
│ Check Auth State│
└─────────────────┘
    │
    ├─── Authenticated ───► (tabs)/index (Dashboard)
    │
    └─── Not Authenticated ───► (tabs)/index (Dashboard avec CTA login)
                                     │
                                     ▼ (si action protégée)
                              ┌─────────────┐
                              │   /login    │
                              └─────────────┘
                                     │
                                     ├── Success ──► Previous screen
                                     │
                                     └── Signup ──► /signup ──► /login
```

### B. Flux Asset Discovery

```
Dashboard (index)
    │
    ├── Tap Asset Card ──────────────► /asset/[ticker]
    │                                       │
    │                                       ├── Add to Watchlist
    │                                       ├── View Chart (period select)
    │                                       └── Back to Dashboard
    │
    └── Tap "Explorer" Quick Action ──► /explorer
                                            │
                                            ├── Search (debounced)
                                            ├── Filter (scope, type)
                                            └── Tap Result ──► /asset/[ticker]
```

### C. Flux Stratégies

```
Settings
    │
    └── Tap "Stratégies" ──► /settings/strategies
                                    │
                                    └── Tap Template ──► /strategy/[slug]
                                                              │
                                                              ├── View Details
                                                              └── [TODO] Create Strategy
```

### D. Flux Barbell

```
Dashboard
    │
    └── Tap "Barbell" Quick Action ──► /strategy/barbell
                                            │
                                            ├── Select Risk Profile
                                            ├── Select Market Scope
                                            ├── View Suggestions
                                            └── Refresh
```

### E. Flux News

```
Tab News
    │
    ├── Scroll Feed (paginated)
    │
    ├── Apply Filters (country, zone, tag)
    │
    └── Tap Article ──► /news/[slug]
                            │
                            ├── Read Full Article
                            └── [TODO] Save Article
```

### F. Flux Billing

```
Settings
    │
    └── Tap "Abonnement" ──► /settings/billing
                                    │
                                    ├── View Current Plan
                                    │
                                    ├── Tap "Upgrade" ──► /checkout (modal)
                                    │                          │
                                    │                          ├── Select Plan
                                    │                          └── Stripe Checkout (WebBrowser)
                                    │
                                    └── Tap "Gérer" ──► Stripe Portal (WebBrowser)
```

---

## PARAMÈTRES DE NAVIGATION

### Route Params

```typescript
// Asset Detail
type AssetParams = {
  ticker: string;  // ex: "AAPL", "NPN.JSE", "BTC.CRYPTO"
}

// News Article
type NewsParams = {
  slug: string;  // ex: "fintech-africa-2026"
}

// Strategy Template
type StrategyParams = {
  slug: string;  // ex: "permanent-portfolio", "all-weather"
}
```

### Navigation Options

```typescript
// Modal presentation
<Stack.Screen
  name="checkout"
  options={{
    presentation: 'modal',
    headerShown: true,
    title: 'Upgrade to Pro',
  }}
/>

// Card presentation (partial modal)
<Stack.Screen
  name="strategy/barbell"
  options={{
    presentation: 'card',
    headerShown: true,
    title: 'Barbell Builder',
  }}
/>

// Full screen detail
<Stack.Screen
  name="asset/[ticker]"
  options={{
    headerShown: true,
    headerBackTitle: 'Back',
  }}
/>
```

---

## DEEP LINKS (FUTURS)

| Pattern | Route | Exemple |
|---------|-------|---------|
| `marketgps://asset/{ticker}` | `/asset/[ticker]` | `marketgps://asset/AAPL` |
| `marketgps://news/{slug}` | `/news/[slug]` | `marketgps://news/fintech-2026` |
| `marketgps://strategy/{slug}` | `/strategy/[slug]` | `marketgps://strategy/all-weather` |
| `marketgps://upgrade` | `/checkout` | `marketgps://upgrade` |

---

## ROUTES MANQUANTES (À IMPLÉMENTER)

| Route Proposée | Description | Priorité |
|----------------|-------------|----------|
| `/strategy/create` | Créer nouvelle stratégie | P0 |
| `/strategy/edit/[id]` | Éditer stratégie utilisateur | P0 |
| `/strategy/simulate` | Simulation/backtest | P1 |
| `/portfolio/[id]` | Détail portfolio Barbell | P1 |
| `/explorer/africa` | Explorer filtré Afrique | P1 |
| `/explorer/region/[region]` | Explorer par région | P2 |
| `/watchlist/notes/[ticker]` | Éditer notes watchlist | P2 |

---

## GUARDS & PROTECTIONS

### Auth Guard
```typescript
// Routes nécessitant authentification
const PROTECTED_ROUTES = [
  '/settings/profile',
  '/settings/billing',
  '/settings/notifications',
  '/settings/security',
  '/watchlist',  // Partial - affiche CTA login si non auth
];

// Redirection si non authentifié
if (!isAuthenticated && PROTECTED_ROUTES.includes(route)) {
  router.push('/login');
}
```

### Subscription Guard
```typescript
// Routes nécessitant abonnement Pro
const PRO_ROUTES = [
  // Actuellement aucune route 100% bloquée
  // Features Pro sont gated au niveau composant
];
```

---

**Fin de la carte de navigation**
