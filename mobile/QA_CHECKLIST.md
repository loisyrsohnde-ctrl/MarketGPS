# MarketGPS Mobile - QA Checklist

## Tests par Écran

### 1. Authentification

#### Login
- [ ] Affichage correct du formulaire
- [ ] Validation email format
- [ ] Validation mot de passe (min 6 caractères)
- [ ] Affichage erreurs inline
- [ ] Login avec credentials valides → redirection Dashboard
- [ ] Login avec credentials invalides → message erreur
- [ ] Lien "Mot de passe oublié" fonctionne
- [ ] Lien "Créer un compte" fonctionne
- [ ] Bouton retour fonctionne

#### Signup
- [ ] Validation email
- [ ] Validation mot de passe (min 8 caractères)
- [ ] Validation confirmation mot de passe
- [ ] Création compte → email de confirmation
- [ ] Affichage des CGU

#### Forgot Password
- [ ] Envoi email reset
- [ ] Message de confirmation
- [ ] Retour login

### 2. Dashboard

- [ ] Affichage greeting avec nom utilisateur
- [ ] Sélecteur US/EU et Afrique fonctionne
- [ ] Compteurs dynamiques s'affichent
- [ ] Top 5 assets chargent correctement
- [ ] Score badge couleur correcte
- [ ] Pull-to-refresh fonctionne
- [ ] Quick actions (Barbell, Stratégies, Marchés) naviguent
- [ ] CTA Pro visible pour utilisateurs gratuits
- [ ] CTA Pro mène à checkout

### 3. Explorer

- [ ] Barre de recherche fonctionne
- [ ] Debounce recherche (300ms)
- [ ] Filtres marché (US/EU, Afrique)
- [ ] Filtres type (EQUITY, ETF, BOND, FX)
- [ ] Compteur résultats correct
- [ ] AssetCard affiche toutes les infos
- [ ] Navigation vers AssetDetail
- [ ] Pagination infinie
- [ ] État vide si pas de résultats

### 4. Watchlist

#### Non connecté
- [ ] Message "Connexion requise"
- [ ] Bouton "Se connecter"

#### Connecté
- [ ] Liste des actifs watchlist
- [ ] Swipe ou tap pour retirer
- [ ] Confirmation avant suppression
- [ ] État vide avec CTA vers Explorer
- [ ] Pull-to-refresh
- [ ] Compteur d'actifs

### 5. News

- [ ] Feed d'actualités charge
- [ ] Image featured article
- [ ] Filtres régions fonctionnent
- [ ] Filtres tags fonctionnent
- [ ] Date formatée correctement
- [ ] Source affichée
- [ ] Navigation vers article
- [ ] État vide gracieux

#### Article Detail
- [ ] Image hero
- [ ] Tags affichés
- [ ] Titre sans markdown (**)
- [ ] Contenu sans markdown
- [ ] TLDR si disponible
- [ ] Bouton partage natif
- [ ] Bouton source (ouvre navigateur)

### 6. Asset Detail

- [ ] Header avec symbol et type
- [ ] Prix actuel
- [ ] Variation journalière (couleur +/-)
- [ ] Bouton watchlist toggle
- [ ] Période selector (1J, 1S, 1M, etc.)
- [ ] Score global avec badge
- [ ] Score breakdown (Value, Momentum, Safety)
- [ ] Métriques grid (RSI, Vol, Max DD, Z-Score)
- [ ] Infos additionnelles (marché, exchange, P/E, etc.)
- [ ] Garde Institutionnel si dispo

### 7. Stratégies

- [ ] Quick action Barbell
- [ ] Liste des templates
- [ ] Affichage risque (couleur)
- [ ] Horizon, rebalance, blocs
- [ ] Navigation vers détail template

#### Template Detail
- [ ] Header avec nom et description
- [ ] Métadonnées (risque, horizon, rebalance)
- [ ] Barre d'allocation visuelle
- [ ] Liste des blocs avec %
- [ ] Sélection bloc → instruments éligibles
- [ ] Bouton simulation (message coming soon OK)

### 8. Barbell Builder

- [ ] Introduction card
- [ ] Sélecteur marché
- [ ] Sélecteur profil risque (Conservateur, Modéré, Agressif)
- [ ] Barre d'allocation Core/Satellite
- [ ] Légende
- [ ] Suggestions Core chargent
- [ ] Suggestions Satellite chargent
- [ ] AssetCards fonctionnels

### 9. Settings

#### Menu principal
- [ ] User card avec avatar, email, plan
- [ ] Navigation Stratégies
- [ ] Navigation Barbell
- [ ] Navigation Marchés
- [ ] Navigation Profil (si connecté)
- [ ] Navigation Abonnement (si connecté)
- [ ] Navigation Notifications (si connecté)
- [ ] Navigation Sécurité (si connecté)
- [ ] Navigation Aide
- [ ] Navigation CGU
- [ ] Navigation Confidentialité
- [ ] Déconnexion avec confirmation

#### Profil
- [ ] Avatar avec initiale
- [ ] Nom d'affichage éditable
- [ ] Email (non éditable)
- [ ] ID utilisateur
- [ ] Date création
- [ ] Bouton modifier/sauvegarder

#### Billing
- [ ] Card plan actuel
- [ ] Badge statut (Actif, etc.)
- [ ] Date prochaine facturation
- [ ] Bouton gérer (ouvre portail Stripe)
- [ ] OU bouton "Passer à Pro" si gratuit
- [ ] Features comparison

#### Notifications
- [ ] Toggle email notifications
- [ ] Toggle alertes marché
- [ ] Toggle alertes prix
- [ ] Toggle mises à jour portefeuille
- [ ] Sauvegarde automatique

#### Security
- [ ] Formulaire changement mot de passe
- [ ] Validation mot de passe
- [ ] Session active affichée
- [ ] Zone danger (supprimer compte)
- [ ] Double confirmation suppression

### 10. Checkout

- [ ] Header avec icône diamond
- [ ] 2 plans affichés (Mensuel, Annuel)
- [ ] Badge "Économisez 17%"
- [ ] Sélection toggle
- [ ] Features par plan
- [ ] Bouton CTA avec prix
- [ ] Terms en bas
- [ ] Garanties (paiement sécurisé, annulation)
- [ ] Ouverture Stripe Checkout
- [ ] Retour après paiement

### 11. Marchés

- [ ] Card US/EU avec compteur
- [ ] Card Afrique avec compteur
- [ ] Navigation vers Explorer filtré
- [ ] Régions africaines listées
- [ ] Pays par région

## Tests Transversaux

### Performance
- [ ] Temps de chargement initial < 3s
- [ ] Navigation instantanée entre tabs
- [ ] Scroll fluide sur listes longues
- [ ] Pas de freeze sur recherche

### Offline/Réseau
- [ ] Message d'erreur si offline
- [ ] Cache React Query fonctionne
- [ ] Retry automatique sur erreur réseau

### Accessibilité
- [ ] Texte lisible (contraste)
- [ ] Zones tactiles suffisantes (44x44 min)
- [ ] Labels sur tous les boutons

### UI/UX
- [ ] Dark mode cohérent partout
- [ ] Pas de text overflow
- [ ] États loading visibles (skeleton/spinner)
- [ ] États error explicites
- [ ] Haptic feedback sur actions

### Auth Flow
- [ ] Token refresh automatique
- [ ] Redirection login si session expirée
- [ ] Déconnexion vide le cache

### Deep Links
- [ ] `marketgps://` scheme configuré
- [ ] Retour Stripe checkout fonctionne

## Tests par Plateforme

### iOS
- [ ] Safe area respectée (notch, home indicator)
- [ ] Keyboard avoiding view
- [ ] Gestures navigation
- [ ] Face ID/Touch ID si implémenté

### Android
- [ ] Back button hardware
- [ ] Keyboard handling
- [ ] Status bar style
- [ ] Navigation bar handling

## Régression

- [ ] Le web Next.js fonctionne toujours
- [ ] Les endpoints API non modifiés
- [ ] La pipeline data fonctionne
- [ ] Les webhooks Stripe fonctionnent

## Sign-off

| Écran | iOS | Android | Testeur | Date |
|-------|-----|---------|---------|------|
| Login | ⬜ | ⬜ | | |
| Signup | ⬜ | ⬜ | | |
| Dashboard | ⬜ | ⬜ | | |
| Explorer | ⬜ | ⬜ | | |
| Watchlist | ⬜ | ⬜ | | |
| News | ⬜ | ⬜ | | |
| Asset Detail | ⬜ | ⬜ | | |
| Strategies | ⬜ | ⬜ | | |
| Barbell | ⬜ | ⬜ | | |
| Checkout | ⬜ | ⬜ | | |
| Settings | ⬜ | ⬜ | | |
