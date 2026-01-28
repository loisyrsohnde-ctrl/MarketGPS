/**
 * MarketGPS Mobile - Explorer Screen
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api, Asset } from '@/lib/api';
import { AssetCard, LoadingSpinner, EmptyState } from '@/components/ui';
import { MARKET_SCOPES, ASSET_TYPES, type MarketScope, type AssetType } from '@/lib/config';
import { useDebounce } from '@/hooks';

// Country code to name mapping
const COUNTRY_NAMES: Record<string, string> = {
  MA: 'Maroc', DZ: 'Algérie', TN: 'Tunisie', EG: 'Égypte', LY: 'Libye',
  NG: 'Nigeria', GH: 'Ghana', SN: 'Sénégal', CI: 'Côte d\'Ivoire',
  BF: 'Burkina Faso', ML: 'Mali', NE: 'Niger', TG: 'Togo', BJ: 'Bénin',
  CM: 'Cameroun', GA: 'Gabon', CG: 'Congo', TD: 'Tchad', CF: 'Centrafrique',
  GQ: 'Guinée Éq.', CD: 'RD Congo', KE: 'Kenya', TZ: 'Tanzanie',
  UG: 'Ouganda', RW: 'Rwanda', ET: 'Éthiopie', ZA: 'Afrique du Sud',
  AO: 'Angola', MZ: 'Mozambique', ZW: 'Zimbabwe', NA: 'Namibie', BW: 'Botswana',
};

const REGION_NAMES: Record<string, string> = {
  NORTH: 'Afrique du Nord',
  WEST: 'Afrique de l\'Ouest',
  CENTRAL: 'Afrique Centrale',
  EAST: 'Afrique de l\'Est',
  SOUTH: 'Afrique Australe',
};

const PAGE_SIZE = 30;

export default function ExplorerScreen() {
  // Get URL params for filtered navigation
  const params = useLocalSearchParams<{
    market_scope?: string;
    country?: string;
    region?: string;
  }>();

  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScope, setSelectedScope] = useState<MarketScope>(
    (params.market_scope as MarketScope) || 'US_EU'
  );
  const [selectedType, setSelectedType] = useState<AssetType | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(params.country || null);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(params.region || null);

  // Update filters when URL params change
  useEffect(() => {
    if (params.market_scope) {
      setSelectedScope(params.market_scope as MarketScope);
    }
    if (params.country) {
      setSelectedCountry(params.country);
      setSelectedScope('AFRICA');
    }
    if (params.region) {
      setSelectedRegion(params.region);
      setSelectedScope('AFRICA');
    }
  }, [params.market_scope, params.country, params.region]);

  // Infinite query for pagination
  const {
    data,
    isLoading,
    refetch,
    isRefetching,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['explorer', selectedScope, selectedType, selectedCountry, selectedRegion, searchQuery],
    queryFn: ({ pageParam = 1 }) =>
      api.getExplorer({
        market_scope: selectedScope,
        asset_type: selectedType ?? undefined,
        country: selectedCountry ?? undefined,
        region: selectedRegion ?? undefined,
        query: searchQuery || undefined,
        page: pageParam,
        page_size: PAGE_SIZE,
      }),
    getNextPageParam: (lastPage, allPages) => {
      const totalPages = Math.ceil(lastPage.total / PAGE_SIZE);
      const nextPage = allPages.length + 1;
      return nextPage <= totalPages ? nextPage : undefined;
    },
    initialPageParam: 1,
  });

  // Flatten all pages into single array
  const allAssets = useMemo(() => {
    if (!data?.pages) return [];
    return data.pages.flatMap(page => page.data);
  }, [data?.pages]);

  // Total count from first page
  const totalCount = data?.pages?.[0]?.total ?? 0;

  // Debounced search
  const debouncedSearch = useDebounce((text: string) => {
    setSearchQuery(text);
  }, 300);

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);
  
  const renderItem = ({ item }: { item: Asset }) => (
    <AssetCard asset={item} showWatchlistButton />
  );
  
  // Clear all Africa filters
  const clearAfricaFilters = useCallback(() => {
    setSelectedCountry(null);
    setSelectedRegion(null);
  }, []);

  // Get active filter label
  const getActiveFilterLabel = () => {
    if (selectedCountry) {
      return COUNTRY_NAMES[selectedCountry] || selectedCountry;
    }
    if (selectedRegion) {
      return REGION_NAMES[selectedRegion] || selectedRegion;
    }
    return null;
  };

  const activeFilterLabel = getActiveFilterLabel();

  const renderHeader = () => (
    <>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search-outline" size={20} color="#64748B" />
        <TextInput
          style={styles.searchInput}
          placeholder="Rechercher un actif..."
          placeholderTextColor="#64748B"
          onChangeText={debouncedSearch}
          returnKeyType="search"
        />
      </View>

      {/* Active Filter Banner */}
      {activeFilterLabel && (
        <View style={styles.activeFilterBanner}>
          <View style={styles.activeFilterContent}>
            <Ionicons name="location-outline" size={16} color="#19D38C" />
            <Text style={styles.activeFilterText}>
              Filtré par : <Text style={styles.activeFilterValue}>{activeFilterLabel}</Text>
            </Text>
          </View>
          <TouchableOpacity
            style={styles.clearFilterButton}
            onPress={clearAfricaFilters}
          >
            <Ionicons name="close-circle" size={20} color="#64748B" />
          </TouchableOpacity>
        </View>
      )}

      {/* Scope Filter */}
      <View style={styles.filterRow}>
        {Object.keys(MARKET_SCOPES).map((scope) => (
          <TouchableOpacity
            key={scope}
            style={[
              styles.filterChip,
              selectedScope === scope && styles.filterChipActive,
            ]}
            onPress={() => {
              setSelectedScope(scope as MarketScope);
              // Clear Africa filters when switching to US_EU
              if (scope === 'US_EU') {
                setSelectedCountry(null);
                setSelectedRegion(null);
              }
            }}
          >
            <Text
              style={[
                styles.filterChipText,
                selectedScope === scope && styles.filterChipTextActive,
              ]}
            >
              {scope === 'US_EU' ? 'US/EU' : 'Afrique'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Type Filter */}
      <View style={styles.filterRow}>
        <TouchableOpacity
          style={[styles.filterChip, !selectedType && styles.filterChipActive]}
          onPress={() => {
            setSelectedType(null);
          }}
        >
          <Text style={[styles.filterChipText, !selectedType && styles.filterChipTextActive]}>
            Tous
          </Text>
        </TouchableOpacity>
        {ASSET_TYPES.slice(0, 4).map((type) => (
          <TouchableOpacity
            key={type}
            style={[styles.filterChip, selectedType === type && styles.filterChipActive]}
            onPress={() => {
              setSelectedType(type);
            }}
          >
            <Text
              style={[
                styles.filterChipText,
                selectedType === type && styles.filterChipTextActive,
              ]}
            >
              {type}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Results count */}
      {totalCount > 0 && (
        <Text style={styles.resultsCount}>
          {totalCount.toLocaleString()} actifs trouvés
        </Text>
      )}
    </>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Explorer</Text>
      </View>
      
      {isLoading ? (
        <LoadingSpinner fullScreen message="Chargement des actifs..." />
      ) : (
        <FlatList
          data={allAssets}
          renderItem={renderItem}
          keyExtractor={(item, index) => `${item.asset_id || item.symbol}-${index}`}
          ListHeaderComponent={renderHeader}
          ListEmptyComponent={
            <EmptyState
              icon="search-outline"
              title="Aucun résultat"
              description="Modifiez vos filtres ou effectuez une nouvelle recherche"
            />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching && !isFetchingNextPage}
              onRefresh={refetch}
              tintColor="#19D38C"
            />
          }
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.3}
          ListFooterComponent={
            isFetchingNextPage ? (
              <View style={styles.loadingMore}>
                <ActivityIndicator size="small" color="#19D38C" />
                <Text style={styles.loadingMoreText}>Chargement...</Text>
              </View>
            ) : hasNextPage ? (
              <View style={styles.loadMoreHint}>
                <Text style={styles.loadMoreHintText}>Faites défiler pour plus</Text>
              </View>
            ) : allAssets.length > 0 ? (
              <View style={styles.endOfList}>
                <Text style={styles.endOfListText}>Fin des résultats</Text>
              </View>
            ) : null
          }
          removeClippedSubviews={true}
          maxToRenderPerBatch={15}
          windowSize={10}
          initialNumToRender={15}
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
  listContent: {
    padding: 20,
    paddingTop: 0,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 12,
    fontSize: 16,
    color: '#F1F5F9',
  },
  activeFilterBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#19D38C15',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#19D38C40',
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 12,
  },
  activeFilterContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  activeFilterText: {
    fontSize: 13,
    color: '#94A3B8',
  },
  activeFilterValue: {
    color: '#19D38C',
    fontWeight: '600',
  },
  clearFilterButton: {
    padding: 4,
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#1E293B',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  filterChipActive: {
    backgroundColor: '#19D38C20',
    borderColor: '#19D38C',
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#94A3B8',
  },
  filterChipTextActive: {
    color: '#19D38C',
  },
  resultsCount: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 16,
  },
  loadingMore: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  loadingMoreText: {
    fontSize: 13,
    color: '#64748B',
  },
  loadMoreHint: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  loadMoreHintText: {
    fontSize: 12,
    color: '#475569',
  },
  endOfList: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  endOfListText: {
    fontSize: 12,
    color: '#475569',
  },
});
