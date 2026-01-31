'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  ChevronLeft,
  Plus,
  Trash2,
  Save,
  ArrowRight,
  Loader2,
  Check,
  AlertCircle,
  Search,
} from 'lucide-react';

import {
  createPosition,
  getAccounts,
  createAccount,
  type PortfolioAccount,
  type PositionCreateRequest,
} from '@/lib/api-portfolio';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface PositionEntry {
  id: string;
  symbol: string;
  name: string;
  quantity: string;
  avgCost: string;
  currency: string;
  assetType: string;
  isin: string;
}

const ASSET_TYPES = [
  { value: 'EQUITY', label: 'Action' },
  { value: 'ETF', label: 'ETF' },
  { value: 'BOND', label: 'Obligation' },
  { value: 'CRYPTO', label: 'Crypto' },
  { value: 'FUND', label: 'Fonds' },
  { value: 'REAL_ESTATE', label: 'Immobilier' },
  { value: 'OTHER', label: 'Autre' },
];

const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CAD'];

const ACCOUNT_TYPES = [
  { value: 'CTO', label: 'Compte-Titres' },
  { value: 'PEA', label: 'PEA' },
  { value: 'PEA_PME', label: 'PEA-PME' },
  { value: 'AV', label: 'Assurance Vie' },
  { value: 'PER', label: 'PER' },
  { value: 'CRYPTO', label: 'Crypto' },
  { value: 'OTHER', label: 'Autre' },
];

// ═══════════════════════════════════════════════════════════════════════════════
// POSITION ROW COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

function PositionRow({
  position,
  onChange,
  onRemove,
  showRemove,
}: {
  position: PositionEntry;
  onChange: (updated: PositionEntry) => void;
  onRemove: () => void;
  showRemove: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="bg-surface rounded-xl border border-glass-border p-4"
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Symbol */}
        <div>
          <label className="block text-xs text-text-muted mb-1">
            Symbole <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={position.symbol}
            onChange={(e) => onChange({ ...position, symbol: e.target.value.toUpperCase() })}
            placeholder="AAPL"
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          />
        </div>

        {/* Name */}
        <div>
          <label className="block text-xs text-text-muted mb-1">Nom</label>
          <input
            type="text"
            value={position.name}
            onChange={(e) => onChange({ ...position, name: e.target.value })}
            placeholder="Apple Inc."
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          />
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-xs text-text-muted mb-1">
            Quantité <span className="text-red-400">*</span>
          </label>
          <input
            type="number"
            value={position.quantity}
            onChange={(e) => onChange({ ...position, quantity: e.target.value })}
            placeholder="10"
            min="0"
            step="0.0001"
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          />
        </div>

        {/* Avg Cost */}
        <div>
          <label className="block text-xs text-text-muted mb-1">PRU</label>
          <input
            type="number"
            value={position.avgCost}
            onChange={(e) => onChange({ ...position, avgCost: e.target.value })}
            placeholder="150.00"
            min="0"
            step="0.01"
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          />
        </div>

        {/* Asset Type */}
        <div>
          <label className="block text-xs text-text-muted mb-1">Type</label>
          <select
            value={position.assetType}
            onChange={(e) => onChange({ ...position, assetType: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          >
            {ASSET_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Currency */}
        <div>
          <label className="block text-xs text-text-muted mb-1">Devise</label>
          <select
            value={position.currency}
            onChange={(e) => onChange({ ...position, currency: e.target.value })}
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          >
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* ISIN */}
        <div>
          <label className="block text-xs text-text-muted mb-1">ISIN</label>
          <input
            type="text"
            value={position.isin}
            onChange={(e) => onChange({ ...position, isin: e.target.value.toUpperCase() })}
            placeholder="US0378331005"
            className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted focus:ring-2 focus:ring-accent focus:border-accent text-sm"
          />
        </div>

        {/* Remove button */}
        <div className="flex items-end">
          {showRemove && (
            <button
              onClick={onRemove}
              className="px-3 py-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function ManualEntryPage() {
  const router = useRouter();

  // State
  const [accounts, setAccounts] = useState<PortfolioAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [showNewAccount, setShowNewAccount] = useState(false);
  const [newAccountName, setNewAccountName] = useState('');
  const [newAccountType, setNewAccountType] = useState('CTO');
  const [newAccountBroker, setNewAccountBroker] = useState('');

  const [positions, setPositions] = useState<PositionEntry[]>([
    {
      id: '1',
      symbol: '',
      name: '',
      quantity: '',
      avgCost: '',
      currency: 'EUR',
      assetType: 'EQUITY',
      isin: '',
    },
  ]);

  const [isSaving, setIsSaving] = useState(false);
  const [savedCount, setSavedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Load accounts on mount
  useEffect(() => {
    getAccounts()
      .then(setAccounts)
      .catch(console.error);
  }, []);

  // Handlers
  const addPosition = () => {
    setPositions([
      ...positions,
      {
        id: String(Date.now()),
        symbol: '',
        name: '',
        quantity: '',
        avgCost: '',
        currency: 'EUR',
        assetType: 'EQUITY',
        isin: '',
      },
    ]);
  };

  const updatePosition = (id: string, updated: PositionEntry) => {
    setPositions(positions.map((p) => (p.id === id ? updated : p)));
  };

  const removePosition = (id: string) => {
    if (positions.length > 1) {
      setPositions(positions.filter((p) => p.id !== id));
    }
  };

  const createNewAccount = async () => {
    if (!newAccountName.trim()) return;

    try {
      const account = await createAccount({
        name: newAccountName.trim(),
        broker: newAccountBroker.trim() || undefined,
        account_type: newAccountType,
      });

      setAccounts([account, ...accounts]);
      setSelectedAccountId(account.id);
      setShowNewAccount(false);
      setNewAccountName('');
      setNewAccountBroker('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create account');
    }
  };

  const savePositions = async () => {
    // Validate
    const validPositions = positions.filter(
      (p) => p.symbol.trim() && parseFloat(p.quantity) > 0
    );

    if (validPositions.length === 0) {
      setError('Veuillez saisir au moins une position valide (symbole + quantité)');
      return;
    }

    setIsSaving(true);
    setError(null);
    setSavedCount(0);

    try {
      for (const pos of validPositions) {
        const request: PositionCreateRequest = {
          symbol: pos.symbol.trim(),
          quantity: parseFloat(pos.quantity),
          avg_cost: pos.avgCost ? parseFloat(pos.avgCost) : undefined,
          name: pos.name.trim() || undefined,
          isin: pos.isin.trim() || undefined,
          currency: pos.currency,
          asset_type: pos.assetType,
          account_id: selectedAccountId || undefined,
        };

        await createPosition(request);
        setSavedCount((c) => c + 1);
      }

      // Success - redirect to portfolio
      router.push('/dashboard/wealth');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save positions');
    } finally {
      setIsSaving(false);
    }
  };

  const validCount = positions.filter(
    (p) => p.symbol.trim() && parseFloat(p.quantity) > 0
  ).length;

  return (
    <div className="min-h-screen bg-bg-primary py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back button */}
        <button
          onClick={() => router.push('/dashboard/wealth/connect')}
          className="flex items-center gap-2 text-text-secondary hover:text-text-primary mb-6"
        >
          <ChevronLeft className="w-4 h-4" />
          Retour
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-text-primary mb-2">
            Saisie manuelle
          </h1>
          <p className="text-text-secondary">
            Ajoutez vos positions une par une
          </p>
        </div>

        {/* Account Selection */}
        <div className="bg-surface rounded-xl border border-glass-border p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-text-primary">
              Compte / Enveloppe (optionnel)
            </label>
            <button
              onClick={() => setShowNewAccount(!showNewAccount)}
              className="text-sm text-accent hover:text-accent-dark flex items-center gap-1"
            >
              <Plus className="w-4 h-4" />
              Nouveau compte
            </button>
          </div>

          {showNewAccount ? (
            <div className="grid grid-cols-3 gap-4">
              <input
                type="text"
                value={newAccountName}
                onChange={(e) => setNewAccountName(e.target.value)}
                placeholder="Nom du compte"
                className="px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted text-sm"
              />
              <input
                type="text"
                value={newAccountBroker}
                onChange={(e) => setNewAccountBroker(e.target.value)}
                placeholder="Broker (optionnel)"
                className="px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary placeholder-text-muted text-sm"
              />
              <div className="flex gap-2">
                <select
                  value={newAccountType}
                  onChange={(e) => setNewAccountType(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary text-sm"
                >
                  {ACCOUNT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={createNewAccount}
                  disabled={!newAccountName.trim()}
                  className="px-4 py-2 rounded-lg bg-accent text-white text-sm hover:bg-accent-dark disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Créer
                </button>
              </div>
            </div>
          ) : (
            <select
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-glass-border text-text-primary text-sm"
            >
              <option value="">Sans compte spécifique</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} {a.broker ? `(${a.broker})` : ''} - {a.account_type}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Positions */}
        <div className="space-y-4 mb-6">
          {positions.map((pos) => (
            <PositionRow
              key={pos.id}
              position={pos}
              onChange={(updated) => updatePosition(pos.id, updated)}
              onRemove={() => removePosition(pos.id)}
              showRemove={positions.length > 1}
            />
          ))}
        </div>

        {/* Add position button */}
        <button
          onClick={addPosition}
          className="w-full py-3 px-4 rounded-xl border border-dashed border-glass-border text-text-secondary hover:border-accent hover:text-accent transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Ajouter une position
        </button>

        {/* Error */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Save button */}
        <div className="mt-8 flex items-center justify-between">
          <p className="text-sm text-text-muted">
            {validCount} position{validCount > 1 ? 's' : ''} valide{validCount > 1 ? 's' : ''}
          </p>

          <button
            onClick={savePositions}
            disabled={validCount === 0 || isSaving}
            className={cn(
              'px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2',
              validCount > 0 && !isSaving
                ? 'bg-accent text-white hover:bg-accent-dark'
                : 'bg-surface text-text-muted cursor-not-allowed'
            )}
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Enregistrement ({savedCount}/{validCount})...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Enregistrer
              </>
            )}
          </button>
        </div>

        {/* Info */}
        <div className="mt-8 p-4 rounded-xl bg-surface/50 border border-glass-border text-center">
          <p className="text-sm text-text-muted">
            Les positions seront automatiquement enrichies avec les scores MarketGPS 
            si le symbole correspond à un actif dans notre base de données.
          </p>
        </div>
      </div>
    </div>
  );
}
