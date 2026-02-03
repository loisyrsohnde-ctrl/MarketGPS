'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import {
  X,
  Send,
  Sparkles,
  TrendingUp,
  Shield,
  Target,
  Zap,
  ChevronRight,
  BarChart3,
  Wallet,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Lightbulb,
  Building2,
  Globe,
  ArrowRight,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

type CoachProfile = 'conservative' | 'balanced' | 'aggressive';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ElementType;
  prompt: string;
  category: 'analysis' | 'optimization' | 'risk' | 'market';
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actions?: ActionButton[];
  metrics?: MetricCard[];
}

interface ActionButton {
  label: string;
  action: string;
  type: 'primary' | 'secondary';
}

interface MetricCard {
  label: string;
  value: string;
  change?: number;
  icon?: React.ElementType;
}

interface AIConciergeProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioValue?: number;
  portfolioScore?: number;
  userName?: string;
}

// =============================================================================
// Constants
// =============================================================================

const COACH_PROFILES: Record<CoachProfile, { name: string; description: string; icon: React.ElementType; color: string }> = {
  conservative: {
    name: 'Prudent',
    description: 'Priorité à la préservation du capital et aux revenus stables',
    icon: Shield,
    color: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  },
  balanced: {
    name: 'Équilibré',
    description: 'Optimisation du rapport rendement/risque',
    icon: Target,
    color: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  },
  aggressive: {
    name: 'Dynamique',
    description: 'Maximisation de la croissance à long terme',
    icon: Zap,
    color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  },
};

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'analyze-portfolio',
    label: 'Analyser mon portefeuille',
    icon: BarChart3,
    prompt: 'Analyse mon portefeuille actuel et donne-moi un diagnostic complet.',
    category: 'analysis',
  },
  {
    id: 'optimize-allocation',
    label: 'Optimiser mon allocation',
    icon: Target,
    prompt: 'Comment puis-je optimiser mon allocation pour améliorer mon rendement ajusté au risque ?',
    category: 'optimization',
  },
  {
    id: 'risk-assessment',
    label: 'Évaluer mes risques',
    icon: Shield,
    prompt: 'Quels sont les principaux risques de mon portefeuille actuel ?',
    category: 'risk',
  },
  {
    id: 'market-opportunities',
    label: 'Opportunités du moment',
    icon: TrendingUp,
    prompt: 'Quelles sont les meilleures opportunités du marché selon mon profil ?',
    category: 'market',
  },
  {
    id: 'rebalance-check',
    label: 'Besoin de rééquilibrer ?',
    icon: RefreshCw,
    prompt: 'Mon portefeuille nécessite-t-il un rééquilibrage ?',
    category: 'optimization',
  },
  {
    id: 'next-investment',
    label: 'Prochain investissement',
    icon: Lightbulb,
    prompt: 'Quel devrait être mon prochain investissement ?',
    category: 'market',
  },
];

// =============================================================================
// Response Generator (Demo - would be replaced by API)
// =============================================================================

function generateResponse(
  prompt: string, 
  profile: CoachProfile,
  portfolioValue?: number,
  portfolioScore?: number
): Message {
  const responses: Record<string, () => Message> = {
    'analyze-portfolio': () => ({
      id: Date.now().toString(),
      role: 'assistant',
      content: `**Diagnostic de votre portefeuille**

Votre portefeuille affiche un score global de **${portfolioScore || 72}/100**, ce qui le place dans la catégorie "Bon" avec une marge d'amélioration.

**Points forts :**
- Diversification sectorielle satisfaisante (7 secteurs)
- Exposition tech bien calibrée (28%)
- Liquidité suffisante pour saisir des opportunités

**Points d'attention :**
- Surpondération légère sur les valeurs US (68% vs 55% recommandé)
- Absence d'exposition aux marchés émergents
- Duration obligataire courte dans un contexte de baisse des taux

**Recommandation ${COACH_PROFILES[profile].name} :**
${profile === 'conservative' 
  ? 'Renforcer la poche obligataire investment grade et réduire l\'exposition aux valeurs de croissance.'
  : profile === 'balanced'
    ? 'Ajouter 5-10% d\'exposition aux marchés émergents via un ETF diversifié.'
    : 'Profiter de la correction tech pour renforcer les positions sur les leaders IA.'}`,
      timestamp: new Date(),
      metrics: [
        { label: 'Score Global', value: `${portfolioScore || 72}`, icon: BarChart3 },
        { label: 'Rendement YTD', value: '+12.4%', change: 12.4, icon: TrendingUp },
        { label: 'Volatilité', value: '14.2%', icon: AlertTriangle },
        { label: 'Sharpe Ratio', value: '1.24', icon: Target },
      ],
      actions: [
        { label: 'Voir le détail', action: 'view_portfolio', type: 'secondary' },
        { label: 'Appliquer les suggestions', action: 'apply_suggestions', type: 'primary' },
      ],
    }),
    
    'optimize-allocation': () => ({
      id: Date.now().toString(),
      role: 'assistant',
      content: `**Optimisation de votre allocation**

Basé sur votre profil **${COACH_PROFILES[profile].name}**, voici les ajustements recommandés :

| Classe d'actifs | Actuel | Cible | Action |
|-----------------|--------|-------|--------|
| Actions US | 45% | ${profile === 'aggressive' ? '50%' : '40%'} | ${profile === 'aggressive' ? '🟢 Renforcer' : '🔴 Réduire'} |
| Actions EU | 18% | 20% | 🟢 Renforcer |
| Émergents | 0% | ${profile === 'conservative' ? '5%' : '10%'} | 🟢 Initier |
| Obligations | 25% | ${profile === 'conservative' ? '30%' : '20%'} | ${profile === 'conservative' ? '🟢 Renforcer' : '🔴 Réduire'} |
| Immobilier | 8% | 10% | 🟢 Renforcer |
| Cash | 4% | 5% | ➡️ Maintenir |

**Impact estimé :**
- Rendement attendu : ${profile === 'aggressive' ? '+1.8%' : '+0.8%'} / an
- Volatilité : ${profile === 'conservative' ? '-2.1%' : '+1.2%'}
- Score ProphetIA : +${profile === 'aggressive' ? '8' : '5'} points`,
      timestamp: new Date(),
      actions: [
        { label: 'Simuler ce scénario', action: 'simulate', type: 'secondary' },
        { label: 'Générer les ordres', action: 'generate_orders', type: 'primary' },
      ],
    }),
    
    'risk-assessment': () => ({
      id: Date.now().toString(),
      role: 'assistant',
      content: `**Évaluation des risques**

Votre portefeuille présente un profil de risque **modéré** avec quelques points de vigilance.

🔴 **Risques élevés :**
- **Concentration tech** : 32% sur 5 valeurs. Un repli du Nasdaq de 20% impacterait votre portefeuille de -6.4%.
- **Risque de change** : 68% en USD sans couverture.

🟡 **Risques modérés :**
- **Duration** : Sensibilité taux de 2.3 ans. Impact limité à court terme.
- **Liquidité** : 3 positions représentent plus de 2 jours de volume moyen.

🟢 **Risques maîtrisés :**
- **Contrepartie** : Diversification courtiers satisfaisante.
- **Réglementaire** : Pas d'exposition aux secteurs sensibles.

**Stress test :**
- Scénario "Récession US" : -18% estimé
- Scénario "Hausse taux +100bp" : -4% estimé
- Scénario "Crash tech" : -12% estimé`,
      timestamp: new Date(),
      metrics: [
        { label: 'VaR 95%', value: '-4.2%', icon: AlertTriangle },
        { label: 'Beta', value: '1.12', icon: TrendingUp },
        { label: 'Drawdown Max', value: '-14%', icon: Shield },
      ],
    }),
    
    'market-opportunities': () => ({
      id: Date.now().toString(),
      role: 'assistant',
      content: `**Opportunités du moment** (profil ${COACH_PROFILES[profile].name})

🎯 **Top 3 recommandations :**

1. **${profile === 'aggressive' ? 'NVDA - Nvidia' : 'MSFT - Microsoft'}** — Score 84
   - Signal : Breakout technique confirmé
   - Potentiel : +${profile === 'aggressive' ? '25' : '15'}% sur 12 mois
   - Risque : ${profile === 'aggressive' ? 'Élevé' : 'Modéré'}

2. **${profile === 'conservative' ? 'VIG - Vanguard Dividend' : 'QQQM - Nasdaq 100'}** — Score 78
   - Signal : Accumulation institutionnelle
   - Potentiel : +${profile === 'conservative' ? '8' : '18'}% sur 12 mois
   - Risque : ${profile === 'conservative' ? 'Faible' : 'Modéré'}

3. **${profile === 'conservative' ? 'TLT - Treasury 20Y' : 'IEMG - Emerging Markets'}** — Score 72
   - Signal : ${profile === 'conservative' ? 'Pivot BCE anticipé' : 'Valorisation attractive'}
   - Potentiel : +${profile === 'conservative' ? '6' : '22'}% sur 12 mois
   - Risque : ${profile === 'conservative' ? 'Faible' : 'Élevé'}

**Compatible avec votre allocation :** 
Ces recommandations permettraient d'améliorer votre score de +5 points.`,
      timestamp: new Date(),
      actions: [
        { label: 'Voir les détails', action: 'view_opportunities', type: 'secondary' },
        { label: 'Ajouter à la watchlist', action: 'add_watchlist', type: 'primary' },
      ],
    }),
    
    default: () => ({
      id: Date.now().toString(),
      role: 'assistant',
      content: `Je comprends votre question. En tant que conseiller **${COACH_PROFILES[profile].name}**, voici mon analyse :

${prompt.toLowerCase().includes('risque') 
  ? 'La gestion du risque est primordiale. Je vous recommande de maintenir une diversification adéquate et de surveiller votre exposition aux actifs volatils.'
  : prompt.toLowerCase().includes('rendement') || prompt.toLowerCase().includes('performance')
    ? 'Pour optimiser votre rendement, concentrez-vous sur les actifs avec un score ProphetIA supérieur à 70 et une tendance haussière confirmée.'
    : 'Basé sur votre profil et les conditions de marché actuelles, je vous suggère de maintenir une approche disciplinée avec des révisions mensuelles de votre allocation.'}

Souhaitez-vous que j'approfondisse un aspect particulier ?`,
      timestamp: new Date(),
    }),
  };
  
  // Find matching response
  const actionId = QUICK_ACTIONS.find(a => a.prompt === prompt)?.id;
  const generator = responses[actionId || 'default'];
  
  return generator();
}

// =============================================================================
// Sub-Components
// =============================================================================

function CoachSelector({
  selected,
  onSelect,
}: {
  selected: CoachProfile;
  onSelect: (profile: CoachProfile) => void;
}) {
  return (
    <div className="grid grid-cols-3 gap-2 p-2 bg-slate-900/50 rounded-xl">
      {(Object.entries(COACH_PROFILES) as [CoachProfile, typeof COACH_PROFILES.balanced][]).map(([key, profile]) => {
        const Icon = profile.icon;
        const isSelected = selected === key;
        
        return (
          <button
            key={key}
            onClick={() => onSelect(key)}
            className={`
              p-3 rounded-lg border transition-all text-center
              ${isSelected 
                ? profile.color + ' border-current' 
                : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'}
            `}
          >
            <Icon size={18} className={`mx-auto mb-1 ${isSelected ? '' : 'text-slate-400'}`} />
            <p className={`text-xs font-medium ${isSelected ? '' : 'text-slate-400'}`}>
              {profile.name}
            </p>
          </button>
        );
      })}
    </div>
  );
}

function QuickActionButton({
  action,
  onClick,
}: {
  action: QuickAction;
  onClick: () => void;
}) {
  const Icon = action.icon;
  
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg transition-all text-left group"
    >
      <Icon size={14} className="text-indigo-400" />
      <span className="text-xs text-slate-300 group-hover:text-slate-200">{action.label}</span>
      <ChevronRight size={12} className="text-slate-500 ml-auto group-hover:translate-x-0.5 transition-transform" />
    </button>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[85%] ${isUser ? 'order-1' : 'order-2'}`}>
        {/* Avatar */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
              <Sparkles size={12} className="text-white" />
            </div>
            <span className="text-xs text-slate-400">ProphetIA</span>
          </div>
        )}
        
        {/* Content */}
        <div
          className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? 'bg-indigo-600 text-white rounded-br-md'
              : 'bg-slate-800 text-slate-200 rounded-bl-md'}
          `}
        >
          <div className="prose prose-sm prose-invert max-w-none">
            <ReactMarkdown
              components={{
                p: ({ node, ...props }) => <p {...props} className="mb-2 last:mb-0" />,
                strong: ({ node, ...props }) => <strong {...props} className="font-semibold" />,
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-2 mb-2">
                    <table {...props} className="w-full text-xs border-collapse border border-slate-600" />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th {...props} className="border border-slate-600 px-2 py-1 bg-slate-700/50 text-left" />
                ),
                td: ({ node, ...props }) => (
                  <td {...props} className="border border-slate-600 px-2 py-1" />
                ),
                ul: ({ node, ...props }) => <ul {...props} className="list-disc list-inside mb-2" />,
                ol: ({ node, ...props }) => <ol {...props} className="list-decimal list-inside mb-2" />,
                li: ({ node, ...props }) => <li {...props} className="mb-1" />,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
        
        {/* Metrics */}
        {message.metrics && message.metrics.length > 0 && (
          <div className="grid grid-cols-2 gap-2 mt-3">
            {message.metrics.map((metric, i) => {
              const Icon = metric.icon || BarChart3;
              return (
                <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-lg p-2">
                  <div className="flex items-center gap-1 mb-1">
                    <Icon size={10} className="text-slate-500" />
                    <span className="text-[10px] text-slate-500">{metric.label}</span>
                  </div>
                  <p className="text-sm font-semibold">{metric.value}</p>
                </div>
              );
            })}
          </div>
        )}
        
        {/* Actions */}
        {message.actions && message.actions.length > 0 && (
          <div className="flex gap-2 mt-3">
            {message.actions.map((action, i) => (
              <button
                key={i}
                className={`
                  flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-colors
                  ${action.type === 'primary' 
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white' 
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'}
                `}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
        
        {/* Timestamp */}
        <p className={`text-[10px] text-slate-500 mt-2 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </motion.div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function AIConcierge({
  isOpen,
  onClose,
  portfolioValue = 250000,
  portfolioScore = 72,
  userName = 'Investisseur',
}: AIConciergeProps) {
  const [coachProfile, setCoachProfile] = useState<CoachProfile>('balanced');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSend = (prompt: string) => {
    if (!prompt.trim()) return;
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: prompt,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    
    // Simulate AI response delay
    setTimeout(() => {
      const response = generateResponse(prompt, coachProfile, portfolioValue, portfolioScore);
      setMessages(prev => [...prev, response]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const handleQuickAction = (action: QuickAction) => {
    handleSend(action.prompt);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: 100, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 100, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="w-full max-w-lg bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="p-4 border-b border-slate-800 bg-gradient-to-r from-indigo-600/10 to-purple-600/10">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                  <Sparkles size={20} className="text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-slate-200">ProphetIA Concierge</h2>
                  <p className="text-xs text-slate-400">Votre conseiller patrimonial IA</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <X size={18} className="text-slate-400" />
              </button>
            </div>
            
            {/* Coach Profile Selector */}
            <CoachSelector selected={coachProfile} onSelect={setCoachProfile} />
          </div>

          {/* Messages or Welcome */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="space-y-4">
                {/* Welcome */}
                <div className="text-center py-4">
                  <p className="text-slate-400 text-sm">
                    Bonjour {userName}, je suis votre conseiller {COACH_PROFILES[coachProfile].name.toLowerCase()}.
                  </p>
                  <p className="text-slate-500 text-xs mt-1">
                    Comment puis-je vous aider aujourd&apos;hui ?
                  </p>
                </div>
                
                {/* Quick Actions */}
                <div className="grid grid-cols-1 gap-2">
                  {QUICK_ACTIONS.slice(0, 4).map(action => (
                    <QuickActionButton
                      key={action.id}
                      action={action}
                      onClick={() => handleQuickAction(action)}
                    />
                  ))}
                </div>
                
                {/* More Actions */}
                <div className="pt-2 border-t border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-2">
                    Autres questions
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {QUICK_ACTIONS.slice(4).map(action => (
                      <QuickActionButton
                        key={action.id}
                        action={action}
                        onClick={() => handleQuickAction(action)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <>
                {messages.map(message => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                
                {isTyping && (
                  <div className="flex items-center gap-2 text-slate-400">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                      <Sparkles size={12} className="text-white animate-pulse" />
                    </div>
                    <span className="text-xs">ProphetIA réfléchit...</span>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/50">
            <form 
              onSubmit={(e) => { e.preventDefault(); handleSend(input); }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Posez votre question..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                className="p-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-xl transition-colors"
              >
                <Send size={18} className="text-white" />
              </button>
            </form>
            
            <p className="text-[10px] text-slate-500 text-center mt-2">
              Les conseils sont à titre informatif. Consultez un professionnel pour des décisions d&apos;investissement.
            </p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
