# MARKETGPS - AUDIT DE PARITÉ WEB → MOBILE

**Date**: 27 Janvier 2026
**Version**: 1.0
**Auteur**: Claude (Senior Mobile + Full-Stack + QA)

---

## RÉSUMÉ EXÉCUTIF

Cet audit compare l'application web MarketGPS (https://app.marketgps.online) avec l'application mobile Expo/React Native. L'objectif est d'identifier toutes les fonctionnalités manquantes ou partiellement implémentées pour atteindre une parité complète.

### Score de Parité Global: **68%**

| Catégorie | Web | Mobile | Parité |
|-----------|-----|--------|--------|
| Dashboard | ✅ | ⚠️ | 75% |
| Explorer/Marché | ✅ | ⚠️ | 60% |
| Détail Asset | ✅ | ⚠️ | 55% |
| Watchlist | ✅ | ✅ | 95% |
| Stratégies | ✅ | ⚠️ | 40% |
| Barbell | ✅ | ⚠️ | 70% |
| News/Actualités | ✅ | ✅ | 85% |
| Settings | ✅ | ⚠️ | 65% |
| Auth | ✅ | ✅ | 100% |
| Billing | ✅ | ✅ | 90% |

---

## 1. DASHBOARD

### Web Features
- Top 10 assets scorés avec pagination
- Filtrage multi-marché (US, EU, Africa, All)
- Filtrage par type d'actif (Equity, ETF, FX, Bonds, etc.)
- Panneau détail asset (droite) avec scores + KPIs + graphique
- Toggle watchlist sur chaque asset
- Graphique de prix avec sélecteur de période (7d, 30d, 3m, 1y)
- Compteurs par scope et type d'actif

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Top 10 assets scorés | ✅ OK | Fonctionne |
| Toggle scope US_EU/AFRICA | ✅ OK | Fonctionne |
| Quick actions (Barbell, Strategies) | ✅ OK | Fonctionne |
| Pro upgrade CTA | ✅ OK | Fonctionne |
| Pull-to-refresh | ✅ OK | Fonctionne |
| Filtrage par type d'actif | ❌ MANQUANT | Non implémenté sur dashboard |
| Graphique inline | ❌ MANQUANT | Aucun chart visible |
| Compteurs par type | ❌ MANQUANT | Web affiche counts, mobile non |
| Panneau détail intégré | ⚠️ PARTIEL | Navigation vers page séparée |

### Actions Requises
1. **[CRITIQUE]** Ajouter bibliothèque de charts (react-native-svg-charts ou victory-native)
2. Ajouter filtres par type d'actif sur dashboard
3. Ajouter compteurs dynamiques par scope/type
4. Considérer panneau latéral ou modal pour détail rapide

---

## 2. EXPLORER / MARCHÉ

### Web Features
- Recherche full-text (ticker, nom)
- Filtrage par scope (US_EU, AFRICA)
- Filtrage par type d'actif
- Filtrage par pays/région (Africa)
- Toggle "Only Scored"
- Tri multi-critères (score, prix, liquidité)
- Pagination complète
- Navigation vers détail asset

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Recherche full-text | ✅ OK | Avec debounce |
| Filtrage scope | ✅ OK | US_EU / AFRICA |
| Filtrage type actif | ✅ OK | Dropdown multi-type |
| Pagination | ✅ OK | Infinite scroll |
| Résultat count | ✅ OK | Affiche total |
| Filtrage pays Afrique | ❌ MANQUANT | Non implémenté |
| Filtrage région Afrique | ❌ MANQUANT | Non implémenté |
| Toggle "Only Scored" | ❌ MANQUANT | Non implémenté |
| Tri multi-critères | ❌ MANQUANT | Pas de sort options |
| Liens régions muets | ❌ BUG | Certains liens ne font rien |

### Actions Requises
1. **[CRITIQUE]** Implémenter filtrage pays/région Afrique
2. **[CRITIQUE]** Corriger liens régionaux "muets" dans Settings > Markets
3. Ajouter toggle "Only Scored"
4. Ajouter options de tri (score, prix, volatilité)

---

## 3. DÉTAIL D'UN ACTIF

### Web Features
- Score global + jauge visuelle
- 3 sous-scores (Value, Momentum, Safety) avec barres
- KPIs: Coverage, Liquidity, FX Risk
- Métriques techniques (RSI, Vol, Drawdown, Z-Score)
- Métriques fondamentales (P/E, Dividend Yield, Market Cap)
- Score institutionnel (si disponible)
- Graphique OHLC avec sélecteur période (7d, 30d, 3m, 6m, 1y, 5y)
- Toggle watchlist
- Liens externes (Yahoo Finance, Google Finance)

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Score global | ✅ OK | Affiché |
| Sous-scores (V/M/S) | ✅ OK | Barres de progression |
| Métriques techniques | ✅ OK | RSI, Vol, Drawdown, Z-Score |
| Métriques fondamentales | ✅ OK | P/E, Div Yield, Market Cap |
| Score institutionnel | ✅ OK | Si disponible |
| Toggle watchlist | ✅ OK | Fonctionne |
| Sélecteur période chart | ✅ OK | UI présente |
| **GRAPHIQUE PRIX** | ❌ MANQUANT | **Espace vide - pas de chart** |
| Liens externes | ❌ MANQUANT | Pas de Yahoo/Google links |

### Actions Requises
1. **[CRITIQUE]** Implémenter composant de graphique prix (library: victory-native ou react-native-chart-kit)
2. Ajouter liens externes vers Yahoo Finance / Google Finance
3. Optimiser le layout pour affichage mobile

---

## 4. WATCHLIST / LISTE DE SUIVI

### Web Features
- Liste des assets suivis avec scores
- Vue détaillée de l'asset sélectionné
- Notes personnelles par asset
- Date d'ajout / dernière mise à jour
- Actions bulk (refresh)
- Add/remove depuis liste

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Liste assets suivis | ✅ OK | Fonctionne |
| Affichage scores | ✅ OK | Score total visible |
| Remove asset | ✅ OK | Swipe ou bouton |
| Empty state | ✅ OK | CTA vers explorer |
| Auth guard | ✅ OK | Requiert login |
| Notes personnelles | ❌ MANQUANT | Non implémenté UI |
| Date d'ajout | ❌ MANQUANT | Non affiché |
| Vue détaillée intégrée | ⚠️ PARTIEL | Navigation séparée |

### Actions Requises
1. Ajouter affichage/édition des notes
2. Afficher date d'ajout
3. Considérer vue split sur tablette

---

## 5. STRATÉGIES

### Web Features
- Liste des templates de stratégies (6+)
- Filtrage par catégorie (Defensive, Balanced, Growth, Tactical)
- Filtrage par niveau de risque (Low, Moderate, High)
- Détail template avec compositions
- **Créer ma stratégie** (clone template)
- Édition pondérations (sliders + validation 100%)
- Simulation / backtest (rendement, risque, score fit)
- Mes stratégies (CRUD complet)
- Recommandation IA (BETA)

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Liste templates | ✅ OK | Via Settings > Strategies |
| Badge niveau risque | ✅ OK | Affiché |
| Preview composition | ✅ OK | 3 premiers blocs |
| Meta info (horizon, rebal) | ✅ OK | Affiché |
| Navigation vers détail | ✅ OK | Fonctionne |
| **Créer stratégie** | ❌ MANQUANT | **Pas de bouton/flow** |
| **Édition pondérations** | ❌ MANQUANT | **Pas de sliders** |
| **Simulation/backtest** | ❌ MANQUANT | **API existe, UI absente** |
| Mes stratégies (liste) | ❌ MANQUANT | Pas de section "Mes stratégies" |
| CRUD stratégies user | ❌ MANQUANT | Non implémenté |
| Recommandation IA | ❌ MANQUANT | Non implémenté |
| Filtrage catégorie | ❌ MANQUANT | Non implémenté |
| Filtrage risque | ❌ MANQUANT | Non implémenté |

### Actions Requises
1. **[CRITIQUE]** Implémenter page détail template complète
2. **[CRITIQUE]** Ajouter bouton "Créer ma stratégie" (clone template)
3. **[CRITIQUE]** Implémenter écran édition pondérations avec sliders
4. **[CRITIQUE]** Intégrer simulation/backtest (endpoint existe)
5. Ajouter section "Mes Stratégies"
6. Implémenter CRUD stratégies utilisateur
7. Ajouter filtres catégorie/risque

---

## 6. BARBELL / HALTÈRES

### Web Features
- 3 onglets: Suggestion, Candidates, Builder
- Sélecteur profil de risque (Conservative 85/15, Moderate 75/25, Aggressive 65/35)
- Sélecteur scope marché
- Visualisation allocation Core/Satellite
- Table candidates avec filtres
- Builder drag-drop avec ajustement poids
- Sauvegarde portfolio
- Simulation backtest

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Sélecteur profil risque | ✅ OK | 3 profils |
| Sélecteur scope | ✅ OK | US_EU / AFRICA |
| Barre allocation visuelle | ✅ OK | Core/Satellite % |
| Suggestions Core | ✅ OK | Liste assets |
| Suggestions Satellite | ✅ OK | Liste assets |
| Légende descriptive | ✅ OK | Explications |
| Refresh allocation | ✅ OK | Bouton fonctionne |
| Onglet Candidates | ❌ MANQUANT | Non implémenté |
| Onglet Builder | ❌ MANQUANT | Non implémenté |
| Ajustement poids manuel | ❌ MANQUANT | Non implémenté |
| Sauvegarde portfolio | ❌ MANQUANT | Non implémenté |
| Simulation backtest | ❌ MANQUANT | Non implémenté |

### Actions Requises
1. Ajouter navigation par onglets (Suggestion/Candidates/Builder)
2. Implémenter table Candidates avec filtres
3. Implémenter Builder avec ajustement poids
4. Ajouter sauvegarde portfolio
5. Intégrer simulation backtest

---

## 7. NEWS / ACTUALITÉS

### Web Features
- Feed principal avec hero article
- Grille 3 articles secondaires
- Liste chronologique
- Sidebar régionale (CEMAC, UEMOA, etc.)
- Newsletter signup CTA
- Market ticker animé
- Filtrage par région/pays
- Filtrage par tag
- Articles sauvegardés
- Vue article complète

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Feed paginé | ✅ OK | 20 articles/page |
| Featured article variant | ✅ OK | Première carte plus grande |
| Filtrage pays | ✅ OK | 14 pays francophones |
| Filtrage zone économique | ✅ OK | CEMAC, UEMOA, etc. |
| Filtrage tags | ✅ OK | Fintech, Startup, etc. |
| Vue article complète | ✅ OK | Page /news/[slug] |
| Articles sauvegardés | ⚠️ PARTIEL | API existe, UI basique |
| Market ticker | ❌ MANQUANT | Non implémenté |
| Newsletter signup | ❌ MANQUANT | Non pertinent mobile |
| Sidebar régionale | ⚠️ ADAPTÉ | Filtres inline |

### Actions Requises
1. Améliorer UI articles sauvegardés
2. Considérer ticker market en header (optionnel)

---

## 8. SETTINGS / PARAMÈTRES

### Web Features
- Profil: Display name, avatar, email
- Sécurité: Changement mot de passe, logout, delete account
- Notifications: 4 toggles configurables
- Billing: Plan actuel, upgrade/downgrade, portal Stripe

### Mobile Status

| Feature | Status | Notes |
|---------|--------|-------|
| Hub settings structuré | ✅ OK | Sections organisées |
| Carte profil user | ✅ OK | Avatar, email, badge plan |
| Section Trading | ✅ OK | Strategies, Barbell, Markets |
| Section Account | ✅ OK | Profile, Billing, etc. |
| Section App | ✅ OK | Help, Terms, Privacy |
| Sign out | ✅ OK | Avec confirmation |
| Page Profile | ⚠️ BASIQUE | Affiche infos, update minimal |
| Page Billing | ✅ OK | Statut, checkout, portal |
| Page Notifications | ⚠️ BASIQUE | Toggles existent |
| Page Security | ⚠️ PLACEHOLDER | UI minimale |
| Page Markets | ❌ BROKEN | **Liens muets, pas d'action** |
| Haptic feedback | ✅ OK | Sur interactions |

### Actions Requises
1. **[CRITIQUE]** Corriger page Markets - tous les liens doivent naviguer
2. Améliorer page Profile avec édition complète
3. Améliorer page Security avec changement mot de passe fonctionnel
4. Finaliser page Notifications

---

## 9. AUTHENTIFICATION

| Feature | Web | Mobile | Status |
|---------|-----|--------|--------|
| Login email/password | ✅ | ✅ | ✅ PARITÉ |
| Signup | ✅ | ✅ | ✅ PARITÉ |
| Forgot password | ✅ | ✅ | ✅ PARITÉ |
| Session persistence | ✅ | ✅ | ✅ PARITÉ |
| Secure token storage | ✅ | ✅ | ✅ PARITÉ |

---

## 10. BILLING / ABONNEMENT

| Feature | Web | Mobile | Status |
|---------|-----|--------|--------|
| Affichage plan actuel | ✅ | ✅ | ✅ PARITÉ |
| Checkout Stripe | ✅ | ✅ | ✅ PARITÉ |
| Portal management | ✅ | ✅ | ✅ PARITÉ |
| Feature comparison | ✅ | ✅ | ✅ PARITÉ |
| Cancel at period end | ✅ | ✅ | ✅ PARITÉ |

---

## PROBLÈMES CRITIQUES IDENTIFIÉS

### 🔴 P0 - Bloquants

1. **Absence de graphiques/charts**
   - Impact: Impossible de visualiser l'évolution des prix
   - Solution: Intégrer victory-native ou react-native-chart-kit
   - Effort: 2-3 jours

2. **Liens régions Afrique muets (Settings > Markets)**
   - Impact: Navigation cassée, UX frustrante
   - Solution: Implémenter navigation vers explorer filtré
   - Effort: 0.5 jour

3. **Module Stratégies incomplet**
   - Impact: Feature majeure non utilisable
   - Solution: Implémenter création + édition + simulation
   - Effort: 3-4 jours

### 🟠 P1 - Importants

4. **Filtres Afrique manquants dans Explorer**
   - Impact: Impossible de filtrer par pays/région
   - Solution: Ajouter dropdowns pays/région
   - Effort: 1 jour

5. **Barbell Builder incomplet**
   - Impact: Impossible de personnaliser allocation
   - Solution: Ajouter onglets Candidates + Builder
   - Effort: 2 jours

6. **Pagination actifs limitée**
   - Impact: Scroll infini fonctionne mais pas optimal
   - Solution: Optimiser et ajouter indicateur chargement
   - Effort: 0.5 jour

### 🟡 P2 - Améliorations

7. **Settings pages incomplètes** (Profile, Security, Notifications)
8. **Notes watchlist non éditables**
9. **Liens externes manquants** (Yahoo, Google Finance)
10. **Market ticker absent**

---

## PLAN D'ACTION RECOMMANDÉ

### Phase 1 - Corrections Critiques (Semaine 1)
- [ ] Intégrer bibliothèque de charts
- [ ] Implémenter composant PriceChart
- [ ] Corriger navigation Settings > Markets
- [ ] Ajouter filtres pays/région Afrique dans Explorer

### Phase 2 - Module Stratégies (Semaine 2)
- [ ] Page détail template complète
- [ ] Écran création stratégie
- [ ] Sliders édition pondérations
- [ ] Intégration simulation/backtest
- [ ] Section "Mes Stratégies"

### Phase 3 - Barbell & Polish (Semaine 3)
- [ ] Onglets Barbell (Candidates, Builder)
- [ ] Sauvegarde portfolio Barbell
- [ ] Finaliser Settings pages
- [ ] Améliorer Watchlist (notes, dates)

### Phase 4 - QA & Finitions (Semaine 4)
- [ ] Tests end-to-end tous les flows
- [ ] Optimisation performance
- [ ] GPS Loading animation
- [ ] Documentation finale

---

## ANNEXE: ENDPOINTS API NON UTILISÉS PAR MOBILE

Ces endpoints existent côté backend mais ne sont pas encore branchés sur mobile:

```
Stratégies:
- POST /api/strategies/user (créer stratégie)
- PUT /api/strategies/user/{id} (éditer)
- DELETE /api/strategies/user/{id} (supprimer)
- POST /api/strategies/simulate (backtest)
- POST /api/strategies/ai-suggest (IA)

Barbell:
- GET /api/barbell/candidates/core (avec filtres)
- GET /api/barbell/candidates/satellite (avec filtres)
- POST /api/barbell/simulate (backtest)
- POST /api/barbell/portfolios (sauvegarder)
- GET /api/barbell/portfolios (lister)

Explorer:
- GET /api/assets/explorer (avec country, region params)
- GET /api/metrics/counts/v2 (compteurs dynamiques)

User:
- POST /users/security/change-password
- POST /users/avatar/upload
```

---

**Fin du rapport d'audit**
