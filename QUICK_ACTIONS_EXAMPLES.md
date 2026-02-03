# Quick Actions - Exemples d'Utilisation

## 1. Utilisation Basique dans un Composant

```tsx
import { QuickActions } from '@/components/asset/QuickActions';
import { CreateAlertModal } from '@/components/alerts/CreateAlertModal';
import { AssetComparator } from '@/components/asset/AssetComparator';
import type { Asset } from '@/types';

export function MyAssetPage() {
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [isComparatorOpen, setIsComparatorOpen] = useState(false);

  const asset: Asset = {
    asset_id: '1',
    ticker: 'AAPL',
    symbol: 'AAPL',
    name: 'Apple Inc.',
    asset_type: 'EQUITY',
    market_scope: 'US_EU',
    market_code: 'US',
    score_total: 75.5,
    score_value: 70,
    score_momentum: 80,
    score_safety: 75,
    coverage: 0.95,
    liquidity: 0.9,
    fx_risk: 0.1,
    last_price: 150.25,
    currency: 'USD',
    updated_at: new Date().toISOString(),
  };

  return (
    <>
      <QuickActions
        asset={asset}
        onOpenAlert={() => setIsAlertOpen(true)}
        onOpenComparator={() => setIsComparatorOpen(true)}
        variant="horizontal"
      />

      <CreateAlertModal
        isOpen={isAlertOpen}
        onClose={() => setIsAlertOpen(false)}
        asset={asset}
        onCreateAlert={async (config) => {
          console.log('Alert config:', config);
          // Envoyer à l'API
          // await api.createAlert(config);
        }}
      />

      <AssetComparator
        isOpen={isComparatorOpen}
        onClose={() => setIsComparatorOpen(false)}
        initialAsset={asset}
      />
    </>
  );
}
```

## 2. Utilisation avec Raccourcis Clavier

```tsx
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { QuickActions } from '@/components/asset/QuickActions';

export function AssetWithShortcuts() {
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [isComparatorOpen, setIsComparatorOpen] = useState(false);
  const { isInWatchlist, toggleWatchlist } = useQuickActions({...});

  useKeyboardShortcuts({
    toggleWatchlist,
    openAlert: () => setIsAlertOpen(true),
    openComparator: () => setIsComparatorOpen(true),
  });

  return (
    <QuickActions
      asset={asset}
      onOpenAlert={() => setIsAlertOpen(true)}
      onOpenComparator={() => setIsComparatorOpen(true)}
      variant="horizontal"
    />
  );
}
```

## 3. Variante Verticale (Sidebar)

```tsx
<div className="flex gap-6">
  {/* Main content */}
  <div className="flex-1">
    {/* Asset details */}
  </div>

  {/* Sidebar with vertical actions */}
  <aside className="w-64">
    <QuickActions
      asset={asset}
      onOpenAlert={() => setIsAlertOpen(true)}
      onOpenComparator={() => setIsComparatorOpen(true)}
      variant="vertical"
    />
  </aside>
</div>
```

## 4. Variante Floating (FAB)

```tsx
<QuickActions
  asset={asset}
  onOpenAlert={() => setIsAlertOpen(true)}
  onOpenComparator={() => setIsComparatorOpen(true)}
  variant="floating"
/>
```

## 5. Barre Sticky avec Actions

```tsx
import { QuickActionsBar } from '@/components/asset/QuickActionsBar';

export function PageWithStickyActions() {
  return (
    <>
      <QuickActionsBar
        asset={asset}
        onOpenAlert={() => setIsAlertOpen(true)}
        onOpenComparator={() => setIsComparatorOpen(true)}
        sticky={true}
        showTooltips={true}
      />

      {/* Page content */}
    </>
  );
}
```

## 6. Créer une Alerte

```tsx
const { onCreateAlert } = async (config) => {
  try {
    // Exemple d'appel API
    const response = await fetch('/api/alerts/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        asset_ticker: 'AAPL',
        type: 'price_threshold',
        condition: '>',
        threshold_value: 150,
        channels: ['in_app', 'email'],
        frequency: 'immediate',
        enabled: true,
      }),
    });

    if (response.ok) {
      console.log('Alert créée avec succès');
    }
  } catch (error) {
    console.error('Erreur lors de la création:', error);
  }
};

<CreateAlertModal
  isOpen={isAlertOpen}
  onClose={() => setIsAlertOpen(false)}
  asset={asset}
  onCreateAlert={onCreateAlert}
/>
```

## 7. Comparaison d'Actifs

```tsx
const handleCompare = (selectedAssets: Asset[]) => {
  console.log('Actifs à comparer:', selectedAssets.map(a => a.ticker));

  // Optionnel: envoyer à une autre page
  // navigate(`/compare?tickers=${selectedAssets.map(a => a.ticker).join(',')}`);
};

<AssetComparator
  isOpen={isComparatorOpen}
  onClose={() => setIsComparatorOpen(false)}
  initialAsset={asset}
  assets={allAvailableAssets} // Liste de tous les assets
  onCompare={handleCompare}
/>
```

## 8. Intégration Complète dans AssetDetailPage

```tsx
'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { QuickActions } from '@/components/asset/QuickActions';
import { QuickActionsBar } from '@/components/asset/QuickActionsBar';
import { CreateAlertModal } from '@/components/alerts/CreateAlertModal';
import { AssetComparator } from '@/components/asset/AssetComparator';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useQuickActions } from '@/hooks/useQuickActions';
import { api } from '@/lib/api';

export default function AssetDetailPage() {
  const params = useParams();
  const ticker = params.ticker as string;
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [isComparatorOpen, setIsComparatorOpen] = useState(false);

  // Fetch asset
  const { data: asset } = useQuery({
    queryKey: ['asset', ticker],
    queryFn: () => api.getAssetDetails(ticker),
  });

  // Quick actions hook
  const { toggleWatchlist } = useQuickActions({
    assetId: asset?.asset_id || '',
    ticker,
    userId: 'default',
  });

  // Keyboard shortcuts
  useKeyboardShortcuts({
    toggleWatchlist,
    openAlert: () => setIsAlertOpen(true),
    openComparator: () => setIsComparatorOpen(true),
  });

  if (!asset) return <div>Chargement...</div>;

  return (
    <>
      {/* Sticky action bar */}
      <QuickActionsBar
        asset={asset}
        onOpenAlert={() => setIsAlertOpen(true)}
        onOpenComparator={() => setIsComparatorOpen(true)}
        sticky
      />

      {/* Main content */}
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Asset info */}
        <div>
          <h1>{asset.ticker} - {asset.name}</h1>
          <p>Score: {asset.score_total}</p>
        </div>

        {/* Quick actions card */}
        <div className="card">
          <h2>Actions rapides</h2>
          <QuickActions
            asset={asset}
            onOpenAlert={() => setIsAlertOpen(true)}
            onOpenComparator={() => setIsComparatorOpen(true)}
            variant="horizontal"
          />
        </div>

        {/* More content */}
      </div>

      {/* Modals */}
      <CreateAlertModal
        isOpen={isAlertOpen}
        onClose={() => setIsAlertOpen(false)}
        asset={asset}
        onCreateAlert={async (config) => {
          // TODO: API call
          console.log('Creating alert:', config);
        }}
      />

      <AssetComparator
        isOpen={isComparatorOpen}
        onClose={() => setIsComparatorOpen(false)}
        initialAsset={asset}
        onCompare={(selected) => {
          console.log('Compare:', selected.map(a => a.ticker));
        }}
      />
    </>
  );
}
```

## 9. Style Personnalisé

```tsx
// Override styles avec className
<QuickActions
  asset={asset}
  onOpenAlert={() => setIsAlertOpen(true)}
  className="rounded-2xl shadow-xl"
/>

// Ou avec Tailwind CSS customization
<div className="[&_.quick-action-btn]:rounded-full">
  <QuickActions
    asset={asset}
    onOpenAlert={() => setIsAlertOpen(true)}
  />
</div>
```

## 10. Gestion des Erreurs

```tsx
const [error, setError] = useState<string | null>(null);

const handleCreateAlert = async (config: AlertConfig) => {
  try {
    const response = await api.createAlert(config);
    if (!response.ok) {
      setError('Impossible de créer l\'alerte');
      return;
    }
    // Success
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Erreur');
  }
};

{error && (
  <div className="alert alert-error">
    {error}
  </div>
)}

<CreateAlertModal
  isOpen={isAlertOpen}
  onClose={() => {
    setIsAlertOpen(false);
    setError(null);
  }}
  asset={asset}
  onCreateAlert={handleCreateAlert}
/>
```

## 11. Responsive Design

```tsx
// Mobile: floating FAB
// Tablet: vertical actions
// Desktop: horizontal actions + sticky bar

import { useMediaQuery } from '@/hooks/useMediaQuery';

export function ResponsiveQuickActions() {
  const isMobile = useMediaQuery('(max-width: 640px)');
  const isTablet = useMediaQuery('(max-width: 1024px)');

  return (
    <QuickActions
      asset={asset}
      variant={isMobile ? 'floating' : isTablet ? 'vertical' : 'horizontal'}
    />
  );
}
```

## 12. Intégration avec Analytics

```tsx
const handleAction = (action: string, success: boolean) => {
  // Track user action
  analytics.track('quick_action', {
    action,
    success,
    asset_ticker: asset.ticker,
    timestamp: new Date().toISOString(),
  });
};

<QuickActions
  asset={asset}
  onOpenAlert={() => {
    handleAction('open_alert', true);
    setIsAlertOpen(true);
  }}
  {...otherProps}
/>
```

## 13. Afficher l'Aide des Raccourcis

```tsx
import { KeyboardShortcutsHelp } from '@/components/asset/KeyboardShortcutsHelp';

export function AssetHeader() {
  return (
    <div className="flex justify-between items-center">
      <h1>{asset.ticker}</h1>
      <KeyboardShortcutsHelp />
    </div>
  );
}
```

## 14. Formulaire d'Alerte Avancée

```tsx
<CreateAlertModal
  isOpen={isAlertOpen}
  onClose={() => setIsAlertOpen(false)}
  asset={asset}
  onCreateAlert={async (config) => {
    // Support des conditions avancées
    const advancedConfig = {
      ...config,
      type: 'price_threshold',
      condition: '>' as const,
      threshold_value: 150.50,
      range_min: undefined,
      range_max: undefined,
      channels: ['in_app', 'email'] as const,
      frequency: 'immediate' as const,
    };

    const response = await fetch('/api/alerts/rules', {
      method: 'POST',
      body: JSON.stringify(advancedConfig),
    });
    // ...
  }}
/>
```

## 15. État Partagé avec Context (Optionnel)

```tsx
import { createContext, useContext } from 'react';

const QuickActionsContext = createContext<{
  isAlertOpen: boolean;
  setIsAlertOpen: (open: boolean) => void;
  isComparatorOpen: boolean;
  setIsComparatorOpen: (open: boolean) => void;
}>({
  isAlertOpen: false,
  setIsAlertOpen: () => {},
  isComparatorOpen: false,
  setIsComparatorOpen: () => {},
});

export function useQuickActionsState() {
  return useContext(QuickActionsContext);
}

export function QuickActionsProvider({ children }: { children: React.ReactNode }) {
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [isComparatorOpen, setIsComparatorOpen] = useState(false);

  return (
    <QuickActionsContext.Provider
      value={{ isAlertOpen, setIsAlertOpen, isComparatorOpen, setIsComparatorOpen }}
    >
      {children}
    </QuickActionsContext.Provider>
  );
}

// Usage dans un composant
const { isAlertOpen, setIsAlertOpen } = useQuickActionsState();
```

---

Ces exemples couvrent les cas d'usage principaux et les patterns courants pour intégrer les Quick Actions dans votre application.
