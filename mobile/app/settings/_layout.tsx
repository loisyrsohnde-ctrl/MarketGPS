/**
 * MarketGPS Mobile - Settings Stack Layout
 */

import { Stack } from 'expo-router';

export default function SettingsLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerStyle: { backgroundColor: '#0A0F1C' },
        headerTintColor: '#F1F5F9',
        headerBackTitle: 'Retour',
        contentStyle: { backgroundColor: '#0A0F1C' },
      }}
    >
      <Stack.Screen name="strategies" options={{ title: 'Stratégies' }} />
      <Stack.Screen name="markets" options={{ title: 'Marchés' }} />
      <Stack.Screen name="profile" options={{ title: 'Profil' }} />
      <Stack.Screen name="billing" options={{ title: 'Abonnement' }} />
      <Stack.Screen name="notifications" options={{ title: 'Notifications' }} />
      <Stack.Screen name="security" options={{ title: 'Sécurité' }} />
      <Stack.Screen name="help" options={{ title: 'Aide' }} />
      <Stack.Screen name="terms" options={{ title: 'Conditions' }} />
      <Stack.Screen name="privacy" options={{ title: 'Confidentialité' }} />
    </Stack>
  );
}
