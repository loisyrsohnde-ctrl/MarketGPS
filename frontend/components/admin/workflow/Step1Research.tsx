'use client';

import { ExternalLink, Globe, Calendar, Flag } from 'lucide-react';
import { WorkflowArticle } from '@/hooks/useArticleWorkflow';
import ProgressBar from '@/components/admin/ProgressBar';

interface Step1ResearchProps {
  article: WorkflowArticle;
}

const countryFlags: { [key: string]: string } = {
  'FR': '🇫🇷',
  'CA': '🇨🇦',
  'BE': '🇧🇪',
  'CH': '🇨🇭',
  'CI': '🇨🇮',
  'SN': '🇸🇳',
  'CM': '🇨🇲',
  'ZA': '🇿🇦',
  'NG': '🇳🇬',
  'EG': '🇪🇬',
  'KE': '🇰🇪',
  'RW': '🇷🇼',
  'UG': '🇺🇬',
  'TZ': '🇹🇿',
  'ZM': '🇿🇲',
  'ZW': '🇿🇼',
  'BW': '🇧🇼',
  'NA': '🇳🇦',
  'MZ': '🇲🇿',
  'MW': '🇲🇼',
  'GA': '🇬🇦',
  'CG': '🇨🇬',
  'CD': '🇨🇩',
  'AO': '🇦🇴',
  'GH': '🇬🇭',
  'TG': '🇹🇬',
  'BJ': '🇧🇯',
  'NE': '🇳🇪',
  'ML': '🇲🇱',
  'MR': '🇲🇷',
  'ET': '🇪🇹',
  'SD': '🇸🇩',
  'MA': '🇲🇦',
  'TN': '🇹🇳',
  'DZ': '🇩🇿',
  'LY': '🇱🇾',
};

const languageLabels: { [key: string]: string } = {
  'en': 'Anglais',
  'fr': 'Français',
  'es': 'Espagnol',
  'de': 'Allemand',
  'pt': 'Portugais',
  'ar': 'Arabe',
  'sw': 'Swahili',
  'yo': 'Yoruba',
  'zu': 'Zulu',
};

export default function Step1Research({ article }: Step1ResearchProps) {
  const countryFlag = countryFlags[article.country] || '🌍';
  const languageLabel = languageLabels[article.language.toLowerCase()] || article.language;

  const getViralityBadge = () => {
    if (!article.interactions_count) return null;

    let level = 'Faible';
    let color = 'bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-slate-200';

    if (article.interactions_count > 10000) {
      level = 'Virale';
      color = 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    } else if (article.interactions_count > 5000) {
      level = 'Très élevée';
      color = 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    } else if (article.interactions_count > 1000) {
      level = 'Élevée';
      color = 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200';
    } else if (article.interactions_count > 100) {
      level = 'Modérée';
      color = 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${color}`}>
        {level} ({article.interactions_count.toLocaleString()})
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Article Info Card */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
        <div className="p-8">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">
            Informations de l&apos;article
          </h2>

          <div className="space-y-6">
            {/* Title */}
            <div>
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Titre
              </h3>
              <p className="text-lg text-slate-900 dark:text-slate-100">{article.title}</p>
            </div>

            {/* Source Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Source
                </h3>
                <p className="text-slate-900 dark:text-slate-100">{article.source_title}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Lien source
                </h3>
                <a
                  href={article.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors break-all"
                >
                  {article.source_url}
                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                </a>
              </div>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Flag className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    Pays
                  </h4>
                </div>
                <p className="text-base font-medium text-slate-900 dark:text-slate-100">
                  {countryFlag} {article.country}
                </p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    Langue
                  </h4>
                </div>
                <p className="text-base font-medium text-slate-900 dark:text-slate-100">
                  {languageLabel}
                </p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    Publication
                  </h4>
                </div>
                <p className="text-base font-medium text-slate-900 dark:text-slate-100">
                  {new Date(article.published_date).toLocaleDateString('fr-FR')}
                </p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">
                    Catégorie
                  </h4>
                </div>
                <p className="text-base font-medium text-slate-900 dark:text-slate-100">
                  {article.category || 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Editorial Scores */}
      {article.editorial_scores && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-6">
            Analyse éditoriale
          </h2>

          <div className="space-y-5">
            <ProgressBar
              label="Pertinence"
              value={article.editorial_scores.relevance}
              max={10}
            />
            <ProgressBar
              label="Impact"
              value={article.editorial_scores.impact}
              max={10}
            />
            <ProgressBar
              label="Originalité"
              value={article.editorial_scores.originality}
              max={10}
            />
            <ProgressBar
              label="Opportunité"
              value={article.editorial_scores.timeliness}
              max={10}
            />
            <ProgressBar
              label="Engagement"
              value={article.editorial_scores.engagement}
              max={10}
            />
          </div>
        </div>
      )}

      {/* Virality and Interactions */}
      {article.interactions_count !== undefined && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">
            Intérêt du public
          </h2>
          <div className="flex items-center gap-4">
            {getViralityBadge()}
          </div>
        </div>
      )}

      {/* Next Step Button */}
      <div className="flex justify-end">
        <button
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors dark:bg-blue-700 dark:hover:bg-blue-600"
        >
          Passer à la rédaction
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 10l-4.293-4.293a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
