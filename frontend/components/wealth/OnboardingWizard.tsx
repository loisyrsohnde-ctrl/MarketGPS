'use client';

import React, { useState } from 'react';
import {
  MapPin,
  Wallet,
  Target,
  ChevronRight,
  ChevronLeft,
  Check,
  Sparkles,
  Building2,
  TrendingUp,
  Shield,
} from 'lucide-react';

import type { OnboardingAnswers, OnboardingResult } from '@/types/wealth-agent';
import { formatCurrency } from '@/lib/api-wealth';

// =============================================================================
// Types
// =============================================================================

interface OnboardingWizardProps {
  onComplete: (result: OnboardingResult) => void;
  onSubmit: (answers: OnboardingAnswers) => Promise<OnboardingResult>;
  isLoading?: boolean;
}

interface StepProps {
  onNext: () => void;
  onBack?: () => void;
  isFirst?: boolean;
  isLast?: boolean;
}

// =============================================================================
// Location Options
// =============================================================================

const LOCATION_OPTIONS = [
  { code: 'FR', name: 'France', flag: '🇫🇷', cities: ['Paris', 'Lyon', 'Bordeaux', 'Marseille', 'Nantes'] },
  { code: 'BE', name: 'Belgique', flag: '🇧🇪', cities: ['Bruxelles', 'Anvers', 'Gand', 'Liège'] },
  { code: 'DE', name: 'Allemagne', flag: '🇩🇪', cities: ['Berlin', 'Munich', 'Francfort', 'Hambourg'] },
  { code: 'UK', name: 'Royaume-Uni', flag: '🇬🇧', cities: ['Londres', 'Manchester', 'Birmingham'] },
  { code: 'US', name: 'États-Unis', flag: '🇺🇸', cities: ['New York', 'Miami', 'Los Angeles', 'Austin'] },
  { code: 'CA', name: 'Canada', flag: '🇨🇦', cities: ['Montréal', 'Toronto', 'Vancouver'] },
];

const CAPITAL_RANGES = [
  { value: 50000, label: '50 000 €', description: 'Studio ou parking' },
  { value: 100000, label: '100 000 €', description: 'T1-T2 petite ville' },
  { value: 200000, label: '200 000 €', description: 'T2-T3 ville moyenne' },
  { value: 350000, label: '350 000 €', description: 'T3 grande ville' },
  { value: 500000, label: '500 000 €', description: 'Appartement premium' },
  { value: 1000000, label: '1 000 000 €+', description: 'Immeuble ou multi-lots' },
];

// =============================================================================
// Step Components
// =============================================================================

function LocationStep({
  selectedLocations,
  onToggleLocation,
  ...stepProps
}: StepProps & {
  selectedLocations: string[];
  onToggleLocation: (code: string) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-indigo-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <MapPin size={32} className="text-indigo-400" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Où souhaitez-vous investir ?</h2>
        <p className="text-slate-400">
          Sélectionnez un ou plusieurs marchés
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {LOCATION_OPTIONS.map((loc) => {
          const isSelected = selectedLocations.includes(loc.code);
          return (
            <button
              key={loc.code}
              onClick={() => onToggleLocation(loc.code)}
              className={`p-4 rounded-xl border transition-all text-left ${
                isSelected
                  ? 'bg-indigo-500/20 border-indigo-500 ring-1 ring-indigo-500'
                  : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{loc.flag}</span>
                <span className="font-medium">{loc.name}</span>
                {isSelected && <Check size={16} className="text-indigo-400 ml-auto" />}
              </div>
              <p className="text-xs text-slate-400">
                {loc.cities.slice(0, 3).join(', ')}
              </p>
            </button>
          );
        })}
      </div>

      <div className="flex justify-end pt-4">
        <button
          onClick={stepProps.onNext}
          disabled={selectedLocations.length === 0}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 rounded-xl font-medium transition-colors flex items-center gap-2"
        >
          Continuer
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}

function CapitalStep({
  selectedCapital,
  onSelectCapital,
  ...stepProps
}: StepProps & {
  selectedCapital: number | null;
  onSelectCapital: (value: number) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <Wallet size={32} className="text-emerald-400" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Quel est votre capital disponible ?</h2>
        <p className="text-slate-400">
          Apport personnel pour l&apos;investissement
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {CAPITAL_RANGES.map((range) => {
          const isSelected = selectedCapital === range.value;
          return (
            <button
              key={range.value}
              onClick={() => onSelectCapital(range.value)}
              className={`p-4 rounded-xl border transition-all text-left ${
                isSelected
                  ? 'bg-emerald-500/20 border-emerald-500 ring-1 ring-emerald-500'
                  : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
              }`}
            >
              <p className="font-semibold text-lg mb-1">{range.label}</p>
              <p className="text-xs text-slate-400">{range.description}</p>
              {isSelected && (
                <Check size={16} className="text-emerald-400 mt-2" />
              )}
            </button>
          );
        })}
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={stepProps.onBack}
          className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-xl font-medium transition-colors flex items-center gap-2"
        >
          <ChevronLeft size={18} />
          Retour
        </button>
        <button
          onClick={stepProps.onNext}
          disabled={!selectedCapital}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 rounded-xl font-medium transition-colors flex items-center gap-2"
        >
          Continuer
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}

function GoalStep({
  selectedGoal,
  onSelectGoal,
  onSubmit,
  isLoading,
  ...stepProps
}: StepProps & {
  selectedGoal: 'income' | 'wealth' | null;
  onSelectGoal: (goal: 'income' | 'wealth') => void;
  onSubmit: () => void;
  isLoading: boolean;
}) {
  const goals = [
    {
      id: 'income' as const,
      icon: <TrendingUp size={28} className="text-emerald-400" />,
      title: 'Rente Mensuelle',
      subtitle: 'Cash-flow positif dès le départ',
      description: 'Maximiser les revenus locatifs réguliers. Idéal pour compléter vos revenus.',
      features: ['Studios & T2', 'Zones étudiantes', 'Yield 5%+', 'LMNP optimisé'],
    },
    {
      id: 'wealth' as const,
      icon: <Building2 size={28} className="text-indigo-400" />,
      title: 'Patrimoine Long Terme',
      subtitle: 'Plus-value et transmission',
      description: 'Construire un patrimoine valorisable. Vision 10+ ans.',
      features: ['Emplacements premium', 'Diversification', 'Effet de levier', 'Transmission'],
    },
  ];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <Target size={32} className="text-amber-400" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Quel est votre objectif ?</h2>
        <p className="text-slate-400">
          Nous adapterons les recommandations en conséquence
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map((goal) => {
          const isSelected = selectedGoal === goal.id;
          return (
            <button
              key={goal.id}
              onClick={() => onSelectGoal(goal.id)}
              className={`p-6 rounded-xl border transition-all text-left ${
                isSelected
                  ? 'bg-slate-800/80 border-indigo-500 ring-1 ring-indigo-500'
                  : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="p-3 bg-slate-900 rounded-lg">
                  {goal.icon}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{goal.title}</h3>
                  <p className="text-sm text-slate-400 mb-3">{goal.subtitle}</p>
                  <p className="text-xs text-slate-500 mb-4">{goal.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {goal.features.map((feat) => (
                      <span
                        key={feat}
                        className="px-2 py-1 bg-slate-900 rounded text-xs text-slate-400"
                      >
                        {feat}
                      </span>
                    ))}
                  </div>
                </div>
                {isSelected && (
                  <Check size={20} className="text-indigo-400 flex-shrink-0" />
                )}
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={stepProps.onBack}
          className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-xl font-medium transition-colors flex items-center gap-2"
        >
          <ChevronLeft size={18} />
          Retour
        </button>
        <button
          onClick={onSubmit}
          disabled={!selectedGoal || isLoading}
          className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 rounded-xl font-medium transition-all flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
              Génération...
            </>
          ) : (
            <>
              <Sparkles size={18} />
              Générer mon plan
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// Progress Indicator
// =============================================================================

function ProgressIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div
          key={i}
          className={`h-2 rounded-full transition-all ${
            i === currentStep
              ? 'w-8 bg-indigo-500'
              : i < currentStep
              ? 'w-2 bg-indigo-400'
              : 'w-2 bg-slate-700'
          }`}
        />
      ))}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function OnboardingWizard({
  onComplete,
  onSubmit,
  isLoading = false,
}: OnboardingWizardProps) {
  const [step, setStep] = useState(0);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [selectedCapital, setSelectedCapital] = useState<number | null>(null);
  const [selectedGoal, setSelectedGoal] = useState<'income' | 'wealth' | null>(null);

  const handleToggleLocation = (code: string) => {
    setSelectedLocations((prev) =>
      prev.includes(code)
        ? prev.filter((c) => c !== code)
        : [...prev, code]
    );
  };

  const handleSubmit = async () => {
    if (!selectedCapital || !selectedGoal) return;

    const answers: OnboardingAnswers = {
      locations: selectedLocations,
      capital_available: selectedCapital,
      investment_goal: selectedGoal,
      risk_profile: selectedGoal === 'income' ? 'balanced' : 'aggressive',
    };

    try {
      const result = await onSubmit(answers);
      onComplete(result);
    } catch (error) {
      console.error('Onboarding failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Shield className="text-indigo-400" size={24} />
            <span className="text-xl font-semibold">MarketGPS</span>
          </div>
          <p className="text-sm text-slate-400">
            Configurez votre Agent Patrimonial en 3 étapes
          </p>
        </div>

        <ProgressIndicator currentStep={step} totalSteps={3} />

        {/* Card */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8">
          {step === 0 && (
            <LocationStep
              selectedLocations={selectedLocations}
              onToggleLocation={handleToggleLocation}
              onNext={() => setStep(1)}
              isFirst
            />
          )}

          {step === 1 && (
            <CapitalStep
              selectedCapital={selectedCapital}
              onSelectCapital={setSelectedCapital}
              onNext={() => setStep(2)}
              onBack={() => setStep(0)}
            />
          )}

          {step === 2 && (
            <GoalStep
              selectedGoal={selectedGoal}
              onSelectGoal={setSelectedGoal}
              onSubmit={handleSubmit}
              isLoading={isLoading}
              onNext={handleSubmit}
              onBack={() => setStep(1)}
              isLast
            />
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-500 mt-6">
          Vos données restent privées. Aucune promesse de rendement.
        </p>
      </div>
    </div>
  );
}
