/**
 * MarketGPS Mobile - Alerte Info Banner
 * Displays breaking news alerts at the top of the news screen
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api, NewsArticle } from '@/lib/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface AlerteInfoBannerProps {
  onDismiss?: () => void;
}

export function AlerteInfoBanner({ onDismiss }: AlerteInfoBannerProps) {
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDismissed, setIsDismissed] = useState(false);
  const fadeAnim = useRef(new Animated.Value(1)).current;

  // Fetch breaking news
  const { data, isLoading } = useQuery({
    queryKey: ['breaking-news'],
    queryFn: () => api.getBreakingNews({ limit: 5, max_age_hours: 6 }),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });

  // Auto-rotate through alerts
  useEffect(() => {
    if (!data?.data.length || data.data.length <= 1) return;

    const interval = setInterval(() => {
      // Fade out
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start(() => {
        setCurrentIndex((prev) => (prev + 1) % data.data.length);
        // Fade in
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }).start();
      });
    }, 6000);

    return () => clearInterval(interval);
  }, [data?.data.length, fadeAnim]);

  // Don't render if no breaking news, loading, or dismissed
  if (isLoading || !data?.has_breaking || isDismissed) {
    return null;
  }

  const currentItem = data.data[currentIndex];
  if (!currentItem) return null;

  const handlePress = () => {
    router.push(`/news/${currentItem.slug}`);
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  // Format time ago
  const formatTimeAgo = (publishedAt?: string): string => {
    if (!publishedAt) return '';

    try {
      const published = new Date(publishedAt);
      const now = new Date();
      const diffMs = now.getTime() - published.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return "À l'instant";
      if (diffMins < 60) return `${diffMins} min`;

      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h`;

      return published.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    } catch {
      return '';
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.content}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        {/* Alert Icon with pulse */}
        <View style={styles.iconContainer}>
          <Ionicons name="alert-circle" size={20} color="#FFFFFF" />
          <View style={styles.pulseIndicator} />
        </View>

        {/* Label */}
        <View style={styles.labelContainer}>
          <Text style={styles.label}>ALERTE INFO</Text>
        </View>

        {/* Divider */}
        <View style={styles.divider} />

        {/* Content */}
        <Animated.View style={[styles.textContainer, { opacity: fadeAnim }]}>
          <Text style={styles.title} numberOfLines={1}>
            {currentItem.title}
          </Text>
          <View style={styles.meta}>
            <Text style={styles.source}>{currentItem.source_name}</Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.time}>{formatTimeAgo(currentItem.published_at)}</Text>
          </View>
        </Animated.View>

        {/* Arrow */}
        <Ionicons name="chevron-forward" size={16} color="#FCA5A5" />
      </TouchableOpacity>

      {/* Indicators (if multiple) */}
      {data.data.length > 1 && (
        <View style={styles.indicators}>
          {data.data.map((_, idx) => (
            <TouchableOpacity
              key={idx}
              onPress={() => setCurrentIndex(idx)}
              style={[
                styles.indicator,
                idx === currentIndex && styles.indicatorActive,
              ]}
            />
          ))}
        </View>
      )}

      {/* Dismiss button */}
      <TouchableOpacity
        style={styles.dismissButton}
        onPress={handleDismiss}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <Ionicons name="close" size={16} color="#FCA5A5" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#DC2626',
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    position: 'relative',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingRight: 24, // Space for dismiss button
  },
  iconContainer: {
    position: 'relative',
  },
  pulseIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FFFFFF',
  },
  labelContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  label: {
    fontSize: 10,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  divider: {
    width: 1,
    height: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  source: {
    fontSize: 10,
    color: '#FCA5A5',
  },
  metaDot: {
    fontSize: 10,
    color: '#FCA5A5',
  },
  time: {
    fontSize: 10,
    color: '#FCA5A5',
  },
  indicators: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 4,
    marginTop: 8,
  },
  indicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  indicatorActive: {
    backgroundColor: '#FFFFFF',
  },
  dismissButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    padding: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 12,
  },
});

export default AlerteInfoBanner;
