# MarketGPS Mobile

Application mobile iOS/Android pour MarketGPS - Scoring et analyse d'actifs financiers.

## Technologies

- **Framework**: React Native avec Expo SDK 51
- **Navigation**: expo-router (file-based routing)
- **State Management**: Zustand + TanStack Query (React Query)
- **Auth**: Supabase Auth avec SecureStore
- **Styling**: StyleSheet natif (design system custom)
- **Payments**: Stripe (via WebBrowser)

## Prérequis

- Node.js 18+
- npm ou yarn
- Expo CLI (`npm install -g expo-cli`)
- Xcode (pour iOS) ou Android Studio (pour Android)

## Installation

```bash
# Cloner le repo et naviguer vers le dossier mobile
cd mobile

# Installer les dépendances
npm install

# Copier les variables d'environnement
cp .env.example .env

# Éditer .env avec vos clés
```

## Configuration

Créez un fichier `.env` à la racine du dossier mobile :

```env
# API Backend
EXPO_PUBLIC_API_URL=https://api.marketgps.online

# Supabase
EXPO_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...

# Stripe
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx

# Web URL (pour les redirections)
EXPO_PUBLIC_WEB_URL=https://app.marketgps.online
```

## Développement

```bash
# Démarrer le serveur de développement
npm start

# Démarrer sur iOS
npm run ios

# Démarrer sur Android
npm run android
```

## Structure du Projet

```
mobile/
├── app/                    # Routes expo-router
│   ├── (auth)/            # Écrans d'authentification
│   │   ├── login.tsx
│   │   ├── signup.tsx
│   │   └── forgot-password.tsx
│   ├── (tabs)/            # Navigation principale (bottom tabs)
│   │   ├── index.tsx      # Dashboard
│   │   ├── explorer.tsx   # Explorer les actifs
│   │   ├── watchlist.tsx  # Watchlist utilisateur
│   │   ├── news.tsx       # Actualités
│   │   └── settings.tsx   # Paramètres
│   ├── asset/[ticker].tsx # Détail d'un actif
│   ├── news/[slug].tsx    # Article de news
│   ├── strategy/          # Stratégies
│   │   ├── [slug].tsx     # Détail template
│   │   └── barbell.tsx    # Barbell builder
│   ├── settings/          # Sous-pages settings
│   │   ├── strategies.tsx
│   │   ├── markets.tsx
│   │   ├── billing.tsx
│   │   ├── profile.tsx
│   │   └── ...
│   ├── checkout.tsx       # Page d'abonnement
│   └── _layout.tsx        # Layout racine
├── src/
│   ├── components/ui/     # Composants UI réutilisables
│   ├── lib/               # Utilitaires et clients
│   │   ├── api.ts         # Client API typé
│   │   ├── supabase.ts    # Client Supabase
│   │   └── config.ts      # Configuration
│   └── store/             # Stores Zustand
│       └── auth.ts        # Store authentification
├── assets/                # Images et fonts
├── app.json              # Configuration Expo
├── package.json
└── tsconfig.json
```

## Fonctionnalités

### Authentification
- Login / Signup / Forgot Password
- Sessions persistantes avec SecureStore
- Refresh token automatique

### Dashboard
- Top scores par marché (US/EU, Afrique)
- Actions rapides (Barbell, Stratégies, Marchés)
- Compteurs dynamiques

### Explorer
- Recherche d'actifs
- Filtres par marché, type d'actif
- Pagination infinie
- Scores en temps réel

### Watchlist
- Ajout/suppression d'actifs
- Synchronisation avec le backend
- États loading/error

### News
- Feed Fintech/Startups Afrique
- Filtres par région et catégorie
- Partage natif
- Affichage propre (sans markdown)

### Stratégies
- Templates prédéfinis
- Barbell Builder (Core/Satellite)
- Simulation de portefeuille

### Billing
- Checkout Stripe (WebBrowser)
- Gestion abonnement (portail Stripe)
- Vérification entitlements

### Settings
- Profil utilisateur
- Notifications
- Sécurité (changement mot de passe)
- Aide et conditions

## Build Production

### Configuration EAS

```bash
# Installer EAS CLI
npm install -g eas-cli

# Login
eas login

# Configurer le projet
eas build:configure
```

### Build iOS

```bash
# Build pour App Store
eas build --platform ios --profile production

# Build pour TestFlight
eas build --platform ios --profile preview
```

### Build Android

```bash
# Build APK
eas build --platform android --profile preview

# Build AAB (Play Store)
eas build --platform android --profile production
```

## Tests

```bash
# Linting
npm run lint

# Type checking
npm run typecheck

# Tests unitaires
npm run test
```

## API Endpoints Utilisés

Voir `API_MAP.md` pour la liste complète des endpoints backend consommés.

## QA Checklist

Voir `QA_CHECKLIST.md` pour la liste des tests manuels par écran.

## Notes Importantes

1. **Pas de modification du backend existant** - L'app mobile consomme l'API existante sans modification destructive.

2. **Gestion des régions** - Le mapping des scopes (US_EU, AFRICA) est strict et cohérent avec le backend.

3. **Offline** - Cache React Query pour navigation offline basique sur les données déjà chargées.

4. **Sécurité** - Tokens stockés dans SecureStore (chiffré), pas en AsyncStorage.

5. **Deep Links** - Schéma URL `marketgps://` configuré pour les retours Stripe.

## Troubleshooting

### Erreur de cache Metro
```bash
npx expo start --clear
```

### Problème de pods iOS
```bash
cd ios && pod install --repo-update && cd ..
```

### Variables d'environnement non chargées
Vérifiez que le fichier `.env` est présent et redémarrez Expo.

## Contribuer

1. Les modifications doivent être ADDITIVES uniquement
2. Ne pas casser le web existant
3. Suivre les conventions de code existantes
4. Tester sur iOS ET Android avant PR

## Licence

Propriétaire - MarketGPS © 2026
