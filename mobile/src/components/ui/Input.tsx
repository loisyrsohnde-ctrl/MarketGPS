/**
 * MarketGPS Mobile - Input Component
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import React, { useState } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  ViewStyle,
  TextInputProps,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, spacing, typography } from '@/theme/tokens';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  helper?: string;
  leftIcon?: keyof typeof Ionicons.glyphMap;
  rightIcon?: keyof typeof Ionicons.glyphMap;
  onRightIconPress?: () => void;
  containerStyle?: ViewStyle;
}

export function Input({
  label,
  error,
  helper,
  leftIcon,
  rightIcon,
  onRightIconPress,
  containerStyle,
  secureTextEntry,
  ...props
}: InputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const isPassword = secureTextEntry !== undefined;
  const actualSecureEntry = isPassword && !showPassword;
  
  return (
    <View style={[styles.container, containerStyle]}>
      {label && <Text style={styles.label}>{label}</Text>}
      
      <View
        style={[
          styles.inputContainer,
          isFocused && styles.inputFocused,
          error && styles.inputError,
        ]}
      >
        {leftIcon && (
          <Ionicons name={leftIcon} size={20} color={colors.textMutedSolid} style={styles.leftIcon} />
        )}
        
        <TextInput
          style={[styles.input, leftIcon && styles.inputWithLeftIcon]}
          placeholderTextColor={colors.textMutedSolid}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          secureTextEntry={actualSecureEntry}
          {...props}
        />
        
        {isPassword && (
          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            style={styles.rightIcon}
          >
            <Ionicons
              name={showPassword ? 'eye-off-outline' : 'eye-outline'}
              size={20}
              color={colors.textMutedSolid}
            />
          </TouchableOpacity>
        )}
        
        {rightIcon && !isPassword && (
          <TouchableOpacity
            onPress={onRightIconPress}
            style={styles.rightIcon}
            disabled={!onRightIconPress}
          >
            <Ionicons name={rightIcon} size={20} color={colors.textMutedSolid} />
          </TouchableOpacity>
        )}
      </View>
      
      {error && <Text style={styles.error}>{error}</Text>}
      {helper && !error && <Text style={styles.helper}>{helper}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing[4],
  },
  label: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondarySolid,
    marginBottom: spacing[2],
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bgSecondary,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.borderDefault,
  },
  inputFocused: {
    borderColor: colors.accent, // Green focus state like web
  },
  inputError: {
    borderColor: colors.error,
  },
  input: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: spacing[4],
    fontSize: typography.fontSize.base,
    color: colors.textPrimary,
  },
  inputWithLeftIcon: {
    paddingLeft: 0,
  },
  leftIcon: {
    marginLeft: spacing[4],
  },
  rightIcon: {
    padding: spacing[3],
  },
  error: {
    fontSize: typography.fontSize.xs,
    color: colors.error,
    marginTop: spacing[1],
  },
  helper: {
    fontSize: typography.fontSize.xs,
    color: colors.textMutedSolid,
    marginTop: spacing[1],
  },
});
