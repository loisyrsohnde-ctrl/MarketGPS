/**
 * MarketGPS Mobile - Markets Screen
 * Browsable markets with navigation to filtered explorer
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/lib/api';
import { Card, LoadingSpinner } from '@/components/ui';
import { AFRICA_REGIONS } from '@/lib/config';

// Country code to name mapping for display
const COUNTRY_NAMES: Record<string, string> = {
  // North Africa
  MA: 'Maroc',
  DZ: 'Algérie',
  TN: 'Tunisie',
  EG: 'Égypte',
  LY: 'Libye',
  // West Africa
  NG: 'Nigeria',
  GH: 'Ghana',
  SN: 'Sénégal',
  CI: 'Côte d\'Ivoire',
  BF: 'Burkina Faso',
  ML: 'Mali',
  NE: 'Niger',
  TG: 'Togo',
  BJ: 'Bénin',
  // Central Africa
  CM: 'Cameroun',
  GA: 'Gabon',
  CG: 'Congo',
  TD: 'Tchad',
  CF: 'Centrafrique',
  GQ: 'Guinée Éq.',
  CD: 'RD Congo',
  // East Africa
  KE: 'Kenya',
  TZ: 'Tanzanie',
  UG: 'Ouganda',
  RW: 'Rwanda',
  ET: 'Éthiopie',
  // Southern Africa
  ZA: 'Afrique du Sud',
  AO: 'Angola',
  MZ: 'Mozambique',
  ZW: 'Zimbabwe',
  NA: 'Namibie',
  BW: 'Botswana',
};

// Region key to code mapping for API
const REGION_CODES: Record<string, string> = {
  NORTH: 'NORTH',
  WEST: 'WEST',
  CENTRAL: 'CENTRAL',
  EAST: 'EAST',
  SOUTH: 'SOUTH',
};

export default function MarketsScreen() {
  const router = useRouter();

  // Fetch scope counts
  const { data: counts, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['scopeCounts'],
    queryFn: () => api.getScopeCounts(),
  });

  const handleMarketPress = (scope: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push({
      pathname: '/(tabs)/explorer',
      params: { market_scope: scope },
    });
  };

  const handleRegionPress = (regionKey: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push({
      pathname: '/(tabs)/explorer',
      params: {
        market_scope: 'AFRICA',
        region: REGION_CODES[regionKey],
      },
    });
  };

  const handleCountryPress = (countryCode: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push({
      pathname: '/(tabs)/explorer',
      params: {
        market_scope: 'AFRICA',
        country: countryCode,
      },
    });
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Chargement..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={refetch}
          tintColor="#19D38C"
        />
      }
    >
      {/* Global Markets */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Marchés Globaux</Text>

        <TouchableOpacity
          style={styles.marketCard}
          onPress={() => handleMarketPress('US_EU')}
          activeOpacity={0.7}
        >
          <View style={styles.marketIcon}>
            <Text style={styles.flagEmoji}>🇺🇸</Text>
          </View>
          <View style={styles.marketContent}>
            <Text style={styles.marketName}>États-Unis & Europe</Text>
            <Text style={styles.marketDescription}>
              Actions, ETFs et obligations des marchés développés
            </Text>
          </View>
          <View style={styles.marketStats}>
            <Text style={styles.marketCount}>
              {counts?.US_EU?.toLocaleString() || 0}
            </Text>
            <Text style={styles.marketLabel}>actifs</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#64748B" />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.marketCard}
          onPress={() => handleMarketPress('AFRICA')}
          activeOpacity={0.7}
        >
          <View style={styles.marketIcon}>
            <Ionicons name="globe-outline" size={28} color="#19D38C" />
          </View>
          <View style={styles.marketContent}>
            <Text style={styles.marketName}>Afrique</Text>
            <Text style={styles.marketDescription}>
              Actions et obligations des marchés africains
            </Text>
          </View>
          <View style={styles.marketStats}>
            <Text style={styles.marketCount}>
              {counts?.AFRICA?.toLocaleString() || 0}
            </Text>
            <Text style={styles.marketLabel}>actifs</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#64748B" />
        </TouchableOpacity>
      </View>

      {/* Africa Regions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Régions Africaines</Text>
        <Text style={styles.sectionHint}>
          Touchez une région ou un pays pour explorer ses actifs
        </Text>

        {Object.entries(AFRICA_REGIONS).map(([key, region]) => (
          <Card key={key} style={styles.regionCard}>
            <TouchableOpacity
              style={styles.regionHeader}
              onPress={() => handleRegionPress(key)}
              activeOpacity={0.7}
            >
              <View style={styles.regionTitleRow}>
                <Text style={styles.regionName}>{region.name}</Text>
                <View style={styles.regionAction}>
                  <Text style={styles.viewAllText}>Voir tous</Text>
                  <Ionicons name="chevron-forward" size={16} color="#19D38C" />
                </View>
              </View>
            </TouchableOpacity>
            <View style={styles.countriesRow}>
              {region.countries.map((country) => (
                <TouchableOpacity
                  key={country}
                  style={styles.countryChip}
                  onPress={() => handleCountryPress(country)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.countryCode}>{country}</Text>
                  <Text style={styles.countryName}>
                    {COUNTRY_NAMES[country] || country}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </Card>
        ))}
      </View>

      {/* Quick Access */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Accès Rapide</Text>

        <View style={styles.quickAccessGrid}>
          <TouchableOpacity
            style={styles.quickAccessCard}
            onPress={() => handleCountryPress('ZA')}
            activeOpacity={0.7}
          >
            <Text style={styles.quickAccessEmoji}>🇿🇦</Text>
            <Text style={styles.quickAccessLabel}>Afrique du Sud</Text>
            <Text style={styles.quickAccessSub}>JSE</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickAccessCard}
            onPress={() => handleCountryPress('NG')}
            activeOpacity={0.7}
          >
            <Text style={styles.quickAccessEmoji}>🇳🇬</Text>
            <Text style={styles.quickAccessLabel}>Nigeria</Text>
            <Text style={styles.quickAccessSub}>NSE</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickAccessCard}
            onPress={() => handleCountryPress('KE')}
            activeOpacity={0.7}
          >
            <Text style={styles.quickAccessEmoji}>🇰🇪</Text>
            <Text style={styles.quickAccessLabel}>Kenya</Text>
            <Text style={styles.quickAccessSub}>NSE</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickAccessCard}
            onPress={() => handleCountryPress('MA')}
            activeOpacity={0.7}
          >
            <Text style={styles.quickAccessEmoji}>🇲🇦</Text>
            <Text style={styles.quickAccessLabel}>Maroc</Text>
            <Text style={styles.quickAccessSub}>CSE</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Market Info */}
      <Card style={styles.infoCard}>
        <View style={styles.infoIcon}>
          <Ionicons name="information-circle-outline" size={24} color="#19D38C" />
        </View>
        <Text style={styles.infoTitle}>À propos des données</Text>
        <Text style={styles.infoText}>
          Les données sont mises à jour quotidiennement. Les scores sont calculés
          à partir d'indicateurs techniques, fondamentaux et de sentiment.
        </Text>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  sectionHint: {
    fontSize: 12,
    color: '#475569',
    marginBottom: 12,
  },
  marketCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  marketIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#0F172A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  flagEmoji: {
    fontSize: 24,
  },
  marketContent: {
    flex: 1,
    marginLeft: 16,
  },
  marketName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  marketDescription: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  marketStats: {
    alignItems: 'flex-end',
    marginRight: 12,
  },
  marketCount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#19D38C',
  },
  marketLabel: {
    fontSize: 11,
    color: '#64748B',
  },
  regionCard: {
    marginBottom: 12,
  },
  regionHeader: {
    marginBottom: 12,
  },
  regionTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  regionName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  regionAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewAllText: {
    fontSize: 12,
    color: '#19D38C',
    fontWeight: '500',
  },
  countriesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  countryChip: {
    backgroundColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  countryCode: {
    fontSize: 11,
    fontWeight: '700',
    color: '#19D38C',
    marginBottom: 2,
  },
  countryName: {
    fontSize: 12,
    fontWeight: '500',
    color: '#94A3B8',
  },
  quickAccessGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  quickAccessCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  quickAccessEmoji: {
    fontSize: 32,
    marginBottom: 8,
  },
  quickAccessLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  quickAccessSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  infoCard: {
    alignItems: 'center',
    marginTop: 8,
  },
  infoIcon: {
    marginBottom: 12,
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 13,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 20,
  },
});
