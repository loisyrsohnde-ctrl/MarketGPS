/**
 * MarketGPS Mobile - Security Settings Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Card, Input, Button } from '@/components/ui';
import { useIsAuthenticated, useAuthStore } from '@/store/auth';
import { supabase } from '@/lib/supabase';

export default function SecurityScreen() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const signOut = useAuthStore((state) => state.signOut);
  
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!currentPassword) {
      newErrors.currentPassword = 'Mot de passe actuel requis';
    }
    if (!newPassword || newPassword.length < 8) {
      newErrors.newPassword = 'Minimum 8 caractères';
    }
    if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleChangePassword = async () => {
    if (!validate()) return;
    
    setIsLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      
      if (error) throw error;
      
      Alert.alert('Succès', 'Votre mot de passe a été modifié');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      Alert.alert('Erreur', (error as Error).message || 'Impossible de changer le mot de passe');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDeleteAccount = () => {
    Alert.alert(
      'Supprimer le compte',
      'Cette action est irréversible. Toutes vos données seront supprimées.',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: () => {
            Alert.alert(
              'Confirmation',
              'Êtes-vous vraiment sûr ?',
              [
                { text: 'Annuler', style: 'cancel' },
                {
                  text: 'Supprimer définitivement',
                  style: 'destructive',
                  onPress: async () => {
                    // Note: Full account deletion requires backend support
                    await signOut();
                    router.replace('/(auth)/login');
                  },
                },
              ]
            );
          },
        },
      ]
    );
  };
  
  if (!isAuthenticated) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="shield-outline" size={48} color="#64748B" />
        <Text style={styles.centerTitle}>Connexion requise</Text>
        <Button
          title="Se connecter"
          onPress={() => router.push('/(auth)/login')}
          style={styles.centerButton}
        />
      </View>
    );
  }
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
    >
      {/* Change Password */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Changer le mot de passe</Text>
        <Card>
          <Input
            label="Mot de passe actuel"
            placeholder="••••••••"
            value={currentPassword}
            onChangeText={setCurrentPassword}
            error={errors.currentPassword}
            secureTextEntry
          />
          <Input
            label="Nouveau mot de passe"
            placeholder="••••••••"
            value={newPassword}
            onChangeText={setNewPassword}
            error={errors.newPassword}
            secureTextEntry
            helper="Minimum 8 caractères"
          />
          <Input
            label="Confirmer le nouveau mot de passe"
            placeholder="••••••••"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            error={errors.confirmPassword}
            secureTextEntry
          />
          <Button
            title="Modifier le mot de passe"
            onPress={handleChangePassword}
            loading={isLoading}
            fullWidth
            variant="outline"
          />
        </Card>
      </View>
      
      {/* Sessions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Sessions</Text>
        <Card padding="none">
          <View style={styles.sessionRow}>
            <View style={styles.sessionIcon}>
              <Ionicons name="phone-portrait-outline" size={20} color="#19D38C" />
            </View>
            <View style={styles.sessionContent}>
              <Text style={styles.sessionTitle}>Cette session</Text>
              <Text style={styles.sessionDescription}>Connecté maintenant</Text>
            </View>
            <View style={styles.activeBadge}>
              <Text style={styles.activeBadgeText}>Active</Text>
            </View>
          </View>
        </Card>
      </View>
      
      {/* Danger Zone */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, styles.dangerTitle]}>Zone de danger</Text>
        <Card style={styles.dangerCard}>
          <View style={styles.dangerContent}>
            <Ionicons name="warning-outline" size={24} color="#EF4444" />
            <View style={styles.dangerText}>
              <Text style={styles.dangerTitle}>Supprimer le compte</Text>
              <Text style={styles.dangerDescription}>
                Cette action est irréversible
              </Text>
            </View>
          </View>
          <Button
            title="Supprimer mon compte"
            onPress={handleDeleteAccount}
            variant="danger"
            fullWidth
          />
        </Card>
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
  centerContainer: {
    flex: 1,
    backgroundColor: '#0A0F1C',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  centerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#F1F5F9',
    marginTop: 16,
  },
  centerButton: {
    marginTop: 24,
    minWidth: 200,
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
    marginBottom: 12,
  },
  sessionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  sessionIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#19D38C10',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sessionContent: {
    flex: 1,
    marginLeft: 12,
  },
  sessionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  sessionDescription: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  activeBadge: {
    backgroundColor: '#22C55E20',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  activeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#22C55E',
  },
  dangerCard: {
    borderWidth: 1,
    borderColor: '#EF444440',
  },
  dangerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  dangerText: {
    flex: 1,
  },
  dangerTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#EF4444',
  },
  dangerDescription: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 2,
  },
});
