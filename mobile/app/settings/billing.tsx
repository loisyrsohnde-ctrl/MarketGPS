/**
 * MarketGPS Mobile - Billing Screen
 * 
 * Uses design tokens from theme/tokens.ts (synced with web)
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/lib/api';
import { Card, Button, LoadingSpinner } from '@/components/ui';
import { useSubscription, useAuthStore, useIsAuthenticated } from '@/store/auth';
import { colors, spacing, radius, typography } from '@/theme/tokens';

export default function BillingScreen() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const subscription = useSubscription();
  const refreshSubscription = useAuthStore((state) => state.refreshSubscription);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isRestoring, setIsRestoring] = React.useState(false);
  
  const handleManageSubscription = async () => {
    setIsLoading(true);
    try {
      const { url } = await api.createPortalSession();
      await WebBrowser.openBrowserAsync(url);
      // Refresh subscription status after returning
      await refreshSubscription();
    } catch (error) {
      Alert.alert('Erreur', 'Impossible d\'ouvrir le portail de gestion');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Restore/sync subscription from server
  const handleRestorePurchase = async () => {
    setIsRestoring(true);
    try {
      await refreshSubscription();
      const updatedSubscription = useAuthStore.getState().subscription;
      
      if (updatedSubscription?.is_active) {
        Alert.alert(
          'Abonnement restauré',
          `Votre abonnement ${updatedSubscription.plan === 'annual' ? 'annuel' : 'mensuel'} a été restauré avec succès.`
        );
      } else {
        Alert.alert(
          'Aucun abonnement actif',
          'Aucun abonnement actif n\'a été trouvé pour ce compte. Si vous pensez qu\'il s\'agit d\'une erreur, contactez le support.'
        );
      }
    } catch (error) {
      Alert.alert(
        'Erreur de synchronisation',
        'Impossible de vérifier votre abonnement. Vérifiez votre connexion internet et réessayez.'
      );
    } finally {
      setIsRestoring(false);
    }
  };
  
  if (!isAuthenticated) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="lock-closed-outline" size={48} color={colors.textMutedSolid} />
        <Text style={styles.centerTitle}>Connexion requise</Text>
        <Text style={styles.centerText}>
          Connectez-vous pour gérer votre abonnement
        </Text>
        <Button
          title="Se connecter"
          onPress={() => router.push('/(auth)/login')}
          style={styles.centerButton}
        />
      </View>
    );
  }
  
  const isPro = subscription?.is_active ?? false;
  const planName = subscription?.plan === 'annual' ? 'Pro Annuel' :
                   subscription?.plan === 'monthly' ? 'Pro Mensuel' : 'Gratuit';
  
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Current Plan */}
      <Card style={styles.planCard}>
        <View style={styles.planHeader}>
          <View style={[styles.planIcon, isPro && styles.planIconPro]}>
            <Ionicons
              name={isPro ? 'diamond' : 'cube-outline'}
              size={32}
              color={isPro ? colors.accent : colors.textMutedSolid}
            />
          </View>
          <View style={styles.planInfo}>
            <Text style={styles.planName}>{planName}</Text>
            <View style={[styles.statusBadge, isPro && styles.statusBadgeActive]}>
              <Text style={[styles.statusText, isPro && styles.statusTextActive]}>
                {subscription?.status === 'active' ? 'Actif' :
                 subscription?.status === 'trialing' ? 'Essai' :
                 subscription?.status === 'past_due' ? 'Impayé' :
                 subscription?.status === 'canceled' ? 'Annulé' : 'Inactif'}
              </Text>
            </View>
          </View>
        </View>
        
        {isPro && (
          <View style={styles.planDetails}>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Prochaine facturation</Text>
              <Text style={styles.detailValue}>
                {formatDate(subscription?.current_period_end)}
              </Text>
            </View>
            {subscription?.cancel_at_period_end && (
              <View style={styles.warningBanner}>
                <Ionicons name="warning-outline" size={18} color={colors.warning} />
                <Text style={styles.warningText}>
                  Annulation programmée à la fin de la période
                </Text>
              </View>
            )}
          </View>
        )}
      </Card>
      
      {/* Actions */}
      {isPro ? (
        <Button
          title="Gérer mon abonnement"
          onPress={handleManageSubscription}
          variant="outline"
          loading={isLoading}
          fullWidth
          icon={<Ionicons name="settings-outline" size={18} color={colors.textPrimary} />}
        />
      ) : (
        <View style={styles.actionsContainer}>
          <Button
            title="Passer à Pro"
            onPress={() => router.push('/checkout')}
            fullWidth
            icon={<Ionicons name="diamond" size={18} color={colors.bgPrimary} />}
          />
          <Button
            title="Restaurer mon achat"
            onPress={handleRestorePurchase}
            variant="ghost"
            loading={isRestoring}
            fullWidth
            icon={<Ionicons name="refresh-outline" size={18} color={colors.accent} />}
            style={styles.restoreButton}
          />
        </View>
      )}
      
      {/* Features Comparison */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Avantages Pro</Text>
        
        <Card padding="none">
          <FeatureRow
            icon="infinite-outline"
            title="Scores illimités"
            description="Calculez autant de scores que vous voulez"
            included={isPro}
          />
          <FeatureRow
            icon="globe-outline"
            title="Tous les marchés"
            description="Accès complet US/EU et Afrique"
            included={isPro}
          />
          <FeatureRow
            icon="layers-outline"
            title="Stratégies avancées"
            description="Templates et simulations"
            included={isPro}
          />
          <FeatureRow
            icon="barbell-outline"
            title="Barbell Builder"
            description="Construisez votre portefeuille optimal"
            included={isPro}
          />
          <FeatureRow
            icon="notifications-outline"
            title="Alertes personnalisées"
            description="Soyez notifié des opportunités"
            included={isPro}
            last
          />
        </Card>
      </View>
      
      {/* Payment Methods */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Paiement sécurisé</Text>
        <Card>
          <View style={styles.paymentLogos}>
            <Ionicons name="card-outline" size={32} color={colors.textMutedSolid} />
            <View style={styles.paymentText}>
              <Text style={styles.paymentTitle}>Paiement via Stripe</Text>
              <Text style={styles.paymentDescription}>
                Vos données bancaires sont sécurisées
              </Text>
            </View>
          </View>
        </Card>
      </View>
    </ScrollView>
  );
}

function FeatureRow({
  icon,
  title,
  description,
  included,
  last = false,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  description: string;
  included: boolean;
  last?: boolean;
}) {
  return (
    <View style={[styles.featureRow, !last && styles.featureRowBorder]}>
      <View style={[styles.featureIcon, included && styles.featureIconActive]}>
        <Ionicons name={icon} size={20} color={included ? colors.accent : colors.textMutedSolid} />
      </View>
      <View style={styles.featureContent}>
        <Text style={styles.featureTitle}>{title}</Text>
        <Text style={styles.featureDescription}>{description}</Text>
      </View>
      <Ionicons
        name={included ? 'checkmark-circle' : 'lock-closed'}
        size={20}
        color={included ? colors.success : colors.textMutedSolid}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bgPrimary,
  },
  content: {
    padding: spacing[5],
    paddingBottom: spacing[10],
  },
  centerContainer: {
    flex: 1,
    backgroundColor: colors.bgPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing[6],
  },
  centerTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
    marginTop: spacing[4],
  },
  centerText: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondarySolid,
    marginTop: spacing[2],
    textAlign: 'center',
  },
  centerButton: {
    marginTop: spacing[6],
    minWidth: 200,
  },
  actionsContainer: {
    gap: spacing[3],
  },
  restoreButton: {
    marginTop: spacing[2],
  },
  planCard: {
    marginBottom: spacing[5],
  },
  planHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  planIcon: {
    width: 64,
    height: 64,
    borderRadius: radius.lg,
    backgroundColor: colors.bgSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  planIconPro: {
    backgroundColor: colors.accentDim,
  },
  planInfo: {
    flex: 1,
    marginLeft: spacing[4],
  },
  planName: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.borderDefault,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginTop: spacing[1],
  },
  statusBadgeActive: {
    backgroundColor: colors.successBg,
  },
  statusText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textMutedSolid,
  },
  statusTextActive: {
    color: colors.success,
  },
  planDetails: {
    marginTop: spacing[5],
    paddingTop: spacing[5],
    borderTopWidth: 1,
    borderTopColor: colors.borderDefault,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailLabel: {
    fontSize: typography.fontSize.sm,
    color: colors.textSecondarySolid,
  },
  detailValue: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.warningBg,
    borderRadius: radius.sm,
    padding: spacing[3],
    marginTop: spacing[3],
    gap: spacing[2],
  },
  warningText: {
    fontSize: typography.fontSize.xs,
    color: colors.warning,
    flex: 1,
  },
  section: {
    marginTop: spacing[8],
  },
  sectionTitle: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textMutedSolid,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing[3],
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing[4],
  },
  featureRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: colors.borderDefault,
  },
  featureIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: colors.bgSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  featureIconActive: {
    backgroundColor: colors.accentDim,
  },
  featureContent: {
    flex: 1,
    marginLeft: spacing[3],
  },
  featureTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  featureDescription: {
    fontSize: typography.fontSize.xs,
    color: colors.textMutedSolid,
    marginTop: 2,
  },
  paymentLogos: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[4],
  },
  paymentText: {
    flex: 1,
  },
  paymentTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
  },
  paymentDescription: {
    fontSize: typography.fontSize.xs,
    color: colors.textMutedSolid,
    marginTop: 2,
  },
});
