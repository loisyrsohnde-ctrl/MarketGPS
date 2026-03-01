'use client';

import { useState, useRef } from 'react';
import { useViralNews } from '@/hooks/useViralNews';
import { useEditorialScores } from '@/hooks/useEditorialScores';
import { NewsTable } from '@/components/admin/NewsTable';
import { EditorialTable } from '@/components/admin/EditorialTable';
import { CountryFilterSelector, BatchActionBar } from '@/components/admin';
import { getApiBaseUrl } from '@/lib/config';
import type { ViralArticle } from '@/types/admin';
import {
  Filter,
  RefreshCw,
  LayoutGrid,
  List,
  Flame,
  Award,
  Loader2,
  Link2,
  CheckCircle2,
  XCircle,
  Video,
  Upload,
} from 'lucide-react';

type TabType = 'viral' | 'editorial';

export default function NewsPage() {
  // ── Shared state ──────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<TabType>('viral');
  const [region, setRegion] = useState<string>();
  const [language, setLanguage] = useState<string>();
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [countries, setCountries] = useState<string[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchLoading, setBatchLoading] = useState(false);

  // ── URL Generator state ────────────────────────────────────────────────────
  const [articleUrl, setArticleUrl] = useState('');
  const [urlGenerating, setUrlGenerating] = useState(false);
  const [urlResult, setUrlResult] = useState<{ success: boolean; message: string; title?: string } | null>(null);

  // ── Video Article state ──────────────────────────────────────────────────
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoSubject, setVideoSubject] = useState('');
  const [videoContext, setVideoContext] = useState('');
  const [videoGenerating, setVideoGenerating] = useState(false);
  const [videoUploadProgress, setVideoUploadProgress] = useState(0);
  const [videoResult, setVideoResult] = useState<{ success: boolean; message: string; title?: string; slug?: string } | null>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  // ── Viral News state ──────────────────────────────────────────────────────
  const [minViralityScore, setMinViralityScore] = useState<number>();
  const [page, setPage] = useState(1);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const { articles, total, loading, error, refetch, publishArticle, rejectArticle } = useViralNews({
    region,
    language,
    minViralityScore,
    page,
    limit: 20,
  });

  // ── Editorial state ───────────────────────────────────────────────────────
  const [topK, setTopK] = useState(50);
  const [daysBack, setDaysBack] = useState(3);
  const [minScore, setMinScore] = useState(25);

  const {
    articles: editorialArticles,
    total: editorialTotal,
    updatedAt,
    loading: editorialLoading,
    error: editorialError,
    refetch: editorialRefetch,
    rescore,
    rescoring,
  } = useEditorialScores({ topK, daysBack, minScore });

  // ── URL Generator handler ────────────────────────────────────────────────
  const handleGenerateFromUrl = async () => {
    if (!articleUrl.trim()) return;
    setUrlGenerating(true);
    setUrlResult(null);
    try {
      const API_BASE = getApiBaseUrl();
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/generate-from-url`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: articleUrl.trim() }),
      });
      const data = await response.json();
      setUrlResult({
        success: data.success,
        message: data.message,
        title: data.title,
      });
      if (data.success) {
        setArticleUrl('');
        await refetch();
      }
    } catch (err) {
      setUrlResult({ success: false, message: 'Erreur de connexion au serveur' });
    } finally {
      setUrlGenerating(false);
    }
  };

  // ── Video Article handler ────────────────────────────────────────────────
  const handleGenerateVideoArticle = async () => {
    if (!videoFile || !videoSubject.trim()) return;
    setVideoGenerating(true);
    setVideoResult(null);
    setVideoUploadProgress(0);

    const API_BASE = getApiBaseUrl();
    const adminKey = localStorage.getItem('adminKey') || '';

    try {
      // Step 1: Upload the video file
      const formData = new FormData();
      formData.append('file', videoFile);

      const xhr = new XMLHttpRequest();
      const uploadResult = await new Promise<{ success: boolean; video_url?: string; size_mb?: number; detail?: string }>((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            setVideoUploadProgress(Math.round((e.loaded / e.total) * 100));
          }
        });
        xhr.addEventListener('load', () => {
          try {
            const data = JSON.parse(xhr.responseText);
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(data);
            } else {
              resolve({ success: false, detail: data.detail || 'Erreur upload' });
            }
          } catch {
            resolve({ success: false, detail: 'Erreur de parsing' });
          }
        });
        xhr.addEventListener('error', () => {
          console.error('[VideoArticle] XHR error — status:', xhr.status, 'readyState:', xhr.readyState, 'URL:', `${API_BASE}/api/article-videos/upload`);
          reject(new Error(`Network error (status=${xhr.status}, state=${xhr.readyState})`));
        });
        xhr.open('POST', `${API_BASE}/api/article-videos/upload`);
        console.log('[VideoArticle] Uploading to:', `${API_BASE}/api/article-videos/upload`);
        xhr.setRequestHeader('X-Admin-Key', adminKey);
        xhr.send(formData);
      });

      if (!uploadResult.success || !uploadResult.video_url) {
        setVideoResult({
          success: false,
          message: uploadResult.detail || 'Erreur lors de l\'upload de la vidéo',
        });
        return;
      }

      setVideoUploadProgress(100);

      // Step 2: Generate the article with AI
      const genResponse = await fetch(`${API_BASE}/api/admin/generate-video-article`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject: videoSubject.trim(),
          context: videoContext.trim(),
          video_url: uploadResult.video_url,
        }),
      });
      const genData = await genResponse.json();

      setVideoResult({
        success: genData.success,
        message: genData.message,
        title: genData.title,
        slug: genData.slug,
      });

      if (genData.success) {
        setVideoFile(null);
        setVideoSubject('');
        setVideoContext('');
        if (videoInputRef.current) videoInputRef.current.value = '';
        await refetch();
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      console.error('[VideoArticle] Error:', errMsg, err);
      setVideoResult({ success: false, message: `Erreur: ${errMsg}` });
    } finally {
      setVideoGenerating(false);
      setVideoUploadProgress(0);
    }
  };

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleGenerateScript = async (articleId: string) => {
    setGeneratingId(articleId);
    try {
      const { getApiBaseUrl } = await import('@/lib/config');
      const API_BASE = getApiBaseUrl();
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/scripts`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article_id: articleId }),
      });

      if (response.ok) {
        await refetch();
      } else {
        const errorData = await response.json();
        console.error('Error generating script:', errorData);
      }
    } catch (err) {
      console.error('Erreur lors de la génération du script:', err);
    } finally {
      setGeneratingId(null);
    }
  };

  const handleRescore = async () => {
    const result = await rescore(daysBack, topK);
    if (!result.success) {
      console.error('Rescore failed:', result.message);
    }
  };

  // ── Batch Operations ──────────────────────────────────────────────────────
  const handleBatchPublish = async () => {
    if (selectedIds.size === 0) return;
    setBatchLoading(true);
    try {
      const API_BASE = getApiBaseUrl();
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/articles/batch`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'publish',
          article_ids: Array.from(selectedIds),
        }),
      });

      if (response.ok) {
        setSelectedIds(new Set());
        await refetch();
      } else {
        const errorData = await response.json();
        console.error('Error publishing articles:', errorData);
      }
    } catch (err) {
      console.error('Erreur lors de la publication en masse:', err);
    } finally {
      setBatchLoading(false);
    }
  };

  const handleBatchReject = async () => {
    if (selectedIds.size === 0) return;
    setBatchLoading(true);
    try {
      const API_BASE = getApiBaseUrl();
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/articles/batch`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'reject',
          article_ids: Array.from(selectedIds),
        }),
      });

      if (response.ok) {
        setSelectedIds(new Set());
        await refetch();
      } else {
        const errorData = await response.json();
        console.error('Error rejecting articles:', errorData);
      }
    } catch (err) {
      console.error('Erreur lors du rejet en masse:', err);
    } finally {
      setBatchLoading(false);
    }
  };

  const handleBatchExport = () => {
    if (selectedIds.size === 0) return;

    const selectedArticles = articles.filter((a) => selectedIds.has(a.id));
    const csv = generateCSV(selectedArticles);

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `articles_${new Date().toISOString()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const generateCSV = (articles: ViralArticle[]): string => {
    const headers = [
      'ID',
      'Titre',
      'Source',
      'Région',
      'Interactions',
      'Viralité',
      'URL',
      'Date Publiée',
    ];
    const rows = articles.map((article: ViralArticle) => [
      article.id,
      `"${article.title.replace(/"/g, '""')}"`,
      article.source,
      article.region,
      article.interactions,
      article.viralityScore,
      article.url || '',
      new Date(article.publishedAt).toISOString(),
    ] as string[]);

    return [
      headers.join(','),
      ...rows.map((row: string[]) => row.join(',')),
    ].join('\n');
  };

  const totalPages = Math.ceil(total / 20);
  const currentLoading = activeTab === 'viral' ? loading : editorialLoading;
  const currentError = activeTab === 'viral' ? error : editorialError;
  const currentTotal = activeTab === 'viral' ? total : editorialTotal;

  return (
    <div className={`space-y-8 ${selectedIds.size > 0 ? 'pb-24' : ''}`}>
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Actualités
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gérez les actualités virales et le classement éditorial
        </p>
      </div>

      {/* Article Generator (URL or Topic) */}
      <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-5 dark:border-emerald-900/40 dark:bg-emerald-900/10">
        <div className="flex items-center gap-2 mb-3">
          <Link2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
            {"Générer un article"}
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {"Collez un lien (URL) ou saisissez un sujet. L'IA va rédiger un article complet en français et le publier directement."}
        </p>
        <div className="flex gap-3">
          <input
            type="text"
            value={articleUrl}
            onChange={(e) => {
              setArticleUrl(e.target.value);
              setUrlResult(null);
            }}
            onKeyDown={(e) => e.key === 'Enter' && handleGenerateFromUrl()}
            placeholder="https://example.com/article... ou un sujet : La fintech au Cameroun en 2026"
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          />
          <button
            onClick={handleGenerateFromUrl}
            disabled={urlGenerating || !articleUrl.trim()}
            className="rounded-lg bg-emerald-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-emerald-500 dark:hover:bg-emerald-600 flex items-center gap-2 whitespace-nowrap"
          >
            {urlGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {"Génération..."}
              </>
            ) : (
              <>
                <Link2 className="h-4 w-4" />
                {"Générer"}
              </>
            )}
          </button>
        </div>
        {urlResult && (
          <div className={`mt-3 flex items-start gap-2 rounded-md px-3 py-2 text-sm ${
            urlResult.success
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
              : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
          }`}>
            {urlResult.success ? (
              <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
            )}
            <div>
              <p>{urlResult.message}</p>
              {urlResult.title && (
                <p className="font-medium mt-0.5">{urlResult.title}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Video Article Generator */}
      <div className="rounded-lg border border-purple-200 bg-purple-50/50 p-5 dark:border-purple-900/40 dark:bg-purple-900/10">
        <div className="flex items-center gap-2 mb-3">
          <Video className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
            {"Article Vidéo"}
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {"Uploadez une vidéo, décrivez le sujet et le contexte. L'IA génère un article complet qui accompagne la vidéo."}
        </p>

        <div className="space-y-3">
          {/* Video file input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Fichier vidéo
            </label>
            <div className="flex items-center gap-3">
              <input
                ref={videoInputRef}
                type="file"
                accept=".mp4,.webm,.m4v"
                onChange={(e) => {
                  setVideoFile(e.target.files?.[0] || null);
                  setVideoResult(null);
                }}
                className="flex-1 text-sm text-gray-600 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-100 file:text-purple-700 hover:file:bg-purple-200 dark:file:bg-purple-900/30 dark:file:text-purple-300"
              />
              {videoFile && (
                <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  {(videoFile.size / (1024 * 1024)).toFixed(1)} MB
                </span>
              )}
            </div>
          </div>

          {/* Subject input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Sujet de la vidéo
            </label>
            <input
              type="text"
              value={videoSubject}
              onChange={(e) => {
                setVideoSubject(e.target.value);
                setVideoResult(null);
              }}
              placeholder="Ex: L'essor de la fintech mobile au Sénégal"
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
            />
          </div>

          {/* Context textarea */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Contexte additionnel <span className="text-gray-400 font-normal">(optionnel)</span>
            </label>
            <textarea
              value={videoContext}
              onChange={(e) => setVideoContext(e.target.value)}
              rows={3}
              placeholder="Décrivez le contenu de la vidéo, les points clés abordés, les intervenants..."
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500 resize-none"
            />
          </div>

          {/* Upload progress */}
          {videoGenerating && videoUploadProgress > 0 && videoUploadProgress < 100 && (
            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
              <div
                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${videoUploadProgress}%` }}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Upload : {videoUploadProgress}%
              </p>
            </div>
          )}
          {videoGenerating && videoUploadProgress >= 100 && (
            <p className="text-xs text-purple-600 dark:text-purple-400 flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              {"Génération de l'article en cours..."}
            </p>
          )}

          {/* Generate button */}
          <button
            onClick={handleGenerateVideoArticle}
            disabled={videoGenerating || !videoFile || !videoSubject.trim()}
            className="rounded-lg bg-purple-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-purple-500 dark:hover:bg-purple-600 flex items-center gap-2"
          >
            {videoGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {videoUploadProgress < 100 ? 'Upload...' : 'Génération...'}
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                {"Générer l'article vidéo"}
              </>
            )}
          </button>
        </div>

        {/* Result */}
        {videoResult && (
          <div className={`mt-3 flex items-start gap-2 rounded-md px-3 py-2 text-sm ${
            videoResult.success
              ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300'
              : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
          }`}>
            {videoResult.success ? (
              <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
            )}
            <div>
              <p>{videoResult.message}</p>
              {videoResult.title && (
                <p className="font-medium mt-0.5">{videoResult.title}</p>
              )}
              {videoResult.slug && (
                <a
                  href={`/news/${videoResult.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-700 dark:text-purple-300 underline text-xs mt-1 inline-block"
                >
                  {"Voir l'article →"}
                </a>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
        <button
          onClick={() => setActiveTab('viral')}
          className={`flex items-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all ${
            activeTab === 'viral'
              ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
              : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Flame className="h-4 w-4" />
          {"Actualités Virales"}
        </button>
        <button
          onClick={() => setActiveTab('editorial')}
          className={`flex items-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all ${
            activeTab === 'editorial'
              ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
              : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Award className="h-4 w-4" />
          {"Intelligence Éditoriale"}
        </button>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Filtres
          </h3>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {/* Countries Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Pays
            </label>
            <CountryFilterSelector
              selected={countries}
              onChange={(selectedCountries) => {
                setCountries(selectedCountries);
                setPage(1);
              }}
            />
          </div>

          {/* Language Filter (shared) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Langue
            </label>
            <select
              value={language || ''}
              onChange={(e) => {
                setLanguage(e.target.value || undefined);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Toutes les langues</option>
              <option value="fr">{"Français"}</option>
              <option value="en">Anglais</option>
              <option value="de">Allemand</option>
              <option value="es">Espagnol</option>
            </select>
          </div>

          {/* Tab-specific filters */}
          {activeTab === 'viral' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                {"Viralité Min"}
              </label>
              <select
                value={minViralityScore || ''}
                onChange={(e) => {
                  setMinViralityScore(
                    e.target.value ? Number(e.target.value) : undefined
                  );
                  setPage(1);
                }}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              >
                <option value="">Tous les niveaux</option>
                <option value="2">2x</option>
                <option value="5">5x</option>
                <option value="10">10x</option>
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Score Min
              </label>
              <select
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              >
                <option value={0}>Tous</option>
                <option value={25}>25+</option>
                <option value={40}>40+</option>
                <option value={60}>60+</option>
                <option value={80}>80+</option>
              </select>
            </div>
          )}

          {/* Action Button */}
          <div className="flex items-end gap-2">
            <button
              onClick={() =>
                activeTab === 'viral' ? refetch() : editorialRefetch()
              }
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 flex items-center justify-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Actualiser
            </button>
            {activeTab === 'editorial' && (
              <button
                onClick={handleRescore}
                disabled={rescoring}
                className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-600 flex items-center justify-center gap-2"
                title="Relancer le scoring éditorial sur les articles récents"
              >
                {rescoring ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Award className="h-4 w-4" />
                )}
                {rescoring ? 'Scoring...' : 'Rescorer'}
              </button>
            )}
          </div>
        </div>

        {/* Editorial-specific: days back selector */}
        {activeTab === 'editorial' && (
          <div className="mt-4 flex items-center gap-4 text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              {"Période :"}
            </span>
            {[1, 3, 7, 14].map((d) => (
              <button
                key={d}
                onClick={() => setDaysBack(d)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  daysBack === d
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                {d}j
              </button>
            ))}
            {updatedAt && (
              <span className="ml-auto text-xs text-gray-500 dark:text-gray-500">
                {"Mis à jour :"}{' '}
                {new Date(updatedAt).toLocaleString('fr-FR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Error Message */}
      {currentError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">
            Erreur: {currentError}
          </p>
        </div>
      )}

      {/* View Controls & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {!currentLoading && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {currentTotal > 0 ? (
              <>
                <strong>{currentTotal}</strong>{' '}
                {activeTab === 'viral' ? 'actualités' : 'articles classés'}
              </>
            ) : (
              <span>Aucun r&eacute;sultat</span>
            )}
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('cards')}
            className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              viewMode === 'cards'
                ? 'bg-blue-600 text-white dark:bg-blue-500'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
            }`}
          >
            <LayoutGrid className="h-4 w-4" />
            Cartes
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              viewMode === 'table'
                ? 'bg-blue-600 text-white dark:bg-blue-500'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
            }`}
          >
            <List className="h-4 w-4" />
            Tableau
          </button>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'viral' ? (
        <>
          <NewsTable
            articles={articles}
            isLoading={loading}
            onGenerateScript={handleGenerateScript}
            onPublish={publishArticle}
            onReject={rejectArticle}
            viewMode={viewMode}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
          />
          <BatchActionBar
            selectedCount={selectedIds.size}
            onPublish={handleBatchPublish}
            onReject={handleBatchReject}
            onExport={handleBatchExport}
            onClear={() => setSelectedIds(new Set())}
            loading={batchLoading}
          />
        </>
      ) : (
        <EditorialTable
          articles={editorialArticles}
          isLoading={editorialLoading}
          viewMode={viewMode}
        />
      )}

      {/* Pagination (viral only) */}
      {activeTab === 'viral' && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            {"Précédent"}
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter(
              (p) => Math.abs(p - page) <= 2 || p === 1 || p === totalPages
            )
            .map((p, i, arr) => (
              <div key={p}>
                {i > 0 && arr[i - 1] !== p - 1 && (
                  <span className="px-2 text-gray-600 dark:text-gray-400">
                    ...
                  </span>
                )}
                <button
                  onClick={() => setPage(p)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium ${
                    page === p
                      ? 'bg-blue-600 text-white dark:bg-blue-500'
                      : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
                  }`}
                >
                  {p}
                </button>
              </div>
            ))}

          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  );
}
