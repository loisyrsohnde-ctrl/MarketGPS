'use client';

import { useState, useMemo } from 'react';
import { useNewsSources } from '@/hooks/useNewsSources';
import { Plus, Edit2, Eye, EyeOff, AlertCircle, Loader, Search } from 'lucide-react';
import { NewsSource } from '@/types/admin';

type Region = 'PAN' | 'NORTH' | 'WEST' | 'CENTRAL' | 'EAST' | 'SOUTH' | 'EUROPE';
type Language = 'fr' | 'en' | 'de';

const REGIONS: Record<Region, string> = {
  PAN: 'Panafricain',
  NORTH: 'Afrique du Nord',
  WEST: 'Afrique de l\'Ouest',
  CENTRAL: 'Afrique Centrale',
  EAST: 'Afrique de l\'Est',
  SOUTH: 'Afrique Australe',
  EUROPE: 'Europe',
};

const LANGUAGES: Record<Language, string> = {
  fr: 'Français',
  en: 'Anglais',
  de: 'Allemand',
};

export default function SourcesPage() {
  const { sources, loading, error, toggleSource, refetch } = useNewsSources();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRegion, setSelectedRegion] = useState<Region | ''>('');
  const [selectedLanguage, setSelectedLanguage] = useState<Language | ''>('');
  const [sortBy, setSortBy] = useState<'name' | 'trust_score' | 'region'>('name');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<NewsSource | null>(null);

  // Filter and sort sources
  const filteredSources = useMemo(() => {
    let filtered = sources.filter((source) => {
      if (searchTerm && !source.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      if (selectedRegion && source.region !== selectedRegion) {
        return false;
      }
      if (selectedLanguage && source.language !== selectedLanguage) {
        return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'trust_score') {
        return b.trust_score - a.trust_score;
      } else if (sortBy === 'region') {
        return a.region.localeCompare(b.region);
      }
      return 0;
    });

    return filtered;
  }, [sources, searchTerm, selectedRegion, selectedLanguage, sortBy]);

  // Calculate stats
  const stats = useMemo(() => {
    const active = sources.filter((s) => s.enabled).length;
    const byRegion: Record<string, number> = {};
    sources.forEach((s) => {
      byRegion[s.region] = (byRegion[s.region] || 0) + 1;
    });
    return {
      total: sources.length,
      active,
      byRegion,
    };
  }, [sources]);

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Gestion des Sources
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Gérez les sources de contenu du système
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader className="h-6 w-6 animate-spin text-blue-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Gestion des Sources
          </h1>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <p className="text-sm text-red-800 dark:text-red-300">
              Erreur lors du chargement des sources: {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Gestion des Sources ({sources.length})
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Gérez les sources de contenu du système
          </p>
        </div>
        <button
          onClick={() => {
            setEditingSource(null);
            setIsModalOpen(true);
          }}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          <Plus className="h-4 w-4" />
          Ajouter une Source
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Total Sources
          </p>
          <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
            {stats.total}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Sources Actives
          </p>
          <p className="mt-2 text-2xl font-bold text-green-600 dark:text-green-400">
            {stats.active}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Régions
          </p>
          <p className="mt-2 text-2xl font-bold text-blue-600 dark:text-blue-400">
            {Object.keys(stats.byRegion).length}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Score Moyen
          </p>
          <p className="mt-2 text-2xl font-bold text-orange-600 dark:text-orange-400">
            {(
              sources.reduce((sum, s) => sum + s.trust_score, 0) / sources.length
            ).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-4 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <div className="grid gap-4 md:grid-cols-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Rechercher
            </label>
            <div className="mt-1 flex items-center rounded-lg border border-gray-300 dark:border-gray-600">
              <Search className="ml-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Nom de la source..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 border-0 bg-transparent px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none dark:text-white dark:placeholder-gray-400"
              />
            </div>
          </div>

          {/* Region Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Région
            </label>
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value as Region | '')}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Toutes les régions</option>
              {Object.entries(REGIONS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Langue
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value as Language | '')}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Toutes les langues</option>
              {Object.entries(LANGUAGES).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Trier par
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'trust_score' | 'region')}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="name">Nom</option>
              <option value="trust_score">Score de Confiance</option>
              <option value="region">Région</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Nom
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Région
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Langue
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Score
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Type
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Statut
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredSources.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                  Aucune source trouvée
                </td>
              </tr>
            ) : (
              filteredSources.map((source, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
                >
                  <td className="px-6 py-4">
                    <p className="font-medium text-gray-900 dark:text-white">
                      {source.name}
                    </p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {REGIONS[source.region as Region]}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {LANGUAGES[source.language as Language]}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {(source.trust_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-block rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                      {source.type}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => toggleSource(source.name)}
                      className="flex items-center gap-1 text-sm font-medium"
                    >
                      {source.enabled ? (
                        <>
                          <Eye className="h-4 w-4 text-green-600 dark:text-green-400" />
                          <span className="text-green-600 dark:text-green-400">Actif</span>
                        </>
                      ) : (
                        <>
                          <EyeOff className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-400">Inactif</span>
                        </>
                      )}
                    </button>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditingSource(source);
                          setIsModalOpen(true);
                        }}
                        className="rounded-lg bg-gray-100 p-2 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
                        title="Éditer"
                      >
                        <Edit2 className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <SourceModal
          source={editingSource}
          onClose={() => {
            setIsModalOpen(false);
            setEditingSource(null);
          }}
          onSave={() => {
            setIsModalOpen(false);
            setEditingSource(null);
            refetch();
          }}
        />
      )}
    </div>
  );
}

interface SourceModalProps {
  source: NewsSource | null;
  onClose: () => void;
  onSave: () => void;
}

function SourceModal({ source, onClose, onSave }: SourceModalProps) {
  const [formData, setFormData] = useState<NewsSource>(
    source || {
      name: '',
      url: '',
      rss_url: '',
      type: 'rss',
      country: null,
      region: 'PAN',
      language: 'en',
      tags: [],
      trust_score: 0.7,
      enabled: true,
    }
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Implementation would connect to API
    onSave();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 dark:bg-gray-900">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {source ? 'Éditer la Source' : 'Ajouter une Source'}
        </h2>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Nom
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Type
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as 'rss' | 'scraper' })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              >
                <option value="rss">RSS</option>
                <option value="scraper">Scraper</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                URL
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                URL RSS
              </label>
              <input
                type="url"
                value={formData.rss_url}
                onChange={(e) => setFormData({ ...formData, rss_url: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Région
              </label>
              <select
                value={formData.region}
                onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              >
                {Object.entries(REGIONS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Langue
              </label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value as 'fr' | 'en' | 'de' })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              >
                {Object.entries(LANGUAGES).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Score de Confiance ({(formData.trust_score * 100).toFixed(0)}%)
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={formData.trust_score}
                onChange={(e) => setFormData({ ...formData, trust_score: parseFloat(e.target.value) })}
                className="mt-2 w-full"
              />
            </div>
            <div className="flex items-end gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="h-4 w-4 rounded"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Actif
                </span>
              </label>
            </div>
          </div>

          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
            >
              Sauvegarder
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
