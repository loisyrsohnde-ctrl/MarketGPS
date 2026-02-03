/**
 * MarketGPS Mobile - Portfolio Positions Screen
 * Liste et gestion des positions
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter, useLocalSearchParams } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, PortfolioPosition, PortfolioAccount, Asset } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState, Button, ScoreBadge } from '@/components/ui';

function formatCurrency(value: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export default function PortfolioPositionsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ account_id?: string }>();
  const queryClient = useQueryClient();

  const [showModal, setShowModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<string | null>(params.account_id || null);
  const [searchTicker, setSearchTicker] = useState('');
  const [searchResults, setSearchResults] = useState<Asset[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [formData, setFormData] = useState({
    account_id: '',
    ticker: '',
    quantity: '',
    avg_cost: '',
  });

  // Fetch accounts
  const { data: accounts } = useQuery({
    queryKey: ['portfolio', 'accounts'],
    queryFn: () => api.getPortfolioAccounts(),
  });

  // Fetch positions
  const { data: positions, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['portfolio', 'positions', selectedAccount],
    queryFn: () => api.getPortfolioPositions(selectedAccount || undefined),
  });

  // Add position mutation
  const addMutation = useMutation({
    mutationFn: (data: {
      account_id: string;
      ticker: string;
      quantity: number;
      avg_cost: number;
    }) => api.addPortfolioPosition(data),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      setShowModal(false);
      resetForm();
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible d\'ajouter la position');
    },
  });

  // Delete position mutation
  const deleteMutation = useMutation({
    mutationFn: (positionId: string) => api.deletePortfolioPosition(positionId),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de supprimer la position');
    },
  });

  const resetForm = () => {
    setFormData({
      account_id: selectedAccount || (accounts?.[0]?.id ?? ''),
      ticker: '',
      quantity: '',
      avg_cost: '',
    });
    setSearchTicker('');
    setSearchResults([]);
  };

  const handleAdd = () => {
    resetForm();
    if (accounts && accounts.length > 0) {
      setFormData(prev => ({
        ...prev,
        account_id: selectedAccount || accounts[0].id,
      }));
      setShowModal(true);
    } else {
      Alert.alert(
        'Aucun compte',
        'Créez d\'abord un compte de courtage',
        [
          { text: 'Annuler', style: 'cancel' },
          { text: 'Créer un compte', onPress: () => router.push('/portfolio/accounts' as any) },
        ]
      );
    }
  };

  const handleDelete = (position: PortfolioPosition) => {
    Alert.alert(
      'Supprimer la position',
      `Êtes-vous sûr de vouloir supprimer ${position.quantity} ${position.ticker} ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(position.id),
        },
      ]
    );
  };

  const handleSearch = async (query: string) => {
    setSearchTicker(query);
    if (query.length >= 2) {
      setIsSearching(true);
      try {
        const results = await api.searchAssets(query, undefined, 10);
        setSearchResults(results);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleSelectTicker = (asset: Asset) => {
    setFormData(prev => ({
      ...prev,
      ticker: asset.symbol,
    }));
    setSearchTicker(asset.symbol);
    setSearchResults([]);
  };

  const handleSave = () => {
    const quantity = parseFloat(formData.quantity);
    const avgCost = parseFloat(formData.avg_cost);

    if (!formData.ticker.trim()) {
      Alert.alert('Erreur', 'Veuillez sélectionner un actif');
      return;
    }

    if (isNaN(quantity) || quantity <= 0) {
      Alert.alert('Erreur', 'Veuillez entrer une quantité valide');
      return;
    }

    if (isNaN(avgCost) || avgCost <= 0) {
      Alert.alert('Erreur', 'Veuillez entrer un prix d\'achat valide');
      return;
    }

    addMutation.mutate({
      account_id: formData.account_id,
      ticker: formData.ticker.toUpperCase(),
      quantity,
      avg_cost: avgCost,
    });
  };

  const renderPosition = ({ item }: { item: PortfolioPosition }) => {
    const pnl = item.unrealized_pnl || 0;
    const pnlPct = item.unrealized_pnl_pct || 0;
    const isProfitable = pnl >= 0;

    return (
      <TouchableOpacity
        style={styles.positionCard}
        onPress={() => router.push(`/asset/${item.ticker}`)}
        onLongPress={() => handleDelete(item)}
        activeOpacity={0.7}
        delayLongPress={500}
      >
        <View style={styles.positionHeader}>
          <View style={styles.positionInfo}>
            <View style={styles.tickerRow}>
              <Text style={styles.positionTicker}>{item.ticker}</Text>
              {item.asset?.score_total && (
                <ScoreBadge score={item.asset.score_total} size="sm" />
              )}
            </View>
            <Text style={styles.positionName} numberOfLines={1}>
              {item.asset?.name || item.ticker}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => handleDelete(item)}
          >
            <Ionicons name="close-circle" size={22} color="#64748B" />
          </TouchableOpacity>
        </View>

        <View style={styles.positionDetails}>
          <View style={styles.detailColumn}>
            <Text style={styles.detailLabel}>Quantité</Text>
            <Text style={styles.detailValue}>{item.quantity}</Text>
          </View>
          <View style={styles.detailColumn}>
            <Text style={styles.detailLabel}>PRU</Text>
            <Text style={styles.detailValue}>{formatCurrency(item.avg_cost)}</Text>
          </View>
          <View style={styles.detailColumn}>
            <Text style={styles.detailLabel}>Valeur</Text>
            <Text style={styles.detailValue}>
              {item.market_value ? formatCurrency(item.market_value) : '-'}
            </Text>
          </View>
          <View style={styles.detailColumn}>
            <Text style={styles.detailLabel}>+/- Value</Text>
            <View style={[styles.pnlBadge, isProfitable ? styles.pnlPositive : styles.pnlNegative]}>
              <Text style={[styles.pnlText, isProfitable ? styles.pnlTextPositive : styles.pnlTextNegative]}>
                {formatPercent(pnlPct)}
              </Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const renderHeader = () => (
    <View style={styles.filtersContainer}>
      {/* Account Filter */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterChips}
      >
        <TouchableOpacity
          style={[styles.filterChip, !selectedAccount && styles.filterChipActive]}
          onPress={() => setSelectedAccount(null)}
        >
          <Text style={[styles.filterChipText, !selectedAccount && styles.filterChipTextActive]}>
            Tous
          </Text>
        </TouchableOpacity>
        {accounts?.map((account) => (
          <TouchableOpacity
            key={account.id}
            style={[styles.filterChip, selectedAccount === account.id && styles.filterChipActive]}
            onPress={() => setSelectedAccount(account.id)}
          >
            <Text style={[styles.filterChipText, selectedAccount === account.id && styles.filterChipTextActive]}>
              {account.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Positions',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
          headerRight: () => (
            <TouchableOpacity
              onPress={handleAdd}
              style={styles.headerButton}
            >
              <Ionicons name="add-circle" size={28} color="#19D38C" />
            </TouchableOpacity>
          ),
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        {isLoading ? (
          <LoadingSpinner fullScreen message="Chargement des positions..." />
        ) : (
          <FlatList
            data={positions || []}
            renderItem={renderPosition}
            keyExtractor={(item) => item.id}
            ListHeaderComponent={renderHeader}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            ListEmptyComponent={
              <EmptyState
                icon="briefcase-outline"
                title="Aucune position"
                description="Ajoutez des positions pour suivre vos investissements"
                actionLabel="Ajouter une position"
                onAction={handleAdd}
              />
            }
            refreshControl={
              <RefreshControl
                refreshing={isRefetching}
                onRefresh={refetch}
                tintColor="#19D38C"
              />
            }
          />
        )}

        {/* Add Position Modal */}
        <Modal
          visible={showModal}
          transparent
          animationType="slide"
          onRequestClose={() => setShowModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Nouvelle position</Text>
                <TouchableOpacity
                  onPress={() => setShowModal(false)}
                  style={styles.modalClose}
                >
                  <Ionicons name="close" size={24} color="#94A3B8" />
                </TouchableOpacity>
              </View>

              <ScrollView style={styles.modalBody} keyboardShouldPersistTaps="handled">
                {/* Account Selector */}
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Compte</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.accountOptions}>
                      {accounts?.map((account) => (
                        <TouchableOpacity
                          key={account.id}
                          style={[
                            styles.accountOption,
                            formData.account_id === account.id && styles.accountOptionActive,
                          ]}
                          onPress={() => setFormData({ ...formData, account_id: account.id })}
                        >
                          <Text
                            style={[
                              styles.accountOptionText,
                              formData.account_id === account.id && styles.accountOptionTextActive,
                            ]}
                          >
                            {account.name}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                {/* Ticker Search */}
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Actif *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={searchTicker}
                    onChangeText={handleSearch}
                    placeholder="Rechercher un ticker (ex: AAPL, LVMH)"
                    placeholderTextColor="#64748B"
                    autoCapitalize="characters"
                  />
                  {isSearching && (
                    <View style={styles.searchLoading}>
                      <LoadingSpinner />
                    </View>
                  )}
                  {searchResults.length > 0 && (
                    <View style={styles.searchResults}>
                      {searchResults.map((asset) => (
                        <TouchableOpacity
                          key={asset.asset_id}
                          style={styles.searchResult}
                          onPress={() => handleSelectTicker(asset)}
                        >
                          <View style={styles.searchResultInfo}>
                            <Text style={styles.searchResultTicker}>{asset.symbol}</Text>
                            <Text style={styles.searchResultName} numberOfLines={1}>
                              {asset.name}
                            </Text>
                          </View>
                          {asset.score_total && (
                            <ScoreBadge score={asset.score_total} size="sm" />
                          )}
                        </TouchableOpacity>
                      ))}
                    </View>
                  )}
                </View>

                {/* Quantity */}
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Quantité *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formData.quantity}
                    onChangeText={(text) => setFormData({ ...formData, quantity: text })}
                    placeholder="Ex: 10"
                    placeholderTextColor="#64748B"
                    keyboardType="decimal-pad"
                  />
                </View>

                {/* Average Cost */}
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Prix d'achat moyen *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formData.avg_cost}
                    onChangeText={(text) => setFormData({ ...formData, avg_cost: text })}
                    placeholder="Ex: 150.50"
                    placeholderTextColor="#64748B"
                    keyboardType="decimal-pad"
                  />
                </View>
              </ScrollView>

              <View style={styles.modalFooter}>
                <Button
                  title="Annuler"
                  variant="outline"
                  onPress={() => setShowModal(false)}
                  style={styles.footerButton}
                />
                <Button
                  title="Ajouter"
                  onPress={handleSave}
                  loading={addMutation.isPending}
                  style={styles.footerButton}
                />
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
  listContent: {
    padding: 20,
    paddingBottom: 40,
  },
  headerButton: {
    marginRight: 8,
  },
  filtersContainer: {
    marginBottom: 16,
  },
  filterChips: {
    flexDirection: 'row',
    gap: 8,
  },
  filterChip: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 16,
    paddingVertical: 8,
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
  positionCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  positionInfo: {
    flex: 1,
  },
  tickerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  positionTicker: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  positionName: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  deleteButton: {
    padding: 4,
  },
  positionDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailColumn: {
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 11,
    color: '#64748B',
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  pnlBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  pnlPositive: {
    backgroundColor: '#22C55E20',
  },
  pnlNegative: {
    backgroundColor: '#EF444420',
  },
  pnlText: {
    fontSize: 12,
    fontWeight: '600',
  },
  pnlTextPositive: {
    color: '#22C55E',
  },
  pnlTextNegative: {
    color: '#EF4444',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1E293B',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  modalClose: {
    padding: 4,
  },
  modalBody: {
    padding: 20,
  },
  formGroup: {
    marginBottom: 20,
  },
  formLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#94A3B8',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#0A0F1C',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#F1F5F9',
  },
  accountOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  accountOption: {
    backgroundColor: '#0A0F1C',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  accountOptionActive: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  accountOptionText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748B',
  },
  accountOptionTextActive: {
    color: '#19D38C',
  },
  searchLoading: {
    padding: 12,
    alignItems: 'center',
  },
  searchResults: {
    backgroundColor: '#0A0F1C',
    borderRadius: 12,
    marginTop: 8,
    maxHeight: 200,
  },
  searchResult: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  searchResultInfo: {
    flex: 1,
  },
  searchResultTicker: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  searchResultName: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  modalFooter: {
    flexDirection: 'row',
    gap: 12,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  footerButton: {
    flex: 1,
  },
});
