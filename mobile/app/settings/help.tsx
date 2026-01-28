/**
 * MarketGPS Mobile - Help Screen
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '@/components/ui';

const FAQ = [
  {
    question: "Comment fonctionne le score MarketGPS ?",
    answer: "Le score MarketGPS combine des indicateurs techniques (RSI, momentum, volatilité), fondamentaux (valuation, croissance) et de sentiment pour donner une note globale de 0 à 100. Plus le score est élevé, plus l'actif est attractif selon notre modèle.",
  },
  {
    question: "Qu'est-ce que la stratégie Barbell ?",
    answer: "La stratégie Barbell divise votre portefeuille entre des actifs sûrs (Core) pour la stabilité et des actifs dynamiques (Satellite) pour la croissance. Cette approche équilibre risque et rendement.",
  },
  {
    question: "Comment ajouter un actif à ma watchlist ?",
    answer: "Sur n'importe quelle page d'actif, appuyez sur l'icône signet en haut à droite. Vous retrouverez ensuite tous vos actifs suivis dans l'onglet Watchlist.",
  },
  {
    question: "Les données sont-elles mises à jour en temps réel ?",
    answer: "Les données de prix sont mises à jour plusieurs fois par jour. Les scores sont recalculés quotidiennement après la clôture des marchés.",
  },
  {
    question: "Comment annuler mon abonnement ?",
    answer: "Allez dans Plus > Abonnement > Gérer mon abonnement. Vous serez redirigé vers le portail Stripe où vous pouvez modifier ou annuler votre abonnement.",
  },
];

export default function HelpScreen() {
  const handleEmail = () => {
    Linking.openURL('mailto:support@marketgps.online');
  };
  
  const handleWebsite = () => {
    Linking.openURL('https://marketgps.online');
  };
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Contact */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Nous contacter</Text>
        <View style={styles.contactRow}>
          <TouchableOpacity style={styles.contactCard} onPress={handleEmail}>
            <View style={styles.contactIcon}>
              <Ionicons name="mail-outline" size={24} color="#19D38C" />
            </View>
            <Text style={styles.contactText}>Email</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.contactCard} onPress={handleWebsite}>
            <View style={styles.contactIcon}>
              <Ionicons name="globe-outline" size={24} color="#19D38C" />
            </View>
            <Text style={styles.contactText}>Site web</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {/* FAQ */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Questions fréquentes</Text>
        {FAQ.map((item, index) => (
          <Card key={index} style={styles.faqCard}>
            <Text style={styles.faqQuestion}>{item.question}</Text>
            <Text style={styles.faqAnswer}>{item.answer}</Text>
          </Card>
        ))}
      </View>
      
      {/* App Info */}
      <Card style={styles.appInfo}>
        <Text style={styles.appName}>MarketGPS Mobile</Text>
        <Text style={styles.appVersion}>Version 1.0.0</Text>
        <Text style={styles.appCopyright}>© 2026 MarketGPS. Tous droits réservés.</Text>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
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
    marginBottom: 12,
  },
  contactRow: {
    flexDirection: 'row',
    gap: 12,
  },
  contactCard: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  contactIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#19D38C20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  contactText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  faqCard: {
    marginBottom: 12,
  },
  faqQuestion: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  faqAnswer: {
    fontSize: 14,
    color: '#94A3B8',
    lineHeight: 20,
  },
  appInfo: {
    alignItems: 'center',
  },
  appName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  appVersion: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  appCopyright: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 8,
  },
});
