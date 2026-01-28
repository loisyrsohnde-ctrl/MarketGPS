/**
 * MarketGPS Mobile - Login Screen
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
import { signInWithEmail } from '@/lib/supabase';
import { Input, Button } from '@/components/ui';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  
  const validate = () => {
    const newErrors: typeof errors = {};
    
    if (!email) {
      newErrors.email = 'Email requis';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Email invalide';
    }
    
    if (!password) {
      newErrors.password = 'Mot de passe requis';
    } else if (password.length < 6) {
      newErrors.password = 'Minimum 6 caractères';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleLogin = async () => {
    if (!validate()) return;
    
    setIsLoading(true);
    try {
      await signInWithEmail(email, password);
      router.replace('/(tabs)');
    } catch (error) {
      Alert.alert(
        'Erreur de connexion',
        (error as Error).message || 'Impossible de se connecter'
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
            <Text style={styles.title}>Connexion</Text>
            <Text style={styles.subtitle}>
              Accédez à votre compte pour suivre vos investissements
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
              autoComplete="password"
            />
            
            <TouchableOpacity
              style={styles.forgotPassword}
              onPress={() => router.push('/(auth)/forgot-password')}
            >
              <Text style={styles.forgotPasswordText}>
                Mot de passe oublié ?
              </Text>
            </TouchableOpacity>
            
            <Button
              title="Se connecter"
              onPress={handleLogin}
              loading={isLoading}
              fullWidth
              style={styles.submitButton}
            />
          </View>
          
          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>Pas encore de compte ?</Text>
            <TouchableOpacity onPress={() => router.push('/(auth)/signup')}>
              <Text style={styles.footerLink}>Créer un compte</Text>
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
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotPasswordText: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '500',
  },
  submitButton: {
    marginTop: 8,
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
