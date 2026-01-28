/**
 * MarketGPS Mobile - News Article Screen
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Share,
  Linking,
} from 'react-native';
import { Image } from 'expo-image';
import { useLocalSearchParams, useNavigation } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/lib/api';
import { LoadingSpinner, Button } from '@/components/ui';

export default function NewsArticleScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const navigation = useNavigation();
  
  // Fetch article
  const { data: article, isLoading, error } = useQuery({
    queryKey: ['news', slug],
    queryFn: () => api.getNewsArticle(slug!),
    enabled: !!slug,
  });
  
  // Set navigation title
  React.useLayoutEffect(() => {
    navigation.setOptions({
      headerTitle: 'Article',
    });
  }, [navigation]);
  
  const handleShare = async () => {
    if (!article) return;
    
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    try {
      await Share.share({
        title: article.title,
        message: `${article.title}\n\nLu sur MarketGPS`,
        url: article.source_url,
      });
    } catch (error) {
      console.error('Share error:', error);
    }
  };
  
  const handleOpenSource = () => {
    if (article?.source_url) {
      Linking.openURL(article.source_url);
    }
  };
  
  // Sanitize content - remove markdown formatting for plain text display
  const sanitizeContent = (content?: string) => {
    if (!content) return '';
    return content
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .replace(/#{1,6}\s/g, '')
      .replace(/`{1,3}/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to text
      .replace(/!\[([^\]]*)\]\([^)]+\)/g, '') // Remove images
      .trim();
  };
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };
  
  if (isLoading) {
    return <LoadingSpinner fullScreen message="Chargement de l'article..." />;
  }
  
  if (error || !article) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
        <Text style={styles.errorText}>Impossible de charger l'article</Text>
      </View>
    );
  }
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero Image */}
      {article.image_url && (
        <Image
          source={{ uri: article.image_url }}
          style={styles.heroImage}
          contentFit="cover"
        />
      )}
      
      {/* Tags */}
      <View style={styles.tags}>
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
        {article.sentiment && (
          <View style={[
            styles.tag,
            article.sentiment === 'positive' && styles.positiveTag,
            article.sentiment === 'negative' && styles.negativeTag,
          ]}>
            <Ionicons
              name={article.sentiment === 'positive' ? 'trending-up' : article.sentiment === 'negative' ? 'trending-down' : 'remove'}
              size={12}
              color="#FFFFFF"
            />
          </View>
        )}
      </View>
      
      {/* Title */}
      <Text style={styles.title}>{sanitizeContent(article.title)}</Text>
      
      {/* Meta */}
      <View style={styles.meta}>
        <View style={styles.metaItem}>
          <Ionicons name="newspaper-outline" size={16} color="#64748B" />
          <Text style={styles.metaText}>{article.source_name}</Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="time-outline" size={16} color="#64748B" />
          <Text style={styles.metaText}>{formatDate(article.published_at)}</Text>
        </View>
      </View>
      
      {/* TLDR */}
      {article.tldr && article.tldr.length > 0 && (
        <View style={styles.tldrCard}>
          <Text style={styles.tldrTitle}>En bref</Text>
          {article.tldr.map((point, index) => (
            <View key={index} style={styles.tldrItem}>
              <Ionicons name="checkmark-circle" size={18} color="#19D38C" />
              <Text style={styles.tldrText}>{sanitizeContent(point)}</Text>
            </View>
          ))}
        </View>
      )}
      
      {/* Content */}
      <View style={styles.contentSection}>
        <Text style={styles.contentText}>
          {sanitizeContent(article.content_md || article.excerpt)}
        </Text>
      </View>
      
      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
          <Ionicons name="share-outline" size={20} color="#19D38C" />
          <Text style={styles.actionButtonText}>Partager</Text>
        </TouchableOpacity>
        
        {article.source_url && (
          <TouchableOpacity style={styles.actionButton} onPress={handleOpenSource}>
            <Ionicons name="open-outline" size={20} color="#19D38C" />
            <Text style={styles.actionButtonText}>Source</Text>
          </TouchableOpacity>
        )}
      </View>
      
      {/* Tags Footer */}
      {article.tags && article.tags.length > 0 && (
        <View style={styles.tagsFooter}>
          <Text style={styles.tagsFooterTitle}>Tags</Text>
          <View style={styles.tagsRow}>
            {article.tags.map((tag, index) => (
              <View key={index} style={styles.footerTag}>
                <Text style={styles.footerTagText}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  content: {
    paddingBottom: 40,
  },
  heroImage: {
    width: '100%',
    height: 240,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    padding: 20,
    paddingBottom: 12,
  },
  tag: {
    backgroundColor: '#19D38C20',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  countryTag: {
    backgroundColor: '#8B5CF620',
  },
  positiveTag: {
    backgroundColor: '#22C55E',
  },
  negativeTag: {
    backgroundColor: '#EF4444',
  },
  tagText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#19D38C',
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#F1F5F9',
    lineHeight: 32,
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  meta: {
    flexDirection: 'row',
    gap: 20,
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 13,
    color: '#64748B',
  },
  tldrCard: {
    backgroundColor: '#1E293B',
    marginHorizontal: 20,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  tldrTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#19D38C',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  tldrItem: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  tldrText: {
    flex: 1,
    fontSize: 15,
    color: '#F1F5F9',
    lineHeight: 22,
  },
  contentSection: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  contentText: {
    fontSize: 16,
    color: '#CBD5E1',
    lineHeight: 26,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#1E293B',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#19D38C',
  },
  tagsFooter: {
    paddingHorizontal: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  tagsFooterTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 12,
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  footerTag: {
    backgroundColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  footerTagText: {
    fontSize: 12,
    color: '#94A3B8',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0A0F1C',
    padding: 24,
  },
  errorText: {
    fontSize: 16,
    color: '#94A3B8',
    marginTop: 12,
  },
});
