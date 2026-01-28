/**
 * MarketGPS Mobile - Subscription Gate Component
 * Controls access to features based on subscription status
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useIsPro, useIsAuthenticated } from '@/store/auth';

interface SubscriptionGateProps {
  children: React.ReactNode;
  feature?: string;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

/**
 * Wraps content that requires a Pro subscription
 * Shows upgrade prompt for free users
 */
export function SubscriptionGate({
  children,
  feature = 'cette fonctionnalité',
  fallback,
  showUpgradePrompt = true,
}: SubscriptionGateProps) {
  const isPro = useIsPro();
  const isAuthenticated = useIsAuthenticated();
  const router = useRouter();

  // Pro users get full access
  if (isPro) {
    return <>{children}</>;
  }

  // Not authenticated - show login prompt
  if (!isAuthenticated) {
    return (
      <View style={styles.container}>
        <View style={styles.iconContainer}>
          <Ionicons name="lock-closed-outline" size={32} color="#64748B" />
        </View>
        <Text style={styles.title}>Connexion requise</Text>
        <Text style={styles.description}>
          Connectez-vous pour accéder à {feature}
        </Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => router.push('/(auth)/login')}
        >
          <Text style={styles.buttonText}>Se connecter</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Free user - show upgrade prompt or fallback
  if (fallback) {
    return <>{fallback}</>;
  }

  if (showUpgradePrompt) {
    return (
      <View style={styles.container}>
        <View style={styles.iconContainer}>
          <Ionicons name="diamond-outline" size={32} color="#19D38C" />
        </View>
        <Text style={styles.title}>Fonctionnalité Pro</Text>
        <Text style={styles.description}>
          Passez à Pro pour accéder à {feature}
        </Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => router.push('/checkout')}
        >
          <Text style={styles.buttonText}>Passer à Pro</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return null;
}

/**
 * Hook to check if current user has access to Pro features
 */
export function useHasProAccess(): boolean {
  return useIsPro();
}

/**
 * Higher-order component for Pro-only screens
 */
export function withProAccess<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  feature: string
) {
  return function ProGatedComponent(props: P) {
    return (
      <SubscriptionGate feature={feature}>
        <WrappedComponent {...props} />
      </SubscriptionGate>
    );
  };
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  iconContainer: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#1E293B',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 8,
    textAlign: 'center',
  },
  description: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  button: {
    backgroundColor: '#19D38C',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#0A0F1C',
  },
});
