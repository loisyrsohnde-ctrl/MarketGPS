# MarketGPS Mobile Audit Report

**Date**: 2025-01-27  
**Objectif**: Rendre la version mobile parfaitement cohérente avec la version web

---

## Résumé Exécutif

### Problèmes Critiques Identifiés

| Priorité | Problème | Impact | Statut |
|----------|----------|--------|--------|
| 🔴 P0 | Endpoint billing mobile inexistant | Abonnements non reconnus | ✅ Corrigé |
| 🟠 P1 | Design tokens incohérents | UI différente du web | ✅ Corrigé |
| 🟡 P2 | Fonctionnalités manquantes | Parité incomplète | À planifier |

---

## A. ANALYSE DES DESIGN TOKENS

### Comparaison Web vs Mobile

| Token | Web | Mobile | Écart |
|-------|-----|--------|-------|
| **Primary Accent** | `#19D38C` (vert) | `#22D3EE` (cyan) | ❌ Différent |
| **Background Primary** | `#070A0B` | `#0A0F1C` | ⚠️ Proche |
| **Background Secondary** | `#0A0E10` | `#0F172A` | ⚠️ Proche |
| **Background Card** | `#0D1214` | `#1E293B` | ❌ Différent |
| **Text Primary** | `#EAF2EE` | `#F1F5F9` | ⚠️ Proche |
| **Text Secondary** | `rgba(234,242,238,0.85)` | `#CBD5E1` | ⚠️ Proche |
| **Text Muted** | `rgba(234,242,238,0.70)` | `#94A3B8` | ⚠️ Proche |
| **Border** | `rgba(255,255,255,0.08)` | `#334155` | ❌ Différent |
| **Success** | `#22C55E` | `#22C55E` | ✅ Identique |
| **Error** | `#EF4444` | `#EF4444` | ✅ Identique |
| **Warning** | `#F59E0B` | `#EAB308` | ⚠️ Proche |

### Cause Racine
- Pas de système de tokens partagé
- Couleurs hardcodées dans chaque composant mobile
- Web utilise CSS variables + Tailwind, Mobile utilise StyleSheet natif

### Solution Proposée
1. Créer `mobile/src/theme/tokens.ts` avec les valeurs exactes du web
2. Remplacer toutes les couleurs hardcodées par des références aux tokens
3. Documenter le mapping pour futures modifications

---

## B. ANALYSE DU FLUX BILLING

### Architecture Actuelle

```
┌─────────────────────────────────────────────────────────────────┐
│                        STRIPE WEBHOOKS                          │
│                              │                                  │
│                              ▼                                  │
│                   Supabase: entitlements                        │
│                    (source de vérité)                           │
└─────────────────────────────────────────────────────────────────┘
                               │
           ┌───────────────────┴───────────────────┐
           ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────┐
│   WEB FRONTEND      │               │   MOBILE APP        │
│                     │               │                     │
│ GET /users/         │               │ GET /api/billing/me │
│     entitlements    │               │     ❌ N'EXISTE PAS  │
│                     │               │                     │
│ ✅ Fonctionne       │               │ ❌ Erreur réseau    │
└─────────────────────┘               └─────────────────────┘
```

### Cause Racine du Bug

**Le mobile appelle `/api/billing/me` mais cet endpoint n'existe pas dans le backend.**

Endpoints disponibles dans le backend:
- `/users/entitlements` ✅ (utilisé par le web)
- `/api/billing/subscription` ✅ (retourne données hardcodées)
- `/api/billing/me` ❌ **N'EXISTE PAS**

Code mobile problématique (`mobile/src/lib/api.ts` ligne 363-365):
```typescript
async getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return this.fetch('/api/billing/me');  // ❌ Endpoint inexistant
}
```

### Solution

**Option A (Recommandée)**: Modifier le mobile pour utiliser `/users/entitlements`
- Avantage: Aucun changement backend
- Inconvénient: Adapter le format de réponse

**Option B**: Créer `/api/billing/me` dans le backend
- Avantage: Pas de changement mobile
- Inconvénient: Nouveau code à maintenir

### Autres Problèmes Identifiés

1. **Double source de données**:
   - Webhooks Stripe → Supabase `entitlements`
   - Web lit depuis SQLite `user_entitlements`
   - Ces tables ne sont pas synchronisées

2. **Format de réponse différent**:
   - Web attend: `{ plan, status, dailyRequestsLimit }`
   - Mobile attend: `{ user_id, plan, status, current_period_end, is_active, ... }`

---

## C. ANALYSE DE LA NAVIGATION

### Matrice de Parité

| Feature | Web | Mobile | Notes |
|---------|-----|--------|-------|
| Dashboard | ✅ Full | ✅ Full | Parité complète |
| Explorer | ✅ Full | ✅ Full | Parité complète |
| Watchlist | ✅ Full | ✅ Full | Parité complète |
| News Feed | ✅ Full | ✅ Full | Parité complète |
| News Article | ✅ Full | ✅ Full | Parité complète |
| Asset Detail | ✅ Full | ✅ Full | Parité complète |
| Markets Overview | ✅ Full | ✅ Full | Parité complète |
| Strategies (view) | ✅ Full | ✅ Full | Parité complète |
| Strategies (create/edit) | ✅ Full | ❌ Missing | Mobile ne peut pas créer |
| Barbell Builder | ✅ Full | ⚠️ Partial | Mobile manque sauvegarde |
| Saved Articles | ✅ Full | ❌ Missing | Pas de page articles sauvés |
| Profile | ✅ Full | ✅ Full | Parité complète |
| Billing | ✅ Full | ✅ Full | UI OK, backend cassé |
| Security | ✅ Full | ✅ Full | Parité complète |
| Notifications | ✅ Full | ✅ Full | Parité complète |
| Login/Signup | ✅ Full | ✅ Full | Parité complète |
| Contact | ✅ Full | ❌ Missing | Pas de page contact |
| Pricing | ✅ Full | ❌ Missing | Checkout direct |

### Résumé
- **✅ Parité complète**: 14 fonctionnalités
- **⚠️ Parité partielle**: 1 fonctionnalité
- **❌ Manquant**: 4 fonctionnalités

---

## D. PLAN DE CORRECTION

### Phase 1: Corrections Critiques (P0)

#### 1.1 Corriger le flux billing mobile

Modifier `mobile/src/lib/api.ts`:
```typescript
// AVANT
async getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return this.fetch('/api/billing/me');
}

// APRÈS
async getSubscriptionStatus(): Promise<SubscriptionStatus> {
  const data = await this.fetch('/users/entitlements');
  return {
    user_id: '', // sera rempli par le store
    plan: data.plan?.toLowerCase() || 'free',
    status: data.status || 'inactive',
    current_period_end: null,
    cancel_at_period_end: false,
    is_active: data.status === 'active',
    grace_period_remaining_hours: null,
  };
}
```

### Phase 2: Synchronisation Design Tokens (P1)

#### 2.1 Créer le fichier de tokens

Créer `mobile/src/theme/tokens.ts` avec les valeurs web exactes.

#### 2.2 Migrer les composants

Remplacer les couleurs hardcodées par des imports de tokens.

### Phase 3: Fonctionnalités Manquantes (P2)

1. Ajouter création/édition de stratégies
2. Ajouter sauvegarde portfolio Barbell
3. Ajouter page articles sauvegardés
4. Ajouter page contact

---

## E. CHECKLIST QA

### Tests Post-Correction

- [ ] **Auth**: Connexion avec compte existant
- [ ] **Auth**: Création de nouveau compte
- [ ] **Billing**: Compte abonné → accès direct sans paywall
- [ ] **Billing**: Compte gratuit → paywall affiché
- [ ] **Billing**: Après paiement → accès activé immédiatement
- [ ] **Billing**: Logout/login → statut persiste
- [ ] **Billing**: Bouton "Restaurer mon achat" fonctionne
- [ ] **Navigation**: Tous les menus accessibles
- [ ] **UI**: Couleurs cohérentes avec le web (accent vert #19D38C)
- [ ] **UI**: Tab bar avec icône active verte
- [ ] **UI**: Cards avec bordure subtile
- [ ] **Performance**: Pas de lags ou freezes

### Tests Billing Détaillés

1. **Test utilisateur abonné existant**:
   - Se connecter avec un compte qui a un abonnement actif sur Stripe
   - Vérifier que `subscription.is_active === true`
   - Vérifier l'accès aux fonctionnalités Pro

2. **Test restauration**:
   - Aller dans Settings > Abonnement
   - Cliquer sur "Restaurer mon achat"
   - Vérifier que le statut est mis à jour

3. **Test synchronisation**:
   - Se déconnecter puis reconnecter
   - Vérifier que le statut d'abonnement persiste

---

## F. FICHIERS MODIFIÉS

### Corrections P0 (Billing) ✅
- `mobile/src/lib/api.ts` - Endpoint changé de `/api/billing/me` à `/users/entitlements`
- `mobile/app/settings/billing.tsx` - Ajout bouton "Restaurer mon achat"

### Corrections P1 (Tokens) ✅
- `mobile/src/theme/tokens.ts` - **CRÉÉ** - Tokens centralisés
- `mobile/src/theme/index.ts` - **CRÉÉ** - Export centralisé
- `mobile/src/components/ui/Button.tsx` - Couleurs migrées vers tokens
- `mobile/src/components/ui/Card.tsx` - Couleurs migrées vers tokens
- `mobile/src/components/ui/Input.tsx` - Couleurs migrées vers tokens
- `mobile/src/components/ui/ScoreBadge.tsx` - Couleurs migrées vers tokens
- `mobile/src/components/ui/AssetCard.tsx` - Couleurs migrées vers tokens
- `mobile/app/_layout.tsx` - Couleurs migrées vers tokens
- `mobile/app/(tabs)/_layout.tsx` - Couleurs migrées vers tokens
- `mobile/app/settings/billing.tsx` - Couleurs migrées vers tokens
- `mobile/src/lib/config.ts` - Score colors alignés avec web

---

## G. DOCUMENTS PRODUITS

1. **MOBILE_AUDIT_REPORT.md** (ce fichier) - Rapport d'audit complet
2. **THEME_PARITY_REPORT.md** - Mapping des tokens web → mobile

---

*Rapport généré automatiquement par l'audit MarketGPS - 2025-01-27*
