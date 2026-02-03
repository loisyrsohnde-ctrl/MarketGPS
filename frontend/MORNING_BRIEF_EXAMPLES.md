# Morning Brief - Examples & Usage

## Example 1: Basic Integration

### Import et utilisation simple
```tsx
'use client';

import { useMorningBrief } from '@/hooks/useMorningBrief';
import { Loader } from '@/components/ui/loader';

export default function DashboardPage() {
  const { data, isLoading, error } = useMorningBrief();

  if (isLoading) return <Loader />;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;

  return (
    <div>
      <h1>Welcome, {data.greeting.firstName}!</h1>
      <p>Portfolio value: {data.portfolio.totalValue}</p>
      <p>Average score: {data.portfolio.averageScore}</p>
    </div>
  );
}
```

## Example 2: Afficher un widget spécifique

### Afficher uniquement le résumé du portefeuille
```tsx
import { PortfolioSummary } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { useRouter } from 'next/navigation';

export default function PortfolioWidget() {
  const router = useRouter();
  const { data, isLoading } = useMorningBrief();

  if (isLoading || !data) return null;

  return (
    <PortfolioSummary
      metrics={data.portfolio}
      onViewDetails={() => router.push('/dashboard/wealth')}
    />
  );
}
```

## Example 3: Traiter les alertes

### Filtrer et afficher les alertes critiques
```tsx
import { AlertsPreview } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';

export default function CriticalAlertsWidget() {
  const { data } = useMorningBrief();

  if (!data) return null;

  const criticalAlerts = data.alerts.recent.filter(
    (alert) => alert.severity === 'critical'
  );

  return (
    <AlertsPreview
      unreadCount={data.alerts.unreadCount}
      criticalCount={criticalAlerts.length}
      recentAlerts={criticalAlerts}
      onViewAll={() => window.location.href = '/alerts'}
    />
  );
}
```

## Example 4: Créer un widget personnalisé

### Combiner plusieurs données
```tsx
import { MorningBriefCard } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';

export default function CustomSummaryWidget() {
  const { data } = useMorningBrief();

  if (!data) return null;

  const totalOpportunities = data.opportunities.length;
  const totalNews = data.news.breaking.length + data.news.important.length;
  const completedObjectives = data.gamification.objectives.filter(
    (obj) => obj.isCompleted
  ).length;

  return (
    <MorningBriefCard
      title="Quick Overview"
      icon="🎯"
      variant="highlight"
    >
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-score-green">
            {totalOpportunities}
          </p>
          <p className="text-xs text-text-secondary">Opportunities</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-score-blue">
            {totalNews}
          </p>
          <p className="text-xs text-text-secondary">News Items</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-score-yellow">
            {completedObjectives}
          </p>
          <p className="text-xs text-text-secondary">Objectives</p>
        </div>
      </div>
    </MorningBriefCard>
  );
}
```

## Example 5: Ajouter un bouton de refresh

### Rafraîchir les données manuellement
```tsx
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { RefreshCw } from 'lucide-react';
import { useState } from 'react';

export default function RefreshableWidget() {
  const { data, isLoading, refetch } = useMorningBrief();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refetch();
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-score-blue/10 hover:bg-score-blue/20"
      >
        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        <span>Refresh</span>
      </button>
    </div>
  );
}
```

## Example 6: Afficher les opportunités avec actions

### Afficher les opportunités et ajouter à la watchlist
```tsx
import { OpportunitiesWidget } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { useState } from 'react';

export default function OpportunitiesPage() {
  const { data } = useMorningBrief();
  const [addedToWatchlist, setAddedToWatchlist] = useState<string[]>([]);

  const handleAddToWatchlist = async (opportunity: any) => {
    try {
      const response = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: opportunity.asset.ticker,
          notes: `Added from opportunities - ${opportunity.type}`,
        }),
      });

      if (response.ok) {
        setAddedToWatchlist((prev) => [
          ...prev,
          opportunity.asset.ticker,
        ]);
      }
    } catch (error) {
      console.error('Failed to add to watchlist:', error);
    }
  };

  if (!data) return null;

  return (
    <OpportunitiesWidget
      opportunities={data.opportunities}
      onAddToWatchlist={handleAddToWatchlist}
      onViewAll={() => window.location.href = '/opportunities'}
    />
  );
}
```

## Example 7: Afficher les news avec sentiment

### Afficher les news filtrées par sentiment
```tsx
import { NewsDigest } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';

export default function BullishNewsWidget() {
  const { data } = useMorningBrief();

  if (!data) return null;

  // Filter for bullish news only
  const bullishNews = [
    ...data.news.breaking.filter((n) => n.sentiment === 'positive'),
    ...data.news.important.filter((n) => n.sentiment === 'positive'),
  ];

  return (
    <NewsDigest
      breaking={bullishNews.filter((n) => n.isBreaking)}
      important={bullishNews.filter((n) => !n.isBreaking)}
      onViewAll={() => window.location.href = '/news'}
    />
  );
}
```

## Example 8: Gamification - Afficher le level actuel

### Afficher les objectifs et le level
```tsx
import { GamificationWidget } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';

export default function GamificationDisplay() {
  const { data } = useMorningBrief();

  if (!data) return null;

  return (
    <GamificationWidget
      status={data.gamification}
      onViewDetails={() => window.location.href = '/gamification'}
    />
  );
}
```

## Example 9: Affichage conditionnel selon l'état

### Afficher différemment selon l'état du portefeuille
```tsx
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { motion } from 'framer-motion';

export default function PortfolioStatus() {
  const { data } = useMorningBrief();

  if (!data) return null;

  const isPositiveDay = data.portfolio.dayChange > 0;
  const isHighRisk = data.portfolio.riskScore > 75;

  return (
    <motion.div
      className={`p-4 rounded-lg ${
        isHighRisk
          ? 'bg-score-red/10 border border-score-red/30'
          : 'bg-score-green/10 border border-score-green/30'
      }`}
      animate={{
        scale: isHighRisk ? [1, 1.02, 1] : 1,
      }}
      transition={{ duration: 2, repeat: isHighRisk ? Infinity : 0 }}
    >
      <h3 className="font-semibold">
        {isPositiveDay ? '📈 Green Day' : '📉 Red Day'}
      </h3>
      <p className="text-sm text-text-secondary mt-2">
        {isHighRisk && '⚠️ High risk detected. Consider adjusting your strategy.'}
      </p>
    </motion.div>
  );
}
```

## Example 10: Créer une page de dashboard complet

### Page complète avec tous les widgets
```tsx
'use client';

import { useRouter } from 'next/navigation';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import {
  PortfolioSummary,
  AlertsPreview,
  OpportunitiesWidget,
  NewsDigest,
  GamificationWidget,
} from '@/components/dashboard';
import { Loader } from '@/components/ui/loader';
import { RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

export default function FullMorningBrief() {
  const router = useRouter();
  const { data, isLoading, refetch } = useMorningBrief();

  if (isLoading || !data) return <Loader />;

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6 p-6"
    >
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">
          Good {data.greeting.timeOfDay}, {data.greeting.firstName}!
        </h1>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue/10"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PortfolioSummary
            metrics={data.portfolio}
            onViewDetails={() => router.push('/dashboard')}
          />
        </div>
        <div>
          <AlertsPreview
            unreadCount={data.alerts.unreadCount}
            criticalCount={data.alerts.criticalCount}
            recentAlerts={data.alerts.recent}
            onViewAll={() => router.push('/alerts')}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <OpportunitiesWidget
            opportunities={data.opportunities}
            onViewAll={() => router.push('/opportunities')}
          />
        </div>
        <div>
          <GamificationWidget
            status={data.gamification}
            onViewDetails={() => router.push('/gamification')}
          />
        </div>
      </div>

      <NewsDigest
        breaking={data.news.breaking}
        important={data.news.important}
        onViewAll={() => router.push('/news')}
      />
    </motion.div>
  );
}
```

## Conseils de Performance

1. **Memoization** - Utiliser `useMemo` pour les données transformées
2. **Lazy loading** - Charger les composants avec `next/dynamic`
3. **Image optimization** - Utiliser `next/image` pour les news images
4. **Debounce** - Debouncer les refreshes fréquents
5. **Caching** - Implémenter un système de cache côté client

## Debugging

```tsx
// Afficher les données du hook
const { data, isLoading, error } = useMorningBrief();

useEffect(() => {
  console.log('Morning Brief Data:', {
    greeting: data?.greeting,
    portfolio: data?.portfolio,
    alerts: data?.alerts,
    opportunities: data?.opportunities.length,
    news: data?.news,
    gamification: data?.gamification,
  });
}, [data]);
```

## Testing

```tsx
import { render, screen } from '@testing-library/react';
import { PortfolioSummary } from '@/components/dashboard';
import type { PortfolioMetrics } from '@/types/morning-brief';

const mockMetrics: PortfolioMetrics = {
  totalValue: 100000,
  dayChange: 1000,
  dayChangePercent: 1.0,
  weekChange: 2000,
  weekChangePercent: 2.0,
  monthChange: 5000,
  monthChangePercent: 5.0,
  averageScore: 75,
  topGainers: [],
  topLosers: [],
  diversificationScore: 80,
  riskScore: 40,
};

describe('PortfolioSummary', () => {
  it('renders portfolio summary with metrics', () => {
    render(
      <PortfolioSummary
        metrics={mockMetrics}
        onViewDetails={() => {}}
      />
    );

    expect(screen.getByText('Portfolio Performance')).toBeInTheDocument();
    expect(screen.getByText('100000')).toBeInTheDocument(); // totalValue
  });
});
```
