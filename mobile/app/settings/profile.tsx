/**
 * MarketGPS Mobile - Profile Screen
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
import { useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/lib/api';
import { Card, Input, Button, LoadingSpinner } from '@/components/ui';
import { useUser, useIsAuthenticated } from '@/store/auth';

export default function ProfileScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const [displayName, setDisplayName] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  
  // Fetch profile
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.getUserProfile(),
    enabled: isAuthenticated,
  });
  
  // Update displayName when profile loads
  React.useEffect(() => {
    if (profile?.displayName) {
      setDisplayName(profile.displayName);
    }
  }, [profile]);
  
  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: (data: { displayName: string }) => api.updateUserProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setIsEditing(false);
      Alert.alert('Succès', 'Profil mis à jour');
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de mettre à jour le profil');
    },
  });
  
  if (!isAuthenticated) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="person-outline" size={48} color="#64748B" />
        <Text style={styles.centerTitle}>Connexion requise</Text>
        <Button
          title="Se connecter"
          onPress={() => router.push('/(auth)/login')}
          style={styles.centerButton}
        />
      </View>
    );
  }
  
  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Avatar Section */}
      <View style={styles.avatarSection}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {displayName?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U'}
          </Text>
        </View>
        <TouchableOpacity style={styles.changeAvatarButton}>
          <Ionicons name="camera-outline" size={16} color="#19D38C" />
          <Text style={styles.changeAvatarText}>Changer</Text>
        </TouchableOpacity>
      </View>
      
      {/* Profile Form */}
      <Card>
        <Input
          label="Nom d'affichage"
          placeholder="Votre nom"
          value={displayName}
          onChangeText={setDisplayName}
          editable={isEditing}
        />
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Email</Text>
          <Text style={styles.infoValue}>{user?.email}</Text>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>ID</Text>
          <Text style={styles.infoValueSmall}>{user?.id}</Text>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Créé le</Text>
          <Text style={styles.infoValue}>
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString('fr-FR')
              : '—'}
          </Text>
        </View>
      </Card>
      
      {/* Actions */}
      <View style={styles.actions}>
        {isEditing ? (
          <>
            <Button
              title="Enregistrer"
              onPress={() => updateMutation.mutate({ displayName })}
              loading={updateMutation.isLoading}
              fullWidth
            />
            <Button
              title="Annuler"
              onPress={() => {
                setDisplayName(profile?.displayName || '');
                setIsEditing(false);
              }}
              variant="ghost"
              fullWidth
            />
          </>
        ) : (
          <Button
            title="Modifier le profil"
            onPress={() => setIsEditing(true)}
            variant="outline"
            fullWidth
            icon={<Ionicons name="pencil-outline" size={18} color="#F1F5F9" />}
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
  avatarSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 40,
    fontWeight: '700',
    color: '#19D38C',
  },
  changeAvatarButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 12,
    padding: 8,
  },
  changeAvatarText: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '500',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  infoLabel: {
    fontSize: 14,
    color: '#94A3B8',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#F1F5F9',
  },
  infoValueSmall: {
    fontSize: 12,
    color: '#64748B',
    maxWidth: 200,
  },
  actions: {
    marginTop: 24,
    gap: 12,
  },
});
