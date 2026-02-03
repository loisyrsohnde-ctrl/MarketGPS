/**
 * MarketGPS Mobile - Morning Brief Screen
 * Résumé quotidien du marché
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, NewsArticle, Asset } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState, NewsCard, ScoreBadge } from '@/components/ui';

// Simple date formatter (replaces date-fns)
const DAYS_FR = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
const MONTHS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

function formatDateFr(date: Date): string {
  const day = DAYS_FR[date.getDay()];
  const dayNum = date.getDate();
  const month = MONTHS_FR[date.getMonth()];
  const year = date.getFullYear();
  return `${day} ${dayNum} ${month} ${year}`;
}

interface MorningBrief {
  date: string;
  market_summary: {
    sentiment: 'bullish' | 'bearish' | 'neutral';
    headline: string;
    key_points: string[];
  };
  top_movers: {
    gainers: Asset[];
    losers: Asset[];
  };
  watchlist_alerts: Array<{
    ticker: string;
    alert_type: string;
    message: string;
  }>;
  featured_news: NewsArticle[];
  opportunities: Array<{
    ticker: string;
    name: string;
    score: number;
    reason: string;
  }>;
}

const SENTIMENT_CONFIG = {
  bullish: { icon: 'trending-up', color: '#22C55E', label: 'Haussier' },
  bearish: { icon: 'trending-down', color: '#EF4444', label: 'Baissier' },
  neutral: { icon: 'remove', color: '#F59E0B', label: 'Neutre' },
};

export default function MorningBriefScreen() {
  const router = useRouter();

  // Fetch morning brief - mock for now as API might not exist
  const { data: brief, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['notifications', 'brief'],
    queryFn: async (): Promise<MorningBrief> => {
      // This would be a real API call
      // return api.getMorningBrief();

      // Mock data for demonstration
      return {
        date: new Date().toISOString(),
        market_summary: {
          sentiment: 'bullish',
          headline: 'Les marchés européens en hausse portés par les techs',
          key_points: [
            'CAC 40 en hausse de 0.8%, porté par LVMH et L\'Oréal',
            'Wall Street attendu en légère hausse après les bons résultats tech',
            'L\'euro stable face au dollar, pétrole en légère baisse',
          ],
        },
        top_movers: {
          gainers: [],
          losers: [],
        },
        watchlist_alerts: [
          {
            ticker: 'AAPL',
            alert_type: 'score_change',
            message: 'Score passé de 72 à 78 (+8%)',
          },
        ],
        featured_news: [],
        opportunities: [
          {
            ticker: 'MSFT',
            name: 'Microsoft',
            score: 85,
            reason: 'Fort momentum + score value élevé',
          },
        ],
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const todayFormatted = formatDateFr(new Date());

  if (isLoading) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Morning Brief',
            headerStyle: { backgroundColor: '#0A0F1C' },
            headerTintColor: '#F1F5F9',
          }}
        />
        <LoadingSpinner fullScreen message="Chargement du brief..." />
      </>
    );
  }

  if (!brief) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Morning Brief',
            headerStyle: { backgroundColor: '#0A0F1C' },
            headerTintColor: '#F1F5F9',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <EmptyState
            icon="sunny-outline"
            title="Brief non disponible"
            description="Le résumé quotidien sera disponible prochainement"
          />
        </SafeAreaView>
      </>
    );
  }

  const sentimentConfig = SENTIMENT_CONFIG[brief.market_summary.sentiment];

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Morning Brief',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#19D38C"
            />
          }
        >
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.dateContainer}>
              <Ionicons name="sunny" size={24} color="#F59E0B" />
              <Text style={styles.dateText}>{todayFormatted}</Text>
            </View>
            <Text style={styles.greeting}>Bonjour ! Voici votre résumé du jour</Text>
          </View>

          {/* Market Sentiment */}
          <Card style={styles.sentimentCard}>
            <View style={styles.sentimentHeader}>
              <View style={[styles.sentimentIcon, { backgroundColor: `${sentimentConfig.color}20` }]}>
                <Ionicons
                  name={sentimentConfig.icon as any}
                  size={24}
                  color={sentimentConfig.color}
                />
              </View>
              <View style={styles.sentimentInfo}>
                <Text style={styles.sentimentLabel}>Sentiment du marché</Text>
                <Text style={[styles.sentimentValue, { color: sentimentConfig.color }]}>
                  {sentimentConfig.label}
                </Text>
              </View>
            </View>

            <Text style={styles.headline}>{brief.market_summary.headline}</Text>

            <View style={styles.keyPoints}>
              {brief.market_summary.key_points.map((point, index) => (
                <View key={index} style={styles.keyPoint}>
                  <View style={styles.bulletPoint} />
                  <Text style={styles.keyPointText}>{point}</Text>
                </View>
              ))}
            </View>
          </Card>

          {/* Watchlist Alerts */}
          {brief.watchlist_alerts && brief.watchlist_alerts.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Alertes Watchlist</Text>
              <Card padding="none">
                {brief.watchlist_alerts.map((alert, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.alertItem,
                      index < brief.watchlist_alerts.length - 1 && styles.alertItemBorder,
                    ]}
                    onPress={() => router.push(`/asset/${alert.ticker}`)}
                  >
                    <View style={styles.alertIcon}>
                      <Ionicons name="alert-circle" size={20} color="#F59E0B" />
                    </View>
                    <View style={styles.alertContent}>
                      <Text style={styles.alertTicker}>{alert.ticker}</Text>
                      <Text style={styles.alertMessage}>{alert.message}</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color="#64748B" />
                  </TouchableOpacity>
                ))}
              </Card>
            </View>
          )}

          {/* Opportunities */}
          {brief.opportunities && brief.opportunities.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Opportunités du jour</Text>
              {brief.opportunities.map((opportunity, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.opportunityCard}
                  onPress={() => router.push(`/asset/${opportunity.ticker}`)}
                >
                  <View style={styles.opportunityHeader}>
                    <View style={styles.opportunityInfo}>
                      <Text style={styles.opportunityTicker}>{opportunity.ticker}</Text>
                      <Text style={styles.opportunityName}>{opportunity.name}</Text>
                    </View>
                    <ScoreBadge score={opportunity.score} size="lg" />
                  </View>
                  <View style={styles.opportunityReason}>
                    <Ionicons name="sparkles" size={16} color="#19D38C" />
                    <Text style={styles.opportunityReasonText}>{opportunity.reason}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Featured News */}
          {brief.featured_news && brief.featured_news.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>À la une</Text>
              {brief.featured_news.map((article) => (
                <NewsCard key={article.slug} article={article} variant="compact" />
              ))}
            </View>
          )}

          {/* Quick Actions */}
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={styles.quickAction}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                router.push('/(tabs)');
              }}
            >
              <Ionicons name="speedometer-outline" size={24} color="#19D38C" />
              <Text style={styles.quickActionText}>Dashboard</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickAction}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                router.push('/(tabs)/news');
              }}
            >
              <Ionicons name="newspaper-outline" size={24} color="#3B82F6" />
              <Text style={styles.quickActionText}>Actualités</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickAction}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                router.push('/(tabs)/watchlist');
              }}
            >
              <Ionicons name="bookmark-outline" size={24} color="#8B5CF6" />
              <Text style={styles.quickActionText}>Watchlist</Text>
            </TouchableOpacity>
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
  header: {
    marginBottom: 24,
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  dateText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F59E0B',
    textTransform: 'capitalize',
  },
  greeting: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  sentimentCard: {
    marginBottom: 24,
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  sentimentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sentimentIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sentimentInfo: {
    marginLeft: 12,
  },
  sentimentLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  sentimentValue: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 2,
  },
  headline: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F1F5F9',
    lineHeight: 24,
    marginBottom: 16,
  },
  keyPoints: {
    gap: 10,
  },
  keyPoint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  bulletPoint: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#19D38C',
    marginTop: 6,
  },
  keyPointText: {
    flex: 1,
    fontSize: 14,
    color: '#94A3B8',
    lineHeight: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  alertItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  alertItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  alertIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#F59E0B20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  alertContent: {
    flex: 1,
    marginLeft: 12,
  },
  alertTicker: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  alertMessage: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 2,
  },
  opportunityCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#19D38C30',
  },
  opportunityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  opportunityInfo: {},
  opportunityTicker: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  opportunityName: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  opportunityReason: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#19D38C10',
    padding: 10,
    borderRadius: 8,
  },
  opportunityReasonText: {
    flex: 1,
    fontSize: 13,
    color: '#19D38C',
    fontWeight: '500',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  quickAction: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    gap: 8,
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
});
