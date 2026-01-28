/**
 * MarketGPS Mobile - Forgot Password Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { resetPassword } from '@/lib/supabase';
import { Input, Button } from '@/components/ui';

export default function ForgotPasswordScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);
  const [error, setError] = useState('');
  
  const validate = () => {
    if (!email) {
      setError('Email requis');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Email invalide');
      return false;
    }
    setError('');
    return true;
  };
  
  const handleReset = async () => {
    if (!validate()) return;
    
    setIsLoading(true);
    try {
      await resetPassword(email);
      setIsSent(true);
    } catch (error) {
      Alert.alert(
        'Erreur',
        (error as Error).message || 'Impossible d\'envoyer l\'email'
      );
    } finally {
      setIsLoading(false);
    }
  };
  
  if (isSent) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.successContainer}>
          <View style={styles.successIcon}>
            <Ionicons name="mail-outline" size={48} color="#19D38C" />
          </View>
          <Text style={styles.successTitle}>Email envoyé</Text>
          <Text style={styles.successText}>
            Un lien de réinitialisation a été envoyé à {email}
          </Text>
          <Button
            title="Retour à la connexion"
            onPress={() => router.replace('/(auth)/login')}
            variant="outline"
            style={styles.successButton}
          />
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Back Button */}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={24} color="#F1F5F9" />
          </TouchableOpacity>
          
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Mot de passe oublié ?</Text>
            <Text style={styles.subtitle}>
              Entrez votre email et nous vous enverrons un lien pour réinitialiser
              votre mot de passe
            </Text>
          </View>
          
          {/* Form */}
          <View style={styles.form}>
            <Input
              label="Email"
              placeholder="votre@email.com"
              leftIcon="mail-outline"
              value={email}
              onChangeText={setEmail}
              error={error}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
            
            <Button
              title="Envoyer le lien"
              onPress={handleReset}
              loading={isLoading}
              fullWidth
              style={styles.submitButton}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  backButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  header: {
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#94A3B8',
    lineHeight: 24,
  },
  form: {
    flex: 1,
  },
  submitButton: {
    marginTop: 16,
  },
  successContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  successIcon: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 12,
  },
  successText: {
    fontSize: 16,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  successButton: {
    minWidth: 200,
  },
});
