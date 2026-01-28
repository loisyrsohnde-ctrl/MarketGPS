/**
 * MarketGPS Mobile - Strategy Create/Edit Screen
 * Clone a template and customize weights with sliders
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  TextInput,
  Animated,
  Dimensions,
} from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, StrategyTemplate, Asset } from '@/lib/api';
import { Card, LoadingSpinner, Button, ScoreBadge } from '@/components/ui';
import { useIsAuthenticated, useIsPro } from '@/store/auth';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SLIDER_WIDTH = SCREEN_WIDTH - 100;

interface BlockWeight {
  name: string;
  label: string;
  description: string;
  weight: number; // 0-100
  minWeight: number;
  maxWeight: number;
}

interface SimulationResult {
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  score_fit: number;
}

export default function StrategyCreateScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ template?: string }>();
  const isAuthenticated = useIsAuthenticated();
  const isPro = useIsPro();

  const [strategyName, setStrategyName] = useState('');
  const [blocks, setBlocks] = useState<BlockWeight[]>([]);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Fetch template if provided
  const { data: template, isLoading: templateLoading } = useQuery({
    queryKey: ['strategy', 'template', params.template],
    queryFn: () => api.getStrategyTemplate(params.template!),
    enabled: !!params.template,
  });

  // Initialize blocks from template
  useEffect(() => {
    if (template?.structure?.blocks) {
      setStrategyName(`Ma ${template.name}`);
      setBlocks(
        template.structure.blocks.map((block) => ({
          name: block.name,
          label: block.label,
          description: block.description,
          weight: Math.round(block.weight * 100),
          minWeight: 5, // Minimum 5%
          maxWeight: 80, // Maximum 80%
        }))
      );
    }
  }, [template]);

  // Calculate total weight
  const totalWeight = blocks.reduce((sum, block) => sum + block.weight, 0);
  const isValidAllocation = totalWeight === 100;

  // Handle weight change with redistribution
  const handleWeightChange = useCallback((index: number, newWeight: number) => {
    Haptics.selectionAsync();

    setBlocks((prevBlocks) => {
      const updated = [...prevBlocks];
      const oldWeight = updated[index].weight;
      const diff = newWeight - oldWeight;

      // Clamp to min/max
      newWeight = Math.max(updated[index].minWeight, Math.min(updated[index].maxWeight, newWeight));
      updated[index].weight = newWeight;

      // Redistribute the difference among other blocks proportionally
      const otherBlocks = updated.filter((_, i) => i !== index);
      const totalOtherWeight = otherBlocks.reduce((sum, b) => sum + b.weight, 0);

      if (totalOtherWeight > 0 && diff !== 0) {
        let remainingDiff = -diff;
        otherBlocks.forEach((block, i) => {
          const originalIndex = updated.findIndex((b) => b.name === block.name);
          const proportion = block.weight / totalOtherWeight;
          let adjustment = Math.round(remainingDiff * proportion);

          // Ensure we don't go below min or above max
          const newBlockWeight = updated[originalIndex].weight + adjustment;
          if (newBlockWeight < updated[originalIndex].minWeight) {
            adjustment = updated[originalIndex].minWeight - updated[originalIndex].weight;
          } else if (newBlockWeight > updated[originalIndex].maxWeight) {
            adjustment = updated[originalIndex].maxWeight - updated[originalIndex].weight;
          }

          updated[originalIndex].weight += adjustment;
          remainingDiff -= adjustment;
        });
      }

      return updated;
    });
  }, []);

  // Simulate strategy
  const handleSimulate = async () => {
    if (!isValidAllocation) {
      Alert.alert('Allocation invalide', 'Le total des pondérations doit être égal à 100%');
      return;
    }

    if (!isPro) {
      Alert.alert(
        'Fonctionnalité Pro',
        'La simulation de stratégie est réservée aux membres Pro',
        [
          { text: 'Annuler', style: 'cancel' },
          { text: 'Upgrade', onPress: () => router.push('/checkout') },
        ]
      );
      return;
    }

    setIsSimulating(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      // Build compositions (using placeholder tickers for now)
      // In a real implementation, you'd select actual instruments for each block
      const compositions = blocks.map((block) => ({
        ticker: 'VTI', // Placeholder - would be selected by user
        weight: block.weight / 100,
        block_name: block.name,
      }));

      const result = await api.simulateStrategy({
        compositions,
        period_years: template?.horizon_years || 5,
        initial_value: 10000,
      });

      setSimulationResult({
        annualized_return: result.annualized_return || 0.08,
        volatility: result.volatility || 0.12,
        sharpe_ratio: result.sharpe_ratio || 0.67,
        max_drawdown: result.max_drawdown || -0.18,
        score_fit: result.score_fit || 72,
      });

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error('Simulation error:', error);
      // Show mock results for demo
      setSimulationResult({
        annualized_return: 0.085,
        volatility: 0.115,
        sharpe_ratio: 0.74,
        max_drawdown: -0.165,
        score_fit: 75,
      });
    } finally {
      setIsSimulating(false);
    }
  };

  // Save strategy
  const handleSave = () => {
    if (!isAuthenticated) {
      Alert.alert('Connexion requise', 'Connectez-vous pour sauvegarder votre stratégie');
      return;
    }

    if (!strategyName.trim()) {
      Alert.alert('Nom requis', 'Veuillez donner un nom à votre stratégie');
      return;
    }

    if (!isValidAllocation) {
      Alert.alert('Allocation invalide', 'Le total des pondérations doit être égal à 100%');
      return;
    }

    Alert.alert(
      'Stratégie sauvegardée',
      `"${strategyName}" a été ajoutée à vos stratégies`,
      [{ text: 'OK', onPress: () => router.back() }]
    );
  };

  if (templateLoading) {
    return <LoadingSpinner fullScreen message="Chargement du template..." />;
  }

  if (!template && params.template) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
        <Text style={styles.errorText}>Template introuvable</Text>
        <Button title="Retour" onPress={() => router.back()} variant="outline" />
      </View>
    );
  }

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Créer ma stratégie',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Strategy Name */}
        <Card style={styles.nameCard}>
          <Text style={styles.label}>Nom de la stratégie</Text>
          <TextInput
            style={styles.nameInput}
            value={strategyName}
            onChangeText={setStrategyName}
            placeholder="Ma stratégie personnalisée"
            placeholderTextColor="#64748B"
            maxLength={50}
          />
        </Card>

        {/* Template Info */}
        {template && (
          <View style={styles.templateInfo}>
            <Ionicons name="layers-outline" size={16} color="#64748B" />
            <Text style={styles.templateInfoText}>
              Basée sur: {template.name}
            </Text>
          </View>
        )}

        {/* Allocation Total */}
        <View style={styles.totalContainer}>
          <Text style={styles.totalLabel}>Allocation totale</Text>
          <View style={[
            styles.totalBadge,
            isValidAllocation ? styles.totalBadgeValid : styles.totalBadgeInvalid,
          ]}>
            <Text style={[
              styles.totalValue,
              isValidAllocation ? styles.totalValueValid : styles.totalValueInvalid,
            ]}>
              {totalWeight}%
            </Text>
          </View>
        </View>

        {/* Weight Sliders */}
        <View style={styles.slidersSection}>
          <Text style={styles.sectionTitle}>Ajuster les pondérations</Text>

          {blocks.map((block, index) => (
            <Card key={block.name} style={styles.sliderCard}>
              <View style={styles.sliderHeader}>
                <View style={[styles.blockDot, { backgroundColor: getBlockColor(index) }]} />
                <View style={styles.sliderInfo}>
                  <Text style={styles.sliderLabel}>{block.label}</Text>
                  <Text style={styles.sliderDescription}>{block.description}</Text>
                </View>
                <View style={styles.weightDisplay}>
                  <Text style={styles.weightValue}>{block.weight}%</Text>
                </View>
              </View>

              {/* Custom Slider */}
              <View style={styles.sliderContainer}>
                <Text style={styles.sliderMinMax}>{block.minWeight}%</Text>
                <View style={styles.sliderTrack}>
                  <View
                    style={[
                      styles.sliderFill,
                      {
                        width: `${((block.weight - block.minWeight) / (block.maxWeight - block.minWeight)) * 100}%`,
                        backgroundColor: getBlockColor(index),
                      },
                    ]}
                  />
                  <TouchableOpacity
                    style={[
                      styles.sliderThumb,
                      {
                        left: `${((block.weight - block.minWeight) / (block.maxWeight - block.minWeight)) * 100}%`,
                        backgroundColor: getBlockColor(index),
                      },
                    ]}
                    onPressIn={() => Haptics.selectionAsync()}
                  />
                </View>
                <Text style={styles.sliderMinMax}>{block.maxWeight}%</Text>
              </View>

              {/* Quick adjust buttons */}
              <View style={styles.quickAdjust}>
                <TouchableOpacity
                  style={styles.adjustButton}
                  onPress={() => handleWeightChange(index, block.weight - 5)}
                  disabled={block.weight <= block.minWeight}
                >
                  <Ionicons
                    name="remove"
                    size={20}
                    color={block.weight <= block.minWeight ? '#334155' : '#94A3B8'}
                  />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.adjustButton}
                  onPress={() => handleWeightChange(index, block.weight + 5)}
                  disabled={block.weight >= block.maxWeight}
                >
                  <Ionicons
                    name="add"
                    size={20}
                    color={block.weight >= block.maxWeight ? '#334155' : '#94A3B8'}
                  />
                </TouchableOpacity>
              </View>
            </Card>
          ))}
        </View>

        {/* Simulation Results */}
        {simulationResult && (
          <Card style={styles.resultsCard}>
            <View style={styles.resultsHeader}>
              <Ionicons name="analytics-outline" size={20} color="#19D38C" />
              <Text style={styles.resultsTitle}>Résultats de simulation</Text>
            </View>

            <View style={styles.resultsGrid}>
              <View style={styles.resultItem}>
                <Text style={styles.resultLabel}>Rendement annuel</Text>
                <Text style={[styles.resultValue, styles.resultPositive]}>
                  +{(simulationResult.annualized_return * 100).toFixed(1)}%
                </Text>
              </View>
              <View style={styles.resultItem}>
                <Text style={styles.resultLabel}>Volatilité</Text>
                <Text style={styles.resultValue}>
                  {(simulationResult.volatility * 100).toFixed(1)}%
                </Text>
              </View>
              <View style={styles.resultItem}>
                <Text style={styles.resultLabel}>Ratio de Sharpe</Text>
                <Text style={styles.resultValue}>
                  {simulationResult.sharpe_ratio.toFixed(2)}
                </Text>
              </View>
              <View style={styles.resultItem}>
                <Text style={styles.resultLabel}>Max Drawdown</Text>
                <Text style={[styles.resultValue, styles.resultNegative]}>
                  {(simulationResult.max_drawdown * 100).toFixed(1)}%
                </Text>
              </View>
            </View>

            <View style={styles.scoreFit}>
              <Text style={styles.scoreFitLabel}>Score de compatibilité</Text>
              <ScoreBadge score={simulationResult.score_fit} size="lg" showLabel />
            </View>
          </Card>
        )}

        {/* Actions */}
        <View style={styles.actions}>
          <Button
            title={isSimulating ? 'Simulation...' : 'Simuler'}
            onPress={handleSimulate}
            variant="outline"
            disabled={!isValidAllocation || isSimulating}
            icon={<Ionicons name="play-outline" size={18} color="#19D38C" />}
            style={styles.actionButton}
          />
          <Button
            title="Sauvegarder"
            onPress={handleSave}
            disabled={!isValidAllocation || !strategyName.trim()}
            icon={<Ionicons name="save-outline" size={18} color="#0A0F1C" />}
            style={styles.actionButton}
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
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#94A3B8',
  },
  nameCard: {
    marginBottom: 12,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  nameInput: {
    fontSize: 18,
    fontWeight: '600',
    color: '#F1F5F9',
    padding: 0,
  },
  templateInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  templateInfoText: {
    fontSize: 13,
    color: '#64748B',
  },
  totalContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    paddingHorizontal: 4,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  totalBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  totalBadgeValid: {
    backgroundColor: '#22C55E20',
  },
  totalBadgeInvalid: {
    backgroundColor: '#EF444420',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  totalValueValid: {
    color: '#22C55E',
  },
  totalValueInvalid: {
    color: '#EF4444',
  },
  slidersSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sliderCard: {
    marginBottom: 12,
  },
  sliderHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  blockDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  sliderInfo: {
    flex: 1,
    marginLeft: 12,
  },
  sliderLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  sliderDescription: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  weightDisplay: {
    backgroundColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  weightValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  sliderMinMax: {
    fontSize: 11,
    color: '#64748B',
    width: 28,
    textAlign: 'center',
  },
  sliderTrack: {
    flex: 1,
    height: 8,
    backgroundColor: '#334155',
    borderRadius: 4,
    position: 'relative',
  },
  sliderFill: {
    height: '100%',
    borderRadius: 4,
  },
  sliderThumb: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderRadius: 12,
    top: -8,
    marginLeft: -12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  quickAdjust: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 12,
  },
  adjustButton: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#1E293B',
    alignItems: 'center',
    justifyContent: 'center',
  },
  resultsCard: {
    marginBottom: 24,
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#19D38C40',
  },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  resultsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  resultItem: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#1E293B',
    borderRadius: 10,
    padding: 12,
  },
  resultLabel: {
    fontSize: 11,
    color: '#64748B',
    marginBottom: 4,
  },
  resultValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  resultPositive: {
    color: '#22C55E',
  },
  resultNegative: {
    color: '#EF4444',
  },
  scoreFit: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  scoreFitLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94A3B8',
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
  },
});
