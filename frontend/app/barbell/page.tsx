'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Dumbbell, Shield, Rocket, PieChart, Loader2, RefreshCw,
  AlertCircle, ChevronDown, ChevronUp
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Pill } from '@/components/ui/badge';
import { AssetDrawer } from '@/components/barbell/asset-drawer';
import { CandidatesTable } from '@/components/barbell/candidates-table';
import { BarbellBuilder } from '@/components/barbell/barbell-builder';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface BarbellAsset {
  asset_id: string;
  ticker: string;
  name: string;
  asset_type: string;
  allocation_type: 'core' | 'satellite';
  weight: number;
  score_total?: number;
  score_safety?: number;
  score_momentum?: number;
  vol_annual?: number;
  lt_score?: number;
  lt_confidence?: number;
  rationale?: string;
}

interface BarbellSuggestion {
  risk_profile: string;
  core_assets: BarbellAsset[];
  satellite_assets: BarbellAsset[];
  expected_return?: number;
  expected_volatility?: number;
  rationale: string;
}

interface AllocationProfile {
  name: string;
  label: string;
  core_weight: number;
  satellite_weight: number;
  description: string;
}

interface BuilderAsset {
  asset_id: string;
  ticker: string;
  name: string;
  block: 'core' | 'satellite';
  weight: number;
  score_total?: number;
  score_safety?: number;
  score_momentum?: number;
  vol_annual?: number;
  coverage?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function fetchBarbellSuggestion(riskProfile: string): Promise<BarbellSuggestion> {
  const res = await fetch(`${API_BASE}/api/barbell/suggest?risk_profile=${riskProfile}`);
  if (!res.ok) throw new Error('Failed to fetch barbell suggestion');
  return res.json();
}

async function fetchAllocationRatios(): Promise<{ profiles: AllocationProfile[] }> {
  const res = await fetch(`${API_BASE}/api/barbell/allocation-ratios`);
  if (!res.ok) throw new Error('Failed to fetch allocation ratios');
  return res.json();
}

async function savePortfolio(data: {
  name: string;
  risk_profile: string;
  core_ratio: number;
  satellite_ratio: number;
  items: Array<{ asset_id: string; block: string; weight: number }>;
}) {
  const res = await fetch(`${API_BASE}/api/barbell/portfolios?user_id=default_user`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to save portfolio');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function RiskProfileSelector({
  profiles,
  selected,
  onSelect,
}: {
  profiles: AllocationProfile[];
  selected: string;
  onSelect: (profile: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {profiles.map((profile) => (
        <motion.button
          key={profile.name}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSelect(profile.name)}
          className={cn(
            'p-4 rounded-xl border-2 transition-all text-left',
            selected === profile.name
              ? 'border-accent bg-accent-dim'
              : 'border-glass-border bg-surface hover:border-accent/50'
          )}
        >
          <div className="flex items-center gap-3 mb-2">
            <div className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center',
              profile.name === 'conservative' && 'bg-score-green/20 text-score-green',
              profile.name === 'moderate' && 'bg-accent/20 text-accent',
              profile.name === 'aggressive' && 'bg-score-red/20 text-score-red'
            )}>
              {profile.name === 'conservative' && <Shield className="w-5 h-5" />}
              {profile.name === 'moderate' && <PieChart className="w-5 h-5" />}
              {profile.name === 'aggressive' && <Rocket className="w-5 h-5" />}
            </div>
            <span className="font-semibold text-text-primary">{profile.label}</span>
          </div>
          <p className="text-sm text-text-secondary mb-3">{profile.description}</p>
          <div className="flex gap-2">
            <span className="text-xs bg-score-green/20 text-score-green px-2 py-1 rounded">
              Core {Math.round(profile.core_weight * 100)}%
            </span>
            <span className="text-xs bg-score-red/20 text-score-red px-2 py-1 rounded">
              Satellite {Math.round(profile.satellite_weight * 100)}%
            </span>
          </div>
        </motion.button>
      ))}
    </div>
  );
}

function SuggestionCard({ asset, onClick }: { asset: BarbellAsset; onClick: () => void }) {
  const isCore = asset.allocation_type === 'core';
  
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        'p-3 rounded-xl border text-left w-full transition-all',
        isCore ? 'border-score-green/30 bg-score-green/5 hover:border-score-green/50' 
               : 'border-score-red/30 bg-score-red/5 hover:border-score-red/50'
      )}
    >
      <div className="flex items-start justify-between mb-1">
        <div>
          <span className="font-mono font-bold text-text-primary">{asset.ticker}</span>
          <span className={cn(
            'ml-2 text-xs px-2 py-0.5 rounded',
            isCore ? 'bg-score-green/20 text-score-green' : 'bg-score-red/20 text-score-red'
          )}>
            {isCore ? 'Core' : 'Satellite'}
          </span>
        </div>
        <span className="text-sm font-bold text-accent">
          {(asset.weight * 100).toFixed(1)}%
        </span>
      </div>
      <p className="text-xs text-text-secondary truncate">{asset.name}</p>
      {asset.score_total && (
        <div className="mt-2 text-xs text-text-muted">
          Score: {asset.score_total.toFixed(0)}
        </div>
      )}
    </motion.button>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function BarbellPage() {
  // State
  const [selectedProfile, setSelectedProfile] = useState('moderate');
  const [activeTab, setActiveTab] = useState<'suggestion' | 'candidates' | 'builder'>('suggestion');
  const [candidatesTab, setCandidatesTab] = useState<'core' | 'satellite'>('core');
  const [showSuggestion, setShowSuggestion] = useState(true);
  
  // Drawer state
  const [drawerAssetId, setDrawerAssetId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  
  // Builder state
  const [compositions, setCompositions] = useState<BuilderAsset[]>([]);
  
  // Fetch allocation profiles
  const { data: ratiosData } = useQuery({
    queryKey: ['barbell-ratios'],
    queryFn: fetchAllocationRatios,
    staleTime: 1000 * 60 * 60,
  });
  
  // Fetch suggestion based on selected profile
  const { 
    data: suggestion, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['barbell-suggestion', selectedProfile],
    queryFn: () => fetchBarbellSuggestion(selectedProfile),
    staleTime: 1000 * 60 * 5,
  });

  // Save portfolio mutation
  const saveMutation = useMutation({
    mutationFn: savePortfolio,
    onSuccess: () => {
      alert('Portfolio sauvegardé !');
    },
  });
  
  const profiles = ratiosData?.profiles || [
    { name: 'conservative', label: 'Conservateur', core_weight: 0.85, satellite_weight: 0.15, description: 'Priorité à la préservation du capital' },
    { name: 'moderate', label: 'Modéré', core_weight: 0.75, satellite_weight: 0.25, description: 'Équilibre entre sécurité et croissance' },
    { name: 'aggressive', label: 'Dynamique', core_weight: 0.65, satellite_weight: 0.35, description: 'Priorité à la croissance avec risque accru' },
  ];

  const currentProfile = profiles.find(p => p.name === selectedProfile) || profiles[1];

  // Handlers
  const handleOpenDrawer = (assetId: string) => {
    setDrawerAssetId(assetId);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
    setDrawerAssetId(null);
  };

  const handleAddToBuilder = useCallback((asset: any, block?: 'core' | 'satellite') => {
    setCompositions(prev => {
      // Check if already exists
      if (prev.find(c => c.asset_id === asset.asset_id)) {
        return prev;
      }
      
      // Calculate default weight
      const blockType = block || asset.block || (asset.allocation_type === 'core' ? 'core' : 'satellite');
      const targetWeight = blockType === 'core' ? currentProfile.core_weight : currentProfile.satellite_weight;
      const existingBlockWeight = prev
        .filter(c => c.block === blockType)
        .reduce((sum, c) => sum + c.weight, 0);
      const remainingWeight = Math.max(0.01, targetWeight - existingBlockWeight);
      const defaultWeight = Math.min(remainingWeight, 0.1);

      return [...prev, {
        asset_id: asset.asset_id,
        ticker: asset.ticker || asset.symbol,
        name: asset.name,
        block: blockType,
        weight: defaultWeight,
        score_total: asset.score_total,
        score_safety: asset.score_safety,
        score_momentum: asset.score_momentum,
        vol_annual: asset.vol_annual,
        coverage: asset.coverage || asset.confidence,
      }];
    });
    
    // Switch to builder tab
    setActiveTab('builder');
  }, [currentProfile]);

  const handleRemoveFromBuilder = (assetId: string) => {
    setCompositions(prev => prev.filter(c => c.asset_id !== assetId));
  };

  const handleUpdateWeight = (assetId: string, weight: number) => {
    setCompositions(prev => prev.map(c => 
      c.asset_id === assetId ? { ...c, weight: Math.max(0, Math.min(1, weight)) } : c
    ));
  };

  const handleResetToSuggested = () => {
    if (!suggestion) return;
    
    const newComps: BuilderAsset[] = [
      ...suggestion.core_assets.map(a => ({
        asset_id: a.asset_id,
        ticker: a.ticker,
        name: a.name,
        block: 'core' as const,
        weight: a.weight,
        score_total: a.score_total,
        vol_annual: undefined,
      })),
      ...suggestion.satellite_assets.map(a => ({
        asset_id: a.asset_id,
        ticker: a.ticker,
        name: a.name,
        block: 'satellite' as const,
        weight: a.weight,
        score_total: a.score_total,
        vol_annual: undefined,
      })),
    ];
    setCompositions(newComps);
  };

  const handleSavePortfolio = () => {
    saveMutation.mutate({
      name: `Barbell ${selectedProfile} - ${new Date().toLocaleDateString()}`,
      risk_profile: selectedProfile,
      core_ratio: currentProfile.core_weight,
      satellite_ratio: currentProfile.satellite_weight,
      items: compositions.map(c => ({
        asset_id: c.asset_id,
        block: c.block,
        weight: c.weight,
      })),
    });
  };

  const addedAssetIds = compositions.map(c => c.asset_id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
            <Dumbbell className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Stratégie Haltères</h1>
            <p className="text-text-secondary">Portefeuille Core + Satellite personnalisable</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
        </Button>
      </div>
      
      {/* Risk Profile Selector */}
      <div>
        <h2 className="text-lg font-semibold text-text-primary mb-4">Profil de risque</h2>
        <RiskProfileSelector
          profiles={profiles}
          selected={selectedProfile}
          onSelect={setSelectedProfile}
        />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-glass-border pb-2">
        <Pill
          active={activeTab === 'suggestion'}
          onClick={() => setActiveTab('suggestion')}
        >
          💡 Suggestion
        </Pill>
        <Pill
          active={activeTab === 'candidates'}
          onClick={() => setActiveTab('candidates')}
        >
          📋 Candidats
        </Pill>
        <Pill
          active={activeTab === 'builder'}
          onClick={() => setActiveTab('builder')}
        >
          🔧 Builder
          {compositions.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-accent/20 text-accent rounded">
              {compositions.length}
            </span>
          )}
        </Pill>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {/* SUGGESTION TAB */}
        {activeTab === 'suggestion' && (
          <motion.div
            key="suggestion"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {isLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="ml-3 text-text-secondary">Génération du portefeuille...</span>
              </div>
            ) : error ? (
              <GlassCard className="border-score-red/30 bg-score-red/5">
                <div className="flex items-center gap-4">
                  <AlertCircle className="w-8 h-8 text-score-red" />
                  <div>
                    <h3 className="font-semibold text-text-primary">Erreur de chargement</h3>
                    <p className="text-sm text-text-secondary">Impossible de générer le portefeuille.</p>
                  </div>
                </div>
              </GlassCard>
            ) : suggestion ? (
              <>
                {/* Suggestion Header */}
                <GlassCardAccent>
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-text-primary">Portefeuille suggéré</h3>
                      <Button
                        size="sm"
                        onClick={handleResetToSuggested}
                      >
                        Charger dans le Builder
                      </Button>
                    </div>
                    <p className="text-sm text-text-secondary">{suggestion.rationale}</p>
                    
                    {/* Visual Bar */}
                    <div className="mt-4 h-4 rounded-full overflow-hidden flex">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${currentProfile.core_weight * 100}%` }}
                        className="bg-score-green h-full"
                      />
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${currentProfile.satellite_weight * 100}%` }}
                        className="bg-score-red h-full"
                      />
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-text-muted">
                      <span>Core {Math.round(currentProfile.core_weight * 100)}%</span>
                      <span>Satellite {Math.round(currentProfile.satellite_weight * 100)}%</span>
                    </div>
                  </div>
                </GlassCardAccent>

                {/* Assets Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                  {/* Core Assets */}
                  <div>
                    <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                      <Shield className="w-5 h-5 text-score-green" />
                      Core ({suggestion.core_assets.length})
                    </h3>
                    <div className="space-y-2">
                      {suggestion.core_assets.map((asset) => (
                        <SuggestionCard
                          key={asset.asset_id}
                          asset={asset}
                          onClick={() => handleOpenDrawer(asset.asset_id)}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Satellite Assets */}
                  <div>
                    <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                      <Rocket className="w-5 h-5 text-score-red" />
                      Satellite ({suggestion.satellite_assets.length})
                    </h3>
                    <div className="space-y-2">
                      {suggestion.satellite_assets.map((asset) => (
                        <SuggestionCard
                          key={asset.asset_id}
                          asset={asset}
                          onClick={() => handleOpenDrawer(asset.asset_id)}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </motion.div>
        )}

        {/* CANDIDATES TAB */}
        {activeTab === 'candidates' && (
          <motion.div
            key="candidates"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Sub-tabs */}
            <div className="flex gap-2">
              <Pill
                active={candidatesTab === 'core'}
                onClick={() => setCandidatesTab('core')}
              >
                🛡️ Core
              </Pill>
              <Pill
                active={candidatesTab === 'satellite'}
                onClick={() => setCandidatesTab('satellite')}
              >
                🚀 Satellite
              </Pill>
            </div>

            {candidatesTab === 'core' ? (
              <CandidatesTable
                type="core"
                onAddToBuilder={(asset) => handleAddToBuilder(asset, 'core')}
                onSelectAsset={handleOpenDrawer}
                addedAssetIds={addedAssetIds}
              />
            ) : (
              <CandidatesTable
                type="satellite"
                onAddToBuilder={(asset) => handleAddToBuilder(asset, 'satellite')}
                onSelectAsset={handleOpenDrawer}
                addedAssetIds={addedAssetIds}
              />
            )}
          </motion.div>
        )}

        {/* BUILDER TAB */}
        {activeTab === 'builder' && (
          <motion.div
            key="builder"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <BarbellBuilder
              compositions={compositions}
              riskProfile={selectedProfile}
              coreRatio={currentProfile.core_weight}
              satelliteRatio={currentProfile.satellite_weight}
              onUpdateComposition={setCompositions}
              onRemoveAsset={handleRemoveFromBuilder}
              onUpdateWeight={handleUpdateWeight}
              onResetToSuggested={handleResetToSuggested}
              onSave={handleSavePortfolio}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Asset Drawer */}
      <AssetDrawer
        assetId={drawerAssetId}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onAddToBuilder={handleAddToBuilder}
      />
    </div>
  );
}
