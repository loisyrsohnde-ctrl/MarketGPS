/**
 * MarketGPS Mobile - News Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { api, NewsArticle } from '@/lib/api';
import { NewsCard, LoadingSpinner, EmptyState } from '@/components/ui';

// Pays francophones prioritaires
const FRANCOPHONE_COUNTRIES = [
  { id: 'CM', name: 'Cameroun' },
  { id: 'CI', name: 'Côte d\'Ivoire' },
  { id: 'SN', name: 'Sénégal' },
  { id: 'BJ', name: 'Bénin' },
  { id: 'TG', name: 'Togo' },
  { id: 'GA', name: 'Gabon' },
  { id: 'CG', name: 'Congo' },
  { id: 'ML', name: 'Mali' },
  { id: 'BF', name: 'Burkina Faso' },
  { id: 'NE', name: 'Niger' },
  { id: 'TD', name: 'Tchad' },
  { id: 'GN', name: 'Guinée' },
  { id: 'RW', name: 'Rwanda' },
  { id: 'CD', name: 'RD Congo' },
];

// Autres pays (non-francophones)
const OTHER_COUNTRIES = [
  { id: 'NG', name: 'Nigeria' },
  { id: 'ZA', name: 'Afrique du Sud' },
  { id: 'KE', name: 'Kenya' },
  { id: 'GH', name: 'Ghana' },
  { id: 'EG', name: 'Égypte' },
  { id: 'MA', name: 'Maroc' },
  { id: 'TN', name: 'Tunisie' },
  { id: 'DZ', name: 'Algérie' },
];

// Zones économiques régionales
const ECONOMIC_ZONES = [
  { id: 'all', name: 'Tout', countries: [] as string[] },
  { id: 'CEMAC', name: 'CEMAC', countries: ['CM', 'GA', 'CG', 'TD', 'CF', 'GQ'] },
  { id: 'UEMOA', name: 'UEMOA', countries: ['SN', 'CI', 'BJ', 'TG', 'ML', 'BF', 'NE', 'GN'] },
  { id: 'MAGHREB', name: 'Maghreb', countries: ['MA', 'DZ', 'TN', 'LY'] },
  { id: 'EAC', name: 'Afrique Est', countries: ['KE', 'TZ', 'UG', 'RW', 'ET'] },
  { id: 'SADC', name: 'Afrique Sud', countries: ['ZA', 'AO', 'MZ', 'ZW', 'NA', 'BW'] },
  { id: 'WEST', name: 'Afrique Ouest', countries: ['NG', 'GH'] },
];

// Liste complète des pays (francophones d'abord)
const REGIONS = [
  { id: 'all', name: 'Tout' },
  ...FRANCOPHONE_COUNTRIES.map(c => ({ id: c.id, name: c.name })),
  ...OTHER_COUNTRIES.map(c => ({ id: c.id, name: c.name })),
];

const TAGS = [
  { id: 'all', label: 'Tout' },
  { id: 'fintech', label: 'Fintech' },
  { id: 'startup', label: 'Startup' },
  { id: 'vc', label: 'Levées' },
  { id: 'banking', label: 'Banque' },
  { id: 'crypto', label: 'Crypto' },
];

export default function NewsScreen() {
  const [selectedZone, setSelectedZone] = useState('all');
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState('all');
  const [page, setPage] = useState(1);
  
  // Get countries for selected zone
  const getZoneCountries = (): string[] => {
    if (selectedZone === 'all') return [];
    const zone = ECONOMIC_ZONES.find(z => z.id === selectedZone);
    return zone?.countries || [];
  };
  
  // Build country filter
  const getCountryFilter = (): string | undefined => {
    if (selectedCountry) return selectedCountry;
    const zoneCountries = getZoneCountries();
    if (zoneCountries.length > 0) return zoneCountries.join(',');
    return undefined;
  };
  
  // Fetch news with zone/country filter
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['news', selectedZone, selectedCountry, selectedTag, page],
    queryFn: () =>
      api.getNewsFeed({
        page,
        page_size: 20,
        country: getCountryFilter(),
        tag: selectedTag !== 'all' ? selectedTag : undefined,
      }),
  });
  
  // Handle zone selection
  const handleZoneSelect = (zoneId: string) => {
    setSelectedZone(zoneId);
    setSelectedCountry(null); // Reset country when zone changes
    setPage(1);
  };
  
  // Handle country selection
  const handleCountrySelect = (countryId: string) => {
    if (countryId === 'all') {
      setSelectedCountry(null);
    } else {
      setSelectedCountry(countryId);
    }
    setPage(1);
  };
  
  const renderItem = ({ item, index }: { item: NewsArticle; index: number }) => (
    <NewsCard
      article={item}
      variant={index === 0 ? 'featured' : 'default'}
    />
  );
  
  const renderHeader = () => (
    <>
      {/* Zone économique Filter (CEMAC, UEMOA, Maghreb, etc.) */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterScrollView}
        contentContainerStyle={styles.filterContent}
      >
        {ECONOMIC_ZONES.map((zone) => (
          <TouchableOpacity
            key={zone.id}
            style={[
              styles.regionChip,
              selectedZone === zone.id && styles.regionChipActive,
            ]}
            onPress={() => handleZoneSelect(zone.id)}
          >
            <Text style={styles.regionEmoji}>{zone.emoji}</Text>
            <Text
              style={[
                styles.regionText,
                selectedZone === zone.id && styles.regionTextActive,
              ]}
            >
              {zone.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      
      {/* Country Filter (pays francophones d'abord) */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.countryScrollView}
        contentContainerStyle={styles.filterContent}
      >
        {REGIONS.map((region) => (
          <TouchableOpacity
            key={region.id}
            style={[
              styles.countryChip,
              (selectedCountry === region.id || (!selectedCountry && region.id === 'all')) && styles.countryChipActive,
            ]}
            onPress={() => handleCountrySelect(region.id)}
          >
            <Text style={styles.regionEmoji}>{region.emoji}</Text>
            <Text
              style={[
                styles.countryText,
                (selectedCountry === region.id || (!selectedCountry && region.id === 'all')) && styles.countryTextActive,
              ]}
            >
              {region.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      
      {/* Tag Filter */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tagScrollView}
        contentContainerStyle={styles.filterContent}
      >
        {TAGS.map((tag) => (
          <TouchableOpacity
            key={tag.id}
            style={[
              styles.tagChip,
              selectedTag === tag.id && styles.tagChipActive,
            ]}
            onPress={() => {
              setSelectedTag(tag.id);
              setPage(1);
            }}
          >
            <Text
              style={[
                styles.tagText,
                selectedTag === tag.id && styles.tagTextActive,
              ]}
            >
              {tag.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Actualités</Text>
        <Text style={styles.subtitle}>Fintech & Startups Afrique</Text>
      </View>
      
      {isLoading ? (
        <LoadingSpinner fullScreen message="Chargement des actualités..." />
      ) : (
        <FlatList
          data={data?.data || []}
          renderItem={renderItem}
          keyExtractor={(item) => item.slug}
          ListHeaderComponent={renderHeader}
          ListEmptyComponent={
            <EmptyState
              icon="newspaper-outline"
              title="Aucune actualité"
              description="Revenez plus tard pour les dernières nouvelles"
            />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#19D38C"
            />
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 4,
  },
  filterScrollView: {
    marginBottom: 12,
  },
  tagScrollView: {
    marginBottom: 20,
  },
  countryScrollView: {
    marginBottom: 12,
  },
  filterContent: {
    paddingHorizontal: 20,
    gap: 8,
  },
  regionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 8,
    gap: 6,
  },
  regionChipActive: {
    backgroundColor: '#19D38C20',
    borderWidth: 1,
    borderColor: '#19D38C',
  },
  regionEmoji: {
    fontSize: 16,
  },
  regionText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#94A3B8',
  },
  regionTextActive: {
    color: '#19D38C',
  },
  countryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#151B24',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 6,
    gap: 4,
  },
  countryChipActive: {
    backgroundColor: '#19D38C15',
    borderWidth: 1,
    borderColor: '#19D38C50',
  },
  countryText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#64748B',
  },
  countryTextActive: {
    color: '#19D38C',
  },
  tagChip: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
  },
  tagChipActive: {
    backgroundColor: '#8B5CF620',
    borderWidth: 1,
    borderColor: '#8B5CF6',
  },
  tagText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#94A3B8',
  },
  tagTextActive: {
    color: '#8B5CF6',
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
});
