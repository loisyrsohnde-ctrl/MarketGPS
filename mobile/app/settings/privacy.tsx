/**
 * MarketGPS Mobile - Privacy Policy Screen
 */

import React from 'react';
import { ScrollView, Text, StyleSheet } from 'react-native';

export default function PrivacyScreen() {
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.title}>Politique de Confidentialité</Text>
      <Text style={styles.date}>Dernière mise à jour : Janvier 2026</Text>
      
      <Text style={styles.heading}>1. Collecte des données</Text>
      <Text style={styles.paragraph}>
        Nous collectons les informations que vous nous fournissez lors de la 
        création de votre compte : adresse email, nom d'utilisateur, et préférences.
      </Text>
      
      <Text style={styles.heading}>2. Utilisation des données</Text>
      <Text style={styles.paragraph}>
        Vos données sont utilisées pour personnaliser votre expérience, gérer 
        votre compte et votre abonnement, et vous envoyer des communications 
        relatives au service.
      </Text>
      
      <Text style={styles.heading}>3. Stockage et sécurité</Text>
      <Text style={styles.paragraph}>
        Vos données sont stockées de manière sécurisée via Supabase avec 
        chiffrement. Les données de paiement sont traitées par Stripe et ne 
        sont jamais stockées sur nos serveurs.
      </Text>
      
      <Text style={styles.heading}>4. Partage des données</Text>
      <Text style={styles.paragraph}>
        Nous ne vendons ni ne partageons vos données personnelles avec des 
        tiers, sauf obligation légale ou avec votre consentement explicite.
      </Text>
      
      <Text style={styles.heading}>5. Cookies et analytics</Text>
      <Text style={styles.paragraph}>
        L'application mobile n'utilise pas de cookies. Nous pouvons collecter 
        des données anonymisées d'utilisation pour améliorer le service.
      </Text>
      
      <Text style={styles.heading}>6. Vos droits</Text>
      <Text style={styles.paragraph}>
        Conformément au RGPD, vous avez le droit d'accéder à vos données, de les 
        rectifier, de les supprimer, ou de vous opposer à leur traitement. 
        Contactez-nous pour exercer ces droits.
      </Text>
      
      <Text style={styles.heading}>7. Suppression du compte</Text>
      <Text style={styles.paragraph}>
        Vous pouvez demander la suppression de votre compte et de toutes vos 
        données à tout moment via les paramètres de l'application ou en nous 
        contactant.
      </Text>
      
      <Text style={styles.heading}>8. Contact</Text>
      <Text style={styles.paragraph}>
        Pour toute question relative à la confidentialité, contactez notre DPO à 
        privacy@marketgps.online.
      </Text>
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
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  date: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 24,
  },
  heading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
    marginTop: 20,
    marginBottom: 8,
  },
  paragraph: {
    fontSize: 14,
    color: '#94A3B8',
    lineHeight: 22,
  },
});
