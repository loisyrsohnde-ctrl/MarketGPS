/**
 * MarketGPS Mobile - Root Index (Redirect)
 */

import { Redirect } from 'expo-router';

export default function Index() {
  return <Redirect href="/(tabs)" />;
}
