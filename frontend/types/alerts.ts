// ═══════════════════════════════════════════════════════════════════════════
// MARKETGPS - Alert Types
// ═══════════════════════════════════════════════════════════════════════════

export type AlertType = 'price_change' | 'score_change' | 'price_threshold' | 'volatility_change';
export type AlertCondition = '>' | '<' | '=' | 'enters_range' | 'exits_range' | 'increases' | 'decreases';
export type AlertChannel = 'in_app' | 'email' | 'webhook';
export type AlertFrequency = 'immediate' | 'daily' | 'weekly';

// ─────────────────────────────────────────────────────────────────────────────
// Alert Configuration
// ─────────────────────────────────────────────────────────────────────────────

export interface AlertRule {
  id: string;
  user_id: string;
  asset_ticker: string;
  type: AlertType;
  condition: AlertCondition;
  threshold_value?: number;
  range_min?: number;
  range_max?: number;
  channels: AlertChannel[];
  frequency: AlertFrequency;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateAlertPayload {
  asset_ticker: string;
  type: AlertType;
  condition: AlertCondition;
  threshold_value?: number;
  range_min?: number;
  range_max?: number;
  channels: AlertChannel[];
  frequency?: AlertFrequency;
  enabled: boolean;
}

export interface AlertNotification {
  id: string;
  rule_id: string;
  asset_ticker: string;
  type: AlertType;
  message: string;
  triggered_value?: number;
  triggered_at: string;
  read: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Alert Type Definitions
// ─────────────────────────────────────────────────────────────────────────────

export const alertTypeDefinitions: Record<AlertType, {
  label: string;
  description: string;
  defaultConditions: AlertCondition[];
  requiresValue: boolean;
}> = {
  price_threshold: {
    label: 'Seuil de prix',
    description: 'Alerte quand le prix atteint un seuil spécifique',
    defaultConditions: ['>', '<', '='],
    requiresValue: true,
  },
  price_change: {
    label: 'Changement de prix',
    description: 'Alerte quand le prix change d\'un certain pourcentage',
    defaultConditions: ['increases', 'decreases'],
    requiresValue: true,
  },
  score_change: {
    label: 'Changement de score',
    description: 'Alerte quand le score MarketGPS change',
    defaultConditions: ['increases', 'decreases'],
    requiresValue: false,
  },
  volatility_change: {
    label: 'Changement de volatilité',
    description: 'Alerte quand la volatilité dépasse un seuil',
    defaultConditions: ['>', '<'],
    requiresValue: true,
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Condition Definitions
// ─────────────────────────────────────────────────────────────────────────────

export const conditionDefinitions: Record<AlertCondition, {
  label: string;
  symbol: string;
  requiresValue: boolean;
}> = {
  '>': {
    label: 'Supérieur à',
    symbol: '>',
    requiresValue: true,
  },
  '<': {
    label: 'Inférieur à',
    symbol: '<',
    requiresValue: true,
  },
  '=': {
    label: 'Égal à',
    symbol: '=',
    requiresValue: true,
  },
  'enters_range': {
    label: 'Entre dans la plage',
    symbol: '∈',
    requiresValue: true,
  },
  'exits_range': {
    label: 'Sort de la plage',
    symbol: '∉',
    requiresValue: true,
  },
  'increases': {
    label: 'Augmente',
    symbol: '↑',
    requiresValue: true,
  },
  'decreases': {
    label: 'Diminue',
    symbol: '↓',
    requiresValue: true,
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Channel Definitions
// ─────────────────────────────────────────────────────────────────────────────

export const channelDefinitions: Record<AlertChannel, {
  label: string;
  description: string;
  icon: string;
}> = {
  in_app: {
    label: 'Dans l\'app',
    description: 'Notification en direct dans MarketGPS',
    icon: '🔔',
  },
  email: {
    label: 'Email',
    description: 'Notification par email',
    icon: '📧',
  },
  webhook: {
    label: 'Webhook',
    description: 'Notification via webhook personnalisé',
    icon: '🔗',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Frequency Definitions
// ─────────────────────────────────────────────────────────────────────────────

export const frequencyDefinitions: Record<AlertFrequency, {
  label: string;
  description: string;
}> = {
  immediate: {
    label: 'Immédiate',
    description: 'Notifier immédiatement quand l\'alerte est déclenchée',
  },
  daily: {
    label: 'Quotidienne',
    description: 'Récapitulatif quotidien des alertes déclenchées',
  },
  weekly: {
    label: 'Hebdomadaire',
    description: 'Récapitulatif hebdomadaire des alertes déclenchées',
  },
};
