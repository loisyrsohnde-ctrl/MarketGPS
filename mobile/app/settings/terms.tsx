/**
 * MarketGPS Mobile - Terms Screen
 */

import React from 'react';
import { ScrollView, Text, StyleSheet } from 'react-native';

export default function TermsScreen() {
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.title}>Conditions Générales d'Utilisation</Text>
      <Text style={styles.date}>Dernière mise à jour : Janvier 2026</Text>
      
      <Text style={styles.heading}>1. Acceptation des conditions</Text>
      <Text style={styles.paragraph}>
        En utilisant l'application MarketGPS, vous acceptez d'être lié par les présentes 
        conditions générales d'utilisation. Si vous n'acceptez pas ces conditions, 
        veuillez ne pas utiliser l'application.
      </Text>
      
      <Text style={styles.heading}>2. Description du service</Text>
      <Text style={styles.paragraph}>
        MarketGPS est une application d'analyse financière qui fournit des scores et 
        des recommandations sur des actifs financiers. Les informations fournies ne 
        constituent pas des conseils en investissement.
      </Text>
      
      <Text style={styles.heading}>3. Compte utilisateur</Text>
      <Text style={styles.paragraph}>
        Vous êtes responsable de la confidentialité de votre compte et de votre 
        mot de passe. Vous acceptez de nous informer immédiatement de toute 
        utilisation non autorisée de votre compte.
      </Text>
      
      <Text style={styles.heading}>4. Abonnement et paiement</Text>
      <Text style={styles.paragraph}>
        Les abonnements Pro sont facturés mensuellement ou annuellement selon le 
        plan choisi. Vous pouvez annuler votre abonnement à tout moment via le 
        portail de gestion Stripe.
      </Text>
      
      <Text style={styles.heading}>5. Limitation de responsabilité</Text>
      <Text style={styles.paragraph}>
        Les informations fournies par MarketGPS sont à titre informatif uniquement. 
        Nous ne garantissons pas l'exactitude, l'exhaustivité ou la pertinence des 
        données. Les décisions d'investissement sont prises à vos propres risques.
      </Text>
      
      <Text style={styles.heading}>6. Propriété intellectuelle</Text>
      <Text style={styles.paragraph}>
        Tout le contenu de l'application, y compris les algorithmes de scoring, 
        est protégé par les droits de propriété intellectuelle et appartient à 
        MarketGPS.
      </Text>
      
      <Text style={styles.heading}>7. Modifications</Text>
      <Text style={styles.paragraph}>
        Nous nous réservons le droit de modifier ces conditions à tout moment. 
        Les modifications prendront effet dès leur publication dans l'application.
      </Text>
      
      <Text style={styles.heading}>8. Contact</Text>
      <Text style={styles.paragraph}>
        Pour toute question concernant ces conditions, contactez-nous à 
        legal@marketgps.online.
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
