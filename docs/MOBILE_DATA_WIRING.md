# MARKETGPS MOBILE - DATA WIRING & API INTEGRATION

**Date**: 27 Janvier 2026
**Version**: 1.0

---

## CONFIGURATION API

### Base URL

```typescript
// src/lib/config.ts
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://api.marketgps.online';

// Environnements
// Development: http://localhost:8000
// Staging: https://staging-api.marketgps.online
// Production: https://api.marketgps.online
```

### Headers par Défaut

```typescript
const defaultHeaders = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

// Avec authentification
const authHeaders = {
  ...defaultHeaders,
  'Authorization': `Bearer ${accessToken}`,
};
```

### Timeout & Retry

```typescript
const REQUEST_TIMEOUT = 15000; // 15 secondes
const MAX_RETRIES = 2;
const RETRY_DELAY = 1000; // 1 seconde entre retries
```

---

## AUTHENTIFICATION

### Mécanisme

- **Provider**: Supabase Auth
- **Token Storage**: `expo-secure-store`
- **Token Type**: JWT (access_token)
- **Refresh**: Automatique via Supabase client

### Flux Auth

```
1. User login (email/password)
      │
      ▼
2. Supabase signInWithPassword()
      │
      ▼
3. Receive session {access_token, refresh_token, user}
      │
      ▼
4. Store tokens via expo-secure-store
      │
      ▼
5. Update Zustand auth store
      │
      ▼
6. API calls include Bearer token
```

### Code Auth Store

```typescript
// src/store/auth.ts
interface AuthState {
  session: Session | null;
  user: User | null;
  subscription: SubscriptionStatus | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  initialize: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshSubscription: () => Promise<void>;
}

// Selectors
export const useUser = () => useAuthStore((s) => s.user);
export const useIsAuthenticated = () => useAuthStore((s) => !!s.session);
export const useIsPro = () => useAuthStore((s) => s.subscription?.is_active ?? false);
```

---

## ENDPOINTS UTILISÉS

### 1. Assets & Discovery

| Endpoint | Méthode | Usage Mobile | Cache |
|----------|---------|--------------|-------|
| `/api/assets/top-scored` | GET | Dashboard top 10 | 5 min |
| `/api/assets/search` | GET | Explorer search | 1 min |
| `/api/assets/explorer` | GET | Explorer list | 2 min |
| `/api/assets/{ticker}` | GET | Asset detail | 5 min |
| `/api/assets/{ticker}/chart` | GET | Price chart data | 5 min |
| `/api/metrics/counts` | GET | Scope counts | 10 min |
| `/api/logos/{ticker}` | GET | Asset logos | 24h |

**Exemple Requête:**
```typescript
// Top Scored
const response = await api.get('/api/assets/top-scored', {
  params: {
    limit: 10,
    market_scope: 'US_EU', // ou 'AFRICA'
    only_scored: true,
  }
});

// Explorer avec filtres
const response = await api.get('/api/assets/explorer', {
  params: {
    market_scope: 'AFRICA',
    asset_type: 'EQUITY',
    country: 'NG',        // Nigeria
    region: 'WEST',       // West Africa
    query: 'dangote',
    page: 1,
    page_size: 20,
  }
});
```

### 2. Watchlist

| Endpoint | Méthode | Usage Mobile | Auth |
|----------|---------|--------------|------|
| `/api/watchlist` | GET | Liste watchlist | ✅ |
| `/api/watchlist` | POST | Ajouter asset | ✅ |
| `/api/watchlist/{ticker}` | DELETE | Retirer asset | ✅ |
| `/api/watchlist/check/{ticker}` | GET | Vérifier présence | ✅ |

**Exemple Requête:**
```typescript
// Get watchlist
const response = await api.get('/api/watchlist', {
  headers: { Authorization: `Bearer ${token}` },
  params: { market_scope: 'US_EU' }
});

// Add to watchlist
await api.post('/api/watchlist',
  { ticker: 'AAPL', notes: 'Tech leader' },
  { headers: { Authorization: `Bearer ${token}` } }
);
```

### 3. Stratégies

| Endpoint | Méthode | Usage Mobile | Cache |
|----------|---------|--------------|-------|
| `/api/strategies/templates` | GET | Liste templates | 5 min |
| `/api/strategies/templates/{slug}` | GET | Détail template | 5 min |
| `/api/strategies/templates/{slug}/compositions` | GET | Compositions | 5 min |
| `/api/strategies/eligible-instruments` | GET | Assets éligibles | 2 min |
| `/api/strategies/simulate` | POST | Backtest | No cache |
| `/api/strategies/user` | GET | Mes stratégies | 1 min |
| `/api/strategies/user` | POST | Créer stratégie | - |
| `/api/strategies/user/{id}` | PUT | Modifier | - |
| `/api/strategies/user/{id}` | DELETE | Supprimer | - |

**Exemple Requête:**
```typescript
// Get templates
const response = await api.get('/api/strategies/templates', {
  params: {
    category: 'balanced',
    risk_level: 'moderate',
  }
});

// Simulate strategy
const response = await api.post('/api/strategies/simulate', {
  compositions: [
    { ticker: 'VTI', block_name: 'core', weight: 0.4 },
    { ticker: 'BND', block_name: 'bonds', weight: 0.3 },
    { ticker: 'GLD', block_name: 'commodities', weight: 0.15 },
    { ticker: 'CASH', block_name: 'cash', weight: 0.15 },
  ],
  period_years: 5,
  initial_value: 10000,
  rebalance_frequency: 'quarterly',
});
```

### 4. Barbell

| Endpoint | Méthode | Usage Mobile | Cache |
|----------|---------|--------------|-------|
| `/api/barbell/suggest` | GET | Suggestions | 2 min |
| `/api/barbell/core-candidates` | GET | Candidats Core | 5 min |
| `/api/barbell/satellite-candidates` | GET | Candidats Satellite | 5 min |
| `/api/barbell/simulate` | POST | Backtest | No cache |
| `/api/barbell/portfolios` | GET | Mes portfolios | 1 min |
| `/api/barbell/portfolios` | POST | Sauvegarder | - |

**Exemple Requête:**
```typescript
// Get suggestion
const response = await api.get('/api/barbell/suggest', {
  params: {
    risk_profile: 'moderate', // conservative, moderate, aggressive
    market_scope: 'US_EU',
    core_count: 5,
    satellite_count: 5,
  }
});
```

### 5. News

| Endpoint | Méthode | Usage Mobile | Cache |
|----------|---------|--------------|-------|
| `/api/news` | GET | Feed paginé | 10 min |
| `/api/news/{slug}` | GET | Article complet | 30 min |
| `/api/news/saved` | GET | Articles sauvés | 1 min |
| `/api/news/{id}/save` | POST | Sauvegarder | - |
| `/api/news/{id}/save` | DELETE | Retirer | - |
| `/api/news/regions` | GET | Liste régions | 1h |
| `/api/news/countries` | GET | Liste pays | 1h |
| `/api/news/tags` | GET | Liste tags | 1h |

**Exemple Requête:**
```typescript
// Get news feed
const response = await api.get('/api/news', {
  params: {
    page: 1,
    page_size: 20,
    country: 'SN',      // Sénégal
    tag: 'fintech',
  }
});
```

### 6. User & Settings

| Endpoint | Méthode | Usage Mobile | Auth |
|----------|---------|--------------|------|
| `/users/profile` | GET | Profil user | ✅ |
| `/users/profile/update` | POST | Modifier profil | ✅ |
| `/users/notifications` | GET | Préférences notif | ✅ |
| `/users/notifications/update` | POST | Modifier prefs | ✅ |
| `/users/notifications/messages` | GET | Inbox notifs | ✅ |
| `/users/notifications/read` | POST | Marquer lu | ✅ |
| `/users/security/change-password` | POST | Changer mdp | ✅ |
| `/users/entitlements` | GET | Droits/quotas | ✅ |

### 7. Billing

| Endpoint | Méthode | Usage Mobile | Auth |
|----------|---------|--------------|------|
| `/api/billing/me` | GET | Statut abo | ✅ |
| `/api/billing/checkout-session` | POST | Créer checkout | ✅ |
| `/api/billing/portal-session` | POST | Ouvrir portal | ✅ |

---

## REACT QUERY CONFIGURATION

### Query Client

```typescript
// src/lib/queryClient.ts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
      retry: 2,
      retryDelay: 1000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

### Query Keys

```typescript
// Namespace des query keys
const queryKeys = {
  // Assets
  topScored: (scope: string) => ['assets', 'top-scored', scope],
  assetDetail: (ticker: string) => ['assets', 'detail', ticker],
  assetChart: (ticker: string, period: string) => ['assets', 'chart', ticker, period],
  explorer: (filters: ExplorerFilters) => ['assets', 'explorer', filters],

  // Watchlist
  watchlist: (scope?: string) => ['watchlist', scope],
  watchlistCheck: (ticker: string) => ['watchlist', 'check', ticker],

  // Strategies
  strategyTemplates: (filters?: StrategyFilters) => ['strategies', 'templates', filters],
  strategyDetail: (slug: string) => ['strategies', 'detail', slug],
  userStrategies: () => ['strategies', 'user'],

  // Barbell
  barbellSuggest: (profile: string, scope: string) => ['barbell', 'suggest', profile, scope],
  barbellPortfolios: () => ['barbell', 'portfolios'],

  // News
  newsFeed: (filters: NewsFilters) => ['news', 'feed', filters],
  newsArticle: (slug: string) => ['news', 'article', slug],
  savedNews: () => ['news', 'saved'],

  // User
  userProfile: () => ['user', 'profile'],
  userNotifications: () => ['user', 'notifications'],
  userEntitlements: () => ['user', 'entitlements'],
  subscription: () => ['billing', 'subscription'],
};
```

### Exemple Hook

```typescript
// hooks/useTopScored.ts
export function useTopScored(scope: 'US_EU' | 'AFRICA' = 'US_EU') {
  return useQuery({
    queryKey: queryKeys.topScored(scope),
    queryFn: () => api.getTopScored({ limit: 10, market_scope: scope }),
    staleTime: 1000 * 60 * 5, // 5 min
  });
}

// hooks/useWatchlist.ts
export function useWatchlist() {
  const { session } = useAuthStore();

  return useQuery({
    queryKey: queryKeys.watchlist(),
    queryFn: () => api.getWatchlist(),
    enabled: !!session, // Only fetch if authenticated
    staleTime: 1000 * 60 * 2, // 2 min
  });
}

// hooks/useAddToWatchlist.ts
export function useAddToWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticker: string) => api.addToWatchlist(ticker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.watchlist() });
    },
  });
}
```

---

## GESTION DES ERREURS

### Types d'Erreurs

```typescript
// src/lib/api.ts
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public code?: string,
  ) {
    super(message);
  }
}

// Codes d'erreur courants
const ERROR_CODES = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  RATE_LIMITED: 429,
  SERVER_ERROR: 500,
};
```

### Gestion Centralisée

```typescript
// Intercepteur réponse
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    // Redirection login si 401
    if (response.status === 401) {
      useAuthStore.getState().signOut();
      router.replace('/login');
    }

    throw new APIError(
      response.status,
      error.detail || error.message || 'An error occurred',
      error.code,
    );
  }

  return response.json();
};
```

### Affichage Utilisateur

```typescript
// Composant Toast/Alert
const showErrorToast = (error: APIError) => {
  const messages: Record<number, string> = {
    401: 'Session expirée. Veuillez vous reconnecter.',
    403: 'Accès non autorisé.',
    404: 'Ressource non trouvée.',
    429: 'Trop de requêtes. Réessayez dans quelques instants.',
    500: 'Erreur serveur. Réessayez plus tard.',
  };

  Alert.alert(
    'Erreur',
    messages[error.status] || error.message,
    [{ text: 'OK' }]
  );
};
```

---

## PAGINATION

### Pattern Standard

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// Hook infinite scroll
export function useExplorerInfinite(filters: ExplorerFilters) {
  return useInfiniteQuery({
    queryKey: queryKeys.explorer(filters),
    queryFn: ({ pageParam = 1 }) =>
      api.getExplorer({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.page + 1 : undefined,
    staleTime: 1000 * 60 * 2,
  });
}
```

### Utilisation FlatList

```typescript
<FlatList
  data={data?.pages.flatMap(p => p.items) ?? []}
  renderItem={({ item }) => <AssetCard asset={item} />}
  keyExtractor={(item) => item.asset_id}
  onEndReached={() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }}
  onEndReachedThreshold={0.5}
  ListFooterComponent={
    isFetchingNextPage ? <LoadingSpinner size="small" /> : null
  }
/>
```

---

## CACHE OFFLINE (FUTUR)

### AsyncStorage Schema

```typescript
// Cache keys
const CACHE_KEYS = {
  TOP_SCORED: 'cache:top_scored',
  WATCHLIST: 'cache:watchlist',
  USER_PROFILE: 'cache:user_profile',
  STRATEGY_TEMPLATES: 'cache:strategy_templates',
};

// Structure cache
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // milliseconds
}

// Helpers
const getCache = async <T>(key: string): Promise<T | null> => {
  const raw = await AsyncStorage.getItem(key);
  if (!raw) return null;

  const entry: CacheEntry<T> = JSON.parse(raw);
  if (Date.now() - entry.timestamp > entry.ttl) {
    await AsyncStorage.removeItem(key);
    return null;
  }

  return entry.data;
};

const setCache = async <T>(key: string, data: T, ttl: number) => {
  const entry: CacheEntry<T> = {
    data,
    timestamp: Date.now(),
    ttl,
  };
  await AsyncStorage.setItem(key, JSON.stringify(entry));
};
```

---

## OPTIMISATIONS

### 1. Request Debouncing

```typescript
// Recherche avec debounce
const [searchQuery, setSearchQuery] = useState('');
const debouncedQuery = useDebounce(searchQuery, 300);

const { data } = useQuery({
  queryKey: ['search', debouncedQuery],
  queryFn: () => api.searchAssets(debouncedQuery),
  enabled: debouncedQuery.length >= 2,
});
```

### 2. Prefetching

```typescript
// Prefetch asset detail on hover/focus
const prefetchAssetDetail = async (ticker: string) => {
  await queryClient.prefetchQuery({
    queryKey: queryKeys.assetDetail(ticker),
    queryFn: () => api.getAssetDetails(ticker),
    staleTime: 1000 * 60 * 5,
  });
};
```

### 3. Optimistic Updates

```typescript
// Optimistic add to watchlist
const addToWatchlist = useMutation({
  mutationFn: (ticker: string) => api.addToWatchlist(ticker),
  onMutate: async (ticker) => {
    await queryClient.cancelQueries({ queryKey: queryKeys.watchlist() });

    const previous = queryClient.getQueryData(queryKeys.watchlist());

    // Optimistic update
    queryClient.setQueryData(queryKeys.watchlist(), (old: Asset[]) => [
      ...old,
      { ticker, added_at: new Date().toISOString() },
    ]);

    return { previous };
  },
  onError: (err, ticker, context) => {
    // Rollback on error
    queryClient.setQueryData(queryKeys.watchlist(), context?.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.watchlist() });
  },
});
```

---

## VARIABLES D'ENVIRONNEMENT

### .env Configuration

```bash
# .env.local (développement)
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=xxx

# .env.production
EXPO_PUBLIC_API_URL=https://api.marketgps.online
EXPO_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=xxx
```

### Accès dans le code

```typescript
import Constants from 'expo-constants';

const API_URL = process.env.EXPO_PUBLIC_API_URL;
const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;
```

---

**Fin du document Data Wiring**
