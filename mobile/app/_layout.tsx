/**
 * MarketGPS Mobile - Root Layout
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import * as SplashScreen from 'expo-splash-screen';
import { useAuthStore } from '@/store/auth';
import { colors } from '@/theme/tokens';

// Prevent splash screen from hiding
SplashScreen.preventAutoHideAsync();

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
    },
  },
});

export default function RootLayout() {
  const { initialize, isInitialized } = useAuthStore();
  
  useEffect(() => {
    async function init() {
      await initialize();
      await SplashScreen.hideAsync();
    }
    init();
  }, [initialize]);
  
  if (!isInitialized) {
    return null;
  }
  
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: colors.bgPrimary },
            animation: 'slide_from_right',
          }}
        >
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="(auth)" />
          <Stack.Screen
            name="asset/[ticker]"
            options={{
              presentation: 'card',
              headerShown: true,
              headerStyle: { backgroundColor: colors.bgPrimary },
              headerTintColor: colors.textPrimary,
              headerBackTitle: 'Retour',
            }}
          />
          <Stack.Screen
            name="news/[slug]"
            options={{
              presentation: 'card',
              headerShown: true,
              headerStyle: { backgroundColor: colors.bgPrimary },
              headerTintColor: colors.textPrimary,
              headerBackTitle: 'News',
            }}
          />
          <Stack.Screen
            name="strategy/[slug]"
            options={{
              presentation: 'card',
              headerShown: true,
              headerStyle: { backgroundColor: colors.bgPrimary },
              headerTintColor: colors.textPrimary,
            }}
          />
          <Stack.Screen
            name="checkout"
            options={{
              presentation: 'modal',
              headerShown: true,
              headerTitle: 'Abonnement',
              headerStyle: { backgroundColor: colors.bgPrimary },
              headerTintColor: colors.textPrimary,
            }}
          />
        </Stack>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
