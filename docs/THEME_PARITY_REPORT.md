# MarketGPS Theme Parity Report

**Date**: 2025-01-27  
**Status**: Synchronisé

---

## Résumé

Les design tokens mobile ont été synchronisés avec le web. Le fichier source de vérité est désormais :

- **Web**: `frontend/styles/globals.css` (CSS variables)
- **Mobile**: `mobile/src/theme/tokens.ts` (TypeScript)

---

## Mapping Complet des Tokens

### Background Colors

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| Primary BG | `--bg-primary` | `#070A0B` | `colors.bgPrimary` | ✅ Synced |
| Secondary BG | `--bg-secondary` | `#0A0E10` | `colors.bgSecondary` | ✅ Synced |
| Elevated BG | `--bg-elevated` | `#0D1214` | `colors.bgElevated` | ✅ Synced |

### Surface Colors

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| Surface | `--surface` | `rgba(255,255,255,0.04)` | `colors.surface` | ✅ Synced |
| Surface Hover | `--surface-hover` | `rgba(255,255,255,0.06)` | `colors.surfaceHover` | ✅ Synced |
| Surface Active | `--surface-active` | `rgba(255,255,255,0.08)` | `colors.surfaceActive` | ✅ Synced |
| Surface Dark | `--surface-dark` | `rgba(0,0,0,0.35)` | `colors.surfaceDark` | ✅ Synced |

### Accent Colors (Brand Green)

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| Accent | `--accent` | `#19D38C` | `colors.accent` | ✅ Synced |
| Accent Light | `--accent-light` | `#4ADE80` | `colors.accentLight` | ✅ Synced |
| Accent Dark | `--accent-dark` | `#16A34A` | `colors.accentDark` | ✅ Synced |
| Accent Dim | `--accent-dim` | `rgba(25,211,140,0.15)` | `colors.accentDim` | ✅ Synced |
| Accent Glow | `--accent-glow` | `rgba(25,211,140,0.25)` | `colors.accentGlow` | ✅ Synced |

### Text Colors

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| Primary | `--text-primary` | `#EAF2EE` | `colors.textPrimary` | ✅ Synced |
| Secondary | `--text-secondary` | `rgba(234,242,238,0.70)` | `colors.textSecondary` | ✅ Synced |
| Muted | `--text-muted` | `rgba(234,242,238,0.50)` | `colors.textMuted` | ✅ Synced |
| Dim | `--text-dim` | `rgba(234,242,238,0.35)` | `colors.textDim` | ✅ Synced |

### Border Colors

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| Glass Border | `--glass-border` | `rgba(255,255,255,0.08)` | `colors.glassBorder` | ✅ Synced |
| Glass Border Hover | `--glass-border-hover` | `rgba(255,255,255,0.12)` | `colors.glassBorderHover` | ✅ Synced |
| Glass Border Active | `--glass-border-active` | `rgba(25,211,140,0.4)` | `colors.glassBorderActive` | ✅ Synced |

### Score Colors

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| Red | `--score-red` | `#EF4444` | `colors.scoreRed` | ✅ Synced |
| Yellow | `--score-yellow` | `#F59E0B` | `colors.scoreYellow` | ✅ Synced |
| Light Green | `--score-light-green` | `#4ADE80` | `colors.scoreLightGreen` | ✅ Synced |
| Green | `--score-green` | `#22C55E` | `colors.scoreGreen` | ✅ Synced |

### Status Colors

| Token | Web Value | Mobile Token | Status |
|-------|-----------|--------------|--------|
| Success | `#22C55E` | `colors.success` | ✅ Synced |
| Warning | `#F59E0B` | `colors.warning` | ✅ Synced |
| Error | `#EF4444` | `colors.error` | ✅ Synced |
| Info | `#3B82F6` | `colors.info` | ✅ Synced |

### Spacing

| Token | Web Value | Mobile Token | Status |
|-------|-----------|--------------|--------|
| 0 | 0 | `spacing[0]` | ✅ Synced |
| 1 | 4px | `spacing[1]` | ✅ Synced |
| 2 | 8px | `spacing[2]` | ✅ Synced |
| 3 | 12px | `spacing[3]` | ✅ Synced |
| 4 | 16px | `spacing[4]` | ✅ Synced |
| 5 | 20px | `spacing[5]` | ✅ Synced |
| 6 | 24px | `spacing[6]` | ✅ Synced |
| 8 | 32px | `spacing[8]` | ✅ Synced |

### Border Radius

| Token | CSS Variable | Web Value | Mobile Token | Status |
|-------|-------------|-----------|--------------|--------|
| SM | `--radius-sm` | 8px | `radius.sm` | ✅ Synced |
| MD | `--radius-md` | 12px | `radius.md` | ✅ Synced |
| LG | `--radius-lg` | 16px | `radius.lg` | ✅ Synced |
| XL | `--radius-xl` | 20px | `radius.xl` | ✅ Synced |
| 2XL | `--radius-2xl` | 24px | `radius['2xl']` | ✅ Synced |

---

## Changement Majeur : Accent Color

**AVANT (Mobile)**: `#22D3EE` (Cyan)  
**APRÈS (Mobile)**: `#19D38C` (Vert Émeraude)

Ce changement aligne le mobile sur la marque web de MarketGPS.

---

## Fichiers Modifiés

### Nouveaux Fichiers
- `mobile/src/theme/tokens.ts` - Tokens centralisés
- `mobile/src/theme/index.ts` - Export centralisé

### Composants Mis à Jour
- `mobile/src/components/ui/Button.tsx`
- `mobile/src/components/ui/Card.tsx`
- `mobile/src/components/ui/Input.tsx`
- `mobile/src/components/ui/ScoreBadge.tsx`
- `mobile/src/components/ui/AssetCard.tsx`
- `mobile/app/_layout.tsx`
- `mobile/app/(tabs)/_layout.tsx`
- `mobile/app/settings/billing.tsx`

---

## Guide : Ajouter de Nouvelles Couleurs

1. **Web** : Ajouter la CSS variable dans `frontend/styles/globals.css` sous `:root`
2. **Mobile** : Ajouter le token dans `mobile/src/theme/tokens.ts` sous `colors`
3. **Usage Mobile** : Importer depuis `@/theme/tokens` ou `@/theme`

```typescript
// Exemple d'usage mobile
import { colors, spacing, radius } from '@/theme/tokens';

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.bgPrimary,
    padding: spacing[4],
    borderRadius: radius.md,
  },
});
```

---

## Vérification Visuelle

Pour vérifier la parité visuelle :

1. Ouvrir le web sur `https://app.marketgps.online`
2. Ouvrir l'app mobile sur le simulateur
3. Comparer :
   - Couleur des boutons primaires (doit être vert `#19D38C`)
   - Background (doit être noir `#070A0B`)
   - Cards (doit avoir bordure subtile)
   - Scores (même palette de couleurs)
   - Tab bar (icône active en vert)

---

*Rapport généré automatiquement lors de l'audit MarketGPS*
