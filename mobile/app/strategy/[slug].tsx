/**
 * MarketGPS Mobile - Strategy Template Detail Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useNavigation, useRouter, Stack } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api, StrategyTemplate, Asset } from '@/lib/api';
import { Card, AssetCard, LoadingSpinner, EmptyState, Button } from '@/components/ui';
import { getScoreColor } from '@/lib/config';

export default function StrategyDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const navigation = useNavigation();
  const router = useRouter();
  const [selectedBlock, setSelectedBlock] = useState<string | null>(null);
  
  // Fetch strategy template
  const { data: template, isLoading } = useQuery({
    queryKey: ['strategy', 'template', slug],
    queryFn: () => api.getStrategyTemplate(slug!),
    enabled: !!slug && slug !== 'barbell',
  });
  
  // Fetch eligible instruments for selected block
  const { data: instruments, isLoading: instrumentsLoading } = useQuery({
    queryKey: ['strategy', 'instruments', selectedBlock],
    queryFn: () => api.getEligibleInstruments(selectedBlock!, 30),
    enabled: !!selectedBlock,
  });
  
  // Update navigation title
  React.useLayoutEffect(() => {
    navigation.setOptions({
      headerTitle: template?.name || 'Stratégie',
    });
  }, [template, navigation]);
  
  if (slug === 'barbell') {
    // Redirect handled by barbell.tsx
    return null;
  }
  
  if (isLoading) {
    return <LoadingSpinner fullScreen message="Chargement..." />;
  }
  
  if (!template) {
    return (
      <View style={styles.errorContainer}>
        <EmptyState
          icon="layers-outline"
          title="Stratégie introuvable"
          description="Cette stratégie n'existe pas ou a été supprimée"
        />
      </View>
    );
  }
  
  const blocks = template.structure?.blocks || [];
  
  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: template.name,
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />
      
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <Card style={styles.headerCard}>
          <Text style={styles.templateName}>{template.name}</Text>
          <Text style={styles.templateDescription}>{template.description}</Text>
          
          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Ionicons name="shield-outline" size={16} color="#64748B" />
              <Text style={styles.metaText}>
                Risque: {template.risk_level === 'low' ? 'Faible' :
                         template.risk_level === 'moderate' ? 'Modéré' :
                         template.risk_level === 'high' ? 'Élevé' : 'Très élevé'}
              </Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="time-outline" size={16} color="#64748B" />
              <Text style={styles.metaText}>Horizon: {template.horizon_years} ans</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="refresh-outline" size={16} color="#64748B" />
              <Text style={styles.metaText}>{template.rebalance_frequency}</Text>
            </View>
          </View>
        </Card>
        
        {/* Blocks Structure */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Structure</Text>
          
          {/* Allocation Bar */}
          <Card padding="sm" style={styles.allocationCard}>
            <View style={styles.allocationBar}>
              {blocks.map((block, index) => (
                <TouchableOpacity
                  key={block.name}
                  style={[
                    styles.allocationSegment,
                    {
                      flex: block.weight,
                      backgroundColor: getBlockColor(index),
                    },
                    selectedBlock === block.name && styles.allocationSegmentSelected,
                  ]}
                  onPress={() => setSelectedBlock(
                    selectedBlock === block.name ? null : block.name
                  )}
                >
                  <Text style={styles.allocationSegmentText}>
                    {Math.round(block.weight * 100)}%
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </Card>
          
          {/* Block Cards */}
          {blocks.map((block, index) => (
            <TouchableOpacity
              key={block.name}
              style={[
                styles.blockCard,
                selectedBlock === block.name && styles.blockCardSelected,
              ]}
              onPress={() => setSelectedBlock(
                selectedBlock === block.name ? null : block.name
              )}
              activeOpacity={0.7}
            >
              <View style={styles.blockHeader}>
                <View style={[styles.blockDot, { backgroundColor: getBlockColor(index) }]} />
                <View style={styles.blockInfo}>
                  <Text style={styles.blockLabel}>{block.label}</Text>
                  <Text style={styles.blockDescription}>{block.description}</Text>
                </View>
                <Text style={styles.blockWeight}>{Math.round(block.weight * 100)}%</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
        
        {/* Eligible Instruments */}
        {selectedBlock && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Instruments éligibles: {blocks.find(b => b.name === selectedBlock)?.label}
              </Text>
              <TouchableOpacity onPress={() => setSelectedBlock(null)}>
                <Ionicons name="close-circle-outline" size={24} color="#64748B" />
              </TouchableOpacity>
            </View>
            
            {instrumentsLoading ? (
              <LoadingSpinner message="Chargement des instruments..." />
            ) : instruments && instruments.length > 0 ? (
              instruments.map((asset: Asset) => (
                <AssetCard
                  key={asset.asset_id || asset.symbol}
                  asset={asset}
                  showWatchlistButton
                />
              ))
            ) : (
              <EmptyState
                icon="cube-outline"
                title="Aucun instrument"
                description="Aucun instrument éligible pour ce bloc"
              />
            )}
          </View>
        )}
        
        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <Button
            title="Créer ma stratégie"
            onPress={() => {
              router.push({
                pathname: '/strategy/create',
                params: { template: template.slug },
              });
            }}
            fullWidth
            icon={<Ionicons name="create-outline" size={20} color="#0A0F1C" />}
          />
          <Button
            title="Simuler ce template"
            onPress={() => {
              Alert.alert(
                'Simulation rapide',
                'Cette fonctionnalité permet de tester le template avec les allocations par défaut. Pour personnaliser, utilisez "Créer ma stratégie".',
                [{ text: 'OK' }]
              );
            }}
            variant="outline"
            fullWidth
            icon={<Ionicons name="play-outline" size={20} color="#19D38C" />}
            style={styles.simulateButton}
          />
        </View>
      </ScrollView>
    </>
  );
}

function getBlockColor(index: number): string {
  const colors = ['#19D38C', '#8B5CF6', '#22C55E', '#F59E0B', '#EF4444', '#EC4899'];
  return colors[index % colors.length];
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
  errorContainer: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  headerCard: {
    marginBottom: 24,
  },
  templateName: {
    fontSize: 24,
    fontWeight: '800',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  templateDescription: {
    fontSize: 15,
    color: '#94A3B8',
    lineHeight: 22,
    marginBottom: 16,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 13,
    color: '#64748B',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 12,
  },
  allocationCard: {
    marginBottom: 16,
  },
  allocationBar: {
    flexDirection: 'row',
    height: 48,
    borderRadius: 10,
    overflow: 'hidden',
  },
  allocationSegment: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRightWidth: 1,
    borderRightColor: '#0A0F1C',
  },
  allocationSegmentSelected: {
    transform: [{ scaleY: 1.1 }],
  },
  allocationSegmentText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0A0F1C',
  },
  blockCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  blockCardSelected: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  blockHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  blockDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  blockInfo: {
    flex: 1,
    marginLeft: 12,
  },
  blockLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  blockDescription: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  blockWeight: {
    fontSize: 16,
    fontWeight: '700',
    color: '#19D38C',
  },
  actionButtons: {
    gap: 12,
    marginTop: 8,
  },
  simulateButton: {
    marginTop: 0,
  },
});
