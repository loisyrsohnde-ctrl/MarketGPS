/**
 * MarketGPS Mobile - Score Badge Component
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { getScoreColor, getScoreLabel } from '@/lib/config';
import { radius, spacing, typography } from '@/theme/tokens';

interface ScoreBadgeProps {
  score: number | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ScoreBadge({ score, size = 'md', showLabel = false }: ScoreBadgeProps) {
  const color = getScoreColor(score);
  const label = getScoreLabel(score);
  
  return (
    <View style={styles.container}>
      <View
        style={[
          styles.badge,
          styles[`badge_${size}`],
          { backgroundColor: `${color}20`, borderColor: color },
        ]}
      >
        <Text style={[styles.text, styles[`text_${size}`], { color }]}>
          {score !== null ? Math.round(score) : '—'}
        </Text>
      </View>
      {showLabel && (
        <Text style={[styles.label, { color }]}>{label}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  badge: {
    borderRadius: radius.sm,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge_sm: {
    width: 32,
    height: 24,
  },
  badge_md: {
    width: 44,
    height: 32,
  },
  badge_lg: {
    width: 56,
    height: 40,
  },
  text: {
    fontWeight: typography.fontWeight.bold,
  },
  text_sm: {
    fontSize: typography.fontSize['2xs'],
  },
  text_md: {
    fontSize: typography.fontSize.sm,
  },
  text_lg: {
    fontSize: typography.fontSize.lg,
  },
  label: {
    fontSize: typography.fontSize['2xs'],
    fontWeight: typography.fontWeight.medium,
    marginTop: spacing[0.5],
  },
});
