/**
 * MarketGPS Mobile - Barbell Strategy Screen
 * Avec sauvegarde de portfolios
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/lib/api';
import { Card, AssetCard, LoadingSpinner, EmptyState, Button } from '@/components/ui';
import { MARKET_SCOPES, type MarketScope } from '@/lib/config';

const RISK_PROFILES = [
  { id: 'conservative', label: 'Conservateur', icon: 'shield-outline', ratio: '85/15' },
  { id: 'moderate', label: 'Modéré', icon: 'options-outline', ratio: '75/25' },
  { id: 'aggressive', label: 'Agressif', icon: 'rocket-outline', ratio: '60/40' },
];

export default function BarbellScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [marketScope, setMarketScope] = useState<MarketScope>('US_EU');
  const [riskProfile, setRiskProfile] = useState('moderate');
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [portfolioName, setPortfolioName] = useState('');

  // Save portfolio mutation
  const saveMutation = useMutation({
    mutationFn: (data: Parameters<typeof api.saveBarbellPortfolio>[0]) =>
      api.saveBarbellPortfolio(data),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['barbell', 'portfolios'] });
      setShowSaveModal(false);
      setPortfolioName('');
      Alert.alert('Succès', 'Portfolio sauvegardé !');
    },
    onError: (error) => {
      Alert.alert('Erreur', 'Impossible de sauvegarder le portfolio');
    },
  });

  const handleSavePortfolio = () => {
    if (!portfolioName.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer un nom pour le portfolio');
      return;
    }
    if (!suggestion) return;

    const coreAssets = (suggestion.core || []).slice(0, 5).map((asset: any, index: number) => ({
      ticker: asset.symbol,
      weight: Math.floor((parseInt(selectedRisk?.ratio.split('/')[0] || '75') / 5)),
    }));

    const satelliteAssets = (suggestion.satellite || []).slice(0, 5).map((asset: any, index: number) => ({
      ticker: asset.symbol,
      weight: Math.floor((parseInt(selectedRisk?.ratio.split('/')[1] || '25') / 5)),
    }));

    saveMutation.mutate({
      name: portfolioName.trim(),
      risk_profile: riskProfile,
      market_scope: marketScope,
      core_assets: coreAssets,
      satellite_assets: satelliteAssets,
    });
  };
  
  // Fetch barbell suggestion
  const { data: suggestion, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['barbell', 'suggest', riskProfile, marketScope],
    queryFn: () => api.getBarbellSuggestion({
      risk_profile: riskProfile,
      market_scope: marketScope,
      core_count: 5,
      satellite_count: 5,
    }),
  });
  
  // Fetch core candidates
  const { data: coreCandidates } = useQuery({
    queryKey: ['barbell', 'core', marketScope],
    queryFn: () => api.getCoreCandidates(20, marketScope),
  });
  
  // Fetch satellite candidates
  const { data: satelliteCandidates } = useQuery({
    queryKey: ['barbell', 'satellite', marketScope],
    queryFn: () => api.getSatelliteCandidates(20, marketScope),
  });
  
  const selectedRisk = RISK_PROFILES.find(r => r.id === riskProfile);
  
  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Barbell Builder',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />
      
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#19D38C"
            />
          }
        >
          {/* Introduction */}
          <Card style={styles.introCard}>
            <View style={styles.introIcon}>
              <Ionicons name="barbell-outline" size={32} color="#19D38C" />
            </View>
            <Text style={styles.introTitle}>Stratégie Barbell</Text>
            <Text style={styles.introText}>
              Combinez stabilité et croissance en répartissant vos investissements entre actifs sûrs (Core) 
              et actifs dynamiques (Satellite).
            </Text>
          </Card>
          
          {/* Market Scope Selector */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Marché</Text>
            <View style={styles.scopeSelector}>
              {Object.keys(MARKET_SCOPES).map((scope) => (
                <TouchableOpacity
                  key={scope}
                  style={[
                    styles.scopeButton,
                    marketScope === scope && styles.scopeButtonActive,
                  ]}
                  onPress={() => setMarketScope(scope as MarketScope)}
                >
                  <Text
                    style={[
                      styles.scopeButtonText,
                      marketScope === scope && styles.scopeButtonTextActive,
                    ]}
                  >
                    {scope === 'US_EU' ? 'US/EU' : 'Afrique'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          {/* Risk Profile Selector */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Profil de Risque</Text>
            <View style={styles.riskSelector}>
              {RISK_PROFILES.map((profile) => (
                <TouchableOpacity
                  key={profile.id}
                  style={[
                    styles.riskCard,
                    riskProfile === profile.id && styles.riskCardActive,
                  ]}
                  onPress={() => setRiskProfile(profile.id)}
                >
                  <Ionicons
                    name={profile.icon as any}
                    size={24}
                    color={riskProfile === profile.id ? '#19D38C' : '#64748B'}
                  />
                  <Text
                    style={[
                      styles.riskLabel,
                      riskProfile === profile.id && styles.riskLabelActive,
                    ]}
                  >
                    {profile.label}
                  </Text>
                  <Text style={styles.riskRatio}>{profile.ratio}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          {/* Allocation Visual */}
          <Card style={styles.allocationCard}>
            <Text style={styles.allocationTitle}>Répartition suggérée</Text>
            <View style={styles.allocationBar}>
              <View
                style={[
                  styles.coreBar,
                  { flex: parseInt(selectedRisk?.ratio.split('/')[0] || '75') },
                ]}
              >
                <Text style={styles.allocationBarText}>Core</Text>
              </View>
              <View
                style={[
                  styles.satelliteBar,
                  { flex: parseInt(selectedRisk?.ratio.split('/')[1] || '25') },
                ]}
              >
                <Text style={styles.allocationBarText}>Satellite</Text>
              </View>
            </View>
            <View style={styles.allocationLegend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#19D38C' }]} />
                <Text style={styles.legendText}>Core: Stabilité, faible volatilité</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#8B5CF6' }]} />
                <Text style={styles.legendText}>Satellite: Croissance, momentum</Text>
              </View>
            </View>
          </Card>
          
          {/* Suggested Portfolio */}
          {isLoading ? (
            <LoadingSpinner message="Génération du portefeuille..." />
          ) : suggestion ? (
            <>
              {/* Core Suggestions */}
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>Core</Text>
                  <View style={styles.coreBadge}>
                    <Text style={styles.coreBadgeText}>
                      {selectedRisk?.ratio.split('/')[0]}%
                    </Text>
                  </View>
                </View>
                {suggestion.core?.slice(0, 5).map((asset: any) => (
                  <AssetCard
                    key={asset.asset_id || asset.symbol}
                    asset={asset}
                    showWatchlistButton
                  />
                ))}
              </View>
              
              {/* Satellite Suggestions */}
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>Satellite</Text>
                  <View style={styles.satelliteBadge}>
                    <Text style={styles.satelliteBadgeText}>
                      {selectedRisk?.ratio.split('/')[1]}%
                    </Text>
                  </View>
                </View>
                {suggestion.satellite?.slice(0, 5).map((asset: any) => (
                  <AssetCard
                    key={asset.asset_id || asset.symbol}
                    asset={asset}
                    showWatchlistButton
                  />
                ))}
              </View>
            </>
          ) : (
            <EmptyState
              icon="barbell-outline"
              title="Aucune suggestion"
              description="Impossible de générer des suggestions pour le moment"
              actionLabel="Réessayer"
              onAction={() => refetch()}
            />
          )}

          {/* Action Buttons */}
          {suggestion && (
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.savedPortfoliosButton}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  router.push('/strategy/barbell-saved');
                }}
              >
                <Ionicons name="folder-outline" size={20} color="#19D38C" />
                <Text style={styles.savedPortfoliosText}>Mes Portfolios</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.saveButton}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                  setShowSaveModal(true);
                }}
              >
                <Ionicons name="save-outline" size={20} color="#0A0F1C" />
                <Text style={styles.saveButtonText}>Sauvegarder</Text>
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>

        {/* Save Modal */}
        <Modal
          visible={showSaveModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowSaveModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Sauvegarder le Portfolio</Text>
              <Text style={styles.modalSubtitle}>
                Donnez un nom à votre portfolio Barbell
              </Text>
              <TextInput
                style={styles.modalInput}
                value={portfolioName}
                onChangeText={setPortfolioName}
                placeholder="Ex: Mon Portfolio Agressif"
                placeholderTextColor="#64748B"
                autoFocus
              />
              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.modalCancelButton}
                  onPress={() => {
                    setShowSaveModal(false);
                    setPortfolioName('');
                  }}
                >
                  <Text style={styles.modalCancelText}>Annuler</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.modalSaveButton,
                    saveMutation.isPending && styles.modalSaveButtonDisabled,
                  ]}
                  onPress={handleSavePortfolio}
                  disabled={saveMutation.isPending}
                >
                  <Text style={styles.modalSaveText}>
                    {saveMutation.isPending ? 'Sauvegarde...' : 'Sauvegarder'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  introCard: {
    alignItems: 'center',
    marginBottom: 24,
  },
  introIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  introTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  introText: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 12,
  },
  scopeSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  scopeButton: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  scopeButtonActive: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  scopeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94A3B8',
  },
  scopeButtonTextActive: {
    color: '#19D38C',
  },
  riskSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  riskCard: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  riskCardActive: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  riskLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
    marginTop: 8,
  },
  riskLabelActive: {
    color: '#19D38C',
  },
  riskRatio: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 4,
  },
  allocationCard: {
    marginBottom: 24,
  },
  allocationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
    marginBottom: 16,
  },
  allocationBar: {
    flexDirection: 'row',
    height: 40,
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 16,
  },
  coreBar: {
    backgroundColor: '#19D38C',
    alignItems: 'center',
    justifyContent: 'center',
  },
  satelliteBar: {
    backgroundColor: '#8B5CF6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  allocationBarText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0A0F1C',
  },
  allocationLegend: {
    gap: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    fontSize: 12,
    color: '#94A3B8',
  },
  coreBadge: {
    backgroundColor: '#19D38C20',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  coreBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#19D38C',
  },
  satelliteBadge: {
    backgroundColor: '#8B5CF620',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  satelliteBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8B5CF6',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
    marginBottom: 20,
  },
  savedPortfoliosButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#19D38C20',
    borderRadius: 12,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: '#19D38C',
  },
  savedPortfoliosText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#19D38C',
  },
  saveButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#19D38C',
    borderRadius: 12,
    paddingVertical: 14,
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0A0F1C',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#94A3B8',
    marginBottom: 20,
  },
  modalInput: {
    backgroundColor: '#0A0F1C',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#334155',
  },
  modalCancelText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94A3B8',
  },
  modalSaveButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#19D38C',
  },
  modalSaveButtonDisabled: {
    opacity: 0.6,
  },
  modalSaveText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0A0F1C',
  },
});
