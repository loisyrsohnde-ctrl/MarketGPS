# Guide de Test d'Accessibilité

Ce guide fourni les procédures pour tester l'accessibilité de MarketGPS.

## 1. Tests Manuels - Navigation au Clavier

### 1.1 Tab Navigation
**Procédure**:
1. Ouvrir la page
2. Appuyer sur `Tab` plusieurs fois
3. Vérifier que:
   - L'ordre de focus est logique (haut en bas, gauche à droite)
   - Tous les éléments interactifs peuvent être atteints
   - Pas de focus piégé
   - Un indicateur de focus visible sur chaque élément

**Éléments à tester**:
- Inputs de formulaire
- Boutons
- Links
- Select dropdowns
- Checkboxes/Radios

### 1.2 Shift+Tab Navigation (En Arrière)
**Procédure**:
1. Appuyer sur `Shift+Tab` depuis le dernier élément
2. Vérifier que la navigation inverse fonctionne correctement
3. Focus devrait revenir à travers tous les éléments

### 1.3 Touche Enter
**Procédure**:
1. Naviguer à un bouton avec `Tab`
2. Appuyer sur `Enter`
3. Vérifier que l'action se déclenche (form submit, dialog open, etc.)

### 1.4 Touche Escape
**Procédure**:
1. Ouvrir une modale/dialog
2. Appuyer sur `Escape`
3. Vérifier que la modale se ferme

### 1.5 Touche Space
**Procédure**:
1. Naviguer à un bouton avec `Tab`
2. Appuyer sur `Space`
3. Vérifier que l'action se déclenche

## 2. Tests au Lecteur d'Écran

### 2.1 Configuration NVDA (Windows Gratuit)

**Installation**:
```bash
# Télécharger depuis https://www.nvaccess.org/
# Installer et lancer
```

**Test de Base**:
1. Lancer NVDA (Insert+N)
2. Naviguer au page web
3. Écouter si le contenu est annoncé correctement

### 2.2 Commandes NVDA Essentielles

| Commande | Raccourci |
|----------|-----------|
| Arrêter la lecture | Ctrl |
| Lire tout | Insert+Flèche Bas |
| Ligne suivante | Flèche Bas |
| Mot suivant | Ctrl+Flèche Droite |
| Focus mode | Insert+Espace |
| Lister les liens | Insert+F7 |
| Lister les headings | Insert+F6 |
| Lister les landmarks | Insert+D |

### 2.3 Checklist NVDA

- [ ] Tous les inputs ont des labels anoncés
- [ ] Les erreurs sont annoncées (role="alert")
- [ ] Les modales sont annoncées comme dialogues
- [ ] Les boutons sans texte ont des labels (aria-label)
- [ ] Les icônes décoratives ne sont pas lues (aria-hidden)
- [ ] Les headings ont une structure logique (h1, h2, h3...)
- [ ] Les listes sont annoncées correctement
- [ ] Les menus/dropdowns sont navigables

### 2.4 VoiceOver (macOS/iOS)

**Activer**:
- macOS: Cmd+F5
- iOS: Réglages > Accessibilité > VoiceOver

**Commandes**:
- VO = Control+Option
- VO+U: Rotor (navigateur)
- VO+Flèches: Navigation
- VO+Espace: Activer

## 3. Tests de Contraste

### 3.1 WebAIM Color Contrast Checker

**En ligne**: https://webaim.org/resources/contrastchecker/

**Procédure**:
1. Identifier une couleur de texte et de fond
2. Entrer les couleurs
3. Vérifier que le ratio est ≥ 4.5:1 (AA) ou ≥ 7:1 (AAA)

**Combinaisons clés à vérifier**:
```
- text-primary (par défaut) sur bg-primary
- text-secondary sur surface
- text-accent sur bg-primary
- text-score-red sur background blanc
- Links (text-accent) sur fond sombre
```

### 3.2 Utiliser Chrome DevTools

**Procédure**:
1. Inspecter un élément (F12)
2. Aller à l'onglet "Computed Styles"
3. Scroller jusqu'à "Color Contrast"
4. Vérifier le ratio

## 4. Tests Automatisés

### 4.1 Lighthouse Audit

**Procédure**:
1. Ouvrir Chrome DevTools (F12)
2. Onglet "Lighthouse"
3. Cocher "Accessibility"
4. Cliquer "Analyze page load"
5. Vérifier le score ≥ 85+

**Points clés**:
- Background and foreground colors
- Buttons have accessible names
- Form inputs have associated labels
- Images have alt text
- Links have distinguishable focus state

### 4.2 axe DevTools Extension

**Installation**:
1. Chrome Web Store: "axe DevTools"
2. Ouvrir DevTools (F12)
3. Onglet "axe DevTools"
4. Cliquer "Scan ALL of my page"

**Résoudre les problèmes**:
- **Critical**: Fixer immédiatement
- **Serious**: Fixer avant release
- **Moderate**: Planifier la correction
- **Minor**: Documenter et suivre

### 4.3 Tests Unitaires avec jest-axe

```typescript
// components/Button.test.tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Button should not have accessibility violations', async () => {
  const { container } = render(
    <Button ariaLabel="Save changes">Save</Button>
  );

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## 5. Tests de Zoom et Redimensionnement

### 5.1 Zoom à 200%

**Procédure**:
1. Ctrl++ (ou Cmd++ sur Mac)
2. Appuyer 4 fois pour atteindre ~200%
3. Vérifier que:
   - Tout est lisible
   - Pas de texte coupé
   - Pas de scroll horizontal
   - Tous les boutons sont accessibles

### 5.2 Redimensionnement de Texte

**Procédure**:
1. Appuyer sur Ctrl+. pour augmenter la taille du texte
2. Vérifier que:
   - Pas de débordement
   - Pas de chevauchement
   - Tout reste lisible

### 5.3 Responsive Design

**Procédure**:
1. F12 pour DevTools
2. Toggle device toolbar (Ctrl+Shift+M)
3. Tester sur:
   - Mobile (320px)
   - Tablet (768px)
   - Desktop (1024px)
4. Vérifier que tous les éléments interactifs restent accessibles

## 6. Checklist de Test Complet

### Avant tout commit
- [ ] Tab navigation fonctionne correctement
- [ ] Escape ferme les modales
- [ ] Enter soumet les formulaires
- [ ] Tous les inputs ont des labels
- [ ] Les boutons icon-only ont aria-label
- [ ] Pas d'erreurs dans console

### Avant release
- [ ] Lighthouse accessibility ≥ 90
- [ ] axe DevTools: 0 violations
- [ ] Test NVDA complet (au moins 5 min)
- [ ] Vérifier contraste sur tous les textes
- [ ] Test zoom à 200%
- [ ] Test sur mobile (clavier virtuel)
- [ ] Test des formulaires au clavier
- [ ] VoiceOver sur macOS testé

## 7. Outils Recommandés

### Gratuit
- **NVDA**: Lecteur d'écran Windows
- **axe DevTools**: Extension Chrome
- **Lighthouse**: Chrome DevTools intégré
- **WebAIM Contrast Checker**: En ligne
- **WAVE**: Extension Firefox/Chrome

### Payant (Optionnel)
- **JAWS**: Lecteur d'écran professionnel
- **VoiceOver**: macOS/iOS intégré
- **Color Oracle**: Simulateur de daltonisme

## 8. Procédure de Test Automatisé (CI/CD)

### Configuration GitHub Actions

```yaml
# .github/workflows/accessibility.yml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run build
      - run: npm run test:a11y
```

### npm Scripts

```json
{
  "scripts": {
    "test:a11y": "jest --testPathPattern=a11y",
    "test:lighthouse": "lighthouse https://localhost:3000 --view",
    "lint:a11y": "eslint --ext .tsx --config .eslintrc.a11y.js"
  }
}
```

## 9. Problèmes Courants et Solutions

### Problème: Focus pas visible
**Cause**: CSS reset supprime `outline`
**Solution**: Ajouter `focus:ring-2 focus:ring-accent-dim` à tous les éléments interactifs

### Problème: Label pas associé
**Cause**: `<input>` sans `htmlFor` sur `<label>`
**Solution**: Utiliser `<label htmlFor="input-id">` avec `id="input-id"` sur l'input

### Problème: Bouton sans texte pas accessible
**Cause**: Juste une icône sans label
**Solution**: Ajouter `aria-label="Description"` ou `ariaLabel` prop

### Problème: Modal piégée
**Cause**: Focus peut sortir de la modale
**Solution**: Implémenter FocusTrap avec `react-focus-lock`

### Problème: Lecteur d'écran ne lit pas l'erreur
**Cause**: Pas de `role="alert"` ou `aria-live`
**Solution**: Ajouter `role="alert" aria-live="assertive"`

## 10. Ressources de Formation

### Vidéos
- [Web Accessibility by Google](https://www.udacity.com/course/web-accessibility--ud891)
- [A11y Bytes](https://www.youtube.com/c/A11yBytes)
- [Deque University](https://dequeuniversity.com/)

### Cours
- [freeCodeCamp Accessibility](https://www.freecodecamp.org/news/accessibility-course/)
- [Khan Academy Accessibility](https://www.khanacademy.org/)

### Documentation
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [W3C WCAG](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

---

**Rappel Important**: L'accessibilité n'est pas un "nice to have", c'est une nécessité pour inclure tous les utilisateurs. Les tests doivent être réguliers et continus, pas juste une vérification ponctuelle.
