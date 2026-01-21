'use client';

import { useState, useMemo, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  AlertCircle,
  Plus,
  Minus,
  Star,
  Sparkles,
  Brain,
  Target,
  Shield,
  Rocket,
  TrendingUp,
  PieChart,
  CheckCircle,
  Lightbulb,
  Wand2,
  Search,
  X,
  Briefcase,
  Edit3,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { ScoreGaugeBadge } from '@/components/ui/badge';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface RiskProfile {
  id: string;
  name: string;
  description: string;
  icon: any;
  color: string;
  volatilityRange: string;
  horizonMin: number;
}

interface Asset {
  ticker: string;
  name: string;
  asset_type: string;
  score_total: number | null;
  vol_annual: number | null;
}

interface StrategyAsset {
  ticker: string;
  name: string;
  weight: number;
  score?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const RISK_PROFILES: RiskProfile[] = [
  {
    id: 'conservative',
    name: 'Conservateur',
    description: 'Capital préservation, revenus stables. Volatilité minimale.',
    icon: Shield,
    color: 'text-score-green',
    volatilityRange: '< 10%',
    horizonMin: 1,
  },
  {
    id: 'balanced',
    name: 'Équilibré',
    description: 'Croissance modérée avec protection. Le juste milieu.',
    icon: Target,
    color: 'text-score-yellow',
    volatilityRange: '10-20%',
    horizonMin: 5,
  },
  {
    id: 'growth',
    name: 'Croissance',
    description: 'Maximiser la croissance long-terme. Tolérance aux fluctuations.',
    icon: TrendingUp,
    color: 'text-accent',
    volatilityRange: '20-30%',
    horizonMin: 10,
  },
  {
    id: 'aggressive',
    name: 'Dynamique',
    description: 'Performance maximale. Forte volatilité acceptée.',
    icon: Rocket,
    color: 'text-score-red',
    volatilityRange: '> 30%',
    horizonMin: 10,
  },
];

const HORIZONS = [
  { value: 1, label: '1 an' },
  { value: 3, label: '3 ans' },
  { value: 5, label: '5 ans' },
  { value: 10, label: '10 ans' },
  { value: 20, label: '20 ans' },
];

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

async function searchAssets(query: string): Promise<Asset[]> {
  if (!query || query.length < 2) return [];
  const res = await fetch(`${API_BASE}/api/assets/search?q=${encodeURIComponent(query)}&limit=20`);
  if (!res.ok) return [];
  const data = await res.json();
  // API returns array directly, not { results: [...] }
  return Array.isArray(data) ? data : (data.results || []);
}

async function getAIRecommendations(profile: string, horizon: number, existingTickers: string[]): Promise<Asset[]> {
  const res = await fetch(`${API_BASE}/api/strategies/ai-suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      risk_profile: profile, 
      horizon_years: horizon,
      exclude_tickers: existingTickers,
      limit: 10
    }),
  });
  if (!res.ok) {
    // Fallback: get top scored assets
    const fallback = await fetch(`${API_BASE}/api/assets/top-scored?market_scope=US_EU&limit=10`);
    if (!fallback.ok) return [];
    return fallback.json();
  }
  return res.json();
}

async function saveStrategy(data: {
  name: string;
  description: string;
  risk_profile: string;
  horizon_years: number;
  compositions: Array<{ ticker: string; weight: number; block_name: string }>;
}): Promise<{ id: number }> {
  const res = await fetch(`${API_BASE}/api/strategies/user?user_id=default`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name,
      description: data.description,
      compositions: data.compositions.map(c => ({
        ticker: c.ticker,
        block_name: c.block_name,
        weight: c.weight,
      })),
    }),
  });
  if (!res.ok) throw new Error('Failed to save strategy');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function StepIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div key={i} className="flex items-center">
          <div
            className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all',
              i < currentStep
                ? 'bg-accent text-white'
                : i === currentStep
                ? 'bg-accent/20 text-accent border-2 border-accent'
                : 'bg-surface text-text-muted'
            )}
          >
            {i < currentStep ? <CheckCircle className="w-4 h-4" /> : i + 1}
          </div>
          {i < totalSteps - 1 && (
            <div
              className={cn(
                'w-12 h-0.5 mx-2',
                i < currentStep ? 'bg-accent' : 'bg-surface'
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}

function AIAssistantCard({
  message,
  suggestions,
  onSuggestionClick,
  isLoading,
}: {
  message: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
  isLoading?: boolean;
}) {
  return (
    <GlassCardAccent>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-accent/20">
            <Brain className="w-5 h-5 text-accent" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-accent">Assistant IA</span>
              <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-xs">BETA</span>
            </div>
            {isLoading ? (
              <div className="flex items-center gap-2 text-text-secondary">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyse en cours...</span>
              </div>
            ) : (
              <>
                <p className="text-sm text-text-secondary">{message}</p>
                {suggestions && suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => onSuggestionClick?.(suggestion)}
                        className="px-3 py-1.5 rounded-lg bg-surface hover:bg-surface-hover text-sm text-text-primary transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </GlassCardAccent>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PAGE CONTENT
// ═══════════════════════════════════════════════════════════════════════════

function NewStrategyPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // Pre-fill ticker if coming from asset drawer
  const initialTicker = searchParams.get('ticker') || '';

  // Wizard state
  const [step, setStep] = useState(1);
  const [strategyName, setStrategyName] = useState('');
  const [strategyDescription, setStrategyDescription] = useState('');
  const [riskProfile, setRiskProfile] = useState<string | null>(null);
  const [horizon, setHorizon] = useState(10);
  const [assets, setAssets] = useState<StrategyAsset[]>(
    initialTicker ? [{ ticker: initialTicker, name: '', weight: 0.1 }] : []
  );
  
  // Success state
  const [createdStrategy, setCreatedStrategy] = useState<{
    id: number;
    name: string;
    description: string;
    risk_profile: string;
    horizon: number;
    positions: number;
  } | null>(null
  );

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Asset[]>([]);

  // AI state
  const [aiRecommendations, setAiRecommendations] = useState<Asset[]>([]);
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  
  // AI Strategy Generation state
  const [aiDescription, setAiDescription] = useState('');
  const [aiGeneratedStrategy, setAiGeneratedStrategy] = useState<{
    strategy_name: string;
    description: string;
    risk_profile: string;
    investment_horizon: number;
    rationale: string;
    blocks: Array<{
      name: string;
      description: string;
      target_weight: number;
      asset_types: string[];
    }>;
    key_principles: string[];
    warnings: string[];
    matched_assets: Record<string, Array<{
      ticker: string;
      name: string;
      score: number;
    }>>;
    explanation: string;
  } | null>(null);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  // Save error state
  const [saveError, setSaveError] = useState<string | null>(null);

  // Mutations
  const saveMutation = useMutation({
    mutationFn: saveStrategy,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['user-strategies'] });
      setSaveError(null);
      // Show success screen instead of redirecting immediately
      setCreatedStrategy({
        id: data.id,
        name: strategyName,
        description: strategyDescription,
        risk_profile: riskProfile || 'balanced',
        horizon: horizon,
        positions: assets.length,
      });
      setStep(4); // Move to success step
    },
    onError: (error: Error) => {
      console.error('Save strategy error:', error);
      setSaveError(error.message || 'Erreur lors de la sauvegarde de la stratégie');
    },
  });

  // Calculate total weight
  const totalWeight = useMemo(() => {
    return assets.reduce((sum, a) => sum + a.weight, 0);
  }, [assets]);

  // Handlers
  const handleSearch = async () => {
    if (!searchQuery || searchQuery.length < 2) return;
    setIsSearching(true);
    try {
      const results = await searchAssets(searchQuery);
      setSearchResults(results);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddAsset = (asset: Asset) => {
    if (assets.find((a) => a.ticker === asset.ticker)) return;
    const remainingWeight = Math.max(0, 1 - totalWeight);
    const defaultWeight = Math.min(remainingWeight, 0.1);
    setAssets([
      ...assets,
      { ticker: asset.ticker, name: asset.name, weight: defaultWeight, score: asset.score_total || undefined },
    ]);
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleRemoveAsset = (ticker: string) => {
    setAssets(assets.filter((a) => a.ticker !== ticker));
  };

  const handleWeightChange = (ticker: string, newWeight: number) => {
    setAssets(
      assets.map((a) =>
        a.ticker === ticker ? { ...a, weight: Math.max(0, Math.min(1, newWeight)) } : a
      )
    );
  };

  const handleGetAIRecommendations = async () => {
    if (!riskProfile) return;
    setIsLoadingAI(true);
    try {
      const recommendations = await getAIRecommendations(
        riskProfile,
        horizon,
        assets.map((a) => a.ticker)
      );
      setAiRecommendations(recommendations);
    } finally {
      setIsLoadingAI(false);
    }
  };

  const handleNormalizeWeights = () => {
    if (assets.length === 0) return;
    const equalWeight = 1 / assets.length;
    setAssets(assets.map((a) => ({ ...a, weight: Math.round(equalWeight * 100) / 100 })));
  };

  // AI Strategy Generation
  const handleGenerateAIStrategy = async () => {
    if (!aiDescription || aiDescription.length < 20) {
      setAiError('Veuillez décrire votre stratégie en au moins 20 caractères');
      return;
    }

    setIsGeneratingAI(true);
    setAiError(null);
    setAiGeneratedStrategy(null);

    try {
      const res = await fetch(`${API_BASE}/api/strategies/ai-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: aiDescription }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Erreur lors de la génération');
      }

      const data = await res.json();
      setAiGeneratedStrategy(data);

      // Auto-fill form with AI suggestions
      if (data.strategy_name) {
        setStrategyName(data.strategy_name);
      }
      if (data.description) {
        setStrategyDescription(data.description);
      }
      if (data.risk_profile) {
        const profileMap: Record<string, string> = {
          conservative: 'conservative',
          balanced: 'balanced',
          growth: 'growth',
          aggressive: 'aggressive',
        };
        setRiskProfile(profileMap[data.risk_profile] || 'balanced');
      }
      if (data.investment_horizon) {
        setHorizon(data.investment_horizon);
      }

    } catch (error: any) {
      console.error('AI generation error:', error);
      setAiError(error.message || 'Erreur lors de la génération de la stratégie');
    } finally {
      setIsGeneratingAI(false);
    }
  };

  // Apply AI-suggested assets to strategy
  const applyAIAssets = () => {
    if (!aiGeneratedStrategy) return;

    const newAssets: StrategyAsset[] = [];

    for (const block of aiGeneratedStrategy.blocks) {
      const blockAssets = aiGeneratedStrategy.matched_assets[block.name] || [];
      const assetWeight = block.target_weight / Math.max(blockAssets.length, 1);

      for (const asset of blockAssets.slice(0, 3)) { // Take top 3 per block
        if (!newAssets.find(a => a.ticker === asset.ticker)) {
          newAssets.push({
            ticker: asset.ticker,
            name: asset.name,
            weight: Math.round(assetWeight * 100) / 100,
            score: asset.score,
          });
        }
      }
    }

    // Normalize weights to sum to 1
    const totalW = newAssets.reduce((s, a) => s + a.weight, 0);
    if (totalW > 0) {
      newAssets.forEach(a => {
        a.weight = Math.round((a.weight / totalW) * 100) / 100;
      });
    }

    setAssets(newAssets);
  };

  const handleApplyAIAssets = () => {
    applyAIAssets();
    setStep(2); // Move to assets step
  };

  // Handle step progression - apply AI assets when moving from step 1 to step 2
  const handleNextStep = () => {
    if (!canProceed()) return;
    
    // If on step 1 and AI has generated a strategy, ALWAYS apply the assets
    // This ensures AI suggestions are used even if user just clicks "Suivant"
    if (step === 1 && aiGeneratedStrategy) {
      applyAIAssets();
    }
    
    setStep(step + 1);
  };

  const handleSave = () => {
    if (!strategyName || assets.length === 0) {
      console.error('Missing strategy name or assets');
      return;
    }
    
    // Normalize weights if they don't sum exactly to 1
    let normalizedAssets = assets;
    if (Math.abs(totalWeight - 1) > 0.01) {
      // Auto-normalize weights to sum to 1
      normalizedAssets = assets.map(a => ({
        ...a,
        weight: a.weight / totalWeight
      }));
    }
    
    saveMutation.mutate({
      name: strategyName,
      description: strategyDescription,
      risk_profile: riskProfile || 'balanced',
      horizon_years: horizon,
      compositions: normalizedAssets.map((a) => ({
        ticker: a.ticker,
        weight: a.weight,
        block_name: 'custom',
      })),
    });
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return !!strategyName && !!riskProfile;
      case 2:
        return assets.length > 0;
      case 3:
        // Allow saving even if weights are slightly off - we'll normalize them
        return assets.length > 0 && totalWeight > 0;
      default:
        return true;
    }
  };

  // AI message based on current state
  const getAIMessage = () => {
    if (step === 1) {
      if (!riskProfile) {
        return "Bienvenue ! Commençons par définir votre profil de risque. Cela m'aidera à vous suggérer les actifs les plus adaptés.";
      }
      const profile = RISK_PROFILES.find((p) => p.id === riskProfile);
      return `Excellent choix ! Avec un profil ${profile?.name.toLowerCase()}, je recommande un horizon d'investissement d'au moins ${profile?.horizonMin} ans pour optimiser les rendements.`;
    }
    if (step === 2) {
      if (assets.length === 0) {
        return "Ajoutez des actifs à votre stratégie. Utilisez la recherche ou laissez-moi vous suggérer des actifs adaptés à votre profil.";
      }
      return `Vous avez ${assets.length} actif(s). Pour une diversification optimale, je recommande entre 5 et 15 positions. Cliquez sur "Suggestions IA" pour des recommandations personnalisées.`;
    }
    if (step === 3) {
      if (Math.abs(totalWeight - 1) > 0.02) {
        return `Le total de vos allocations est de ${(totalWeight * 100).toFixed(0)}%. Ajustez pour atteindre 100%. Utilisez "Égaliser" pour répartir équitablement.`;
      }
      return "Parfait ! Votre allocation est équilibrée. Vérifiez une dernière fois et validez votre stratégie.";
    }
    return "Créez votre stratégie personnalisée étape par étape.";
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/strategies">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
            <Wand2 className="w-6 h-6 text-accent" />
            Créer ma stratégie
          </h1>
          <p className="text-sm text-text-secondary">
            Construisez votre portefeuille personnalisé avec l&apos;aide de l&apos;IA
          </p>
        </div>
      </div>

      {/* Step Indicator */}
      <StepIndicator currentStep={step} totalSteps={step === 4 ? 4 : 3} />

      {/* AI Assistant */}
      <AIAssistantCard
        message={getAIMessage()}
        isLoading={isLoadingAI}
        suggestions={
          step === 1 && !riskProfile
            ? ['Conservateur', 'Équilibré', 'Croissance']
            : undefined
        }
        onSuggestionClick={(suggestion) => {
          const profile = RISK_PROFILES.find(
            (p) => p.name.toLowerCase() === suggestion.toLowerCase()
          );
          if (profile) setRiskProfile(profile.id);
        }}
      />

      {/* Step Content */}
      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* AI Strategy Generator */}
            <GlassCardAccent>
              <div className="p-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-xl bg-gradient-to-br from-accent to-emerald-600">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-text-primary">🪄 Création assistée par IA</h3>
                    <p className="text-sm text-text-secondary">Décrivez votre stratégie et laissez l&apos;IA faire le reste</p>
                  </div>
                </div>
                
                <textarea
                  value={aiDescription}
                  onChange={(e) => setAiDescription(e.target.value)}
                  placeholder="Ex: Je veux une stratégie défensive pour ma retraite dans 15 ans. Je préfère les dividendes stables et une exposition limitée aux marchés émergents. Je suis prêt à accepter une volatilité modérée pour de meilleurs rendements..."
                  rows={4}
                  className="w-full px-4 py-3 bg-bg-primary border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent resize-none mb-4"
                />
                
                {aiError && (
                  <div className="mb-4 p-3 rounded-xl bg-score-red/10 border border-score-red/30 text-score-red text-sm flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    {aiError}
                  </div>
                )}
                
                <Button
                  onClick={handleGenerateAIStrategy}
                  disabled={isGeneratingAI || aiDescription.length < 20}
                  className="w-full bg-gradient-to-r from-accent to-emerald-600 hover:from-accent/90 hover:to-emerald-600/90"
                >
                  {isGeneratingAI ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyse en cours... (peut prendre quelques secondes)
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      Générer ma stratégie avec l&apos;IA
                    </>
                  )}
                </Button>
              </div>
            </GlassCardAccent>

            {/* AI Generated Strategy Display */}
            {aiGeneratedStrategy && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <GlassCard className="border-accent/30 bg-accent/5">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 rounded-xl bg-accent/20">
                      <CheckCircle className="w-5 h-5 text-accent" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold text-lg text-text-primary">
                        {aiGeneratedStrategy.strategy_name}
                      </h3>
                      <p className="text-sm text-text-secondary">
                        {aiGeneratedStrategy.description}
                      </p>
                    </div>
                  </div>

                  {/* Risk & Horizon */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-3 bg-surface rounded-xl">
                      <div className="text-xs text-text-muted uppercase tracking-wider">Profil de risque</div>
                      <div className="text-lg font-bold text-text-primary capitalize">
                        {aiGeneratedStrategy.risk_profile === 'conservative' && '🛡️ Conservateur'}
                        {aiGeneratedStrategy.risk_profile === 'balanced' && '⚖️ Équilibré'}
                        {aiGeneratedStrategy.risk_profile === 'growth' && '📈 Croissance'}
                        {aiGeneratedStrategy.risk_profile === 'aggressive' && '🚀 Dynamique'}
                      </div>
                    </div>
                    <div className="p-3 bg-surface rounded-xl">
                      <div className="text-xs text-text-muted uppercase tracking-wider">Horizon</div>
                      <div className="text-lg font-bold text-text-primary">
                        {aiGeneratedStrategy.investment_horizon} ans
                      </div>
                    </div>
                  </div>

                  {/* Rationale */}
                  <div className="p-4 bg-surface rounded-xl mb-4">
                    <h4 className="font-semibold text-text-primary mb-2 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      Pourquoi cette stratégie ?
                    </h4>
                    <p className="text-sm text-text-secondary leading-relaxed">
                      {aiGeneratedStrategy.rationale}
                    </p>
                  </div>

                  {/* Blocks */}
                  <div className="mb-4">
                    <h4 className="font-semibold text-text-primary mb-3">📊 Composition suggérée</h4>
                    <div className="space-y-2">
                      {aiGeneratedStrategy.blocks.map((block, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-surface rounded-xl">
                          <div className="flex-1">
                            <div className="font-medium text-text-primary">{block.name}</div>
                            <div className="text-xs text-text-muted">{block.description}</div>
                            {aiGeneratedStrategy.matched_assets[block.name]?.length > 0 && (
                              <div className="flex gap-1 mt-1">
                                {aiGeneratedStrategy.matched_assets[block.name].slice(0, 3).map((a) => (
                                  <span key={a.ticker} className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded">
                                    {a.ticker}
                                  </span>
                                ))}
                                {aiGeneratedStrategy.matched_assets[block.name].length > 3 && (
                                  <span className="text-xs text-text-muted">+{aiGeneratedStrategy.matched_assets[block.name].length - 3}</span>
                                )}
                              </div>
                            )}
                          </div>
                          <div className="text-lg font-bold text-accent">
                            {Math.round(block.target_weight * 100)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Key Principles */}
                  {aiGeneratedStrategy.key_principles?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-text-primary mb-2">✅ Principes clés</h4>
                      <ul className="space-y-1">
                        {aiGeneratedStrategy.key_principles.map((p, i) => (
                          <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                            <span className="text-accent">•</span> {p}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Warnings */}
                  {aiGeneratedStrategy.warnings?.length > 0 && (
                    <div className="p-3 rounded-xl bg-score-yellow/10 border border-score-yellow/30">
                      <h4 className="font-semibold text-score-yellow mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Points d&apos;attention
                      </h4>
                      <ul className="space-y-1">
                        {aiGeneratedStrategy.warnings.map((w, i) => (
                          <li key={i} className="text-sm text-score-yellow/80">{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </GlassCard>

                {/* Apply Button */}
                <Button
                  onClick={handleApplyAIAssets}
                  className="w-full bg-accent hover:bg-accent/90"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Appliquer cette stratégie et passer aux actifs
                </Button>
              </motion.div>
            )}

            {/* Divider */}
            {!aiGeneratedStrategy && (
              <div className="flex items-center gap-4">
                <div className="flex-1 h-px bg-glass-border" />
                <span className="text-text-dim text-sm">ou créez manuellement</span>
                <div className="flex-1 h-px bg-glass-border" />
              </div>
            )}

            {/* Name & Description */}
            <GlassCard>
              <h3 className="font-semibold text-text-primary mb-4">Identité de la stratégie</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-text-secondary mb-2 block">
                    Nom de la stratégie *
                  </label>
                  <input
                    type="text"
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                    placeholder="Ex: Mon Portefeuille Croissance 2025"
                    className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-2 block">
                    Description (optionnel)
                  </label>
                  <textarea
                    value={strategyDescription}
                    onChange={(e) => setStrategyDescription(e.target.value)}
                    placeholder="Décrivez l'objectif de cette stratégie..."
                    rows={3}
                    className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent resize-none"
                  />
                </div>
              </div>
            </GlassCard>

            {/* Risk Profile */}
            <GlassCard>
              <h3 className="font-semibold text-text-primary mb-4">Profil de risque *</h3>
              <div className="grid grid-cols-2 gap-4">
                {RISK_PROFILES.map((profile) => {
                  const Icon = profile.icon;
                  return (
                    <button
                      key={profile.id}
                      onClick={() => setRiskProfile(profile.id)}
                      className={cn(
                        'p-4 rounded-xl border transition-all text-left',
                        riskProfile === profile.id
                          ? 'border-accent bg-accent/10'
                          : 'border-glass-border bg-surface hover:bg-surface-hover'
                      )}
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <Icon className={cn('w-5 h-5', profile.color)} />
                        <span className="font-medium text-text-primary">{profile.name}</span>
                      </div>
                      <p className="text-xs text-text-muted">{profile.description}</p>
                      <div className="mt-2 text-xs text-text-dim">
                        Volatilité: {profile.volatilityRange}
                      </div>
                    </button>
                  );
                })}
              </div>
            </GlassCard>

            {/* Horizon */}
            <GlassCard>
              <h3 className="font-semibold text-text-primary mb-4">Horizon d&apos;investissement</h3>
              <div className="flex gap-2">
                {HORIZONS.map((h) => (
                  <button
                    key={h.value}
                    onClick={() => setHorizon(h.value)}
                    className={cn(
                      'flex-1 py-3 rounded-xl text-sm font-medium transition-all',
                      horizon === h.value
                        ? 'bg-accent text-white'
                        : 'bg-surface text-text-secondary hover:bg-surface-hover'
                    )}
                  >
                    {h.label}
                  </button>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Search */}
            <GlassCard>
              <h3 className="font-semibold text-text-primary mb-4">Ajouter des actifs</h3>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="Rechercher un actif (ticker ou nom)..."
                    className="w-full pl-10 pr-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent"
                  />
                </div>
                <Button onClick={handleSearch} disabled={isSearching}>
                  {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rechercher'}
                </Button>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
                  {searchResults.map((asset) => (
                    <div
                      key={asset.ticker}
                      className="flex items-center justify-between p-3 bg-surface rounded-xl"
                    >
                      <div>
                        <span className="font-medium text-accent">{asset.ticker}</span>
                        <span className="text-text-secondary ml-2">{asset.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {asset.score_total && (
                          <ScoreGaugeBadge score={asset.score_total} size="sm" />
                        )}
                        <button
                          onClick={() => handleAddAsset(asset)}
                          className="p-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>

            {/* AI Suggestions */}
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-accent" />
                  Suggestions IA
                </h3>
                <Button
                  onClick={handleGetAIRecommendations}
                  variant="secondary"
                  size="sm"
                  disabled={isLoadingAI || !riskProfile}
                >
                  {isLoadingAI ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Générer des suggestions'
                  )}
                </Button>
              </div>

              {aiRecommendations.length > 0 ? (
                <div className="grid grid-cols-2 gap-3">
                  {aiRecommendations.map((asset) => (
                    <button
                      key={asset.ticker}
                      onClick={() => handleAddAsset(asset)}
                      disabled={assets.some((a) => a.ticker === asset.ticker)}
                      className={cn(
                        'p-3 rounded-xl border text-left transition-all',
                        assets.some((a) => a.ticker === asset.ticker)
                          ? 'border-accent/30 bg-accent/5 opacity-50'
                          : 'border-glass-border bg-surface hover:border-accent/50'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-accent">{asset.ticker}</span>
                        {asset.score_total && (
                          <ScoreGaugeBadge score={asset.score_total} size="sm" />
                        )}
                      </div>
                      <p className="text-xs text-text-muted mt-1 truncate">{asset.name}</p>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-text-muted">
                  <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">
                    Cliquez sur &quot;Générer des suggestions&quot; pour obtenir des recommandations basées
                    sur votre profil
                  </p>
                </div>
              )}
            </GlassCard>

            {/* Selected Assets */}
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary">
                  Actifs sélectionnés ({assets.length})
                </h3>
              </div>

              {assets.length === 0 ? (
                <div className="text-center py-8 text-text-muted">
                  <PieChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Aucun actif sélectionné</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {assets.map((asset) => (
                    <div
                      key={asset.ticker}
                      className="flex items-center justify-between p-3 bg-surface rounded-xl"
                    >
                      <div className="flex-1">
                        <span className="font-medium text-accent">{asset.ticker}</span>
                        {asset.name && (
                          <span className="text-text-muted ml-2 text-sm">{asset.name}</span>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemoveAsset(asset.ticker)}
                        className="p-2 rounded-lg hover:bg-score-red/10 text-text-muted hover:text-score-red transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Allocation */}
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary">Allocation</h3>
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'text-sm font-medium',
                      Math.abs(totalWeight - 1) < 0.02 ? 'text-score-green' : 'text-score-yellow'
                    )}
                  >
                    Total: {(totalWeight * 100).toFixed(0)}%
                  </span>
                  <Button onClick={handleNormalizeWeights} variant="ghost" size="sm">
                    Égaliser
                  </Button>
                </div>
              </div>

              <div className="space-y-3">
                {assets.map((asset) => (
                  <div
                    key={asset.ticker}
                    className="flex items-center gap-4 p-3 bg-surface rounded-xl"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-text-primary">{asset.ticker}</p>
                      <p className="text-xs text-text-muted truncate">{asset.name}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={Math.round(asset.weight * 100)}
                        onChange={(e) =>
                          handleWeightChange(asset.ticker, parseInt(e.target.value) / 100)
                        }
                        className="w-24 accent-accent"
                      />
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={Math.round(asset.weight * 100)}
                        onChange={(e) =>
                          handleWeightChange(asset.ticker, parseInt(e.target.value) / 100)
                        }
                        className="w-16 px-2 py-1 text-sm text-center bg-bg-primary border border-glass-border rounded-lg focus:outline-none focus:border-accent"
                      />
                      <span className="text-sm text-text-muted">%</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Weight Warning */}
              {Math.abs(totalWeight - 1) > 0.1 && (
                <div className="mt-4 p-3 rounded-xl bg-score-yellow/10 border border-score-yellow/30">
                  <div className="flex items-center gap-2 text-score-yellow text-sm">
                    <AlertCircle className="w-4 h-4" />
                    <span>Le total ({(totalWeight * 100).toFixed(0)}%) sera normalisé à 100%</span>
                  </div>
                </div>
              )}

              {/* Save Error */}
              {saveError && (
                <div className="mt-4 p-3 rounded-xl bg-score-red/10 border border-score-red/30">
                  <div className="flex items-center gap-2 text-score-red text-sm">
                    <AlertCircle className="w-4 h-4" />
                    <span>{saveError}</span>
                  </div>
                </div>
              )}
            </GlassCard>

            {/* Summary */}
            <GlassCardAccent>
              <div className="p-4">
                <h3 className="font-semibold text-text-primary mb-4">Résumé</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-text-muted">Nom:</span>
                    <p className="font-medium text-text-primary">{strategyName}</p>
                  </div>
                  <div>
                    <span className="text-text-muted">Profil:</span>
                    <p className="font-medium text-text-primary capitalize">
                      {RISK_PROFILES.find((p) => p.id === riskProfile)?.name || '-'}
                    </p>
                  </div>
                  <div>
                    <span className="text-text-muted">Horizon:</span>
                    <p className="font-medium text-text-primary">{horizon} ans</p>
                  </div>
                  <div>
                    <span className="text-text-muted">Actifs:</span>
                    <p className="font-medium text-text-primary">{assets.length} positions</p>
                  </div>
                </div>
              </div>
            </GlassCardAccent>
          </motion.div>
        )}

        {/* Step 4: Success Screen */}
        {step === 4 && createdStrategy && (
          <motion.div
            key="step4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Success Hero */}
            <div className="text-center py-8">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', delay: 0.2 }}
                className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-accent to-emerald-600 flex items-center justify-center shadow-glow"
              >
                <CheckCircle className="w-10 h-10 text-white" />
              </motion.div>
              <h2 className="text-2xl font-bold text-text-primary mb-2">
                🎉 Stratégie créée avec succès !
              </h2>
              <p className="text-text-secondary">
                Votre stratégie &quot;{createdStrategy.name}&quot; a été sauvegardée
              </p>
            </div>

            {/* Strategy Summary Card */}
            <GlassCardAccent>
              <div className="p-6">
                <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-accent" />
                  {createdStrategy.name}
                </h3>
                
                {createdStrategy.description && (
                  <p className="text-text-secondary mb-4">{createdStrategy.description}</p>
                )}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-surface rounded-xl">
                    <div className="text-xs text-text-muted uppercase tracking-wider">Profil</div>
                    <div className="text-lg font-bold text-text-primary capitalize">
                      {RISK_PROFILES.find((p) => p.id === createdStrategy.risk_profile)?.name || createdStrategy.risk_profile}
                    </div>
                  </div>
                  <div className="p-3 bg-surface rounded-xl">
                    <div className="text-xs text-text-muted uppercase tracking-wider">Horizon</div>
                    <div className="text-lg font-bold text-text-primary">{createdStrategy.horizon} ans</div>
                  </div>
                  <div className="p-3 bg-surface rounded-xl">
                    <div className="text-xs text-text-muted uppercase tracking-wider">Positions</div>
                    <div className="text-lg font-bold text-accent">{createdStrategy.positions}</div>
                  </div>
                  <div className="p-3 bg-surface rounded-xl">
                    <div className="text-xs text-text-muted uppercase tracking-wider">Statut</div>
                    <div className="text-lg font-bold text-score-green flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      Active
                    </div>
                  </div>
                </div>

                {/* Assets List */}
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-text-muted mb-3">Composition</h4>
                  <div className="flex flex-wrap gap-2">
                    {assets.map((asset) => (
                      <span
                        key={asset.ticker}
                        className="px-3 py-1.5 bg-surface rounded-lg text-sm"
                      >
                        <span className="text-accent font-medium">{asset.ticker}</span>
                        <span className="text-text-muted ml-2">{Math.round(asset.weight * 100)}%</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </GlassCardAccent>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/strategies" className="flex-1">
                <Button variant="secondary" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Retour aux stratégies
                </Button>
              </Link>
              <Link href={`/strategies/edit/${createdStrategy.id}`} className="flex-1">
                <Button variant="secondary" className="w-full">
                  <Target className="w-4 h-4 mr-2" />
                  Modifier la stratégie
                </Button>
              </Link>
              <Link href="/strategies/new" className="flex-1">
                <Button className="w-full bg-accent hover:bg-accent/90">
                  <Plus className="w-4 h-4 mr-2" />
                  Créer une autre
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation - Hidden on success step */}
      {step < 4 && (
        <div className="flex items-center justify-between pt-6 border-t border-glass-border">
          <Button
            onClick={() => setStep(step - 1)}
            variant="ghost"
            disabled={step === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Précédent
          </Button>

          {step < 3 ? (
            <Button onClick={handleNextStep} disabled={!canProceed()}>
              Suivant
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleSave}
              disabled={!canProceed() || saveMutation.isPending}
              className="bg-accent hover:bg-accent/90"
            >
              {saveMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Création...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Créer ma stratégie
                </>
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTED PAGE (with Suspense wrapper)
// ═══════════════════════════════════════════════════════════════════════════

export default function NewStrategyPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    }>
      <NewStrategyPageContent />
    </Suspense>
  );
}
