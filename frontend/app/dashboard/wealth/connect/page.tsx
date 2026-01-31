'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileSpreadsheet,
  Check,
  AlertCircle,
  ChevronRight,
  ChevronLeft,
  Plus,
  Trash2,
  RefreshCw,
  HelpCircle,
  Shield,
  Eye,
  Loader2,
  ArrowRight,
  Download,
  Columns,
  Table,
} from 'lucide-react';

import {
  getBrokerTemplates,
  previewCSV,
  importCSV,
  getAccounts,
  createAccount,
  getPositions,
  type BrokerTemplate,
  type CSVPreviewResult,
  type CSVImportResult,
  type PortfolioAccount,
  type PortfolioPosition,
} from '@/lib/api-portfolio';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

type ImportStep = 'disclaimer' | 'source' | 'upload' | 'mapping' | 'confirm' | 'complete';

interface ColumnMapping {
  symbol_column: string;
  quantity_column: string;
  avg_cost_column?: string;
  isin_column?: string;
  name_column?: string;
  currency_column?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISCLAIMER STEP
// ═══════════════════════════════════════════════════════════════════════════════

function DisclaimerStep({ onAccept }: { onAccept: () => void }) {
  const [accepted, setAccepted] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto"
    >
      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-accent/10 flex items-center justify-center">
          <Shield className="w-8 h-8 text-accent" />
        </div>
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Outil de Recherche & Statistiques
        </h1>
        <p className="text-text-secondary">
          Avant de synchroniser votre portefeuille
        </p>
      </div>

      <div className="bg-surface rounded-2xl border border-glass-border p-6 mb-6">
        <div className="space-y-4 text-text-secondary">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
              <span className="text-xs font-bold text-accent">1</span>
            </div>
            <div>
              <p className="font-medium text-text-primary">Lecture seule</p>
              <p className="text-sm">
                MarketGPS n'exécute aucun ordre. Aucune connexion à vos comptes de 
                courtage n'est utilisée pour le trading.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
              <span className="text-xs font-bold text-accent">2</span>
            </div>
            <div>
              <p className="font-medium text-text-primary">Pas de conseil</p>
              <p className="text-sm">
                Les scores, analyses et données affichés sont des indicateurs 
                statistiques, pas des recommandations d'achat ou de vente.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
              <span className="text-xs font-bold text-accent">3</span>
            </div>
            <div>
              <p className="font-medium text-text-primary">Vos données</p>
              <p className="text-sm">
                Vos positions sont stockées de manière sécurisée et ne sont 
                jamais partagées avec des tiers.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
              <span className="text-xs font-bold text-accent">4</span>
            </div>
            <div>
              <p className="font-medium text-text-primary">Responsabilité</p>
              <p className="text-sm">
                Toute décision d'investissement reste de votre entière responsabilité. 
                Consultez un conseiller financier agréé.
              </p>
            </div>
          </div>
        </div>
      </div>

      <label className="flex items-center gap-3 mb-6 cursor-pointer">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(e) => setAccepted(e.target.checked)}
          className="w-5 h-5 rounded border-glass-border bg-surface text-accent focus:ring-accent"
        />
        <span className="text-text-secondary">
          J'ai lu et j'accepte les conditions ci-dessus
        </span>
      </label>

      <button
        onClick={onAccept}
        disabled={!accepted}
        className={cn(
          'w-full py-3 px-6 rounded-xl font-medium transition-all',
          'flex items-center justify-center gap-2',
          accepted
            ? 'bg-accent text-white hover:bg-accent-dark'
            : 'bg-surface text-text-muted cursor-not-allowed'
        )}
      >
        Continuer
        <ArrowRight className="w-4 h-4" />
      </button>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SOURCE SELECTION STEP
// ═══════════════════════════════════════════════════════════════════════════════

function SourceStep({
  templates,
  onSelectTemplate,
  onManualEntry,
}: {
  templates: BrokerTemplate[];
  onSelectTemplate: (templateId: string | null) => void;
  onManualEntry: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto"
    >
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Comment voulez-vous importer ?
        </h1>
        <p className="text-text-secondary">
          Choisissez votre broker ou importez un fichier CSV générique
        </p>
      </div>

      {/* Broker Templates */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        {templates.map((template) => (
          <button
            key={template.id}
            onClick={() => onSelectTemplate(template.id)}
            className={cn(
              'p-4 rounded-xl border border-glass-border bg-surface',
              'hover:border-accent hover:bg-accent/5 transition-all',
              'flex flex-col items-center gap-2 text-center'
            )}
          >
            <div className="w-12 h-12 rounded-xl bg-bg-primary flex items-center justify-center">
              <FileSpreadsheet className="w-6 h-6 text-accent" />
            </div>
            <span className="font-medium text-text-primary">{template.name}</span>
            <span className="text-xs text-text-muted">{template.description}</span>
          </button>
        ))}

        {/* Generic CSV */}
        <button
          onClick={() => onSelectTemplate('generic')}
          className={cn(
            'p-4 rounded-xl border border-dashed border-glass-border bg-surface/50',
            'hover:border-accent hover:bg-accent/5 transition-all',
            'flex flex-col items-center gap-2 text-center'
          )}
        >
          <div className="w-12 h-12 rounded-xl bg-bg-primary flex items-center justify-center">
            <Table className="w-6 h-6 text-text-secondary" />
          </div>
          <span className="font-medium text-text-primary">CSV Générique</span>
          <span className="text-xs text-text-muted">Colonnes personnalisées</span>
        </button>
      </div>

      {/* Separator */}
      <div className="flex items-center gap-4 mb-8">
        <div className="flex-1 h-px bg-glass-border" />
        <span className="text-text-muted text-sm">ou</span>
        <div className="flex-1 h-px bg-glass-border" />
      </div>

      {/* Manual Entry */}
      <button
        onClick={onManualEntry}
        className={cn(
          'w-full p-4 rounded-xl border border-glass-border bg-surface',
          'hover:border-accent hover:bg-accent/5 transition-all',
          'flex items-center justify-between'
        )}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-bg-primary flex items-center justify-center">
            <Plus className="w-6 h-6 text-accent" />
          </div>
          <div className="text-left">
            <span className="font-medium text-text-primary block">Saisie manuelle</span>
            <span className="text-sm text-text-muted">
              Entrez vos positions une par une
            </span>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-text-muted" />
      </button>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// FILE UPLOAD STEP
// ═══════════════════════════════════════════════════════════════════════════════

function UploadStep({
  templateId,
  onPreview,
  onBack,
}: {
  templateId: string | null;
  onPreview: (preview: CSVPreviewResult, file: File) => void;
  onBack: () => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.endsWith('.csv')) {
        setError('Veuillez sélectionner un fichier CSV');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const preview = await previewCSV(file, templateId || undefined);
        onPreview(preview, file);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erreur lors de la lecture du fichier');
      } finally {
        setIsLoading(false);
      }
    },
    [templateId, onPreview]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto"
    >
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-text-secondary hover:text-text-primary mb-6"
      >
        <ChevronLeft className="w-4 h-4" />
        Retour
      </button>

      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Importez votre fichier CSV
        </h1>
        <p className="text-text-secondary">
          {templateId && templateId !== 'generic'
            ? `Format ${templateId.replace('_', ' ')}`
            : 'Format CSV avec vos positions'}
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          'border-2 border-dashed rounded-2xl p-12 text-center transition-all',
          isDragging
            ? 'border-accent bg-accent/5'
            : 'border-glass-border bg-surface hover:border-accent/50',
          isLoading && 'opacity-50 pointer-events-none'
        )}
      >
        {isLoading ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 text-accent animate-spin" />
            <p className="text-text-secondary">Analyse du fichier...</p>
          </div>
        ) : (
          <>
            <Upload
              className={cn(
                'w-12 h-12 mx-auto mb-4',
                isDragging ? 'text-accent' : 'text-text-muted'
              )}
            />
            <p className="text-text-primary font-medium mb-2">
              Glissez votre fichier CSV ici
            </p>
            <p className="text-text-muted text-sm mb-4">ou</p>
            <label className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white cursor-pointer hover:bg-accent-dark transition-colors">
              <input
                type="file"
                accept=".csv"
                onChange={handleInputChange}
                className="hidden"
              />
              Sélectionner un fichier
            </label>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Help */}
      <div className="mt-8 p-4 rounded-xl bg-surface border border-glass-border">
        <div className="flex items-center gap-3 mb-3">
          <HelpCircle className="w-5 h-5 text-accent" />
          <span className="font-medium text-text-primary">Comment exporter depuis mon broker ?</span>
        </div>
        <ol className="text-sm text-text-secondary space-y-2 ml-8">
          <li>1. Connectez-vous à votre compte broker</li>
          <li>2. Allez dans "Portefeuille" ou "Positions"</li>
          <li>3. Cherchez "Exporter" ou "Télécharger CSV"</li>
          <li>4. Importez le fichier ici</li>
        </ol>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAPPING STEP
// ═══════════════════════════════════════════════════════════════════════════════

function MappingStep({
  preview,
  onConfirm,
  onBack,
}: {
  preview: CSVPreviewResult;
  onConfirm: (mapping: ColumnMapping) => void;
  onBack: () => void;
}) {
  const [mapping, setMapping] = useState<ColumnMapping>({
    symbol_column: preview.suggested_mapping.symbol_column || '',
    quantity_column: preview.suggested_mapping.quantity_column || '',
    avg_cost_column: preview.suggested_mapping.avg_cost_column,
    isin_column: preview.suggested_mapping.isin_column,
    name_column: preview.suggested_mapping.name_column,
  });

  const isValid = mapping.symbol_column && mapping.quantity_column;

  const renderSelect = (
    label: string,
    value: string | undefined,
    onChange: (val: string) => void,
    required: boolean = false
  ) => (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-1">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          'w-full px-3 py-2 rounded-lg bg-bg-primary border transition-colors',
          'text-text-primary focus:ring-2 focus:ring-accent focus:border-accent',
          required && !value ? 'border-red-500/50' : 'border-glass-border'
        )}
      >
        <option value="">-- Sélectionner --</option>
        {preview.headers.map((header) => (
          <option key={header} value={header}>
            {header}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto"
    >
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-text-secondary hover:text-text-primary mb-6"
      >
        <ChevronLeft className="w-4 h-4" />
        Retour
      </button>

      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Configurez le mapping des colonnes
        </h1>
        <p className="text-text-secondary">
          Fichier: {preview.filename} • {preview.row_count} lignes détectées
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Column Mapping */}
        <div className="space-y-4">
          <h2 className="font-medium text-text-primary flex items-center gap-2">
            <Columns className="w-5 h-5" />
            Mapping des colonnes
          </h2>

          <div className="bg-surface rounded-xl border border-glass-border p-4 space-y-4">
            {renderSelect(
              'Symbole / Ticker',
              mapping.symbol_column,
              (val) => setMapping({ ...mapping, symbol_column: val }),
              true
            )}
            {renderSelect(
              'Quantité',
              mapping.quantity_column,
              (val) => setMapping({ ...mapping, quantity_column: val }),
              true
            )}
            {renderSelect(
              'Prix de revient unitaire (PRU)',
              mapping.avg_cost_column,
              (val) => setMapping({ ...mapping, avg_cost_column: val || undefined })
            )}
            {renderSelect(
              'Code ISIN',
              mapping.isin_column,
              (val) => setMapping({ ...mapping, isin_column: val || undefined })
            )}
            {renderSelect(
              'Nom / Libellé',
              mapping.name_column,
              (val) => setMapping({ ...mapping, name_column: val || undefined })
            )}
          </div>
        </div>

        {/* Preview Table */}
        <div className="space-y-4">
          <h2 className="font-medium text-text-primary flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Aperçu des données
          </h2>

          <div className="bg-surface rounded-xl border border-glass-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-bg-primary">
                  <tr>
                    <th className="px-3 py-2 text-left text-text-muted font-medium">Symbole</th>
                    <th className="px-3 py-2 text-right text-text-muted font-medium">Quantité</th>
                    <th className="px-3 py-2 text-right text-text-muted font-medium">PRU</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-glass-border">
                  {preview.sample_rows.slice(0, 5).map((row, i) => (
                    <tr key={i}>
                      <td className="px-3 py-2 text-text-primary font-medium">
                        {row[mapping.symbol_column] || '-'}
                      </td>
                      <td className="px-3 py-2 text-right text-text-secondary">
                        {row[mapping.quantity_column] || '-'}
                      </td>
                      <td className="px-3 py-2 text-right text-text-secondary">
                        {mapping.avg_cost_column ? row[mapping.avg_cost_column] || '-' : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {!isValid && (
            <p className="text-sm text-amber-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Sélectionnez au minimum les colonnes Symbole et Quantité
            </p>
          )}
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button
          onClick={() => onConfirm(mapping)}
          disabled={!isValid}
          className={cn(
            'px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2',
            isValid
              ? 'bg-accent text-white hover:bg-accent-dark'
              : 'bg-surface text-text-muted cursor-not-allowed'
          )}
        >
          Importer les positions
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// IMPORT RESULT STEP
// ═══════════════════════════════════════════════════════════════════════════════

function CompleteStep({
  result,
  onViewPortfolio,
  onImportMore,
}: {
  result: CSVImportResult;
  onViewPortfolio: () => void;
  onImportMore: () => void;
}) {
  const isSuccess = result.status === 'completed';
  const isPartial = result.status === 'partial';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-lg mx-auto text-center"
    >
      <div
        className={cn(
          'w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center',
          isSuccess ? 'bg-green-500/10' : isPartial ? 'bg-amber-500/10' : 'bg-red-500/10'
        )}
      >
        {isSuccess ? (
          <Check className="w-10 h-10 text-green-400" />
        ) : isPartial ? (
          <AlertCircle className="w-10 h-10 text-amber-400" />
        ) : (
          <AlertCircle className="w-10 h-10 text-red-400" />
        )}
      </div>

      <h1 className="text-2xl font-bold text-text-primary mb-2">
        {isSuccess
          ? 'Import réussi !'
          : isPartial
          ? 'Import partiel'
          : 'Import échoué'}
      </h1>

      <p className="text-text-secondary mb-8">
        {result.rows_imported} positions importées sur {result.rows_total}
      </p>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-surface rounded-xl p-4 border border-glass-border">
          <p className="text-2xl font-bold text-green-400">{result.rows_imported}</p>
          <p className="text-xs text-text-muted">Importées</p>
        </div>
        <div className="bg-surface rounded-xl p-4 border border-glass-border">
          <p className="text-2xl font-bold text-amber-400">{result.rows_skipped}</p>
          <p className="text-xs text-text-muted">Ignorées</p>
        </div>
        <div className="bg-surface rounded-xl p-4 border border-glass-border">
          <p className="text-2xl font-bold text-red-400">{result.rows_errors}</p>
          <p className="text-xs text-text-muted">Erreurs</p>
        </div>
      </div>

      {/* Errors */}
      {result.errors.length > 0 && (
        <div className="bg-surface rounded-xl border border-glass-border p-4 mb-8 text-left">
          <p className="text-sm font-medium text-text-primary mb-2">Détails des erreurs:</p>
          <ul className="text-xs text-text-muted space-y-1 max-h-32 overflow-y-auto">
            {result.errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={onImportMore}
          className="flex-1 py-3 px-6 rounded-xl font-medium border border-glass-border text-text-secondary hover:bg-surface transition-colors"
        >
          Importer un autre fichier
        </button>
        <button
          onClick={onViewPortfolio}
          className="flex-1 py-3 px-6 rounded-xl font-medium bg-accent text-white hover:bg-accent-dark transition-colors flex items-center justify-center gap-2"
        >
          Voir mon portefeuille
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function PortfolioConnectPage() {
  const router = useRouter();

  // State
  const [step, setStep] = useState<ImportStep>('disclaimer');
  const [templates, setTemplates] = useState<BrokerTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [csvPreview, setCsvPreview] = useState<CSVPreviewResult | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<CSVImportResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load templates on mount
  useEffect(() => {
    getBrokerTemplates()
      .then((data) => setTemplates(data.templates))
      .catch(console.error);
  }, []);

  // Check if user already accepted disclaimer
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const accepted = localStorage.getItem('portfolio_disclaimer_accepted');
      if (accepted === 'true') {
        setStep('source');
      }
    }
  }, []);

  // Handlers
  const handleAcceptDisclaimer = () => {
    localStorage.setItem('portfolio_disclaimer_accepted', 'true');
    setStep('source');
  };

  const handleSelectTemplate = (templateId: string | null) => {
    setSelectedTemplate(templateId);
    setStep('upload');
  };

  const handleManualEntry = () => {
    // TODO: Implement manual entry page
    router.push('/dashboard/wealth/connect/manual');
  };

  const handlePreview = (preview: CSVPreviewResult, file: File) => {
    setCsvPreview(preview);
    setCsvFile(file);
    setStep('mapping');
  };

  const handleConfirmMapping = async (mapping: ColumnMapping) => {
    if (!csvFile) return;

    setIsLoading(true);
    try {
      const result = await importCSV(
        csvFile,
        mapping,
        undefined, // accountId
        selectedTemplate || undefined
      );
      setImportResult(result);
      setStep('complete');
    } catch (error) {
      console.error('Import failed:', error);
      setImportResult({
        status: 'failed',
        run_id: '',
        rows_total: 0,
        rows_imported: 0,
        rows_skipped: 0,
        rows_errors: 1,
        errors: [error instanceof Error ? error.message : 'Import failed'],
      });
      setStep('complete');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewPortfolio = () => {
    router.push('/dashboard/wealth');
  };

  const handleImportMore = () => {
    setCsvPreview(null);
    setCsvFile(null);
    setImportResult(null);
    setStep('source');
  };

  // Render loading overlay
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-accent animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Import en cours...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary py-8 px-4">
      {/* Progress indicator */}
      {step !== 'disclaimer' && (
        <div className="max-w-2xl mx-auto mb-8">
          <div className="flex items-center justify-center gap-2">
            {['source', 'upload', 'mapping', 'complete'].map((s, i) => (
              <React.Fragment key={s}>
                <div
                  className={cn(
                    'w-3 h-3 rounded-full transition-colors',
                    step === s
                      ? 'bg-accent'
                      : ['source', 'upload', 'mapping', 'complete'].indexOf(step) > i
                      ? 'bg-accent/50'
                      : 'bg-glass-border'
                  )}
                />
                {i < 3 && (
                  <div
                    className={cn(
                      'w-12 h-0.5 transition-colors',
                      ['source', 'upload', 'mapping', 'complete'].indexOf(step) > i
                        ? 'bg-accent/50'
                        : 'bg-glass-border'
                    )}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Step Content */}
      <AnimatePresence mode="wait">
        {step === 'disclaimer' && (
          <DisclaimerStep key="disclaimer" onAccept={handleAcceptDisclaimer} />
        )}

        {step === 'source' && (
          <SourceStep
            key="source"
            templates={templates}
            onSelectTemplate={handleSelectTemplate}
            onManualEntry={handleManualEntry}
          />
        )}

        {step === 'upload' && (
          <UploadStep
            key="upload"
            templateId={selectedTemplate}
            onPreview={handlePreview}
            onBack={() => setStep('source')}
          />
        )}

        {step === 'mapping' && csvPreview && (
          <MappingStep
            key="mapping"
            preview={csvPreview}
            onConfirm={handleConfirmMapping}
            onBack={() => setStep('upload')}
          />
        )}

        {step === 'complete' && importResult && (
          <CompleteStep
            key="complete"
            result={importResult}
            onViewPortfolio={handleViewPortfolio}
            onImportMore={handleImportMore}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
