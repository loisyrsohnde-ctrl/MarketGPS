/**
 * MarketGPS Mobile - Settings Screen
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
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useAuthStore, useUser, useSubscription, useIsAuthenticated, useIsPro } from '@/store/auth';
import { Card, Button } from '@/components/ui';

interface SettingsItemProps {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle?: string;
  onPress: () => void;
  showChevron?: boolean;
  badge?: string;
  destructive?: boolean;
}

function SettingsItem({
  icon,
  title,
  subtitle,
  onPress,
  showChevron = true,
  badge,
  destructive = false,
}: SettingsItemProps) {
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onPress();
  };
  
  return (
    <TouchableOpacity style={styles.settingsItem} onPress={handlePress}>
      <View style={[styles.iconContainer, destructive && styles.iconDestructive]}>
        <Ionicons
          name={icon}
          size={20}
          color={destructive ? '#EF4444' : '#19D38C'}
        />
      </View>
      <View style={styles.itemContent}>
        <Text style={[styles.itemTitle, destructive && styles.textDestructive]}>
          {title}
        </Text>
        {subtitle && <Text style={styles.itemSubtitle}>{subtitle}</Text>}
      </View>
      {badge && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{badge}</Text>
        </View>
      )}
      {showChevron && (
        <Ionicons name="chevron-forward" size={20} color="#64748B" />
      )}
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const router = useRouter();
  const user = useUser();
  const subscription = useSubscription();
  const isAuthenticated = useIsAuthenticated();
  const isPro = useIsPro();
  const signOut = useAuthStore((state) => state.signOut);

  // Determine if user is Free tier (authenticated but not Pro)
  const isFreeTier = isAuthenticated && !isPro;
  
  const handleSignOut = () => {
    Alert.alert(
      'Déconnexion',
      'Êtes-vous sûr de vouloir vous déconnecter ?',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Déconnexion',
          style: 'destructive',
          onPress: async () => {
            await signOut();
            router.replace('/(auth)/login');
          },
        },
      ]
    );
  };
  
  const planLabel = subscription?.plan === 'annual' ? 'Pro Annuel' :
                    subscription?.plan === 'monthly' ? 'Pro Mensuel' : 'Gratuit';

  // Helper to copy user ID (for debugging/admin purposes)
  const handleCopyUserId = () => {
    if (user?.id) {
      // Show user ID in alert (can be copied)
      Alert.alert(
        'ID Utilisateur',
        user.id,
        [
          { text: 'OK' },
        ]
      );
    }
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Plus</Text>
      </View>
      
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* User Card */}
        {isAuthenticated ? (
          <Card style={styles.userCard}>
            <View style={styles.userInfo}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </Text>
              </View>
              <View style={styles.userText}>
                <Text style={styles.userName}>
                  {user?.email?.split('@')[0] || 'Utilisateur'}
                </Text>
                <Text style={styles.userEmail}>{user?.email}</Text>
              </View>
            </View>
            <TouchableOpacity
              style={[styles.planBadge, subscription?.is_active && styles.planBadgePro]}
              onLongPress={handleCopyUserId}
              delayLongPress={1000}
            >
              <Text style={styles.planBadgeText}>{planLabel}</Text>
            </TouchableOpacity>
          </Card>
        ) : (
          <Card style={styles.loginCard}>
            <Ionicons name="person-circle-outline" size={48} color="#64748B" />
            <Text style={styles.loginTitle}>Bienvenue sur MarketGPS</Text>
            <Text style={styles.loginSubtitle}>
              Connectez-vous ou créez un compte pour accéder à toutes les fonctionnalités
            </Text>
            <View style={styles.authButtons}>
              <Button
                title="Se connecter"
                onPress={() => router.push('/(auth)/login')}
                style={styles.loginButton}
              />
              <TouchableOpacity
                style={styles.signupLink}
                onPress={() => router.push('/(auth)/signup')}
              >
                <Text style={styles.signupLinkText}>
                  Pas de compte ? <Text style={styles.signupLinkHighlight}>Créer un compte</Text>
                </Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}

        {/* Upgrade Banner for Free Users */}
        {isFreeTier && (
          <TouchableOpacity
            style={styles.upgradeBanner}
            onPress={() => router.push('/checkout')}
            activeOpacity={0.8}
          >
            <View style={styles.upgradeBannerContent}>
              <View style={styles.upgradeBannerIcon}>
                <Ionicons name="rocket-outline" size={24} color="#19D38C" />
              </View>
              <View style={styles.upgradeBannerText}>
                <Text style={styles.upgradeBannerTitle}>Passez à Pro</Text>
                <Text style={styles.upgradeBannerSubtitle}>
                  Débloquez Dashboard, Explorer, Watchlist et plus
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#19D38C" />
          </TouchableOpacity>
        )}
        
        {/* Trading Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Trading</Text>
          <Card padding="none">
            <SettingsItem
              icon="layers-outline"
              title="Stratégies"
              subtitle="Gérez vos stratégies d'investissement"
              onPress={() => router.push('/settings/strategies')}
            />
            <SettingsItem
              icon="add-circle-outline"
              title="Créer une stratégie"
              subtitle="Personnalisez votre allocation"
              onPress={() => router.push('/strategy/create')}
            />
            <SettingsItem
              icon="barbell-outline"
              title="Barbell Builder"
              subtitle="Construisez votre portefeuille"
              onPress={() => router.push('/strategy/barbell')}
            />
            <SettingsItem
              icon="trending-up-outline"
              title="Marchés"
              subtitle="US/EU et Afrique"
              onPress={() => router.push('/settings/markets')}
            />
          </Card>
        </View>
        
        {/* Account Section */}
        {isAuthenticated && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Compte</Text>
            <Card padding="none">
              <SettingsItem
                icon="person-outline"
                title="Profil"
                onPress={() => router.push('/settings/profile')}
              />
              <SettingsItem
                icon="card-outline"
                title="Abonnement"
                subtitle={planLabel}
                badge={subscription?.is_active ? 'ACTIF' : undefined}
                onPress={() => router.push('/settings/billing')}
              />
              <SettingsItem
                icon="notifications-outline"
                title="Notifications"
                onPress={() => router.push('/settings/notifications')}
              />
              <SettingsItem
                icon="shield-checkmark-outline"
                title="Sécurité"
                onPress={() => router.push('/settings/security')}
              />
            </Card>
          </View>
        )}
        
        {/* App Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Application</Text>
          <Card padding="none">
            <SettingsItem
              icon="chatbubble-ellipses-outline"
              title="Feedback"
              subtitle="Donnez-nous votre avis"
              onPress={() => router.push('/feedback')}
            />
            <SettingsItem
              icon="help-circle-outline"
              title="Aide & Support"
              onPress={() => router.push('/settings/help')}
            />
            <SettingsItem
              icon="document-text-outline"
              title="Conditions d'utilisation"
              onPress={() => router.push('/settings/terms')}
            />
            <SettingsItem
              icon="lock-closed-outline"
              title="Politique de confidentialité"
              onPress={() => router.push('/settings/privacy')}
            />
            <SettingsItem
              icon="information-circle-outline"
              title="À propos"
              subtitle="Version 1.0.0"
              onPress={() => {}}
              showChevron={false}
            />
          </Card>
        </View>
        
        {/* Sign Out */}
        {isAuthenticated && (
          <View style={styles.section}>
            <Card padding="none">
              <SettingsItem
                icon="log-out-outline"
                title="Déconnexion"
                onPress={handleSignOut}
                showChevron={false}
                destructive
              />
            </Card>
          </View>
        )}
        
        <View style={styles.footer}>
          <Text style={styles.footerText}>MarketGPS</Text>
          <Text style={styles.footerVersion}>Version 1.0.0</Text>
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
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  userCard: {
    marginBottom: 24,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#19D38C',
  },
  userText: {
    marginLeft: 16,
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  userEmail: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 2,
  },
  planBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  planBadgePro: {
    backgroundColor: '#19D38C20',
  },
  planBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#19D38C',
  },
  loginCard: {
    alignItems: 'center',
    marginBottom: 24,
  },
  loginTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
    marginTop: 12,
  },
  loginSubtitle: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 4,
    marginBottom: 16,
    textAlign: 'center',
    lineHeight: 20,
  },
  loginButton: {
    width: '100%',
  },
  authButtons: {
    width: '100%',
  },
  signupLink: {
    marginTop: 16,
    alignItems: 'center',
  },
  signupLinkText: {
    fontSize: 14,
    color: '#94A3B8',
  },
  signupLinkHighlight: {
    color: '#19D38C',
    fontWeight: '600',
  },
  upgradeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#19D38C10',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#19D38C30',
    padding: 16,
    marginBottom: 24,
  },
  upgradeBannerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  upgradeBannerIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  upgradeBannerText: {
    flex: 1,
  },
  upgradeBannerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#19D38C',
  },
  upgradeBannerSubtitle: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 2,
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
    marginBottom: 8,
    marginLeft: 4,
  },
  settingsItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#19D38C10',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconDestructive: {
    backgroundColor: '#EF444410',
  },
  itemContent: {
    flex: 1,
    marginLeft: 12,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#F1F5F9',
  },
  textDestructive: {
    color: '#EF4444',
  },
  itemSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  badge: {
    backgroundColor: '#22C55E',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginRight: 8,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  footer: {
    alignItems: 'center',
    paddingTop: 24,
    paddingBottom: 16,
  },
  footerText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  footerVersion: {
    fontSize: 11,
    color: '#475569',
    marginTop: 2,
  },
});
