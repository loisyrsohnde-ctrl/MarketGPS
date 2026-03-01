/**
 * MarketGPS Mobile - Checkout Screen (Apple IAP)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Button } from '@/components/ui';
import {
  initIAP,
  closeIAP,
  fetchIAPProducts,
  purchaseSubscription,
  restorePurchases,
  hasProSubscription,
  setupPurchaseListeners,
  isUserCancelledError,
  IAP_PRODUCTS,
  type IAPProduct,
} from '@/lib/iap';
import { useAuthStore, useIsAuthenticated } from '@/store/auth';

const PLAN_DETAILS: Record<string, { name: string; period: string; badge?: string; features: string[] }> = {
  [IAP_PRODUCTS.MONTHLY]: {
    name: 'Pro Mensuel',
    period: '/mois',
    features: [
      'Accès à tous les actifs',
      'Scores illimités',
      'Stratégies avancées',
      'Support prioritaire',
    ],
  },
  [IAP_PRODUCTS.ANNUAL]: {
    name: 'Pro Annuel',
    period: '/an',
    badge: 'Économisez 17%',
    features: [
      'Tout du plan mensuel',
      '2 mois offerts',
      'Accès anticipé aux nouvelles fonctionnalités',
      'Support VIP',
    ],
  },
};

export default function CheckoutScreen() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const refreshSubscription = useAuthStore((state) => state.refreshSubscription);
  const setLocalApplePurchase = useAuthStore((state) => state.setLocalApplePurchase);
  const [selectedPlan, setSelectedPlan] = useState<string>(IAP_PRODUCTS.ANNUAL);
  const [isLoading, setIsLoading] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [products, setProducts] = useState<IAPProduct[]>([]);

  useEffect(() => {
    let cleanupListeners: (() => void) | null = null;

    const setup = async () => {
      const connected = await initIAP();
      if (!connected) {
        setIsInitializing(false);
        return;
      }

      // Setup purchase listeners
      cleanupListeners = setupPurchaseListeners(
        async (_purchase) => {
          // Purchase successful - update local Apple purchase state
          setLocalApplePurchase(true);
          setIsLoading(false);

          // Sync with backend if authenticated (optional - not required for access)
          if (isAuthenticated) {
            try {
              await refreshSubscription();
            } catch {
              // Non-critical: local Apple receipt provides access
            }
          }

          Alert.alert(
            'Abonnement activé !',
            'Votre abonnement Pro MarketGPS est maintenant actif.',
            [{ text: 'OK', onPress: () => router.back() }]
          );
        },
        (error) => {
          setIsLoading(false);
          if (!isUserCancelledError(error)) {
            Alert.alert('Erreur', error.message || 'Erreur lors de l\'achat.');
          }
        }
      );

      // Fetch products from App Store
      const subs = await fetchIAPProducts();
      setProducts(subs);
      setIsInitializing(false);
    };

    setup();

    return () => {
      cleanupListeners?.();
      closeIAP();
    };
  }, []);

  const handlePurchase = useCallback(async () => {
    // Check product is available from App Store before attempting purchase
    const product = products.find((p) => p.id === selectedPlan);
    if (!product) {
      Alert.alert(
        'Produits indisponibles',
        'Les offres d\'abonnement ne sont pas disponibles pour le moment. Vérifiez votre connexion et réessayez.',
      );
      return;
    }

    setIsLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await purchaseSubscription(selectedPlan);
      // The purchaseUpdatedListener will handle the success
    } catch (error: unknown) {
      setIsLoading(false);
      if (!isUserCancelledError(error)) {
        Alert.alert(
          'Erreur',
          'Impossible de compléter l\'achat. Réessayez plus tard.'
        );
      }
    }
  }, [selectedPlan, products]);

  const handleRestore = useCallback(async () => {
    setIsRestoring(true);
    try {
      const purchases = await restorePurchases();
      const hasPro = hasProSubscription(purchases);
      if (hasPro) {
        await refreshSubscription();
        Alert.alert(
          'Abonnement restauré',
          'Votre abonnement Pro a été restauré avec succès.',
          [{ text: 'OK', onPress: () => router.back() }]
        );
      } else {
        Alert.alert(
          'Aucun abonnement trouvé',
          'Aucun abonnement actif n\'a été trouvé pour ce compte Apple.'
        );
      }
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de restaurer les achats. Réessayez plus tard.');
    } finally {
      setIsRestoring(false);
    }
  }, [refreshSubscription, router]);

  const getProductPrice = (sku: string): string => {
    const product = products.find((p) => p.id === sku);
    if (product) {
      return product.displayPrice || (sku === IAP_PRODUCTS.ANNUAL ? '99,99€' : '9,99€');
    }
    return sku === IAP_PRODUCTS.ANNUAL ? '99,99€' : '9,99€';
  };

  if (isInitializing) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#19D38C" />
          <Text style={styles.loadingText}>Chargement des offres...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const selectedPeriodLabel = selectedPlan === IAP_PRODUCTS.ANNUAL ? 'an' : 'mois';
  const selectedPrice = getProductPrice(selectedPlan);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={true}
        bounces={true}
        alwaysBounceVertical={true}
      >
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
          {[IAP_PRODUCTS.MONTHLY, IAP_PRODUCTS.ANNUAL].map((sku) => {
            const plan = PLAN_DETAILS[sku];
            const price = getProductPrice(sku);
            return (
              <TouchableOpacity
                key={sku}
                style={[
                  styles.planCard,
                  selectedPlan === sku && styles.planCardSelected,
                ]}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  setSelectedPlan(sku);
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
                    {selectedPlan === sku && (
                      <View style={styles.planRadioInner} />
                    )}
                  </View>
                  <View style={styles.planInfo}>
                    <Text style={styles.planName}>{plan.name}</Text>
                    <View style={styles.planPriceRow}>
                      <Text style={styles.planPrice}>{price}</Text>
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
            );
          })}
        </View>

        {/* CTA */}
        <View style={styles.cta}>
          <Button
            title={`S'abonner - ${selectedPrice}/${selectedPeriodLabel}`}
            onPress={handlePurchase}
            loading={isLoading}
            fullWidth
            size="lg"
          />

          {/* Restore Purchases - Required by Apple */}
          <TouchableOpacity
            style={styles.restoreButton}
            onPress={handleRestore}
            disabled={isRestoring}
          >
            {isRestoring ? (
              <ActivityIndicator size="small" color="#19D38C" />
            ) : (
              <Text style={styles.restoreText}>Restaurer un achat existant</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Apple Required Disclosures - Schedule 2, Section 3.8(b) */}
        <View style={styles.disclosures}>
          <Text style={styles.disclosureText}>
            Le paiement sera débité de votre compte Apple à la confirmation de l'achat.{' '}
            L'abonnement est renouvelé automatiquement au tarif de {selectedPrice}/{selectedPeriodLabel}{' '}
            sauf si le renouvellement automatique est désactivé au moins 24 heures avant{' '}
            la fin de la période en cours. Votre compte sera débité pour le renouvellement{' '}
            dans les 24 heures précédant la fin de la période en cours. Vous pouvez gérer{' '}
            et annuler vos abonnements dans les Réglages de votre compte Apple après l'achat.
          </Text>

          {/* Terms & Privacy Links - Required by Apple */}
          <View style={styles.legalLinks}>
            <TouchableOpacity onPress={() => router.push('/settings/terms')}>
              <Text style={styles.legalLink}>Conditions d'utilisation</Text>
            </TouchableOpacity>
            <Text style={styles.legalSeparator}>|</Text>
            <TouchableOpacity onPress={() => router.push('/settings/privacy')}>
              <Text style={styles.legalLink}>Politique de confidentialité</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Guarantees */}
        <View style={styles.guarantees}>
          <View style={styles.guarantee}>
            <Ionicons name="logo-apple" size={20} color="#64748B" />
            <Text style={styles.guaranteeText}>Paiement sécurisé</Text>
          </View>
          <View style={styles.guarantee}>
            <Ionicons name="refresh-outline" size={20} color="#64748B" />
            <Text style={styles.guaranteeText}>Annulation facile</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    color: '#94A3B8',
  },
  content: {
    padding: 20,
    paddingBottom: 80,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
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
    gap: 12,
    marginBottom: 24,
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
    marginBottom: 16,
    alignItems: 'center',
  },
  restoreButton: {
    marginTop: 14,
    paddingVertical: 8,
  },
  restoreText: {
    fontSize: 14,
    color: '#19D38C',
    textDecorationLine: 'underline',
  },
  disclosures: {
    marginBottom: 24,
    paddingHorizontal: 4,
  },
  disclosureText: {
    fontSize: 11,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 17,
  },
  legalLinks: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 12,
    gap: 8,
  },
  legalLink: {
    fontSize: 12,
    color: '#19D38C',
    textDecorationLine: 'underline',
  },
  legalSeparator: {
    fontSize: 12,
    color: '#475569',
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
