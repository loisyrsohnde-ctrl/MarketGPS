/**
 * MarketGPS Mobile - Asset Card Component
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Asset } from '@/lib/api';
import { ScoreBadge } from './ScoreBadge';
import { colors, radius, spacing, typography } from '@/theme/tokens';

interface AssetCardProps {
  asset: Asset;
  onPress?: () => void;
  showWatchlistButton?: boolean;
  isInWatchlist?: boolean;
  onWatchlistToggle?: () => void;
}

export function AssetCard({
  asset,
  onPress,
  showWatchlistButton = false,
  isInWatchlist = false,
  onWatchlistToggle,
}: AssetCardProps) {
  const router = useRouter();
  
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) {
      onPress();
    } else {
      router.push(`/asset/${encodeURIComponent(asset.asset_id || asset.symbol)}`);
    }
  };
  
  const handleWatchlistToggle = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onWatchlistToggle?.();
  };
  
  const priceChange = asset.pct_change_1d ?? 0;
  const isPositive = priceChange >= 0;
  
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <View style={styles.leftSection}>
        <View style={styles.symbolContainer}>
          <Text style={styles.symbol}>{asset.symbol}</Text>
          <Text style={styles.type}>{asset.asset_type}</Text>
        </View>
        <Text style={styles.name} numberOfLines={1}>
          {asset.name}
        </Text>
      </View>
      
      <View style={styles.rightSection}>
        <View style={styles.priceContainer}>
          {asset.last_price && (
            <Text style={styles.price}>
              ${asset.last_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
          )}
          <View style={[styles.changeContainer, isPositive ? styles.changePositive : styles.changeNegative]}>
            <Ionicons
              name={isPositive ? 'arrow-up' : 'arrow-down'}
              size={10}
              color={isPositive ? colors.success : colors.error}
            />
            <Text style={[styles.changeText, isPositive ? styles.textPositive : styles.textNegative]}>
              {Math.abs(priceChange).toFixed(2)}%
            </Text>
          </View>
        </View>
        
        <ScoreBadge score={asset.score_total} size="md" />
        
        {showWatchlistButton && (
          <TouchableOpacity
            style={styles.watchlistButton}
            onPress={handleWatchlistToggle}
          >
            <Ionicons
              name={isInWatchlist ? 'bookmark' : 'bookmark-outline'}
              size={20}
              color={isInWatchlist ? colors.accent : colors.textMutedSolid}
            />
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.bgElevated,
    borderRadius: radius.md,
    padding: spacing[4],
    marginBottom: spacing[2],
    borderWidth: 1,
    borderColor: colors.glassBorder,
  },
  leftSection: {
    flex: 1,
    marginRight: spacing[3],
  },
  symbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
  },
  symbol: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  type: {
    fontSize: typography.fontSize['2xs'],
    fontWeight: typography.fontWeight.medium,
    color: colors.textMutedSolid,
    backgroundColor: colors.bgSecondary,
    paddingHorizontal: spacing[1.5],
    paddingVertical: spacing[0.5],
    borderRadius: 4,
  },
  name: {
    fontSize: typography.fontSize.xs,
    color: colors.textSecondarySolid,
    marginTop: spacing[1],
  },
  rightSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[3],
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  changeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    paddingHorizontal: spacing[1.5],
    paddingVertical: spacing[0.5],
    borderRadius: 4,
    marginTop: spacing[0.5],
  },
  changePositive: {
    backgroundColor: colors.successBg,
  },
  changeNegative: {
    backgroundColor: colors.errorBg,
  },
  changeText: {
    fontSize: typography.fontSize['2xs'],
    fontWeight: typography.fontWeight.semibold,
  },
  textPositive: {
    color: colors.success,
  },
  textNegative: {
    color: colors.error,
  },
  watchlistButton: {
    padding: spacing[2],
  },
});
