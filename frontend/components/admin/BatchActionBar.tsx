'use client';

import { X, FileDown, Check, XCircle } from 'lucide-react';

interface BatchActionBarProps {
  selectedCount: number;
  onPublish: () => void;
  onReject: () => void;
  onExport: () => void;
  onClear: () => void;
  loading: boolean;
}

export function BatchActionBar({
  selectedCount,
  onPublish,
  onReject,
  onExport,
  onClear,
  loading,
}: BatchActionBarProps) {
  if (selectedCount === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-gray-200 bg-gray-900 px-6 py-4 shadow-lg animate-in slide-in-from-bottom dark:border-gray-700 dark:bg-gray-950">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6">
        {/* Left: Selection Info */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-white">
            {selectedCount} article{selectedCount > 1 ? 's' : ''} sélectionné{selectedCount > 1 ? 's' : ''}
          </span>
          <button
            onClick={onClear}
            className="text-sm text-gray-400 hover:text-gray-200 transition-colors underline"
          >
            Effacer la sélection
          </button>
        </div>

        {/* Right: Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={onPublish}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition-colors dark:bg-green-500 dark:hover:bg-green-600"
            title="Publier les articles sélectionnés"
          >
            <Check className="h-4 w-4" />
            Publier
          </button>

          <button
            onClick={onReject}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors dark:bg-red-500 dark:hover:bg-red-600"
            title="Rejeter les articles sélectionnés"
          >
            <XCircle className="h-4 w-4" />
            Rejeter
          </button>

          <button
            onClick={onExport}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-gray-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-600 disabled:opacity-50 transition-colors dark:bg-gray-600 dark:hover:bg-gray-500"
            title="Exporter en CSV"
          >
            <FileDown className="h-4 w-4" />
            Exporter CSV
          </button>
        </div>
      </div>
    </div>
  );
}
