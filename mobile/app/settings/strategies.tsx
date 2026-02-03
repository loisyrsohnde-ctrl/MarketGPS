/**
 * MarketGPS Mobile - Strategies Screen
 * Avec stratégies personnalisées utilisateur
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, StrategyTemplate, UserStrategy } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState } from '@/components/ui';
import { useIsAuthenticated } from '@/store/auth';

const RISK_COLORS: Record<string, string> = {
  low: '#22C55E',
  moderate: '#EAB308',
  high: '#F97316',
  very_high: '#EF4444',
};

export default function StrategiesScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const isAuthenticated = useIsAuthenticated();

  // Fetch strategy templates
  const { data: templates, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['strategies', 'templates'],
    queryFn: () => api.getStrategyTemplates(),
  });

  // Fetch user's saved strategies
  const { data: userStrategies, isLoading: userStrategiesLoading, refetch: refetchUser } = useQuery({
    queryKey: ['user-strategies'],
    queryFn: () => api.getUserStrategies(),
    enabled: isAuthenticated,
  });

  // Delete user strategy mutation
  const deleteMutation = useMutation({
    mutationFn: (strategyId: string) => api.deleteUserStrategy(strategyId),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['user-strategies'] });
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de supprimer la stratégie');
    },
  });

  const handleTemplatePress = (template: StrategyTemplate) => {
    router.push(`/strategy/${template.slug}`);
  };

  const handleUserStrategyPress = (strategy: UserStrategy) => {
    // Navigate to view/edit the user strategy
    router.push(`/strategy/create?id=${strategy.id}`);
  };

  const handleDeleteStrategy = (strategy: UserStrategy) => {
    Alert.alert(
      'Supprimer la stratégie',
      `Êtes-vous sûr de vouloir supprimer "${strategy.name}" ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(strategy.id),
        },
      ]
    );
  };

  const handleRefresh = async () => {
    await Promise.all([refetch(), isAuthenticated ? refetchUser() : Promise.resolve()]);
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Chargement des stratégies..." />;
  }
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={handleRefresh}
          tintColor="#19D38C"
        />
      }
    >
      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.quickAction}
          onPress={() => router.push('/strategy/barbell')}
        >
          <View style={[styles.quickActionIcon, { backgroundColor: '#19D38C20' }]}>
            <Ionicons name="barbell-outline" size={28} color="#19D38C" />
          </View>
          <View style={styles.quickActionContent}>
            <Text style={styles.quickActionTitle}>Barbell Builder</Text>
            <Text style={styles.quickActionSubtitle}>Core + Satellite</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#64748B" />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.quickAction, { marginTop: 12 }]}
          onPress={() => router.push('/strategy/barbell-saved')}
        >
          <View style={[styles.quickActionIcon, { backgroundColor: '#8B5CF620' }]}>
            <Ionicons name="folder-outline" size={28} color="#8B5CF6" />
          </View>
          <View style={styles.quickActionContent}>
            <Text style={styles.quickActionTitle}>Portfolios Barbell</Text>
            <Text style={styles.quickActionSubtitle}>Mes portfolios sauvegardés</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#64748B" />
        </TouchableOpacity>
      </View>

      {/* User Strategies Section */}
      {isAuthenticated && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Mes Stratégies</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                // Show template picker or go to create directly
                if (templates && templates.length > 0) {
                  Alert.alert(
                    'Nouvelle Stratégie',
                    'Choisissez un template pour commencer',
                    [
                      ...templates.slice(0, 3).map((t) => ({
                        text: t.name,
                        onPress: () => router.push(`/strategy/create?template=${t.slug}` as any),
                      })),
                      { text: 'Annuler', style: 'cancel' as const },
                    ]
                  );
                }
              }}
            >
              <Ionicons name="add-circle" size={24} color="#19D38C" />
            </TouchableOpacity>
          </View>

          {userStrategiesLoading ? (
            <View style={styles.loadingContainer}>
              <LoadingSpinner message="Chargement..." />
            </View>
          ) : userStrategies && userStrategies.length > 0 ? (
            userStrategies.map((strategy) => (
              <TouchableOpacity
                key={strategy.id}
                style={styles.userStrategyCard}
                onPress={() => handleUserStrategyPress(strategy)}
                activeOpacity={0.7}
              >
                <View style={styles.userStrategyHeader}>
                  <View style={styles.userStrategyInfo}>
                    <Text style={styles.userStrategyName}>{strategy.name}</Text>
                    {strategy.risk_level && (
                      <View
                        style={[
                          styles.riskBadge,
                          { backgroundColor: `${RISK_COLORS[strategy.risk_level] || '#64748B'}20` },
                        ]}
                      >
                        <Text
                          style={[
                            styles.riskText,
                            { color: RISK_COLORS[strategy.risk_level] || '#64748B' },
                          ]}
                        >
                          {strategy.risk_level === 'low' ? 'Faible' :
                           strategy.risk_level === 'moderate' ? 'Modéré' :
                           strategy.risk_level === 'high' ? 'Élevé' : 'Très élevé'}
                        </Text>
                      </View>
                    )}
                  </View>
                  <TouchableOpacity
                    style={styles.deleteButton}
                    onPress={() => handleDeleteStrategy(strategy)}
                  >
                    <Ionicons name="trash-outline" size={18} color="#EF4444" />
                  </TouchableOpacity>
                </View>

                {strategy.description && (
                  <Text style={styles.userStrategyDescription} numberOfLines={2}>
                    {strategy.description}
                  </Text>
                )}

                {strategy.blocks && strategy.blocks.length > 0 && (
                  <View style={styles.blocksPreview}>
                    {strategy.blocks.slice(0, 3).map((block, index) => (
                      <View key={index} style={styles.blockChip}>
                        <Text style={styles.blockChipText}>
                          {block.label} ({Math.round((block.weight || 0) * 100)}%)
                        </Text>
                      </View>
                    ))}
                    {strategy.blocks.length > 3 && (
                      <View style={styles.blockChip}>
                        <Text style={styles.blockChipText}>
                          +{strategy.blocks.length - 3}
                        </Text>
                      </View>
                    )}
                  </View>
                )}

                <Text style={styles.dateText}>
                  Créée le {new Date(strategy.created_at).toLocaleDateString('fr-FR')}
                </Text>
              </TouchableOpacity>
            ))
          ) : (
            <View style={styles.emptyUserStrategies}>
              <Ionicons name="sparkles-outline" size={40} color="#64748B" />
              <Text style={styles.emptyTitle}>Aucune stratégie personnalisée</Text>
              <Text style={styles.emptySubtitle}>
                Personnalisez un template pour créer votre propre stratégie
              </Text>
            </View>
          )}
        </View>
      )}
      
      {/* Templates Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Templates de Stratégies</Text>
        
        {templates && templates.length > 0 ? (
          templates.map((template) => (
            <TouchableOpacity
              key={template.id}
              style={styles.templateCard}
              onPress={() => handleTemplatePress(template)}
              activeOpacity={0.7}
            >
              <View style={styles.templateHeader}>
                <Text style={styles.templateName}>{template.name}</Text>
                <View
                  style={[
                    styles.riskBadge,
                    { backgroundColor: `${RISK_COLORS[template.risk_level] || '#64748B'}20` },
                  ]}
                >
                  <Text
                    style={[
                      styles.riskText,
                      { color: RISK_COLORS[template.risk_level] || '#64748B' },
                    ]}
                  >
                    {template.risk_level === 'low' ? 'Faible' :
                     template.risk_level === 'moderate' ? 'Modéré' :
                     template.risk_level === 'high' ? 'Élevé' : 'Très élevé'}
                  </Text>
                </View>
              </View>
              
              <Text style={styles.templateDescription} numberOfLines={2}>
                {template.description}
              </Text>
              
              <View style={styles.templateMeta}>
                <View style={styles.metaItem}>
                  <Ionicons name="time-outline" size={14} color="#64748B" />
                  <Text style={styles.metaText}>{template.horizon_years} ans</Text>
                </View>
                <View style={styles.metaItem}>
                  <Ionicons name="refresh-outline" size={14} color="#64748B" />
                  <Text style={styles.metaText}>{template.rebalance_frequency}</Text>
                </View>
                <View style={styles.metaItem}>
                  <Ionicons name="layers-outline" size={14} color="#64748B" />
                  <Text style={styles.metaText}>
                    {template.structure?.blocks?.length || 0} blocs
                  </Text>
                </View>
              </View>
              
              {/* Blocks Preview */}
              {template.structure?.blocks && (
                <View style={styles.blocksPreview}>
                  {template.structure.blocks.slice(0, 3).map((block, index) => (
                    <View key={index} style={styles.blockChip}>
                      <Text style={styles.blockChipText}>
                        {block.label} ({Math.round(block.weight * 100)}%)
                      </Text>
                    </View>
                  ))}
                  {template.structure.blocks.length > 3 && (
                    <View style={styles.blockChip}>
                      <Text style={styles.blockChipText}>
                        +{template.structure.blocks.length - 3}
                      </Text>
                    </View>
                  )}
                </View>
              )}
            </TouchableOpacity>
          ))
        ) : (
          <EmptyState
            icon="layers-outline"
            title="Aucune stratégie"
            description="Les templates de stratégies seront disponibles prochainement"
          />
        )}
      </View>
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
  quickActions: {
    marginBottom: 24,
  },
  quickAction: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionContent: {
    flex: 1,
    marginLeft: 16,
  },
  quickActionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  quickActionSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  addButton: {
    padding: 4,
  },
  loadingContainer: {
    padding: 20,
    alignItems: 'center',
  },
  userStrategyCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  userStrategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  userStrategyInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flexWrap: 'wrap',
  },
  userStrategyName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  userStrategyDescription: {
    fontSize: 13,
    color: '#94A3B8',
    lineHeight: 18,
    marginBottom: 12,
  },
  deleteButton: {
    padding: 6,
    marginLeft: 8,
  },
  dateText: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 8,
  },
  emptyUserStrategies: {
    backgroundColor: '#151B24',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#94A3B8',
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
  },
  templateCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
  },
  templateHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  templateName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#F1F5F9',
    flex: 1,
  },
  riskBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  riskText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  templateDescription: {
    fontSize: 14,
    color: '#94A3B8',
    lineHeight: 20,
    marginBottom: 12,
  },
  templateMeta: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 12,
    color: '#64748B',
  },
  blocksPreview: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  blockChip: {
    backgroundColor: '#334155',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  blockChipText: {
    fontSize: 11,
    color: '#94A3B8',
  },
});
