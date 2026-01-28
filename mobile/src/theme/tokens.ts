/**
 * MarketGPS Mobile Design Tokens
 * 
 * SYNCHRONISÉ AVEC: frontend/styles/globals.css
 * 
 * Ces tokens doivent être identiques aux CSS variables du web.
 * En cas de modification, mettre à jour les deux fichiers.
 */

// ═══════════════════════════════════════════════════════════════════════════
// COULEURS
// ═══════════════════════════════════════════════════════════════════════════

export const colors = {
  // Background
  bgPrimary: '#070A0B',
  bgSecondary: '#0A0E10',
  bgElevated: '#0D1214',
  
  // Surface (Glass effect - using solid colors for RN)
  surface: 'rgba(255, 255, 255, 0.04)',
  surfaceHover: 'rgba(255, 255, 255, 0.06)',
  surfaceActive: 'rgba(255, 255, 255, 0.08)',
  surfaceDark: 'rgba(0, 0, 0, 0.35)',
  
  // Solid surface alternatives (for components that don't support transparency)
  surfaceSolid: '#0F1214',
  surfaceHoverSolid: '#141819',
  surfaceActiveSolid: '#191E21',
  
  // Glass Border
  glassBorder: 'rgba(255, 255, 255, 0.08)',
  glassBorderHover: 'rgba(255, 255, 255, 0.12)',
  glassBorderActive: 'rgba(25, 211, 140, 0.4)',
  
  // Solid border alternatives
  borderDefault: '#1E2426',
  borderHover: '#2A3033',
  borderActive: '#19D38C',
  
  // Accent Green (PRIMARY BRAND COLOR)
  accent: '#19D38C',
  accentLight: '#4ADE80',
  accentDark: '#16A34A',
  accentDim: 'rgba(25, 211, 140, 0.15)',
  accentGlow: 'rgba(25, 211, 140, 0.25)',
  
  // Text
  textPrimary: '#EAF2EE',
  textSecondary: 'rgba(234, 242, 238, 0.70)',
  textMuted: 'rgba(234, 242, 238, 0.50)',
  textDim: 'rgba(234, 242, 238, 0.35)',
  
  // Solid text alternatives
  textSecondarySolid: '#B8C4BE',
  textMutedSolid: '#8A9690',
  textDimSolid: '#606B66',
  
  // Score Colors
  scoreRed: '#EF4444',
  scoreYellow: '#F59E0B',
  scoreLightGreen: '#4ADE80',
  scoreGreen: '#22C55E',
  
  // Status Colors
  success: '#22C55E',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Status backgrounds
  successBg: 'rgba(34, 197, 94, 0.15)',
  warningBg: 'rgba(245, 158, 11, 0.15)',
  errorBg: 'rgba(239, 68, 68, 0.15)',
  infoBg: 'rgba(59, 130, 246, 0.15)',
  
  // Special
  white: '#FFFFFF',
  black: '#000000',
  transparent: 'transparent',
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// SPACING (8px grid)
// ═══════════════════════════════════════════════════════════════════════════

export const spacing = {
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  3.5: 14,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  11: 44,
  12: 48,
  14: 56,
  16: 64,
  20: 80,
  24: 96,
  28: 112,
  32: 128,
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// BORDER RADIUS
// ═══════════════════════════════════════════════════════════════════════════

export const radius = {
  none: 0,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  full: 9999,
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// TYPOGRAPHY
// ═══════════════════════════════════════════════════════════════════════════

export const typography = {
  fontFamily: {
    sans: 'System', // Uses system font on each platform
    mono: 'Menlo',
  },
  fontSize: {
    '2xs': 10,
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
    '5xl': 48,
  },
  fontWeight: {
    normal: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// SHADOWS
// ═══════════════════════════════════════════════════════════════════════════

export const shadows = {
  none: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.5,
    shadowRadius: 32,
    elevation: 12,
  },
  glow: {
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 8,
  },
  glowSm: {
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 4,
  },
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════════════════════

export const animation = {
  duration: {
    fast: 150,
    base: 200,
    slow: 300,
  },
  easing: {
    default: 'ease-out',
  },
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// SCORE COLOR HELPER
// ═══════════════════════════════════════════════════════════════════════════

export function getScoreColor(score: number): string {
  if (score >= 80) return colors.scoreGreen;
  if (score >= 60) return colors.scoreLightGreen;
  if (score >= 40) return colors.scoreYellow;
  if (score >= 20) return colors.warning;
  return colors.scoreRed;
}

export function getScoreBackgroundColor(score: number): string {
  if (score >= 80) return colors.successBg;
  if (score >= 60) return 'rgba(74, 222, 128, 0.15)';
  if (score >= 40) return colors.warningBg;
  if (score >= 20) return 'rgba(249, 115, 22, 0.15)';
  return colors.errorBg;
}

// ═══════════════════════════════════════════════════════════════════════════
// THEME OBJECT (compatible with styled-components / emotion)
// ═══════════════════════════════════════════════════════════════════════════

export const theme = {
  colors,
  spacing,
  radius,
  typography,
  shadows,
  animation,
} as const;

export type Theme = typeof theme;
export type Colors = typeof colors;
export type Spacing = typeof spacing;
export type Radius = typeof radius;

export default theme;
