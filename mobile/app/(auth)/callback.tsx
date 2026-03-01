/**
 * MarketGPS Mobile - Auth Callback
 * Handles deep link redirects from email verification and password reset
 */

import { useEffect } from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { supabase } from '@/lib/supabase';

export default function AuthCallbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();

  useEffect(() => {
    async function handleCallback() {
      try {
        // Supabase handles the token exchange automatically via the URL
        const { data: { session } } = await supabase.auth.getSession();

        if (session) {
          // User is authenticated, go to main app
          router.replace('/(tabs)');
        } else {
          // No session, go to login
          router.replace('/(auth)/login');
        }
      } catch (error) {
        if (__DEV__) console.error('Auth callback error:', error);
        router.replace('/(auth)/login');
      }
    }

    handleCallback();
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#19D38C" />
      <Text style={styles.text}>Vérification en cours...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0A0F1C',
    gap: 16,
  },
  text: {
    color: '#94A3B8',
    fontSize: 16,
  },
});
