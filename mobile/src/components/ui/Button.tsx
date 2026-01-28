/**
 * MarketGPS Mobile - Button Component
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { colors, radius, spacing, typography } from '@/theme/tokens';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  fullWidth = false,
  style,
  textStyle,
}: ButtonProps) {
  const handlePress = () => {
    if (!disabled && !loading) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      onPress();
    }
  };
  
  return (
    <TouchableOpacity
      style={[
        styles.base,
        styles[variant],
        styles[`size_${size}`],
        fullWidth && styles.fullWidth,
        (disabled || loading) && styles.disabled,
        style,
      ]}
      onPress={handlePress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'primary' ? colors.bgPrimary : colors.accent}
          size="small"
        />
      ) : (
        <>
          {icon}
          <Text
            style={[
              styles.text,
              styles[`text_${variant}`],
              styles[`textSize_${size}`],
              textStyle,
            ]}
          >
            {title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    gap: spacing[2],
  },
  
  // Variants - Using web design tokens
  primary: {
    backgroundColor: colors.accent, // #19D38C (web primary green)
  },
  secondary: {
    backgroundColor: colors.surfaceSolid, // Dark surface
  },
  outline: {
    backgroundColor: colors.transparent,
    borderWidth: 1,
    borderColor: colors.borderDefault,
  },
  ghost: {
    backgroundColor: colors.transparent,
  },
  danger: {
    backgroundColor: colors.error, // #EF4444
  },
  
  // Sizes
  size_sm: {
    paddingVertical: spacing[2],
    paddingHorizontal: spacing[3],
  },
  size_md: {
    paddingVertical: spacing[3],
    paddingHorizontal: spacing[5],
  },
  size_lg: {
    paddingVertical: spacing[4],
    paddingHorizontal: spacing[6],
  },
  
  // States
  disabled: {
    opacity: 0.5,
  },
  fullWidth: {
    width: '100%',
  },
  
  // Text
  text: {
    fontWeight: typography.fontWeight.semibold,
  },
  text_primary: {
    color: colors.bgPrimary, // Dark text on green button
  },
  text_secondary: {
    color: colors.textPrimary,
  },
  text_outline: {
    color: colors.textPrimary,
  },
  text_ghost: {
    color: colors.accent,
  },
  text_danger: {
    color: colors.white,
  },
  
  // Text sizes
  textSize_sm: {
    fontSize: typography.fontSize.xs,
  },
  textSize_md: {
    fontSize: typography.fontSize.sm,
  },
  textSize_lg: {
    fontSize: typography.fontSize.base,
  },
});
