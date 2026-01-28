/**
 * MarketGPS Mobile - Feedback Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Platform,
  KeyboardAvoidingView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useUser } from '@/store/auth';
import { Config } from '@/lib/config';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

type FeedbackType = 'general' | 'bug' | 'feature' | 'question' | 'praise';

interface FeedbackTypeOption {
  type: FeedbackType;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const FEEDBACK_TYPES: FeedbackTypeOption[] = [
  { type: 'general', label: 'Général', icon: 'chatbubble-outline', color: '#3B82F6' },
  { type: 'bug', label: 'Bug', icon: 'bug-outline', color: '#EF4444' },
  { type: 'feature', label: 'Idée', icon: 'bulb-outline', color: '#8B5CF6' },
  { type: 'question', label: 'Question', icon: 'help-circle-outline', color: '#F59E0B' },
  { type: 'praise', label: 'Bravo', icon: 'thumbs-up-outline', color: '#10B981' },
];

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export default function FeedbackScreen() {
  const router = useRouter();
  const user = useUser();

  const [feedbackType, setFeedbackType] = useState<FeedbackType>('general');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const [email, setEmail] = useState(user?.email || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSelectType = (type: FeedbackType) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setFeedbackType(type);
  };

  const handleSelectRating = (star: number) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setRating(rating === star ? null : star);
  };

  const handleSubmit = async () => {
    if (!message.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer un message');
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${Config.API_URL}/feedback/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: feedbackType,
          subject: subject.trim() || null,
          message: message.trim(),
          rating,
          user_email: email.trim() || null,
          platform: Platform.OS,
          app_version: '1.0.0',
          device_info: `${Platform.OS} ${Platform.Version}`,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Échec de l'envoi");
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      Alert.alert(
        'Merci !',
        'Votre feedback a été envoyé avec succès. Nous vous répondrons si nécessaire.',
        [
          {
            text: 'OK',
            onPress: () => router.back(),
          },
        ]
      );
    } catch (error) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert(
        'Erreur',
        error instanceof Error ? error.message : 'Une erreur est survenue'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={24} color="#E5E5E5" />
          </TouchableOpacity>
          <Text style={styles.title}>Feedback</Text>
          <View style={styles.placeholder} />
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Feedback Type */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Type de feedback</Text>
            <View style={styles.typeContainer}>
              {FEEDBACK_TYPES.map((item) => (
                <TouchableOpacity
                  key={item.type}
                  style={[
                    styles.typeButton,
                    feedbackType === item.type && styles.typeButtonSelected,
                    feedbackType === item.type && { borderColor: item.color },
                  ]}
                  onPress={() => handleSelectType(item.type)}
                >
                  <Ionicons
                    name={item.icon}
                    size={20}
                    color={feedbackType === item.type ? item.color : '#64748B'}
                  />
                  <Text
                    style={[
                      styles.typeLabel,
                      feedbackType === item.type && { color: item.color },
                    ]}
                  >
                    {item.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Subject */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Sujet <Text style={styles.optional}>(optionnel)</Text>
            </Text>
            <TextInput
              style={styles.input}
              value={subject}
              onChangeText={setSubject}
              placeholder="Ex: Problème avec le graphique..."
              placeholderTextColor="#64748B"
            />
          </View>

          {/* Message */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Message <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={message}
              onChangeText={setMessage}
              placeholder="Décrivez votre feedback en détail..."
              placeholderTextColor="#64748B"
              multiline
              numberOfLines={5}
              textAlignVertical="top"
            />
          </View>

          {/* Rating */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Note globale <Text style={styles.optional}>(optionnel)</Text>
            </Text>
            <View style={styles.ratingContainer}>
              {[1, 2, 3, 4, 5].map((star) => (
                <TouchableOpacity
                  key={star}
                  style={styles.starButton}
                  onPress={() => handleSelectRating(star)}
                >
                  <Ionicons
                    name={rating && star <= rating ? 'star' : 'star-outline'}
                    size={32}
                    color={rating && star <= rating ? '#F59E0B' : '#64748B'}
                  />
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Email (for non-authenticated users) */}
          {!user?.email && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>
                Votre email <Text style={styles.optional}>(pour recevoir une réponse)</Text>
              </Text>
              <TextInput
                style={styles.input}
                value={email}
                onChangeText={setEmail}
                placeholder="email@example.com"
                placeholderTextColor="#64748B"
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>
          )}

          {/* Submit Button */}
          <TouchableOpacity
            style={[
              styles.submitButton,
              (!message.trim() || isSubmitting) && styles.submitButtonDisabled,
            ]}
            onPress={handleSubmit}
            disabled={!message.trim() || isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#0A0F0D" />
            ) : (
              <>
                <Ionicons name="send" size={20} color="#0A0F0D" />
                <Text style={styles.submitButtonText}>Envoyer</Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// STYLES
// ═══════════════════════════════════════════════════════════════════════════

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F0D',
  },
  flex: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  backButton: {
    padding: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#E5E5E5',
  },
  placeholder: {
    width: 40,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#A3A3A3',
    marginBottom: 12,
  },
  optional: {
    color: '#64748B',
    fontWeight: '400',
  },
  required: {
    color: '#EF4444',
  },
  typeContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#141A17',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  typeButtonSelected: {
    backgroundColor: 'rgba(25, 211, 140, 0.1)',
  },
  typeLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748B',
  },
  input: {
    backgroundColor: '#141A17',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#E5E5E5',
  },
  textArea: {
    height: 120,
    paddingTop: 14,
  },
  ratingContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  starButton: {
    padding: 4,
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#19D38C',
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 8,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0A0F0D',
  },
});
