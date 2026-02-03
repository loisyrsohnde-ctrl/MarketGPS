# Guide d'Accessibilité MarketGPS

Ce guide documente les améliorations d'accessibilité et de robustesse apportées au frontend MarketGPS.

## Partie 1: Error Boundary Global

### Fichier: `components/ErrorBoundary.tsx`

Un Error Boundary a été créé pour capturer les erreurs à travers toute l'application.

**Caractéristiques:**
- Capture toutes les erreurs non gérées dans l'arborescence des composants
- Affiche une UI cohérente en cas d'erreur
- Fournit des options de récupération (Réessayer, Retour à l'accueil)
- Stocke les erreurs pour le débogage en développement
- Intégration prête pour les services de suivi d'erreurs (Sentry, LogRocket)

**Utilisation:**
```tsx
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

### Intégration dans `app/providers.tsx`

L'ErrorBoundary enveloppe tous les providers pour une protection maximale.

## Partie 2: Accessibilité ARIA

### Composants Améliorés

#### 1. **Input Component** (`components/ui/input.tsx`)

**Attributs ARIA ajoutés:**
- `aria-label`: Pour les inputs sans label visible
- `aria-describedby`: Relie les inputs aux messages de validation
- `aria-invalid`: Indique l'état d'erreur
- `aria-required`: Indique les champs obligatoires (pour les textateas)
- Génération automatique d'IDs uniques

**Messages d'erreur:**
```tsx
<Input
  id="email"
  type="email"
  error={hasError}
  errorMessage="Email invalide"
  ariaLabel="Adresse email"
  ariaDescribedBy="email-help"
/>
```

#### 2. **SearchInput Component** (`components/ui/input.tsx`)

**Améliorations:**
- `type="search"` pour une meilleure sémantique
- Bouton "Effacer" avec `aria-label`
- Icône marquée avec `aria-hidden="true"`
- Label accessible

#### 3. **Textarea Component** (`components/ui/input.tsx`)

**Attributs:**
- Support complet des attributs ARIA
- Messages d'erreur intégrés
- Gestion d'ID automatique

#### 4. **Button Component** (`components/ui/button.tsx`)

**Améliorations:**
- `aria-label` pour les boutons avec seulement des icônes (`iconOnly={true}`)
- `aria-busy={loading}` pour indiquer l'état de chargement
- Icônes marquées avec `aria-hidden="true"`
- Focus visible avec ring
- Support des attributs natifs HTML

**Utilisation pour boutons icon-only:**
```tsx
<Button
  size="icon"
  iconOnly
  ariaLabel="Supprimer l'élément"
>
  <Trash className="w-4 h-4" />
</Button>
```

#### 5. **Modal Component** (`components/ui/modal.tsx`)

**Attributs d'accessibilité:**
- `role="dialog"`
- `aria-modal="true"`
- `aria-labelledby` pour le titre
- Gestion de l'échappement (Escape key)
- Focus automatique
- Gestion du scroll du body

**Utilisation:**
```tsx
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Titre de la modale"
  size="lg"
>
  {/* Contenu */}
</Modal>
```

### Formulaires Améliorés

#### Signup Page (`app/signup/page.tsx`)

**Changements:**
- IDs explicites pour tous les inputs
- Labels associés via `htmlFor`
- Messages d'erreur avec `aria-describedBy`
- Message de validation password hint
- Alertes avec `role="alert"` et `aria-live="assertive"`
- Icônes marquées avec `aria-hidden="true"`

#### Login Page (`app/login/page.tsx`)

**Changements:**
- IDs explicites pour email et password
- Links avec focus visible amélioré
- Alertes d'erreur accessibles
- Attributs ARIA complets

#### FeedbackModal (`components/feedback/FeedbackModal.tsx`)

**Améliorations d'accessibilité:**

1. **Structure modale:**
   - `role="dialog"` et `aria-modal="true"`
   - `aria-labelledby` pointant vers le titre
   - Fermeture avec Escape key possible

2. **Champs de formulaire:**
   - `fieldset` et `legend` pour groupes de sélection
   - `aria-pressed` pour les boutons de type (General, Bug, etc.)
   - `aria-required="true"` pour le message obligatoire
   - `id` pour la textarea du message

3. **Sélection d'étoiles:**
   - Boutons avec `aria-pressed`
   - `aria-label` descriptif ("3 étoiles", etc.)
   - Icônes avec `aria-hidden="true"`

4. **Messages d'erreur:**
   - `role="alert"` et `aria-live="assertive"`
   - Affichage immédiat et persistant

5. **Bouton de fermeture:**
   - `aria-label="Fermer le formulaire de feedback"`
   - Focus ring visible

## Bonnes Pratiques Implémentées

### 1. Labels et Inputs
```tsx
<label htmlFor="element-id">
  Label Text
</label>
<Input id="element-id" {...props} />
```

### 2. Messages d'Erreur
```tsx
<Input
  id="field-id"
  error={hasError}
  errorMessage="Message d'erreur explicite"
  ariaDescribedBy="field-id-error"
/>
```

### 3. Icônes
```tsx
{/* Icône décorative */}
<Icon aria-hidden="true" />

{/* Icône avec sens */}
<Icon aria-label="Supprimer" />
```

### 4. Alertes
```tsx
<div role="alert" aria-live="assertive">
  Message d'erreur ou succès
</div>
```

### 5. Buttons Icon-Only
```tsx
<Button
  iconOnly
  ariaLabel="Action description"
  size="icon"
>
  <Icon />
</Button>
```

## Checklist de Vérification d'Accessibilité

Lors de l'ajout de nouveaux composants:

- [ ] Tous les inputs ont des labels associés
- [ ] Les boutons icon-only ont `aria-label`
- [ ] Les messages d'erreur ont `role="alert"`
- [ ] Les icônes décoratives ont `aria-hidden="true"`
- [ ] Les modales ont `role="dialog"` et `aria-modal="true"`
- [ ] Les fieldsets utilisent `<legend>` pour les groupes
- [ ] Focus visible sur tous les éléments interactifs
- [ ] Contraste de couleur respectant WCAG AA (4.5:1 pour texte)
- [ ] Ordre de tabulation logique
- [ ] Contenu texte alternatif pour images
- [ ] Support du clavier complet (Enter, Escape, etc.)

## Tests d'Accessibilité

### Outils recommandés:
- **Chrome DevTools**: Lighthouse Accessibility audit
- **axe DevTools**: Extensión Firefox/Chrome
- **NVDA/JAWS**: Lecteurs d'écran pour test
- **Keyboard Navigation**: Test complet du clavier

### Points de test clés:
1. Navigation au clavier (Tab, Shift+Tab, Enter, Escape)
2. Lecteur d'écran (NVDA, JAWS, VoiceOver)
3. Contraste des couleurs
4. Zoom à 200%
5. Redimensionnement du texte

## Ressources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [React Accessibility](https://reactjs.org/docs/accessibility.html)
- [Web Accessibility by Google](https://www.udacity.com/course/web-accessibility--ud891)

## Améliorations Futures

1. **Focus Management:**
   - Implémenter FocusTrap pour modales
   - Gestion de focus lors de navigation dynamique

2. **Tests Automatisés:**
   - Intégrer jest-axe pour tests d'accessibilité
   - CI/CD avec accessibility audit

3. **Internationalisation (i18n):**
   - Support complet des langues RTL
   - Messages d'erreur localisés

4. **Contraste et Couleurs:**
   - Mode contraste élevé
   - Respecter les préférences système (prefers-color-scheme)

5. **Skip Links:**
   - Ajouter un skip link pour sauter à contenu principal
   - Navigation au clavier optimisée

## Support et Questions

Pour des questions sur l'accessibilité ou pour signaler des problèmes:
- Créez une issue avec le label `accessibility`
- Consultez la documentation WCAG
- Testez avec plusieurs outils d'accessibilité
