/**
 * MarketGPS Mobile - Premium GPS Loading Animation
 * Sophisticated, refined, minimal animation for professional look
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Easing,
  AccessibilityInfo,
  Platform,
} from 'react-native';
import * as Haptics from 'expo-haptics';

const COLORS = {
  bgPrimary: '#0A0F1C',
  accent: '#19D38C',
  accentDim: 'rgba(25, 211, 140, 0.25)',
  accentFaint: 'rgba(25, 211, 140, 0.08)',
  textSecondary: '#94A3B8',
};

interface GpsLoadingProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
  minimal?: boolean;
}

const SIZES = {
  small: { container: 48, dot: 6, ring: 36 },
  medium: { container: 80, dot: 8, ring: 56 },
  large: { container: 120, dot: 10, ring: 80 },
};

export function GpsLoading({
  message,
  size = 'medium',
  fullScreen = false,
  minimal = false,
}: GpsLoadingProps) {
  const dimensions = SIZES[size];

  // Animation values
  const dotScale = useRef(new Animated.Value(1)).current;
  const ring1Scale = useRef(new Animated.Value(0.6)).current;
  const ring1Opacity = useRef(new Animated.Value(0.8)).current;
  const ring2Scale = useRef(new Animated.Value(0.6)).current;
  const ring2Opacity = useRef(new Animated.Value(0.6)).current;

  const [reducedMotion, setReducedMotion] = React.useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReducedMotion);
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      dotScale.setValue(1);
      ring1Scale.setValue(1);
      ring1Opacity.setValue(0.5);
      return;
    }

    // Subtle dot pulse
    const dotAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(dotScale, {
          toValue: 1.15,
          duration: 800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(dotScale, {
          toValue: 1,
          duration: 800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );

    // Ring 1 - expanding outward
    const ring1Animation = Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(ring1Scale, {
            toValue: 1.4,
            duration: 1200,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
          Animated.timing(ring1Opacity, {
            toValue: 0,
            duration: 1200,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(ring1Scale, { toValue: 0.6, duration: 0, useNativeDriver: true }),
          Animated.timing(ring1Opacity, { toValue: 0.8, duration: 0, useNativeDriver: true }),
        ]),
      ])
    );

    // Ring 2 - delayed
    const ring2Animation = Animated.loop(
      Animated.sequence([
        Animated.delay(400),
        Animated.parallel([
          Animated.timing(ring2Scale, {
            toValue: 1.4,
            duration: 1200,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
          Animated.timing(ring2Opacity, {
            toValue: 0,
            duration: 1200,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(ring2Scale, { toValue: 0.6, duration: 0, useNativeDriver: true }),
          Animated.timing(ring2Opacity, { toValue: 0.6, duration: 0, useNativeDriver: true }),
        ]),
      ])
    );

    dotAnimation.start();
    ring1Animation.start();
    ring2Animation.start();

    return () => {
      dotAnimation.stop();
      ring1Animation.stop();
      ring2Animation.stop();
    };
  }, [reducedMotion]);

  const content = (
    <View style={[styles.wrapper, minimal && styles.wrapperMinimal]}>
      <View
        style={[styles.container, { width: dimensions.container, height: dimensions.container }]}
        accessibilityRole="progressbar"
        accessibilityLabel={message || 'Chargement'}
      >
        {/* Outer ring */}
        <Animated.View
          style={[
            styles.ring,
            {
              width: dimensions.ring,
              height: dimensions.ring,
              borderRadius: dimensions.ring / 2,
              transform: [{ scale: ring2Scale }],
              opacity: ring2Opacity,
            },
          ]}
        />

        {/* Inner ring */}
        <Animated.View
          style={[
            styles.ring,
            {
              width: dimensions.ring * 0.7,
              height: dimensions.ring * 0.7,
              borderRadius: (dimensions.ring * 0.7) / 2,
              transform: [{ scale: ring1Scale }],
              opacity: ring1Opacity,
            },
          ]}
        />

        {/* Central dot */}
        <Animated.View
          style={[
            styles.dot,
            {
              width: dimensions.dot,
              height: dimensions.dot,
              borderRadius: dimensions.dot / 2,
              transform: [{ scale: dotScale }],
            },
          ]}
        />
      </View>

      {message && !minimal && (
        <Text style={styles.message}>{message}</Text>
      )}
    </View>
  );

  if (fullScreen) {
    return <View style={styles.fullScreen}>{content}</View>;
  }

  return content;
}

// Alias for backwards compatibility
export function LoadingSpinner(props: GpsLoadingProps) {
  return <GpsLoading {...props} />;
}

const styles = StyleSheet.create({
  fullScreen: {
    flex: 1,
    backgroundColor: COLORS.bgPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  wrapperMinimal: {
    padding: 8,
  },
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  dot: {
    position: 'absolute',
    backgroundColor: COLORS.accent,
  },
  ring: {
    position: 'absolute',
    borderWidth: 1.5,
    borderColor: COLORS.accent,
    backgroundColor: 'transparent',
  },
  message: {
    marginTop: 16,
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '500',
  },
});

export default GpsLoading;
