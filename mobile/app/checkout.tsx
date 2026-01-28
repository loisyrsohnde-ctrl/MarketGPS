/**
 * MarketGPS Mobile - Checkout Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/lib/api';
import { Card, Button } from '@/components/ui';
import { useIsAuthenticated } from '@/store/auth';

const PLANS = [
  {
    id: 'monthly',
    name: 'Pro Mensuel',
    price: '9,99',
    period: '/mois',
    features: [
      'Accès à tous les actifs',
      'Scores illimités',
      'Stratégies avancées',
      'Support prioritaire',
    ],
  },
  {
    id: 'annual',
    name: 'Pro Annuel',
    price: '99,99',
    period: '/an',
    badge: 'Économisez 17%',
    features: [
      'Tout du plan mensuel',
      '2 mois offerts',
      'Accès anticipé aux nouvelles fonctionnalités',
      'Support VIP',
    ],
  },
];

export default function CheckoutScreen() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const [selectedPlan, setSelectedPlan] = useState<'monthly' | 'annual'>('annual');
  const [isLoading, setIsLoading] = useState(false);
  
  const handleCheckout = async () => {
    if (!isAuthenticated) {
      Alert.alert(
        'Connexion requise',
        'Vous devez être connecté pour vous abonner',
        [
          { text: 'Annuler', style: 'cancel' },
          { text: 'Se connecter', onPress: () => router.push('/(auth)/login') },
        ]
      );
      return;
    }
    
    setIsLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    try {
      const { url } = await api.createCheckoutSession(selectedPlan);
      
      // Open Stripe checkout in browser
      const result = await WebBrowser.openAuthSessionAsync(url, 'marketgps://billing/success');
      
      if (result.type === 'success') {
        Alert.alert(
          'Abonnement activé',
          'Votre abonnement Pro est maintenant actif !',
          [{ text: 'OK', onPress: () => router.back() }]
        );
      }
    } catch (error) {
      Alert.alert(
        'Erreur',
        'Impossible de créer la session de paiement. Réessayez plus tard.'
      );
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Ionicons name="diamond" size={48} color="#19D38C" />
          <Text style={styles.title}>Passez à Pro</Text>
          <Text style={styles.subtitle}>
            Débloquez tout le potentiel de MarketGPS
          </Text>
        </View>
        
        {/* Plans */}
        <View style={styles.plans}>
          {PLANS.map((plan) => (
            <TouchableOpacity
              key={plan.id}
              style={[
                styles.planCard,
                selectedPlan === plan.id && styles.planCardSelected,
              ]}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                setSelectedPlan(plan.id as 'monthly' | 'annual');
              }}
              activeOpacity={0.7}
            >
              {plan.badge && (
                <View style={styles.planBadge}>
                  <Text style={styles.planBadgeText}>{plan.badge}</Text>
                </View>
              )}
              
              <View style={styles.planHeader}>
                <View style={styles.planRadio}>
                  {selectedPlan === plan.id && (
                    <View style={styles.planRadioInner} />
                  )}
                </View>
                <View style={styles.planInfo}>
                  <Text style={styles.planName}>{plan.name}</Text>
                  <View style={styles.planPriceRow}>
                    <Text style={styles.planPrice}>{plan.price}€</Text>
                    <Text style={styles.planPeriod}>{plan.period}</Text>
                  </View>
                </View>
              </View>
              
              <View style={styles.planFeatures}>
                {plan.features.map((feature, index) => (
                  <View key={index} style={styles.featureRow}>
                    <Ionicons name="checkmark-circle" size={18} color="#22C55E" />
                    <Text style={styles.featureText}>{feature}</Text>
                  </View>
                ))}
              </View>
            </TouchableOpacity>
          ))}
        </View>
        
        {/* CTA */}
        <View style={styles.cta}>
          <Button
            title={`S'abonner - ${selectedPlan === 'annual' ? '99,99' : '9,99'}€${selectedPlan === 'annual' ? '/an' : '/mois'}`}
            onPress={handleCheckout}
            loading={isLoading}
            fullWidth
            size="lg"
          />
          
          <Text style={styles.terms}>
            En vous abonnant, vous acceptez nos conditions d'utilisation.
            Annulable à tout moment.
          </Text>
        </View>
        
        {/* Guarantees */}
        <View style={styles.guarantees}>
          <View style={styles.guarantee}>
            <Ionicons name="shield-checkmark-outline" size={20} color="#64748B" />
            <Text style={styles.guaranteeText}>Paiement sécurisé</Text>
          </View>
          <View style={styles.guarantee}>
            <Ionicons name="refresh-outline" size={20} color="#64748B" />
            <Text style={styles.guaranteeText}>Annulation facile</Text>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#94A3B8',
    marginTop: 8,
    textAlign: 'center',
  },
  plans: {
    gap: 16,
    marginBottom: 32,
  },
  planCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  planCardSelected: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  planBadge: {
    position: 'absolute',
    top: -10,
    right: 16,
    backgroundColor: '#22C55E',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  planBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  planHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  planRadio: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#64748B',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  planRadioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#19D38C',
  },
  planInfo: {
    flex: 1,
  },
  planName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  planPriceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
  },
  planPrice: {
    fontSize: 24,
    fontWeight: '800',
    color: '#19D38C',
  },
  planPeriod: {
    fontSize: 14,
    color: '#64748B',
  },
  planFeatures: {
    gap: 10,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  featureText: {
    fontSize: 14,
    color: '#CBD5E1',
  },
  cta: {
    marginBottom: 24,
  },
  terms: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 12,
    lineHeight: 18,
  },
  guarantees: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
  },
  guarantee: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  guaranteeText: {
    fontSize: 12,
    color: '#64748B',
  },
});
