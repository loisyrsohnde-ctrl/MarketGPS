/**
 * MarketGPS Mobile - News Card Component
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { NewsArticle } from '@/lib/api';

interface NewsCardProps {
  article: NewsArticle;
  variant?: 'default' | 'compact' | 'featured';
  onPress?: () => void;
}

export function NewsCard({ article, variant = 'default', onPress }: NewsCardProps) {
  const router = useRouter();
  
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) {
      onPress();
    } else {
      router.push(`/news/${article.slug}`);
    }
  };
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
    });
  };
  
  // Sanitize content - remove markdown formatting
  const sanitizeText = (text?: string) => {
    if (!text) return '';
    return text
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .replace(/#{1,6}\s/g, '')
      .replace(/`/g, '')
      .trim();
  };
  
  if (variant === 'featured') {
    return (
      <TouchableOpacity
        style={styles.featuredContainer}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        <Image
          source={{ uri: article.image_url || 'https://images.pexels.com/photos/3184287/pexels-photo-3184287.jpeg' }}
          style={styles.featuredImage}
          contentFit="cover"
        />
        <View style={styles.featuredOverlay}>
          <View style={styles.tagContainer}>
            {article.category && (
              <View style={styles.tag}>
                <Text style={styles.tagText}>{article.category}</Text>
              </View>
            )}
          </View>
          <Text style={styles.featuredTitle} numberOfLines={3}>
            {sanitizeText(article.title)}
          </Text>
          <View style={styles.metaRow}>
            <Text style={styles.metaText}>{article.source_name}</Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.metaText}>{formatDate(article.published_at)}</Text>
          </View>
        </View>
      </TouchableOpacity>
    );
  }
  
  if (variant === 'compact') {
    return (
      <TouchableOpacity
        style={styles.compactContainer}
        onPress={handlePress}
        activeOpacity={0.7}
      >
        <View style={styles.compactContent}>
          <Text style={styles.compactTitle} numberOfLines={2}>
            {sanitizeText(article.title)}
          </Text>
          <View style={styles.metaRow}>
            <Text style={styles.metaTextSmall}>{article.source_name}</Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.metaTextSmall}>{formatDate(article.published_at)}</Text>
          </View>
        </View>
        {article.image_url && (
          <Image
            source={{ uri: article.image_url }}
            style={styles.compactImage}
            contentFit="cover"
          />
        )}
      </TouchableOpacity>
    );
  }
  
  // Default variant
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      {article.image_url && (
        <Image
          source={{ uri: article.image_url }}
          style={styles.image}
          contentFit="cover"
        />
      )}
      <View style={styles.content}>
        <View style={styles.tagContainer}>
          {article.category && (
            <View style={styles.tag}>
              <Text style={styles.tagText}>{article.category}</Text>
            </View>
          )}
          {article.country && (
            <View style={[styles.tag, styles.countryTag]}>
              <Text style={styles.tagText}>{article.country}</Text>
            </View>
          )}
        </View>
        <Text style={styles.title} numberOfLines={2}>
          {sanitizeText(article.title)}
        </Text>
        {article.excerpt && (
          <Text style={styles.excerpt} numberOfLines={2}>
            {sanitizeText(article.excerpt)}
          </Text>
        )}
        <View style={styles.metaRow}>
          <Ionicons name="newspaper-outline" size={12} color="#64748B" />
          <Text style={styles.metaText}>{article.source_name}</Text>
          <Text style={styles.metaDot}>•</Text>
          <Ionicons name="time-outline" size={12} color="#64748B" />
          <Text style={styles.metaText}>{formatDate(article.published_at)}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  // Default variant
  container: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
  },
  image: {
    width: '100%',
    height: 180,
  },
  content: {
    padding: 16,
  },
  tagContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  tag: {
    backgroundColor: '#19D38C20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  countryTag: {
    backgroundColor: '#8B5CF620',
  },
  tagText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#19D38C',
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    color: '#F1F5F9',
    lineHeight: 24,
  },
  excerpt: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 8,
    lineHeight: 20,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 12,
  },
  metaText: {
    fontSize: 12,
    color: '#64748B',
  },
  metaTextSmall: {
    fontSize: 11,
    color: '#64748B',
  },
  metaDot: {
    color: '#64748B',
    marginHorizontal: 4,
  },
  
  // Featured variant
  featuredContainer: {
    height: 280,
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 16,
  },
  featuredImage: {
    width: '100%',
    height: '100%',
  },
  featuredOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    paddingTop: 60,
    background: 'linear-gradient(transparent, rgba(0,0,0,0.8))',
    backgroundColor: 'rgba(0,0,0,0.6)',
  },
  featuredTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 28,
  },
  
  // Compact variant
  compactContainer: {
    flexDirection: 'row',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  compactContent: {
    flex: 1,
    marginRight: 12,
  },
  compactTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
    lineHeight: 20,
  },
  compactImage: {
    width: 80,
    height: 60,
    borderRadius: 8,
  },
});
