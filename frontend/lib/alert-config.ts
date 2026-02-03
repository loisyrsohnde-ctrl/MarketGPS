// ═══════════════════════════════════════════════════════════════════════════
// ALERT CONFIGURATION AND UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

import type {
  AlertType,
  AlertCondition,
  AlertChannel,
  AlertFrequency,
} from '@/types/alerts';

/**
 * Validate alert configuration
 */
export function validateAlertConfig(config: {
  type: AlertType;
  condition: AlertCondition;
  threshold_value?: number;
  range_min?: number;
  range_max?: number;
  channels: AlertChannel[];
}): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check channels
  if (!config.channels || config.channels.length === 0) {
    errors.push('Sélectionnez au moins un canal de notification');
  }

  // Check condition
  const validConditions: AlertCondition[] = ['>', '<', '=', 'enters_range', 'exits_range', 'increases', 'decreases'];
  if (!validConditions.includes(config.condition)) {
    errors.push('Condition invalide');
  }

  // Check threshold based on condition
  if (['>', '<', '=', 'increases', 'decreases'].includes(config.condition)) {
    if (config.threshold_value === undefined || config.threshold_value === null) {
      errors.push('Veuillez entrer une valeur seuil');
    } else if (typeof config.threshold_value !== 'number' || config.threshold_value < 0) {
      errors.push('La valeur seuil doit être un nombre positif');
    }
  }

  // Check range
  if (['enters_range', 'exits_range'].includes(config.condition)) {
    if (
      config.range_min === undefined ||
      config.range_max === undefined
    ) {
      errors.push('Veuillez spécifier la plage (min et max)');
    } else if (config.range_min >= config.range_max) {
      errors.push('La valeur min doit être inférieure à max');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Format alert message for display
 */
export function formatAlertMessage(
  type: AlertType,
  condition: AlertCondition,
  asset_ticker: string,
  threshold_value?: number,
  current_value?: number
): string {
  const conditionSymbol: Record<AlertCondition, string> = {
    '>': '>',
    '<': '<',
    '=': '=',
    'enters_range': '↦',
    'exits_range': '↭',
    'increases': '↑',
    'decreases': '↓',
  };

  const typeLabel: Record<AlertType, string> = {
    price_threshold: 'Prix',
    price_change: 'Prix (variation)',
    score_change: 'Score',
    volatility_change: 'Volatilité',
  };

  const symbol = conditionSymbol[condition];
  const label = typeLabel[type];

  if (current_value !== undefined) {
    return `${asset_ticker}: ${label} ${symbol} ${threshold_value} (actuellement: ${current_value})`;
  }

  return `${asset_ticker}: ${label} ${symbol} ${threshold_value}`;
}

/**
 * Get next alert check time based on frequency
 */
export function getNextAlertCheckTime(frequency: AlertFrequency): Date {
  const now = new Date();

  switch (frequency) {
    case 'immediate':
      return new Date(now.getTime() + 1000); // 1 second

    case 'daily':
      const nextDay = new Date(now);
      nextDay.setDate(nextDay.getDate() + 1);
      nextDay.setHours(9, 0, 0, 0);
      return nextDay;

    case 'weekly':
      const nextWeek = new Date(now);
      nextWeek.setDate(nextWeek.getDate() + ((1 + 7 - nextWeek.getDay()) % 7));
      nextWeek.setHours(9, 0, 0, 0);
      return nextWeek;

    default:
      return new Date(now.getTime() + 1000);
  }
}

/**
 * Check if alert should trigger
 */
export function shouldAlertTrigger(
  condition: AlertCondition,
  currentValue: number,
  threshold_value?: number,
  range_min?: number,
  range_max?: number
): boolean {
  switch (condition) {
    case '>':
      return threshold_value !== undefined && currentValue > threshold_value;

    case '<':
      return threshold_value !== undefined && currentValue < threshold_value;

    case '=':
      return threshold_value !== undefined && currentValue === threshold_value;

    case 'enters_range':
      return (
        range_min !== undefined &&
        range_max !== undefined &&
        currentValue >= range_min &&
        currentValue <= range_max
      );

    case 'exits_range':
      return (
        range_min !== undefined &&
        range_max !== undefined &&
        (currentValue < range_min || currentValue > range_max)
      );

    case 'increases':
      return currentValue > 0;

    case 'decreases':
      return currentValue < 0;

    default:
      return false;
  }
}

/**
 * Convert threshold value for different asset types
 */
export function normalizeThresholdValue(
  value: number | string,
  assetType: string
): number {
  let numValue = typeof value === 'string' ? parseFloat(value) : value;

  // For very small prices (crypto, penny stocks), allow more decimals
  if (numValue < 0.01) {
    return Math.round(numValue * 100000) / 100000; // 5 decimals
  }

  // For small prices, round to 2-4 decimals
  if (numValue < 1) {
    return Math.round(numValue * 10000) / 10000;
  }

  // For normal prices, round to 2 decimals
  return Math.round(numValue * 100) / 100;
}

/**
 * Get alert icon based on type
 */
export function getAlertIcon(type: AlertType): string {
  const icons: Record<AlertType, string> = {
    price_threshold: '💲',
    price_change: '📈',
    score_change: '⭐',
    volatility_change: '📊',
  };
  return icons[type];
}

/**
 * Get alert color based on type
 */
export function getAlertColor(type: AlertType): string {
  const colors: Record<AlertType, string> = {
    price_threshold: 'blue',
    price_change: 'green',
    score_change: 'yellow',
    volatility_change: 'orange',
  };
  return colors[type];
}
