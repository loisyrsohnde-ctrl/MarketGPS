/**
 * MarketGPS Mobile - Card Component
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { colors, radius, spacing, shadows } from '@/theme/tokens';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outline' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  style?: ViewStyle;
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  style,
}: CardProps) {
  return (
    <View style={[styles.base, styles[variant], styles[`padding_${padding}`], style]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radius.xl,
    overflow: 'hidden',
  },
  
  // Variants - Using web design tokens
  default: {
    backgroundColor: colors.bgElevated, // #0D1214
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  elevated: {
    backgroundColor: colors.bgElevated,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    ...shadows.lg,
  },
  outline: {
    backgroundColor: colors.transparent,
    borderWidth: 1,
    borderColor: colors.borderDefault,
  },
  glass: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  
  // Padding
  padding_none: {
    padding: spacing[0],
  },
  padding_sm: {
    padding: spacing[3],
  },
  padding_md: {
    padding: spacing[4],
  },
  padding_lg: {
    padding: spacing[6],
  },
});
