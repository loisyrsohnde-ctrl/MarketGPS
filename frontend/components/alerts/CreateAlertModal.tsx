'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import type { Asset } from '@/types';
import { Bell, AlertCircle, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// CREATE ALERT MODAL
// ═══════════════════════════════════════════════════════════════════════════

export type AlertType = 'price_change' | 'score_change' | 'price_threshold';
export type AlertCondition = '>' | '<' | '=' | 'enters_range' | 'exits_range';
export type AlertChannel = 'in_app' | 'email';

export interface AlertConfig {
  asset_ticker: string;
  type: AlertType;
  condition: AlertCondition;
  threshold_value?: number;
  range_min?: number;
  range_max?: number;
  channels: AlertChannel[];
  enabled: boolean;
}

interface CreateAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  asset: Asset;
  onCreateAlert?: (config: AlertConfig) => Promise<void>;
}

const alertTypes: { id: AlertType; label: string; description: string }[] = [
  { id: 'price_change', label: 'Changement de prix', description: 'Alerte sur les variations de prix' },
  { id: 'score_change', label: 'Changement de score', description: 'Alerte quand le score change' },
  { id: 'price_threshold', label: 'Seuil de prix', description: 'Alerte à un prix spécifique' },
];

const conditions: { id: AlertCondition; label: string; symbol: string }[] = [
  { id: '>', label: 'Supérieur à', symbol: '>' },
  { id: '<', label: 'Inférieur à', symbol: '<' },
  { id: '=', label: 'Égal à', symbol: '=' },
];

export function CreateAlertModal({
  isOpen,
  onClose,
  asset,
  onCreateAlert,
}: CreateAlertModalProps) {
  const [alertType, setAlertType] = useState<AlertType>('price_threshold');
  const [condition, setCondition] = useState<AlertCondition>('>');
  const [thresholdValue, setThresholdValue] = useState<string>('');
  const [channels, setChannels] = useState<AlertChannel[]>(['in_app']);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChannelToggle = (channel: AlertChannel) => {
    setChannels((prev) =>
      prev.includes(channel) ? prev.filter((c) => c !== channel) : [...prev, channel]
    );
  };

  const handleCreate = async () => {
    if (!thresholdValue && alertType === 'price_threshold') {
      setError('Veuillez entrer une valeur');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const config: AlertConfig = {
        asset_ticker: asset.ticker,
        type: alertType,
        condition: condition as AlertCondition,
        threshold_value: thresholdValue ? parseFloat(thresholdValue) : undefined,
        channels,
        enabled: true,
      };

      if (onCreateAlert) {
        await onCreateAlert(config);
      }

      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setThresholdValue('');
        setCondition('>');
        setChannels(['in_app']);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Créer une alerte"
      size="md"
    >
      <div className="space-y-6">
        {/* Asset info */}
        <div className="p-4 rounded-lg bg-surface/50 border border-glass-border">
          <p className="text-sm text-text-muted">Asset cible</p>
          <p className="text-lg font-semibold text-text-primary mt-1">
            {asset.ticker} - {asset.name}
          </p>
          {asset.last_price && (
            <p className="text-sm text-text-secondary mt-2">
              Prix actuel: {asset.last_price.toFixed(2)} {asset.currency || 'USD'}
            </p>
          )}
        </div>

        {/* Alert type selection */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-text-primary flex items-center gap-2">
            <Bell className="w-4 h-4 text-accent" />
            Type d'alerte
          </label>
          <div className="grid gap-2">
            {alertTypes.map((type) => (
              <motion.button
                key={type.id}
                whileHover={{ x: 4 }}
                onClick={() => setAlertType(type.id)}
                className={cn(
                  'p-3 rounded-lg text-left transition-all border',
                  alertType === type.id
                    ? 'bg-accent/10 border-accent text-text-primary'
                    : 'bg-surface/50 border-glass-border text-text-secondary hover:border-accent/50'
                )}
              >
                <p className="font-medium">{type.label}</p>
                <p className="text-xs text-text-secondary mt-1">{type.description}</p>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Condition and threshold */}
        {alertType === 'price_threshold' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-primary">Condition</label>
                <select
                  value={condition}
                  onChange={(e) => setCondition(e.target.value as AlertCondition)}
                  className="w-full px-3 py-2 rounded-lg bg-surface border border-glass-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  {conditions.map((cond) => (
                    <option key={cond.id} value={cond.id}>
                      {cond.label} ({cond.symbol})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-text-primary">Valeur</label>
                <input
                  type="number"
                  value={thresholdValue}
                  onChange={(e) => setThresholdValue(e.target.value)}
                  placeholder="Ex: 100"
                  step="0.01"
                  className="w-full px-3 py-2 rounded-lg bg-surface border border-glass-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-text-muted"
                />
              </div>
            </div>
          </div>
        )}

        {/* Channels */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-text-primary">Canaux de notification</label>
          <div className="space-y-2">
            {['in_app', 'email'].map((ch) => (
              <motion.button
                key={ch}
                whileHover={{ x: 2 }}
                onClick={() => handleChannelToggle(ch as AlertChannel)}
                className={cn(
                  'w-full p-3 rounded-lg text-left transition-all border flex items-center gap-3',
                  channels.includes(ch as AlertChannel)
                    ? 'bg-accent/10 border-accent'
                    : 'bg-surface/50 border-glass-border hover:border-accent/50'
                )}
              >
                <div
                  className={cn(
                    'w-5 h-5 rounded border flex items-center justify-center transition-all',
                    channels.includes(ch as AlertChannel)
                      ? 'bg-accent border-accent'
                      : 'border-glass-border'
                  )}
                >
                  {channels.includes(ch as AlertChannel) && (
                    <Check className="w-3 h-3 text-white" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {ch === 'in_app' ? 'Dans l\'app' : 'Email'}
                  </p>
                  <p className="text-xs text-text-secondary mt-0.5">
                    {ch === 'in_app'
                      ? 'Notification en direct dans MarketGPS'
                      : 'Notificationpar email'}
                  </p>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 rounded-lg bg-score-red/10 border border-score-red/30 text-score-red text-sm flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </motion.div>
        )}

        {/* Success message */}
        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 rounded-lg bg-score-green/10 border border-score-green/30 text-score-green text-sm flex items-center gap-2"
          >
            <Check className="w-4 h-4 flex-shrink-0" />
            Alerte créée avec succès
          </motion.div>
        )}

        {/* Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1"
          >
            Annuler
          </Button>
          <Button
            variant="primary"
            onClick={handleCreate}
            disabled={isLoading || !thresholdValue}
            className="flex-1"
          >
            {isLoading ? 'Création...' : 'Créer l\'alerte'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default CreateAlertModal;
