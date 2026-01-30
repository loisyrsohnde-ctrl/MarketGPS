'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Calculator, TrendingUp, Shield, Scale, Building2 } from 'lucide-react';
import { calculateScore, simulateAnnualTax, formatCurrency, formatPercent, getScoreColor, getRatingColor } from '@/lib/api-real-estate';
import type { ProphetIAScore, TaxSimulationResponse, TaxJurisdiction, RiskProfile } from '@/types/wealth';

type Step = 'input' | 'scoring' | 'tax' | 'results';

// Traductions françaises des recommandations
const RECOMMENDATIONS_FR: Record<string, string> = {
  'STRONG_BUY': 'ACHAT FORT',
  'BUY': 'ACHAT',
  'HOLD': 'CONSERVER',
  'SELL': 'VENDRE',
  'STRONG_SELL': 'VENTE FORTE',
};

export default function AnalyzePropertyPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('input');
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    // Financial
    purchase_price: 350000,
    annual_rent: 24000,
    annual_expenses: 4800,
    financing_cost: 8400,
    furniture_value: 5000,
    
    // Building
    year_built: 2005,
    energy_rating: 'C' as const,
    building_condition: 'good' as const,
    
    // Location
    population_growth_5y: 0.03,
    employment_growth_5y: 0.02,
    crime_index: 35,
    school_rating: 7,
    vacancy_rate_area: 0.04,
    
    // Legal
    property_tax_rate: 0.012,
    rent_control: false,
    tenant_protection_level: 'moderate' as const,
    
    // Simulation
    jurisdiction: 'FR' as TaxJurisdiction,
    marginal_tax_rate: 0.30,
    holding_years: 10,
    risk_profile: 'balanced' as RiskProfile,
  });
  
  // Results
  const [score, setScore] = useState<ProphetIAScore | null>(null);
  const [taxSimulation, setTaxSimulation] = useState<TaxSimulationResponse | null>(null);
  
  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };
  
  const handleAnalyze = async () => {
    setLoading(true);
    try {
      // Calculate ProphetIA score
      const scoreResult = await calculateScore({
        purchase_price: formData.purchase_price,
        annual_rent: formData.annual_rent,
        annual_expenses: formData.annual_expenses,
        financing_cost: formData.financing_cost,
        year_built: formData.year_built,
        energy_rating: formData.energy_rating,
        building_condition: formData.building_condition,
        population_growth_5y: formData.population_growth_5y,
        employment_growth_5y: formData.employment_growth_5y,
        crime_index: formData.crime_index,
        school_rating: formData.school_rating,
        vacancy_rate_area: formData.vacancy_rate_area,
        property_tax_rate: formData.property_tax_rate,
        rent_control: formData.rent_control,
        tenant_protection_level: formData.tenant_protection_level,
        risk_profile: formData.risk_profile,
      });
      setScore(scoreResult);
      
      // Run tax simulation
      const taxResult = await simulateAnnualTax({
        property: {
          purchase_price: formData.purchase_price,
          land_ratio: 0.20,
          furniture_value: formData.furniture_value,
          annual_rent: formData.annual_rent,
          annual_charges: formData.annual_expenses,
          annual_interests: formData.financing_cost,
        },
        jurisdiction: formData.jurisdiction,
        marginal_tax_rate: formData.marginal_tax_rate,
        holding_years: formData.holding_years,
      });
      setTaxSimulation(taxResult);
      
      setStep('results');
    } catch (error) {
      console.error('Analyse échouée:', error);
      alert('L\'analyse a échoué. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-8">
      {/* Header */}
      <header className="mb-10">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeft size={18} />
          Retour au Dashboard Patrimoine
        </button>
        <h1 className="text-3xl font-semibold tracking-tight">Analyser un Bien</h1>
        <p className="text-slate-400 mt-1">Score ProphetIA & Simulation Fiscale</p>
      </header>
      
      {step === 'input' && (
        <div className="max-w-4xl mx-auto">
          {/* Property Details Form */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 mb-8">
            <h2 className="text-xl font-medium mb-6 flex items-center gap-2">
              <Building2 size={20} className="text-indigo-400" />
              Détails du Bien
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Financial */}
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Prix d'Achat</label>
                <input
                  type="number"
                  value={formData.purchase_price}
                  onChange={(e) => handleInputChange('purchase_price', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Loyer Annuel</label>
                <input
                  type="number"
                  value={formData.annual_rent}
                  onChange={(e) => handleInputChange('annual_rent', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Charges Annuelles</label>
                <input
                  type="number"
                  value={formData.annual_expenses}
                  onChange={(e) => handleInputChange('annual_expenses', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Intérêts d'Emprunt Annuels</label>
                <input
                  type="number"
                  value={formData.financing_cost}
                  onChange={(e) => handleInputChange('financing_cost', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              
              {/* Building */}
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Année de Construction</label>
                <input
                  type="number"
                  value={formData.year_built}
                  onChange={(e) => handleInputChange('year_built', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Classe DPE</label>
                <select
                  value={formData.energy_rating}
                  onChange={(e) => handleInputChange('energy_rating', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                >
                  {['A', 'B', 'C', 'D', 'E', 'F', 'G'].map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
              
              {/* Jurisdiction */}
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Juridiction Fiscale</label>
                <select
                  value={formData.jurisdiction}
                  onChange={(e) => handleInputChange('jurisdiction', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="FR">France (LMNP)</option>
                  <option value="US">États-Unis</option>
                  <option value="CA">Canada</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Taux Marginal d'Imposition</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="0.6"
                  value={formData.marginal_tax_rate}
                  onChange={(e) => handleInputChange('marginal_tax_rate', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
          
          {/* Analyze Button */}
          <div className="flex justify-center">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 rounded-xl font-medium transition-all flex items-center gap-3"
            >
              {loading ? (
                <>Analyse en cours...</>
              ) : (
                <>
                  <Calculator size={20} />
                  Lancer l'Analyse ProphetIA
                </>
              )}
            </button>
          </div>
        </div>
      )}
      
      {step === 'results' && score && taxSimulation && (
        <div className="max-w-6xl mx-auto">
          {/* Score Summary */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 mb-8">
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
              <div>
                <h2 className="text-xl font-medium mb-2">Score ProphetIA</h2>
                <p className="text-slate-400">{RECOMMENDATIONS_FR[score.recommendation] || score.recommendation}</p>
              </div>
              
              <div className="flex items-center gap-8">
                <div className="text-center">
                  <div className={`text-5xl font-bold tabular-nums ${getScoreColor(score.total_score)}`}>
                    {score.total_score}
                  </div>
                  <div className="text-xs text-slate-500 uppercase mt-1">/ 100</div>
                </div>
                
                <div className={`px-4 py-2 rounded-lg text-lg font-bold ${getRatingColor(score.rating)}`}>
                  {score.rating}
                </div>
              </div>
            </div>
            
            {/* Component Scores */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                  <TrendingUp size={16} />
                  <span className="text-xs uppercase">Rendement</span>
                </div>
                <div className={`text-2xl font-medium ${getScoreColor(score.yield_score)}`}>
                  {score.yield_score}
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                  <Shield size={16} />
                  <span className="text-xs uppercase">Sécurité</span>
                </div>
                <div className={`text-2xl font-medium ${getScoreColor(score.safety_score)}`}>
                  {score.safety_score}
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                  <TrendingUp size={16} />
                  <span className="text-xs uppercase">Croissance</span>
                </div>
                <div className={`text-2xl font-medium ${getScoreColor(score.growth_score)}`}>
                  {score.growth_score}
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-2">
                  <Scale size={16} />
                  <span className="text-xs uppercase">Juridique</span>
                </div>
                <div className={`text-2xl font-medium ${getScoreColor(score.legal_score)}`}>
                  {score.legal_score}
                </div>
              </div>
            </div>
            
            {/* Risk Flags & Opportunities */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
              {score.risk_flags.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-red-400 mb-3">Points de Vigilance</h3>
                  <ul className="space-y-2">
                    {score.risk_flags.map((flag, i) => (
                      <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                        <span className="text-red-400">•</span>
                        {flag}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {score.opportunities.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-emerald-400 mb-3">Opportunités</h3>
                  <ul className="space-y-2">
                    {score.opportunities.map((opp, i) => (
                      <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                        <span className="text-emerald-400">•</span>
                        {opp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
          
          {/* Tax Simulation */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 mb-8">
            <h2 className="text-xl font-medium mb-6">Simulation Fiscale ({taxSimulation.jurisdiction})</h2>
            
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-xs text-slate-500 uppercase mb-1">Amortissement Annuel</div>
                <div className="text-xl font-medium text-indigo-400">
                  {formatCurrency(taxSimulation.annual_summary.depreciation, 'EUR', 'fr-FR')}
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-xs text-slate-500 uppercase mb-1">Revenu Imposable</div>
                <div className="text-xl font-medium text-amber-400">
                  {formatCurrency(taxSimulation.annual_summary.taxable_income, 'EUR', 'fr-FR')}
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-xs text-slate-500 uppercase mb-1">Impôt à Payer</div>
                <div className="text-xl font-medium text-red-400">
                  {formatCurrency(taxSimulation.annual_summary.tax_liability, 'EUR', 'fr-FR')}
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-xs text-slate-500 uppercase mb-1">Cash-Flow Net</div>
                <div className="text-xl font-medium text-emerald-400">
                  {formatCurrency(taxSimulation.annual_summary.cash_flow_net, 'EUR', 'fr-FR')}
                </div>
              </div>
            </div>
            
            {/* Regime Comparison (France only) */}
            {taxSimulation.regime_comparison && (
              <div className="mt-8">
                <h3 className="text-sm font-medium text-slate-400 mb-4">
                  Comparaison des Régimes ({taxSimulation.regime_comparison.years} ans)
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="text-xs text-slate-500 uppercase mb-2">LMNP Réel</div>
                    <div className="text-lg font-medium text-emerald-400">
                      Impôts : {formatCurrency(taxSimulation.regime_comparison.reel.cumulative_tax, 'EUR', 'fr-FR')}
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="text-xs text-slate-500 uppercase mb-2">Micro-BIC</div>
                    <div className="text-lg font-medium text-amber-400">
                      Impôts : {formatCurrency(taxSimulation.regime_comparison.micro_bic.cumulative_tax, 'EUR', 'fr-FR')}
                    </div>
                  </div>
                </div>
                <div className="mt-4 text-center text-sm">
                  <span className="text-slate-400">Recommandation : </span>
                  <span className="text-emerald-400 font-medium">
                    {taxSimulation.regime_comparison.recommendation.replace('_', ' ')}
                  </span>
                  <span className="text-slate-400"> économise </span>
                  <span className="text-emerald-400 font-medium">
                    {formatCurrency(Math.abs(taxSimulation.regime_comparison.advantage_reel), 'EUR', 'fr-FR')}
                  </span>
                </div>
              </div>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setStep('input')}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-xl font-medium transition-all"
            >
              Modifier les Paramètres
            </button>
            <button
              onClick={() => router.push('/dashboard/wealth')}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-medium transition-all"
            >
              Ajouter au Portefeuille
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
