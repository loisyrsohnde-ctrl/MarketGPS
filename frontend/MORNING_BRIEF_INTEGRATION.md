# Morning Brief - Integration Guide

## Ajouter le lien dans la navigation

### 1. Sidebar Navigation

Trouver le fichier de navigation sidebar (généralement dans `components/layout/`):

```tsx
// components/layout/Sidebar.tsx
import Link from 'next/link';

export function Sidebar() {
  return (
    <nav className="space-y-2">
      {/* Existing links */}

      {/* Add Morning Brief Link */}
      <Link
        href="/morning-brief"
        className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-surface transition-colors"
      >
        <span className="text-xl">📊</span>
        <span className="font-medium">Morning Brief</span>
      </Link>

      {/* Rest of navigation */}
    </nav>
  );
}
```

### 2. Top Navigation Bar

Si vous avez une barre de navigation en haut:

```tsx
// components/layout/TopNav.tsx
import Link from 'next/link';

export function TopNav() {
  return (
    <nav className="flex items-center justify-between p-4">
      {/* Logo and links */}

      {/* Add Morning Brief quick access */}
      <Link
        href="/morning-brief"
        className="px-4 py-2 rounded-lg bg-score-blue/10 hover:bg-score-blue/20 text-score-blue font-medium transition-all"
        title="View your personalized daily briefing"
      >
        📊 Brief
      </Link>
    </nav>
  );
}
```

## Redirection après login

### Option 1: Redirection automatique après connexion

```tsx
// app/login/page.tsx
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  const handleLoginSuccess = async () => {
    // ... login logic ...

    // Redirect to Morning Brief instead of dashboard
    router.push('/morning-brief');
  };

  return (
    // ... login form ...
  );
}
```

### Option 2: Ajouter un bouton de redirection post-login

```tsx
// app/login/page.tsx
'use client';

import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      // Redirect to Morning Brief 2 seconds after login
      const timer = setTimeout(() => {
        router.push('/morning-brief');
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, router]);

  return (
    // ... login form ...
  );
}
```

## Intégrer dans le layout principal

### Mettre à jour le layout de l'app

```tsx
// app/layout.tsx
import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <div className="flex h-screen">
          {/* Sidebar avec lien Morning Brief */}
          <Sidebar />

          <div className="flex-1 flex flex-col">
            {/* Top nav avec accès rapide */}
            <TopNav />

            {/* Main content */}
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
```

## Ajouter un widget Morning Brief à d'autres pages

### Dashboard principal

```tsx
// app/dashboard/page.tsx
import { PortfolioSummary } from '@/components/dashboard';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import Link from 'next/link';

export default function DashboardPage() {
  const { data } = useMorningBrief();

  return (
    <div className="space-y-6">
      {/* Full Morning Brief Button */}
      <Link
        href="/morning-brief"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-score-blue/10 hover:bg-score-blue/20 text-score-blue font-medium transition-all"
      >
        <span>📊</span>
        <span>View Full Morning Brief</span>
      </Link>

      {/* Portfolio Summary Widget */}
      {data && (
        <PortfolioSummary
          metrics={data.portfolio}
          onViewDetails={() => {}}
        />
      )}
    </div>
  );
}
```

### Page d'accueil

```tsx
// app/page.tsx
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div>
      {isAuthenticated && (
        <Link
          href="/morning-brief"
          className="inline-block px-6 py-3 rounded-lg bg-score-green text-white font-bold hover:bg-score-green/90 transition-all"
        >
          Go to Your Daily Brief
        </Link>
      )}
    </div>
  );
}
```

## Ajouter des notifications pour le Morning Brief

### Créer une notification au login

```tsx
// hooks/useLoginNotifications.ts
import { useEffect } from 'react';
import { useAuth } from './useAuth';
import { useNotifications } from './useNotifications';

export function useLoginNotifications() {
  const { isAuthenticated } = useAuth();
  const { addNotification } = useNotifications();

  useEffect(() => {
    if (isAuthenticated) {
      addNotification({
        type: 'success',
        title: 'Welcome back!',
        description: 'Check your Morning Brief for today\'s market update',
        action: {
          label: 'View Brief',
          onClick: () => {
            window.location.href = '/morning-brief';
          },
        },
      });
    }
  }, [isAuthenticated, addNotification]);
}
```

## Intégrer avec les settings utilisateur

### Ajouter des préférences du Morning Brief

```tsx
// app/settings/morning-brief-settings/page.tsx
'use client';

import { useState } from 'react';
import { MorningBriefCard } from '@/components/dashboard';

export default function MorningBriefSettingsPage() {
  const [showPortfolio, setShowPortfolio] = useState(true);
  const [showAlerts, setShowAlerts] = useState(true);
  const [showOpportunities, setShowOpportunities] = useState(true);
  const [showNews, setShowNews] = useState(true);
  const [showGamification, setShowGamification] = useState(true);

  const handleSave = async () => {
    // Save preferences to backend
    const response = await fetch('/api/user/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        morningBrief: {
          showPortfolio,
          showAlerts,
          showOpportunities,
          showNews,
          showGamification,
        },
      }),
    });

    if (response.ok) {
      // Show success message
      console.log('Settings saved');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-3xl font-bold">Morning Brief Settings</h1>

      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-lg bg-surface">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={showPortfolio}
              onChange={(e) => setShowPortfolio(e.target.checked)}
            />
            <span>Show Portfolio Summary</span>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-surface">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={showAlerts}
              onChange={(e) => setShowAlerts(e.target.checked)}
            />
            <span>Show Alerts</span>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-surface">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={showOpportunities}
              onChange={(e) => setShowOpportunities(e.target.checked)}
            />
            <span>Show Opportunities</span>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-surface">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={showNews}
              onChange={(e) => setShowNews(e.target.checked)}
            />
            <span>Show News</span>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-surface">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={showGamification}
              onChange={(e) => setShowGamification(e.target.checked)}
            />
            <span>Show Gamification</span>
          </label>
        </div>
      </div>

      <button
        onClick={handleSave}
        className="px-6 py-2 rounded-lg bg-score-blue text-white font-medium hover:bg-score-blue/90 transition-all"
      >
        Save Preferences
      </button>
    </div>
  );
}
```

## Ajouter un widget Morning Brief dans d'autres composants

### Exemple: Widget dans la barre latérale

```tsx
// components/layout/SidebarWidget.tsx
'use client';

import { useMorningBrief } from '@/hooks/useMorningBrief';
import Link from 'next/link';

export function MorningBriefSidebarWidget() {
  const { data, isLoading } = useMorningBrief();

  if (isLoading || !data) return null;

  return (
    <Link
      href="/morning-brief"
      className="block p-4 rounded-lg bg-gradient-to-br from-score-blue/10 to-score-green/10 border border-score-blue/20 hover:border-score-blue/40 transition-all"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-sm">Today's Brief</h3>
        <span className="text-lg">📊</span>
      </div>

      <div className="space-y-1 text-xs text-text-secondary">
        <div className="flex justify-between">
          <span>Portfolio:</span>
          <span className={data.portfolio.dayChange > 0 ? 'text-score-green' : 'text-score-red'}>
            {data.portfolio.dayChange > 0 ? '+' : ''}{data.portfolio.dayChangePercent.toFixed(2)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span>Alerts:</span>
          <span className={data.alerts.unreadCount > 0 ? 'text-score-red' : 'text-text-secondary'}>
            {data.alerts.unreadCount}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Opportunities:</span>
          <span className="text-score-green">{data.opportunities.length}</span>
        </div>
      </div>

      <div className="mt-3 text-xs text-score-blue font-medium">
        → View Full Brief
      </div>
    </Link>
  );
}
```

## Utiliser avec des notifications push

### Ajouter des notifications push pour le Morning Brief

```tsx
// hooks/useMorningBriefNotifications.ts
import { useEffect } from 'react';
import { useMorningBrief } from './useMorningBrief';

export function useMorningBriefNotifications() {
  const { data } = useMorningBrief();

  useEffect(() => {
    if (!data || !('Notification' in window)) return;

    // Notify if there are critical alerts
    if (data.alerts.criticalCount > 0) {
      new Notification('🚨 Critical Alerts', {
        body: `You have ${data.alerts.criticalCount} critical alert(s)`,
        icon: '🚨',
        tag: 'critical-alerts',
      });
    }

    // Notify if portfolio changed significantly
    if (Math.abs(data.portfolio.dayChangePercent) > 5) {
      new Notification('📊 Significant Portfolio Change', {
        body: `Your portfolio changed by ${data.portfolio.dayChangePercent.toFixed(2)}%`,
        icon: '📊',
        tag: 'portfolio-change',
      });
    }
  }, [data]);
}
```

## Tests d'intégration

```tsx
// __tests__/morning-brief-integration.test.tsx
import { render, screen } from '@testing-library/react';
import { MorningBriefIntegration } from '@/app/morning-brief/page';

describe('Morning Brief Integration', () => {
  it('should navigate to morning brief from home page', () => {
    render(<HomePage />);

    const link = screen.getByRole('link', { name: /morning brief/i });
    expect(link).toHaveAttribute('href', '/morning-brief');
  });

  it('should display morning brief after login', () => {
    // Mock login
    // Check that user is redirected to /morning-brief
  });
});
```

## Checklist d'intégration

- [ ] Ajouter le lien dans la sidebar navigation
- [ ] Ajouter le lien dans la top navigation
- [ ] Configurer la redirection post-login
- [ ] Tester la navigation vers /morning-brief
- [ ] Vérifier que tous les widgets se chargent
- [ ] Vérifier que le hook useMorningBrief récupère les données
- [ ] Tester le refresh des données
- [ ] Vérifier l'authentification (redirection si non connecté)
- [ ] Tester la responsivité sur mobile
- [ ] Ajouter les tests d'intégration
- [ ] Déployer et tester en production
