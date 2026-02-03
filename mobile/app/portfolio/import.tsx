/**
 * MarketGPS Mobile - Portfolio Import Screen
 * Import CSV de positions
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';
import { api, PortfolioAccount } from '@/lib/api';
import { Card, Button, LoadingSpinner, EmptyState } from '@/components/ui';

const CSV_EXAMPLE = `ticker,quantity,avg_cost
AAPL,10,175.50
MSFT,5,380.25
GOOGL,2,140.00`;

const CSV_FORMAT_INFO = `Format attendu :
• Colonnes : ticker, quantity, avg_cost
• Séparateur : virgule
• Première ligne : en-têtes
• Prix sans symbole de devise`;

export default function PortfolioImportScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [csvContent, setCsvContent] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [showManualInput, setShowManualInput] = useState(false);

  // Fetch accounts
  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ['portfolio', 'accounts'],
    queryFn: () => api.getPortfolioAccounts(),
  });

  // Import mutation
  const importMutation = useMutation({
    mutationFn: ({ accountId, csv }: { accountId: string; csv: string }) =>
      api.importPortfolioCSV(accountId, csv),
    onSuccess: (data) => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });

      if (data.errors && data.errors.length > 0) {
        Alert.alert(
          'Import partiel',
          `${data.imported_count} positions importées.\n\nErreurs :\n${data.errors.join('\n')}`,
          [{ text: 'OK', onPress: () => router.back() }]
        );
      } else {
        Alert.alert(
          'Import réussi',
          `${data.imported_count} positions importées avec succès`,
          [{ text: 'Voir les positions', onPress: () => router.replace('/portfolio/positions' as any) }]
        );
      }
    },
    onError: (error: any) => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Erreur', error.message || 'Impossible d\'importer les positions');
    },
  });

  const handleSelectFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/csv', 'text/plain', 'application/csv'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const file = result.assets[0];
        setFileName(file.name);

        // Read file content
        const content = await FileSystem.readAsStringAsync(file.uri);
        setCsvContent(content);
        setShowManualInput(false);
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
    } catch (error) {
      console.error('File picker error:', error);
      Alert.alert('Erreur', 'Impossible de lire le fichier');
    }
  };

  const handleImport = () => {
    if (!selectedAccountId) {
      Alert.alert('Erreur', 'Veuillez sélectionner un compte');
      return;
    }

    if (!csvContent.trim()) {
      Alert.alert('Erreur', 'Veuillez sélectionner un fichier ou entrer des données');
      return;
    }

    // Basic validation
    const lines = csvContent.trim().split('\n');
    if (lines.length < 2) {
      Alert.alert('Erreur', 'Le fichier doit contenir au moins une ligne de données');
      return;
    }

    importMutation.mutate({
      accountId: selectedAccountId,
      csv: csvContent,
    });
  };

  const handleUseExample = () => {
    setCsvContent(CSV_EXAMPLE);
    setFileName(null);
    setShowManualInput(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  if (accountsLoading) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Importer',
            headerStyle: { backgroundColor: '#0A0F1C' },
            headerTintColor: '#F1F5F9',
          }}
        />
        <LoadingSpinner fullScreen message="Chargement..." />
      </>
    );
  }

  if (!accounts || accounts.length === 0) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Importer',
            headerStyle: { backgroundColor: '#0A0F1C' },
            headerTintColor: '#F1F5F9',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.emptyContainer}>
            <EmptyState
              icon="wallet-outline"
              title="Aucun compte"
              description="Créez d'abord un compte pour importer des positions"
              actionLabel="Créer un compte"
              onAction={() => router.push('/portfolio/accounts' as any)}
            />
          </View>
        </SafeAreaView>
      </>
    );
  }

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Importer',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Account Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>1. Sélectionner le compte</Text>
            <Card padding="none">
              {accounts.map((account) => (
                <TouchableOpacity
                  key={account.id}
                  style={[
                    styles.accountOption,
                    selectedAccountId === account.id && styles.accountOptionActive,
                  ]}
                  onPress={() => {
                    setSelectedAccountId(account.id);
                    Haptics.selectionAsync();
                  }}
                >
                  <View style={styles.accountInfo}>
                    <Ionicons
                      name="wallet-outline"
                      size={20}
                      color={selectedAccountId === account.id ? '#19D38C' : '#64748B'}
                    />
                    <Text
                      style={[
                        styles.accountName,
                        selectedAccountId === account.id && styles.accountNameActive,
                      ]}
                    >
                      {account.name}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.radioButton,
                      selectedAccountId === account.id && styles.radioButtonActive,
                    ]}
                  >
                    {selectedAccountId === account.id && (
                      <View style={styles.radioButtonInner} />
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </Card>
          </View>

          {/* File Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>2. Fichier CSV</Text>

            <Card style={styles.uploadCard}>
              {fileName ? (
                <View style={styles.selectedFile}>
                  <View style={styles.fileInfo}>
                    <Ionicons name="document-text" size={32} color="#19D38C" />
                    <View style={styles.fileDetails}>
                      <Text style={styles.fileName}>{fileName}</Text>
                      <Text style={styles.fileStatus}>Fichier prêt à importer</Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    style={styles.changeFileButton}
                    onPress={handleSelectFile}
                  >
                    <Text style={styles.changeFileText}>Changer</Text>
                  </TouchableOpacity>
                </View>
              ) : !showManualInput ? (
                <View style={styles.uploadContent}>
                  <View style={styles.uploadIcon}>
                    <Ionicons name="cloud-upload-outline" size={40} color="#64748B" />
                  </View>
                  <Text style={styles.uploadTitle}>Sélectionner un fichier CSV</Text>
                  <Text style={styles.uploadSubtitle}>
                    Format : ticker, quantity, avg_cost
                  </Text>
                  <View style={styles.uploadActions}>
                    <Button
                      title="Parcourir"
                      onPress={handleSelectFile}
                      icon={<Ionicons name="folder-outline" size={18} color="#0A0F1C" />}
                    />
                    <TouchableOpacity
                      style={styles.manualButton}
                      onPress={() => setShowManualInput(true)}
                    >
                      <Text style={styles.manualButtonText}>Saisie manuelle</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ) : (
                <View style={styles.manualInput}>
                  <View style={styles.manualHeader}>
                    <Text style={styles.manualTitle}>Données CSV</Text>
                    <TouchableOpacity onPress={handleUseExample}>
                      <Text style={styles.exampleLink}>Voir exemple</Text>
                    </TouchableOpacity>
                  </View>
                  <TextInput
                    style={styles.csvInput}
                    value={csvContent}
                    onChangeText={setCsvContent}
                    placeholder={CSV_EXAMPLE}
                    placeholderTextColor="#475569"
                    multiline
                    numberOfLines={8}
                    textAlignVertical="top"
                    autoCapitalize="characters"
                  />
                  <TouchableOpacity
                    style={styles.browseInsteadButton}
                    onPress={handleSelectFile}
                  >
                    <Ionicons name="folder-outline" size={16} color="#19D38C" />
                    <Text style={styles.browseInsteadText}>Sélectionner un fichier</Text>
                  </TouchableOpacity>
                </View>
              )}
            </Card>

            {/* Format Info */}
            <Card style={styles.infoCard}>
              <View style={styles.infoHeader}>
                <Ionicons name="information-circle-outline" size={20} color="#3B82F6" />
                <Text style={styles.infoTitle}>Format du fichier</Text>
              </View>
              <Text style={styles.infoText}>{CSV_FORMAT_INFO}</Text>
            </Card>
          </View>

          {/* Import Button */}
          <View style={styles.importSection}>
            <Button
              title={importMutation.isPending ? 'Import en cours...' : 'Importer les positions'}
              onPress={handleImport}
              disabled={!selectedAccountId || !csvContent.trim() || importMutation.isPending}
              loading={importMutation.isPending}
              icon={<Ionicons name="download-outline" size={20} color="#0A0F1C" />}
            />
          </View>
        </ScrollView>
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
    marginBottom: 12,
  },
  accountOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  accountOptionActive: {
    backgroundColor: '#19D38C10',
  },
  accountInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  accountName: {
    fontSize: 15,
    color: '#94A3B8',
  },
  accountNameActive: {
    color: '#F1F5F9',
    fontWeight: '600',
  },
  radioButton: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: '#64748B',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioButtonActive: {
    borderColor: '#19D38C',
  },
  radioButtonInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#19D38C',
  },
  uploadCard: {
    marginBottom: 16,
  },
  uploadContent: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  uploadIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#1E293B',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  uploadTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F1F5F9',
    marginBottom: 4,
  },
  uploadSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 20,
  },
  uploadActions: {
    alignItems: 'center',
    gap: 12,
  },
  manualButton: {
    padding: 8,
  },
  manualButtonText: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '500',
  },
  selectedFile: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  fileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  fileDetails: {
    flex: 1,
  },
  fileName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  fileStatus: {
    fontSize: 12,
    color: '#22C55E',
    marginTop: 2,
  },
  changeFileButton: {
    padding: 8,
  },
  changeFileText: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '500',
  },
  manualInput: {},
  manualHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  manualTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94A3B8',
  },
  exampleLink: {
    fontSize: 13,
    color: '#19D38C',
    fontWeight: '500',
  },
  csvInput: {
    backgroundColor: '#0A0F1C',
    borderRadius: 12,
    padding: 16,
    fontSize: 13,
    fontFamily: 'monospace',
    color: '#F1F5F9',
    minHeight: 160,
  },
  browseInsteadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 12,
    padding: 8,
  },
  browseInsteadText: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '500',
  },
  infoCard: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#3B82F640',
  },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },
  infoText: {
    fontSize: 13,
    color: '#94A3B8',
    lineHeight: 20,
  },
  importSection: {
    marginTop: 8,
  },
});
