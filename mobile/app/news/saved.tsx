/**
 * MarketGPS Mobile - Saved Articles Screen
 * Affiche les articles sauvegardés par l'utilisateur
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, NewsArticle } from '@/lib/api';
import { NewsCard, LoadingSpinner, EmptyState } from '@/components/ui';
import * as Haptics from 'expo-haptics';

export default function SavedArticlesScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  // Fetch saved articles
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['saved-articles', page],
    queryFn: () => api.getSavedArticles({ page, page_size: 20 }),
  });

  // Handle unsave from list
  const handleSaveToggle = (articleId: number, isSaved: boolean) => {
    if (!isSaved) {
      // Article was unsaved, refresh the list
      refetch();
    }
  };

  const renderItem = ({ item }: { item: NewsArticle }) => (
    <NewsCard
      article={{ ...item, is_saved: true }}
      variant="default"
      showSaveButton={true}
      onSaveToggle={handleSaveToggle}
    />
  );

  const renderHeader = () => (
    <View style={styles.headerInfo}>
      <Ionicons name="bookmark" size={20} color="#19D38C" />
      <Text style={styles.headerText}>
        {data?.total || 0} article{(data?.total || 0) > 1 ? 's' : ''} sauvegardé{(data?.total || 0) > 1 ? 's' : ''}
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header with back button */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
        >
          <Ionicons name="arrow-back" size={24} color="#F1F5F9" />
        </TouchableOpacity>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>Articles Sauvegardés</Text>
          <Text style={styles.subtitle}>Vos articles favoris</Text>
        </View>
      </View>

      {isLoading ? (
        <LoadingSpinner fullScreen message="Chargement des articles..." />
      ) : (
        <FlatList
          data={data?.data || []}
          renderItem={renderItem}
          keyExtractor={(item) => item.slug}
          ListHeaderComponent={renderHeader}
          ListEmptyComponent={
            <EmptyState
              icon="bookmark-outline"
              title="Aucun article sauvegardé"
              description="Appuyez sur l'icône signet sur un article pour le sauvegarder"
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
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1E293B',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  subtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  headerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 16,
    paddingHorizontal: 4,
  },
  headerText: {
    fontSize: 14,
    color: '#94A3B8',
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
});
