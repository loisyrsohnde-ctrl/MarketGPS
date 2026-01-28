/**
 * MarketGPS Mobile - Strategies Screen
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
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api, StrategyTemplate } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState } from '@/components/ui';

const RISK_COLORS: Record<string, string> = {
  low: '#22C55E',
  moderate: '#EAB308',
  high: '#F97316',
  very_high: '#EF4444',
};

export default function StrategiesScreen() {
  const router = useRouter();
  
  // Fetch strategy templates
  const { data: templates, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['strategies', 'templates'],
    queryFn: () => api.getStrategyTemplates(),
  });
  
  const handleTemplatePress = (template: StrategyTemplate) => {
    router.push(`/strategy/${template.slug}`);
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
          onRefresh={refetch}
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
      </View>
      
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
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 16,
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
