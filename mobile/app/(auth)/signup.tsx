/**
 * MarketGPS Mobile - Signup Screen
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
import { signUpWithEmail } from '@/lib/supabase';
import { Input, Button } from '@/components/ui';

export default function SignupScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});
  
  const validate = () => {
    const newErrors: typeof errors = {};
    
    if (!email) {
      newErrors.email = 'Email requis';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Email invalide';
    }
    
    if (!password) {
      newErrors.password = 'Mot de passe requis';
    } else if (password.length < 8) {
      newErrors.password = 'Minimum 8 caractères';
    }
    
    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSignup = async () => {
    if (!validate()) return;
    
    setIsLoading(true);
    try {
      await signUpWithEmail(email, password);
      Alert.alert(
        'Inscription réussie',
        'Vérifiez votre email pour confirmer votre compte',
        [
          {
            text: 'OK',
            onPress: () => router.replace('/(auth)/login'),
          },
        ]
      );
    } catch (error) {
      Alert.alert(
        'Erreur',
        (error as Error).message || 'Impossible de créer le compte'
      );
    } finally {
      setIsLoading(false);
    }
  };
  
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
            <Text style={styles.logo}>MarketGPS</Text>
            <Text style={styles.title}>Créer un compte</Text>
            <Text style={styles.subtitle}>
              Rejoignez la communauté d'investisseurs éclairés
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
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
            
            <Input
              label="Mot de passe"
              placeholder="••••••••"
              leftIcon="lock-closed-outline"
              value={password}
              onChangeText={setPassword}
              error={errors.password}
              secureTextEntry
              helper="Minimum 8 caractères"
            />
            
            <Input
              label="Confirmer le mot de passe"
              placeholder="••••••••"
              leftIcon="lock-closed-outline"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              error={errors.confirmPassword}
              secureTextEntry
            />
            
            <Button
              title="Créer mon compte"
              onPress={handleSignup}
              loading={isLoading}
              fullWidth
              style={styles.submitButton}
            />
            
            <Text style={styles.terms}>
              En créant un compte, vous acceptez nos{' '}
              <Text style={styles.termsLink}>Conditions d'utilisation</Text>
              {' '}et notre{' '}
              <Text style={styles.termsLink}>Politique de confidentialité</Text>
            </Text>
          </View>
          
          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>Déjà un compte ?</Text>
            <TouchableOpacity onPress={() => router.push('/(auth)/login')}>
              <Text style={styles.footerLink}>Se connecter</Text>
            </TouchableOpacity>
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
  logo: {
    fontSize: 24,
    fontWeight: '800',
    color: '#19D38C',
    marginBottom: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#F1F5F9',
    marginBottom: 8,
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
    marginBottom: 16,
  },
  terms: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 18,
  },
  termsLink: {
    color: '#19D38C',
    fontWeight: '500',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 24,
    gap: 4,
  },
  footerText: {
    fontSize: 14,
    color: '#94A3B8',
  },
  footerLink: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '600',
  },
});
