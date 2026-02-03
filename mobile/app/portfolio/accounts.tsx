/**
 * MarketGPS Mobile - Portfolio Accounts Management
 * Gestion des comptes de courtage
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
import { Stack, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, PortfolioAccount } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState, Button } from '@/components/ui';

const ACCOUNT_TYPES = [
  { value: 'brokerage', label: 'Compte-titres', icon: 'briefcase-outline' },
  { value: 'pea', label: 'PEA', icon: 'leaf-outline' },
  { value: 'cto', label: 'CTO', icon: 'wallet-outline' },
  { value: 'ira', label: 'IRA', icon: 'umbrella-outline' },
  { value: 'roth_ira', label: 'Roth IRA', icon: 'shield-checkmark-outline' },
  { value: '401k', label: '401(k)', icon: 'business-outline' },
  { value: 'other', label: 'Autre', icon: 'ellipsis-horizontal-circle-outline' },
];

const CURRENCIES = [
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'USD', label: 'Dollar ($)' },
  { value: 'GBP', label: 'Livre (£)' },
  { value: 'XOF', label: 'CFA (XOF)' },
];

function getAccountTypeLabel(type: string): string {
  return ACCOUNT_TYPES.find(t => t.value === type)?.label || type;
}

function getAccountTypeIcon(type: string): string {
  return ACCOUNT_TYPES.find(t => t.value === type)?.icon || 'wallet-outline';
}

export default function PortfolioAccountsScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<PortfolioAccount | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    broker: '',
    account_type: 'brokerage',
    currency: 'EUR',
    is_default: false,
  });

  // Fetch accounts
  const { data: accounts, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['portfolio', 'accounts'],
    queryFn: () => api.getPortfolioAccounts(),
  });

  // Create account mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.createPortfolioAccount(data),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      setShowModal(false);
      resetForm();
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de créer le compte');
    },
  });

  // Update account mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<typeof formData> }) =>
      api.updatePortfolioAccount(id, data),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      setShowModal(false);
      resetForm();
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de modifier le compte');
    },
  });

  // Delete account mutation
  const deleteMutation = useMutation({
    mutationFn: (accountId: string) => api.deletePortfolioAccount(accountId),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de supprimer le compte');
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      broker: '',
      account_type: 'brokerage',
      currency: 'EUR',
      is_default: false,
    });
    setEditingAccount(null);
  };

  const handleAdd = () => {
    resetForm();
    setShowModal(true);
  };

  const handleEdit = (account: PortfolioAccount) => {
    setEditingAccount(account);
    setFormData({
      name: account.name,
      broker: account.broker || '',
      account_type: account.account_type,
      currency: account.currency,
      is_default: account.is_default,
    });
    setShowModal(true);
  };

  const handleDelete = (account: PortfolioAccount) => {
    Alert.alert(
      'Supprimer le compte',
      `Êtes-vous sûr de vouloir supprimer "${account.name}" ? Toutes les positions associées seront également supprimées.`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(account.id),
        },
      ]
    );
  };

  const handleSave = () => {
    if (!formData.name.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer un nom pour le compte');
      return;
    }

    if (editingAccount) {
      updateMutation.mutate({
        id: editingAccount.id,
        data: {
          name: formData.name,
          broker: formData.broker || undefined,
          is_default: formData.is_default,
        },
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const renderAccount = ({ item }: { item: PortfolioAccount }) => (
    <Card style={styles.accountCard}>
      <TouchableOpacity
        style={styles.accountContent}
        onPress={() => router.push(`/portfolio/positions?account_id=${item.id}` as any)}
        activeOpacity={0.7}
      >
        <View style={styles.accountIcon}>
          <Ionicons
            name={getAccountTypeIcon(item.account_type) as any}
            size={24}
            color="#19D38C"
          />
        </View>
        <View style={styles.accountInfo}>
          <View style={styles.accountNameRow}>
            <Text style={styles.accountName}>{item.name}</Text>
            {item.is_default && (
              <View style={styles.defaultBadge}>
                <Text style={styles.defaultBadgeText}>Par défaut</Text>
              </View>
            )}
          </View>
          <Text style={styles.accountDetails}>
            {getAccountTypeLabel(item.account_type)}
            {item.broker && ` • ${item.broker}`}
            {` • ${item.currency}`}
          </Text>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#64748B" />
      </TouchableOpacity>

      <View style={styles.accountActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleEdit(item)}
        >
          <Ionicons name="pencil-outline" size={18} color="#94A3B8" />
          <Text style={styles.actionButtonText}>Modifier</Text>
        </TouchableOpacity>
        <View style={styles.actionDivider} />
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleDelete(item)}
        >
          <Ionicons name="trash-outline" size={18} color="#EF4444" />
          <Text style={[styles.actionButtonText, styles.textDestructive]}>Supprimer</Text>
        </TouchableOpacity>
      </View>
    </Card>
  );

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Mes Comptes',
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
          <LoadingSpinner fullScreen message="Chargement des comptes..." />
        ) : (
          <FlatList
            data={accounts || []}
            renderItem={renderAccount}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            ListEmptyComponent={
              <EmptyState
                icon="wallet-outline"
                title="Aucun compte"
                description="Créez un compte de courtage pour suivre vos investissements"
                actionLabel="Créer un compte"
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

        {/* Add/Edit Modal */}
        <Modal
          visible={showModal}
          transparent
          animationType="slide"
          onRequestClose={() => setShowModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>
                  {editingAccount ? 'Modifier le compte' : 'Nouveau compte'}
                </Text>
                <TouchableOpacity
                  onPress={() => setShowModal(false)}
                  style={styles.modalClose}
                >
                  <Ionicons name="close" size={24} color="#94A3B8" />
                </TouchableOpacity>
              </View>

              <ScrollView style={styles.modalBody}>
                {/* Name */}
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Nom du compte *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formData.name}
                    onChangeText={(text) => setFormData({ ...formData, name: text })}
                    placeholder="Ex: Mon PEA Boursorama"
                    placeholderTextColor="#64748B"
                    maxLength={50}
                  />
                </View>

                {/* Broker */}
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Courtier (optionnel)</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formData.broker}
                    onChangeText={(text) => setFormData({ ...formData, broker: text })}
                    placeholder="Ex: Boursorama, Degiro, IBKR..."
                    placeholderTextColor="#64748B"
                    maxLength={50}
                  />
                </View>

                {/* Account Type */}
                {!editingAccount && (
                  <View style={styles.formGroup}>
                    <Text style={styles.formLabel}>Type de compte</Text>
                    <View style={styles.typeOptions}>
                      {ACCOUNT_TYPES.map((type) => (
                        <TouchableOpacity
                          key={type.value}
                          style={[
                            styles.typeOption,
                            formData.account_type === type.value && styles.typeOptionActive,
                          ]}
                          onPress={() => setFormData({ ...formData, account_type: type.value })}
                        >
                          <Ionicons
                            name={type.icon as any}
                            size={20}
                            color={formData.account_type === type.value ? '#19D38C' : '#64748B'}
                          />
                          <Text
                            style={[
                              styles.typeOptionText,
                              formData.account_type === type.value && styles.typeOptionTextActive,
                            ]}
                          >
                            {type.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>
                )}

                {/* Currency */}
                {!editingAccount && (
                  <View style={styles.formGroup}>
                    <Text style={styles.formLabel}>Devise</Text>
                    <View style={styles.currencyOptions}>
                      {CURRENCIES.map((currency) => (
                        <TouchableOpacity
                          key={currency.value}
                          style={[
                            styles.currencyOption,
                            formData.currency === currency.value && styles.currencyOptionActive,
                          ]}
                          onPress={() => setFormData({ ...formData, currency: currency.value })}
                        >
                          <Text
                            style={[
                              styles.currencyOptionText,
                              formData.currency === currency.value && styles.currencyOptionTextActive,
                            ]}
                          >
                            {currency.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>
                )}

                {/* Default Toggle */}
                <TouchableOpacity
                  style={styles.toggleOption}
                  onPress={() => setFormData({ ...formData, is_default: !formData.is_default })}
                >
                  <View style={styles.toggleContent}>
                    <Ionicons name="star-outline" size={20} color="#F59E0B" />
                    <Text style={styles.toggleText}>Définir comme compte par défaut</Text>
                  </View>
                  <View style={[styles.toggle, formData.is_default && styles.toggleActive]}>
                    {formData.is_default && (
                      <Ionicons name="checkmark" size={16} color="#0A0F1C" />
                    )}
                  </View>
                </TouchableOpacity>
              </ScrollView>

              <View style={styles.modalFooter}>
                <Button
                  title="Annuler"
                  variant="outline"
                  onPress={() => setShowModal(false)}
                  style={styles.footerButton}
                />
                <Button
                  title={editingAccount ? 'Enregistrer' : 'Créer'}
                  onPress={handleSave}
                  loading={createMutation.isPending || updateMutation.isPending}
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
  accountCard: {
    marginBottom: 16,
  },
  accountContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  accountIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  accountInfo: {
    flex: 1,
    marginLeft: 16,
  },
  accountNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  accountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  defaultBadge: {
    backgroundColor: '#F59E0B20',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  defaultBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#F59E0B',
  },
  accountDetails: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  accountActions: {
    flexDirection: 'row',
    paddingTop: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
  },
  actionButtonText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#94A3B8',
  },
  textDestructive: {
    color: '#EF4444',
  },
  actionDivider: {
    width: 1,
    backgroundColor: '#1E293B',
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
  typeOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#0A0F1C',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  typeOptionActive: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  typeOptionText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748B',
  },
  typeOptionTextActive: {
    color: '#19D38C',
  },
  currencyOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  currencyOption: {
    flex: 1,
    backgroundColor: '#0A0F1C',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  currencyOptionActive: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  currencyOptionText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748B',
  },
  currencyOptionTextActive: {
    color: '#19D38C',
  },
  toggleOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0A0F1C',
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
  },
  toggleContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  toggleText: {
    fontSize: 14,
    color: '#F1F5F9',
  },
  toggle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#64748B',
    alignItems: 'center',
    justifyContent: 'center',
  },
  toggleActive: {
    backgroundColor: '#19D38C',
    borderColor: '#19D38C',
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
