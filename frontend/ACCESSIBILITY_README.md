# Accessibilité MarketGPS Frontend

Bienvenue! Ce document explique comment utiliser et maintenir les améliorations d'accessibilité du projet MarketGPS.

## Démarrage Rapide

### Je veux...

#### Créer un formulaire accessible
→ Voir `/EXAMPLES.md` - Section "Créer un formulaire de connexion"
→ Consulter `/components/ui/input.tsx`

#### Utiliser une modale accessible
→ Voir `/EXAMPLES.md` - Section "Créer une Modal Accessible"
→ Consulter `/components/ui/modal.tsx`

#### Créer un bouton sans texte
→ Voir `/EXAMPLES.md` - Section "Créer une Toolbar avec Boutons"
→ Consulter `/components/ui/button.tsx`

#### Tester l'accessibilité
→ Lire `/TESTING_ACCESSIBILITY.md`
→ Suivre les tests manuels et automatisés

#### Comprendre les améliorations
→ Lire `/ACCESSIBILITY_IMPROVEMENTS.md`
→ Consulter `/IMPLEMENTATION_NOTES.md`

## Documents de Référence

### 📖 Guides Principaux

| Document | Contenu | Pour Qui |
|----------|---------|----------|
| `ACCESSIBILITY_GUIDE.md` | Guide complet avec tous les détails | Tous les développeurs |
| `IMPLEMENTATION_NOTES.md` | Notes détaillées de chaque changement | Développeurs qui modifient |
| `TESTING_ACCESSIBILITY.md` | Comment tester l'accessibilité | QA et développeurs |
| `EXAMPLES.md` | 8 exemples pratiques avec code | Tous (particulièrement utile) |
| `ACCESSIBILITY_IMPROVEMENTS.md` | Résumé des améliorations | Vue d'ensemble |

## Fichiers Modifiés

### Composants Créés
- `components/ErrorBoundary.tsx` - Capture les erreurs non gérées
- `components/ui/modal.tsx` - Modale accessible réutilisable

### Composants Améliorés
- `components/ui/input.tsx` - Support ARIA complet
- `components/ui/button.tsx` - Support iconOnly et aria-label
- `components/feedback/FeedbackModal.tsx` - ARIA complet
- `components/feedback/FeedbackButton.tsx` - Accessibilité clavier
- `app/signup/page.tsx` - IDs et labels associés
- `app/login/page.tsx` - IDs et labels associés
- `app/contact/page.tsx` - Accessibilité complète
- `app/providers.tsx` - Intégration ErrorBoundary

## Bonnes Pratiques

### Pour Tous les Inputs
```tsx
<label htmlFor="input-id">Label</label>
<Input id="input-id" {...props} />
```

### Pour les Boutons Sans Texte
```tsx
<Button
  iconOnly
  ariaLabel="Description du bouton"
  size="icon"
>
  <Icon />
</Button>
```

### Pour les Messages d'Erreur
```tsx
<div role="alert" aria-live="assertive">
  Message d'erreur
</div>
```

### Pour les Modales
```tsx
import { Modal } from '@/components/ui/modal';

<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Titre"
>
  Contenu
</Modal>
```

## Checklist Avant Merge

- [ ] Tab navigation fonctionne
- [ ] Escape ferme les modales
- [ ] Tous les inputs ont des labels
- [ ] Boutons icon-only ont aria-label
- [ ] Icônes décoratives ont aria-hidden="true"
- [ ] Focus visible partout
- [ ] Pas d'erreurs console
- [ ] Tests au clavier (Tab, Enter, Escape)

## Tests Recommandés

### Test Rapide (5 min)
1. Appuyer sur Tab plusieurs fois
2. Vérifier que tous les éléments interactifs peuvent être atteints
3. Appuyer sur Escape sur une modale
4. Vérifier que la modale se ferme

### Test Complet (30 min)
1. Suivre `/TESTING_ACCESSIBILITY.md`
2. Tester au clavier (Tab, Shift+Tab, Enter, Escape)
3. Tester avec Lighthouse (Chrome DevTools)
4. Tester avec axe DevTools

### Test Approfondi (1h)
1. Tester avec NVDA (lecteur d'écran)
2. Vérifier contraste (WebAIM)
3. Tester zoom à 200%
4. Vérifier sur mobile

## Outils

### Gratuit
- **Chrome DevTools**: Lighthouse audit (F12)
- **axe DevTools**: Chrome/Firefox extension
- **NVDA**: Lecteur d'écran gratuit (Windows)
- **WebAIM**: Vérifieur de contraste (en ligne)

### À Installer
```bash
npm install --save-dev jest-axe @testing-library/react
```

## FAQ

### Q: Comment créer un bouton sans texte visible?
**R**: Utiliser le prop `iconOnly={true}` et `ariaLabel="description"`:
```tsx
<Button iconOnly ariaLabel="Supprimer" size="icon">
  <Trash2 className="w-4 h-4" />
</Button>
```

### Q: Comment associer un label à un input?
**R**: Utiliser `htmlFor` et `id`:
```tsx
<label htmlFor="email">Email</label>
<Input id="email" type="email" />
```

### Q: Comment afficher une modale?
**R**: Importer et utiliser le composant Modal:
```tsx
<Modal isOpen={open} onClose={handleClose} title="Titre">
  Contenu
</Modal>
```

### Q: Comment afficher une erreur accessible?
**R**: Utiliser `role="alert"` et `aria-live="assertive"`:
```tsx
<div role="alert" aria-live="assertive">
  Erreur du formulaire
</div>
```

### Q: Comment tester avec un lecteur d'écran?
**R**: Lire `/TESTING_ACCESSIBILITY.md` section "Tests au Lecteur d'Écran"

### Q: Lighthouse dit 85. Est-ce acceptable?
**R**: 85+ est bon, mais viser 90+. Consulter les recommandations de Lighthouse.

### Q: Mon bouton n'a pas de focus visible
**R**: Ajouter `focus:ring-2 focus:ring-accent-dim` au Button.

### Q: L'ErrorBoundary ne capture pas mon erreur
**R**: ErrorBoundary capture les erreurs de render. Pour d'autres erreurs, utiliser try/catch.

## Ressources

### Documentation Créée
- `/ACCESSIBILITY_GUIDE.md` - Guide détaillé
- `/IMPLEMENTATION_NOTES.md` - Notes techniques
- `/TESTING_ACCESSIBILITY.md` - Tests et procédures
- `/EXAMPLES.md` - Code prêt à utiliser

### Ressources Externes
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Web Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [The A11y Project](https://www.a11yproject.com/)

### Outils
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [NVDA Screen Reader](https://www.nvaccess.org/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

## Support

Vous avez une question?

1. **Cherchez d'abord dans** `/EXAMPLES.md` pour un code similaire
2. **Consultez** `/ACCESSIBILITY_GUIDE.md` pour les détails
3. **Testez avec** `/TESTING_ACCESSIBILITY.md`
4. **Créez une issue** avec le label `accessibility`

## Améliorations à Venir

- [ ] FocusTrap pour les modales (court terme)
- [ ] Tests automatisés jest-axe (court terme)
- [ ] Support RTL complet (moyen terme)
- [ ] Mode contraste élevé (moyen terme)
- [ ] Certification WCAG AAA (long terme)

## Statistiques

### Fichiers Créés
- 2 composants accessibles
- 5 guides de documentation
- 8 exemples pratiques

### Fichiers Modifiés
- 8 fichiers source
- 50+ lignes d'améliorations ARIA
- Tous les formulaires améliorés

### Standards
- ✅ WCAG 2.1 Level AA
- ✅ ARIA Authoring Practices
- ✅ React Accessibility

---

**Version**: 1.0
**Date**: 2026-02-02
**Statut**: ✅ Prêt à utiliser

**Questions?** Consultez les guides ou créez une issue!
