# Audit Mobile Blockers

**Date**: 2025-01-27  
**Status**: En cours d'investigation

---

## Résumé

Le mobile n'affiche pas de contenu. Cette analyse identifie les causes potentielles.

---

## 1. Configuration API

### Variables d'environnement (mobile/.env)

```bash
EXPO_PUBLIC_API_URL=https://api.marketgps.online
EXPO_PUBLIC_SUPABASE_URL=https://avecmzmcfliaeuxnwimu.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJ... (présent)
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY= (VIDE!)
```

**Status**: ✅ API_URL correcte, ⚠️ Stripe key vide

### Test des endpoints

| Endpoint | Status | Response |
|----------|--------|----------|
| `/api/assets/top-scored?scope=US_EU&limit=10` | ✅ 200 | 10 assets retournés |
| `/api/metrics/counts` | ✅ 200 | `{"US_EU":66080,"AFRICA":664}` |
| `/api/metrics/asset-type-counts` | ✅ 200 | Counts par type |
| `/users/entitlements` | ✅ 401 | Requires auth |

**Conclusion**: L'API backend fonctionne correctement.

---

## 2. Appels API Mobile

### Dashboard (`app/(tabs)/index.tsx`)

```typescript
// Ligne 30-33
const { data: topScored, isLoading, refetch, isRefetching } = useQuery({
  queryKey: ['topScored', selectedScope],
  queryFn: () => api.getTopScored({ limit: 10, market_scope: selectedScope }),
});

// Ligne 36-39
const { data: counts } = useQuery({
  queryKey: ['scopeCounts'],
  queryFn: () => api.getScopeCounts(),
});
```

### API Client (`src/lib/api.ts`)

```typescript
// Ligne 191-205
async getTopScored(params): Promise<PaginatedResponse<Asset>> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.market_scope) searchParams.append('market_scope', params.market_scope);
  return this.fetch(`/api/assets/top-scored${query ? `?${query}` : ''}`);
}

// Ligne 270-272
async getScopeCounts(): Promise<{ US_EU: number; AFRICA: number }> {
  return this.fetch('/api/metrics/counts');
}
```

**Status**: ✅ Les méthodes existent et semblent correctes.

---

## 3. Causes Potentielles Identifiées

### Cause #1: Erreur silencieuse dans getAccessToken()

Le fetch inclut un token d'auth :
```typescript
const authToken = token ?? await getAccessToken();
```

Si `getAccessToken()` échoue silencieusement, les requêtes pourraient échouer.

**Investigation requise**: Vérifier `getAccessToken()` dans `src/lib/supabase.ts`

### Cause #2: React Query non initialisé correctement

Si le `QueryClientProvider` n'est pas bien configuré ou si les queries ne se déclenchent pas.

**Investigation requise**: Vérifier `app/_layout.tsx`

### Cause #3: Erreur de rendu conditionnel

```typescript
{isLoading ? (
  <LoadingSpinner message="Chargement..." />
) : (
  <View>
    {topScored?.data?.slice(0, 5).map((asset, index) => (
      <AssetCard key={asset.asset_id || asset.symbol} asset={asset} />
    ))}
  </View>
)}
```

Si `topScored?.data` est undefined ou vide, rien ne s'affiche (sans message d'erreur).

### Cause #4: CORS ou Network Permissions

React Native nécessite des configurations spécifiques pour les requêtes réseau.

**Investigation requise**: 
- Vérifier `Info.plist` pour iOS (NSAppTransportSecurity)
- Vérifier les permissions Android

---

## 4. Actions Correctives Proposées

### Fix #1: Ajouter des logs de débogage

```typescript
const { data: topScored, isLoading, error } = useQuery({
  queryKey: ['topScored', selectedScope],
  queryFn: async () => {
    console.log('[Dashboard] Fetching top scored...');
    const result = await api.getTopScored({ limit: 10, market_scope: selectedScope });
    console.log('[Dashboard] Got result:', result);
    return result;
  },
});

// Afficher l'erreur si présente
if (error) {
  console.error('[Dashboard] Query error:', error);
}
```

### Fix #2: Ajouter un état d'erreur visible

```typescript
{error && (
  <View style={styles.errorContainer}>
    <Text style={styles.errorText}>Erreur: {error.message}</Text>
    <Button title="Réessayer" onPress={() => refetch()} />
  </View>
)}
```

### Fix #3: Ajouter un état vide

```typescript
{!isLoading && (!topScored?.data || topScored.data.length === 0) && (
  <View style={styles.emptyContainer}>
    <Text style={styles.emptyText}>Aucun actif disponible</Text>
  </View>
)}
```

---

## 5. Fichiers à Vérifier

| Fichier | Vérification |
|---------|--------------|
| `mobile/src/lib/supabase.ts` | getAccessToken() implementation |
| `mobile/app/_layout.tsx` | QueryClientProvider setup |
| `mobile/app/(tabs)/index.tsx` | Error handling |
| `mobile/ios/*/Info.plist` | NSAppTransportSecurity |

---

## 6. Correctifs Appliqués

### ✅ Fix #1: Debugging et logs ajoutés

Dashboard maintenant inclut des logs de débogage pour tracer les appels API.

### ✅ Fix #2: États d'erreur explicites

Ajout d'un affichage d'erreur avec bouton "Réessayer" quand une query échoue.

### ✅ Fix #3: État vide explicite

Ajout d'un message quand aucun actif n'est disponible.

### ✅ Fix #4: Animation GPS Loading

Nouveau composant `GpsLoading` avec animation de localisation premium.

---

## 7. Tests Recommandés

1. Lancer l'app mobile : `npx expo start --clear`
2. Vérifier les logs Metro pour les messages `[Dashboard]`
3. Vérifier que les actifs s'affichent
4. Tester l'animation de chargement
5. Tester le refresh (pull-to-refresh)

---

## 8. Corrections News (Session 2)

### Priorité Pays Francophones

Les pays francophones sont maintenant priorisés dans l'affichage des actualités :

**Ordre de priorité** :
1. Cameroun (CM)
2. Côte d'Ivoire (CI)
3. Sénégal (SN)
4. Bénin (BJ)
5. Togo (TG)
6. Gabon (GA)
7. Congo (CG)
8. Mali (ML)
9. Burkina Faso (BF)
10. Niger (NE)
11. Tchad (TD)
12. Guinée (GN)
13. Rwanda (RW)
14. RD Congo (CD)

### Zones Économiques

Nouveaux onglets de filtrage par zone :
- **CEMAC** : CM, GA, CG, TD, CF, GQ
- **UEMOA** : SN, CI, BJ, TG, ML, BF, NE, GN
- **Maghreb** : MA, DZ, TN, LY
- **EAC** : KE, TZ, UG, RW, ET
- **SADC** : ZA, AO, MZ, ZW, NA, BW

### Nouvelles Sources Ajoutées

- Abidjan.net Économie (CI)
- Fraternité Matin (CI)
- CIO Mag Afrique (PAN)
- Le Matinal Bénin (BJ)
- La Nation Bénin (BJ)
- Dakar Actu Économie (SN)

### Fichiers Modifiés

| Fichier | Modification |
|---------|-------------|
| `mobile/app/(tabs)/news.tsx` | Zones économiques + pays francophones prioritaires |
| `storage/sqlite_store.py` | Tri avec priorité francophone dans get_news_articles |
| `pipeline/news/sources_registry.json` | 6 nouvelles sources francophones |

---

*Rapport mis à jour: 2025-01-27*
