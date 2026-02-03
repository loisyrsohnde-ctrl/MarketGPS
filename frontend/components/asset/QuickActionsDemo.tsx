'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/glass-card';
import { QuickActions } from './QuickActions';
import { CreateAlertModal } from '@/components/alerts/CreateAlertModal';
import { AssetComparator } from './AssetComparator';
import type { Asset } from '@/types';
import { Info } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// QUICK ACTIONS DEMO
// ═══════════════════════════════════════════════════════════════════════════

interface QuickActionsDemoProps {
  asset: Asset;
}

export function QuickActionsDemo({ asset }: QuickActionsDemoProps) {
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [isComparatorOpen, setIsComparatorOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Info box */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 rounded-lg bg-accent/10 border border-accent/30 flex items-start gap-3"
      >
        <Info className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
        <div className="text-sm text-accent">
          <p className="font-medium mb-1">Actions rapides disponibles:</p>
          <ul className="space-y-1 text-xs opacity-90">
            <li>📌 Ajouter/Retirer de watchlist (raccourci: W)</li>
            <li>🔔 Créer une alerte (raccourci: A)</li>
            <li>📊 Comparer avec d'autres actifs (raccourci: C)</li>
            <li>🤖 Demander à l'IA (raccourci: I)</li>
            <li>📋 Copier les infos (raccourci: Cmd+C)</li>
            <li>🔗 Partager l'actif</li>
          </ul>
        </div>
      </motion.div>

      {/* Demo section */}
      <GlassCard>
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Actions disponibles sur cet actif
        </h2>
        <QuickActions
          asset={asset}
          onOpenAlert={() => setIsAlertModalOpen(true)}
          onOpenComparator={() => setIsComparatorOpen(true)}
          onOpenAIChat={() => console.log('Open AI chat')}
          variant="horizontal"
        />
      </GlassCard>

      {/* Modals */}
      <CreateAlertModal
        isOpen={isAlertModalOpen}
        onClose={() => setIsAlertModalOpen(false)}
        asset={asset}
        onCreateAlert={async (config) => {
          console.log('Create alert:', config);
          // Close after success
          setTimeout(() => setIsAlertModalOpen(false), 1500);
        }}
      />

      <AssetComparator
        isOpen={isComparatorOpen}
        onClose={() => setIsComparatorOpen(false)}
        initialAsset={asset}
        assets={[]}
        onCompare={(selectedAssets) => {
          console.log('Compare:', selectedAssets.map(a => a.ticker));
        }}
      />
    </div>
  );
}

export default QuickActionsDemo;
