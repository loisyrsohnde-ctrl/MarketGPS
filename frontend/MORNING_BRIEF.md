# Morning Brief Dashboard

Une dashboard personnalisée et dynamique qui s'affiche à la connexion avec un résumé de tout ce qui est important pour l'utilisateur.

## Vue d'ensemble

Le Morning Brief Dashboard est conçu pour offrir une vue holistique de la situation de marché et du portefeuille de l'utilisateur en moins de 30 secondes. Il combine plusieurs widgets intelligents qui s'adaptent aux données et à l'état de l'utilisateur.

## Architecture

### Structure des fichiers

```
/app/morning-brief/
  ├── page.tsx              # Page principale du Morning Brief
  └── layout.tsx            # Layout avec métadonnées

/components/dashboard/
  ├── MorningBriefCard.tsx  # Composant card réutilisable
  ├── PortfolioSummary.tsx  # Résumé du portefeuille
  ├── AlertsPreview.tsx     # Aperçu des alertes
  ├── OpportunitiesWidget.tsx  # Opportunités détectées
  ├── NewsDigest.tsx        # Digest des news
  ├── GamificationWidget.tsx # Statut de gamification
  └── index.ts              # Barrel export

/hooks/
  └── useMorningBrief.ts    # Hook personnalisé pour les données

/types/
  └── morning-brief.ts      # Types TypeScript

/app/api/
  ├── portfolio/metrics/    # Métriques du portefeuille
  ├── alerts/               # Alertes
  ├── opportunities/        # Opportunités
  ├── news/digest/          # News digest
  ├── gamification/status/  # Statut gamification
  └── watchlist/            # Ajout à la watchlist
```

## Composants

### 1. MorningBriefCard
Composant card réutilisable pour chaque section du brief.

**Props:**
```typescript
interface MorningBriefCardProps {
  title: string;
  icon: ReactNode;
  children: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
  variant?: 'default' | 'highlight' | 'alert';
  size?: 'sm' | 'md' | 'lg';
}
```

### 2. PortfolioSummary
Résumé du portefeuille avec métriques clés.

**Affiche:**
- Valeur totale estimée
- Performance jour/semaine/mois avec pourcentages
- Score moyen du portefeuille
- Actifs en hausse et en baisse
- Score de diversification et de risque avec barre de progression

### 3. AlertsPreview
Aperçu des alertes avec compteur et détails.

**Affiche:**
- Nombre d'alertes non lues
- Nombre d'alertes critiques
- 3 dernières alertes avec icônes par type et sévérité
- Bouton "Voir toutes les alertes"

**Types d'alertes:**
- `price` - Changement de prix
- `score` - Changement de score
- `news` - Nouvelles news
- `opportunity` - Nouvelle opportunité
- `risk` - Alerte risque

### 4. OpportunitiesWidget
Opportunités détectées avec score et tendance.

**Affiche:**
- Top 5 actifs avec opportunités
- Type d'opportunité (high_score, trending, undervalued, breakout)
- Score de l'actif
- Barre de confiance animée
- Bouton "Ajouter à la watchlist"

### 5. NewsDigest
Digest des news avec sentiment et catégorisation.

**Affiche:**
- News "Breaking" avec badge spécial
- News "Important" en ordre d'importance
- Sentiment (positif/négatif/neutre) avec icône
- Source et heure relative
- Tickers associés

### 6. GamificationWidget
Statut de gamification avec level et objectifs.

**Affiche:**
- Level actuel avec icône et points totaux
- Streak de jours consécutifs
- Barre de progression hebdomadaire
- Objectifs actifs avec barre de progression
- Points récompensés

## Hook: useMorningBrief

Hook personnalisé pour récupérer toutes les données du morning brief.

```typescript
const { data, isLoading, error, refetch } = useMorningBrief();
```

**Retourne:**
```typescript
interface UseMorningBriefResponse {
  data: MorningBriefData | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}
```

**Données fetched:**
- Portfolio metrics
- Alerts
- Opportunities
- News digest
- Gamification status

## Types

### MorningBriefData
Structure principale contenant toutes les données du dashboard.

```typescript
interface MorningBriefData {
  greeting: {
    firstName: string;
    timeOfDay: 'morning' | 'afternoon' | 'evening';
  };
  portfolio: PortfolioMetrics;
  alerts: {
    unreadCount: number;
    recent: Alert[];
    criticalCount: number;
  };
  opportunities: Opportunity[];
  news: {
    breaking: NewsItem[];
    important: NewsItem[];
  };
  gamification: GamificationStatus;
  lastUpdated: string;
}
```

## Routes API

### Portfolio Metrics
`GET /api/portfolio/metrics` - Retourne les métriques du portefeuille

### Alerts
`GET /api/alerts?limit=3` - Retourne les alertes récentes

### Opportunities
`GET /api/opportunities?limit=5` - Retourne les opportunités détectées

### News Digest
`GET /api/news/digest?limit=5` - Retourne le digest des news

### Gamification Status
`GET /api/gamification/status` - Retourne le statut de gamification

### Watchlist
`POST /api/watchlist` - Ajoute un actif à la watchlist

## Styles

### Tailwind CSS + Framer Motion
- Grille responsive (1 col mobile, 2 cols tablet, 3 cols desktop)
- Cards avec ombres douces et glassmorphism
- Couleurs:
  - Positif: `text-score-green`
  - Négatif: `text-score-red`
  - Neutre: `text-text-secondary`
- Animations subtiles avec Framer Motion
- Dark mode support intégré

### Variantes de Cards
- `default` - Style standard avec border subtle
- `highlight` - Fond vert avec border verte (données importantes)
- `alert` - Fond rouge avec border rouge (alertes critiques)

## Navigation

### Intégration dans la sidebar
Ajouter un lien "Morning Brief" dans la navigation principale:

```tsx
<Link href="/morning-brief">
  <span>📊 Morning Brief</span>
</Link>
```

### Redirection post-login (optionnel)
Pour rediriger automatiquement vers le Morning Brief après connexion:

```tsx
// Dans le composant login success
router.push('/morning-brief');
```

## Performance

### Optimisations implémentées
1. **Données parallèles** - Toutes les requêtes API sont lancées en parallèle
2. **Caching** - Les données sont mises en cache par le hook
3. **Lazy loading** - Les images et composants non visibles sont chargés tardivement
4. **Animations performantes** - Utilisation de `transform` et `opacity` uniquement
5. **Responsive design** - Pas de changement DOM, juste CSS media queries

### Temps de chargement cible
- First paint: < 1s
- Fully interactive: < 2s
- Refresh: < 500ms

## Accessibilité

- Tous les composants supportent les attributs ARIA
- Contraste de couleur conforme WCAG AA
- Navigation au clavier complète
- Lecteurs d'écran supportés
- Textes informatifs pour les icônes

## Futures améliorations

1. **Résumé audio** - Générer un brief audio basé sur les données
2. **Personnalisation** - Permettre de réorganiser les widgets
3. **Prédictions** - Ajouter des prédictions de prix basées sur l'IA
4. **Comparaisons** - Comparer la performance à des benchmarks
5. **Rapports hebdomadaires** - Générer un rapport résumé
6. **Notifications** - Alertes push pour les événements critiques

## Intégration avec le backend

Les routes API actuelles retournent des données mock. Pour l'intégration réelle:

1. Remplacer les requêtes mock par des appels vers le backend réel
2. Implémenter l'authentification avec Supabase
3. Ajouter la validation et l'error handling
4. Implémenter le caching côté backend

## Exemples d'utilisation

### Importer les composants
```tsx
import {
  MorningBriefCard,
  PortfolioSummary,
  AlertsPreview,
  OpportunitiesWidget,
  NewsDigest,
  GamificationWidget,
} from '@/components/dashboard';

import { useMorningBrief } from '@/hooks/useMorningBrief';
```

### Utiliser le hook
```tsx
export default function MyComponent() {
  const { data, isLoading, error, refetch } = useMorningBrief();

  if (isLoading) return <Loader />;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;

  return (
    <PortfolioSummary
      metrics={data.portfolio}
      onViewDetails={() => console.log('View details')}
    />
  );
}
```

## Dépendances

- `react` - React core
- `next` - Next.js framework
- `framer-motion` - Animations
- `lucide-react` - Icônes
- `tailwindcss` - Styling
- `clsx` - Utility pour les classes
- `tailwind-merge` - Merge de classes Tailwind

## Licence

MIT
