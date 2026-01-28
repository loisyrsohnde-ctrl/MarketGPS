/**
 * MarketGPS Mobile - Tabs Layout
 *
 * Uses design tokens from theme/tokens.ts (synced with web)
 *
 * Subscription Gating Logic:
 * - NOT authenticated: Full access to browse + login/signup prompts (can recover existing Pro account)
 * - Authenticated FREE: Only News tab, other tabs redirect to checkout
 * - Authenticated PRO: Full access to all features
 *
 * This ensures users who reinstall can log back in to recover their Pro subscription.
 */

import { useEffect } from 'react';
import { Tabs, useRouter, useSegments } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, View } from 'react-native';
import { colors, spacing, typography } from '@/theme/tokens';
import { useIsAuthenticated, useIsPro, useAuthStore } from '@/store/auth';

export default function TabsLayout() {
  const router = useRouter();
  const segments = useSegments();
  const isAuthenticated = useIsAuthenticated();
  const isPro = useIsPro();
  const { isInitialized } = useAuthStore();

  // Redirect authenticated free users away from pro-only tabs
  // NOTE: Non-authenticated users CAN browse freely (they need access to login)
  useEffect(() => {
    if (!isInitialized) return;

    // Get current tab name
    const currentTab = segments[1]; // (tabs)/[tabName]

    // Pro-only tabs (when authenticated)
    const proOnlyTabs = ['index', 'explorer', 'watchlist'];
    // Note: 'settings' is NOT locked - users need it to login/manage account

    // ONLY restrict if: authenticated AND not Pro AND on a pro-only tab
    // Non-authenticated users can browse freely to find the login button
    if (isAuthenticated && !isPro && proOnlyTabs.includes(currentTab)) {
      router.replace('/(tabs)/news');
    }
  }, [isAuthenticated, isPro, segments, isInitialized]);

  // Determine if feature should be locked
  // Lock = authenticated but not Pro (Free tier)
  // Unlock = not authenticated (can browse/login) OR Pro user
  const shouldLockFeature = isAuthenticated && !isPro;

  // Custom tab bar icon with lock indicator
  const renderTabBarIcon = (iconName: string, color: string, size: number, isProFeature: boolean) => {
    const showLock = isProFeature && shouldLockFeature;

    return (
      <View style={styles.tabIconContainer}>
        <Ionicons
          name={showLock ? 'lock-closed' : iconName as any}
          size={size}
          color={showLock ? colors.textMutedSolid : color}
        />
      </View>
    );
  };

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textMutedSolid,
        tabBarLabelStyle: styles.tabBarLabel,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) =>
            renderTabBarIcon('speedometer-outline', color, size, true),
        }}
        listeners={{
          tabPress: (e) => {
            // Only block if authenticated AND free tier
            if (shouldLockFeature) {
              e.preventDefault();
              router.push('/checkout');
            }
          },
        }}
      />
      <Tabs.Screen
        name="explorer"
        options={{
          title: 'Explorer',
          tabBarIcon: ({ color, size }) =>
            renderTabBarIcon('search-outline', color, size, true),
        }}
        listeners={{
          tabPress: (e) => {
            if (shouldLockFeature) {
              e.preventDefault();
              router.push('/checkout');
            }
          },
        }}
      />
      <Tabs.Screen
        name="watchlist"
        options={{
          title: 'Watchlist',
          tabBarIcon: ({ color, size }) =>
            renderTabBarIcon('bookmark-outline', color, size, true),
        }}
        listeners={{
          tabPress: (e) => {
            if (shouldLockFeature) {
              e.preventDefault();
              router.push('/checkout');
            }
          },
        }}
      />
      <Tabs.Screen
        name="news"
        options={{
          title: 'Actualités',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="newspaper-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Plus',
          tabBarIcon: ({ color, size }) => (
            // Settings is NEVER locked - users need access to login/account
            <Ionicons name="menu-outline" size={size} color={color} />
          ),
        }}
        // No listener - Settings always accessible for login/account management
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.bgSecondary,
    borderTopColor: colors.borderDefault,
    borderTopWidth: 1,
    paddingTop: spacing[2],
    paddingBottom: spacing[2],
    height: 88,
  },
  tabBarLabel: {
    fontSize: typography.fontSize['2xs'],
    fontWeight: typography.fontWeight.medium,
  },
  tabIconContainer: {
    position: 'relative',
  },
});
