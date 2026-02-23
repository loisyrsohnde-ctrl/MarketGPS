# Quick Actions - Guide de Troubleshooting

## 🔧 Problèmes Courants et Solutions

### 1. Composants ne s'affichent pas

**Symptôme**: QuickActions n'apparaît pas sur la page

**Causes possibles**:
1. Import manquant
2. Asset undefined
3. Composant masqué par CSS

**Solutions**:
```tsx
// ❌ Mauvais
import QuickActions from '@/components/asset/QuickActions';

// ✅ Correct
import { QuickActions } from '@/components/asset/QuickActions';

// ❌ Mauvais - asset peut être undefined
<QuickActions asset={asset} />

// ✅ Correct
{asset && <QuickActions asset={asset} />}
```

---

### 2. Raccourcis clavier ne fonctionnent pas

**Symptôme**: W, A, C, I ne déclenchent pas les actions

**Causes possibles**:
1. useKeyboardShortcuts non utilisé
2. Input field actif (intentionnel, par design)
3. Console errors non visibles

**Solutions**:
```tsx
// Vérifier que le hook est appelé
useKeyboardShortcuts({
  toggleWatchlist: () => console.log('W pressed'),
  openAlert: () => console.log('A pressed'),
  openComparator: () => console.log('C pressed'),
  openAIChat: () => console.log('I pressed'),
});

// Vérifier dans la console
// Appuyer sur W et voir si "W pressed" s'affiche
```

---

### 3. Watchlist toggle ne marche pas

**Symptôme**: Cliquer sur watchlist ne fait rien

**Causes possibles**:
1. API `/api/watchlist` non disponible
2. Pas de userId
3. React Query misconfigured

**Solutions**:
```tsx
// Vérifier l'API dans le navigateur
fetch('/api/watchlist/check/AAPL?user_id=default')
  .then(r => r.json())
  .then(d => console.log(d))

// Vérifier le userId
console.log('User ID:', userId)

// Vérifier React Query DevTools
// npm install @tanstack/react-query-devtools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
<ReactQueryDevtools />
```

---

### 4. Modal ne ferme pas

**Symptôme**: Modal reste ouvert après validation

**Causes possibles**:
1. onCreateAlert ne ferme pas le modal
2. setTimeout trop long
3. Erreur dans callback

**Solutions**:
```tsx
// ❌ Mauvais - modal n'est jamais fermé
<CreateAlertModal
  onCreateAlert={async (config) => {
    console.log('Alert:', config)
    // Oubli de fermer
  }}
/>

// ✅ Correct
<CreateAlertModal
  onCreateAlert={async (config) => {
    try {
      // API call
      await api.createAlert(config)
      // Fermer le modal
      setIsAlertModalOpen(false)
    } catch (err) {
      console.error(err)
    }
  }}
/>

// Ou laisser le modal se fermer automatiquement
// (voir le setTimeout dans CreateAlertModal.tsx ligne ~150)
```

---

### 5. Toast notifications ne s'affichent pas

**Symptôme**: Aucune notification après action

**Causes possibles**:
1. `onActionComplete` non appelé
2. Toast state pas mis à jour
3. Animations désactivées en CSS

**Solutions**:
```tsx
// Vérifier que onActionComplete est appelé
<QuickActions
  asset={asset}
  onActionComplete={(action, success) => {
    console.log('Action:', action, 'Success:', success)
  }}
/>

// Vérifier que le state est mis à jour
const [toasts, setToasts] = useState<ToastMessage[]>([])
console.log('Toasts:', toasts)
```

---

### 6. Comparateur affiche asset dupliqué

**Symptôme**: Impossible de comparer deux fois le même asset

**Causes possibles**:
1. Check `!selectedAssets.some(...)` ne fonctionne pas
2. Objet ticker différent

**Solutions**:
```tsx
// Vérifier les tickers
selectedAssets.forEach(a => console.log(a.ticker))

// S'assurer que les assets ont des tickers uniques
const isAlreadySelected = selectedAssets.some(
  a => a.ticker === newAsset.ticker
)

if (!isAlreadySelected) {
  addAsset(newAsset)
}
```

---

### 7. Bundle size trop gros

**Symptôme**: Build prend longtemps, ou bundle trop lourd

**Causes possibles**:
1. Modals non lazy-loaded
2. Icons non optimisées
3. Framer Motion entier importé

**Solutions**:
```tsx
// Code splitting pour modals
const CreateAlertModal = dynamic(
  () => import('@/components/alerts/CreateAlertModal'),
  { loading: () => <div>Chargement...</div> }
)

// Vérifier la taille du bundle
npm run build -- --analyze
```

---

### 8. Animations non fluides

**Symptôme**: Animations saccadées ou lentes

**Causes possibles**:
1. Trop d'animations simultanées
2. Spring config sub-optimal
3. Rendu inefficace

**Solutions**:
```tsx
// Réduire le nombre d'animations
// Utiliser will-change en CSS
.quick-action { will-change: transform; }

// Vérifier les spring damping values
motion.div initial={{ ... }}
  animate={{ ... }}
  transition={{
    type: 'spring',
    damping: 25, // Augmenter pour moins de bounces
    stiffness: 300 // Réduire pour plus lent
  }}
/>
```

---

### 9. API d'alerte non implémentée

**Symptôme**: `POST /api/alerts/rules` retourne 404

**Cause**: Endpoints non créés

**Solution**:
```bash
# Implémenter les endpoints (backend)
POST   /api/alerts/rules
GET    /api/alerts/rules
DELETE /api/alerts/rules/{id}
...

# Test rapide
curl -X POST http://localhost:3000/api/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{"asset_ticker":"AAPL","type":"price_threshold","condition":">","threshold_value":150,"channels":["in_app"]}'
```

---

### 10. Erreurs TypeScript

**Symptôme**: `TS2339: Property 'X' does not exist`

**Solutions**:
```tsx
// ❌ Mauvais - Asset ne peut pas avoir de propriété custom
asset.customProperty = 'value'

// ✅ Correct - Créer une interface étendue
interface MyAsset extends Asset {
  customProperty?: string
}

// Ou passer les données séparément
<QuickActions asset={asset} customData={customData} />
```

---

## 🐛 Debug Techniques

### 1. Vérifier les Renders

```tsx
// Ajouter un console.log pour tracker les renders
export function QuickActions(props: QuickActionsProps) {
  console.log('QuickActions rendered', props.asset.ticker)
  // ...
}
```

### 2. Inspecter les States

```tsx
// Browser DevTools
// React tab > Components > Find QuickActions
// Voir l'état en temps réel
```

### 3. Network Debugging

```tsx
// Network tab
// Voir les requêtes API
// POST /api/watchlist
// GET /api/watchlist/check/AAPL

// Pour vérifier les erreurs:
// Ouvrir Console et regarder les messages d'erreur
```

### 4. Performance Profiling

```tsx
// Chrome DevTools > Performance
// Enregistrer une session
// Voir où le temps est dépensé
```

### 5. Accessibility Testing

```tsx
// Vérifier avec axe DevTools
// https://www.deque.com/axe/devtools/

// Ou dans le code
// Vérifier ARIA labels avec:
console.log(document.querySelectorAll('[aria-label]'))
```

---

## 📋 Checklist de Debug

- [ ] Vérifier les imports
- [ ] Vérifier les typos dans les noms
- [ ] Ouvrir la console et vérifier les erreurs
- [ ] Vérifier le network tab
- [ ] Vérifier les states avec React DevTools
- [ ] Vérifier que les API endpoints existent
- [ ] Vérifier les permissions/auth
- [ ] Vérifier les CSS classes
- [ ] Vérifier les animations avec timeline
- [ ] Tester sur mobile et desktop

---

## 🚨 Erreurs Spécifiques

### `Uncaught SyntaxError: Unexpected token '<'`
**Cause**: Importer un composant TSX comme du JS
**Fix**: Vérifier les extensions et les imports

### `Cannot read property 'asset_id' of undefined`
**Cause**: Asset est undefined
**Fix**: Ajouter un guard: `{asset && <QuickActions ... />}`

### `Too many re-renders`
**Cause**: État mis à jour dans le render
**Fix**: Utiliser useEffect pour les side effects

### `API returned 401 Unauthorized`
**Cause**: Token d'auth manquant ou expiré
**Fix**: Vérifier l'auth et les headers

### `Modal backdrop appears but content is empty`
**Cause**: Children non passés correctement
**Fix**: Vérifier que le contenu du modal est passé en prop

---

## 📞 Quand Demander de l'Aide

Si le problème n'est pas dans ce guide:

1. **Vérifier la doc complète**: QUICK_ACTIONS_IMPLEMENTATION.md
2. **Chercher des exemples similaires**: QUICK_ACTIONS_EXAMPLES.md
3. **Regarder les tests**: QuickActions.spec.tsx
4. **Chercher dans le code**: Lire les commentaires JSDoc
5. **Demander au team**: Avec screenshot + error message

---

## 🔍 Cas Limites à Tester

1. **Asset sans prix**: `last_price: null`
2. **Asset sans nom**: `name: ''`
3. **Très long ticker**: `ticker: 'VERYLONGTICKERNAME'`
4. **Très long nom**: `name: 'This is an extremely long asset name that might break the layout'`
5. **Nombres très petits**: `last_price: 0.0001` (crypto)
6. **Nombres très grands**: `last_price: 999999.99`
7. **Watchlist 1000+ items**: Performance test
8. **Offline (réseau coupé)**: Gestion d'erreur
9. **Slow 3G**: Timeout management
10. **Mobile portrait**: Responsive layout

---

## ✅ Vérification Avant Production

```bash
# 1. Tests
npm run test

# 2. Type checking
npm run type-check

# 3. Linting
npm run lint

# 4. Build
npm run build

# 5. Build size
npm run build -- --analyze

# 6. Performance lighthouse
npm run lighthouse

# 7. Manual testing checklist
- [ ] W key toggle watchlist
- [ ] A key open alert
- [ ] C key open comparator
- [ ] I key open AI
- [ ] Copy works
- [ ] Share works
- [ ] Toast animations smooth
- [ ] Modal closes on escape
- [ ] Modal closes on backdrop
- [ ] Responsive on mobile
- [ ] Accessible with keyboard
- [ ] Accessible with screen reader
```

---

**Dernière mise à jour**: 2024-02-03
**Version**: 1.0.0
