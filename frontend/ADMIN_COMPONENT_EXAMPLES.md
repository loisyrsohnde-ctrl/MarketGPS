# Exemples d'Utilisation des Composants Admin

Exemples pratiques d'utilisation de tous les composants du dashboard admin.

## AdminSidebar

Le sidebar est automatiquement inclus dans le layout admin. Il n'est pas nécessaire de l'importer manuellement.

```tsx
// Utilisé automatiquement dans /app/admin/layout.tsx
import { AdminSidebar } from '@/components/admin/AdminSidebar';

export default function AdminLayout({ children }) {
  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <AdminSidebar />
      <main className="ml-64 flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
```

**Fonctionnalités automatiques:**
- Navigation actuelle mise en évidence
- Responsive (sidebar fixe)
- Dark mode supporté
- Déconnexion au clic

---

## StatsCard

Affiche une statistique avec un titre, une valeur, et optionnellement un changement en pourcentage.

### Exemple 1: Utilisateurs Total
```tsx
import { StatsCard } from '@/components/admin/StatsCard';
import { Users } from 'lucide-react';

export default function DashboardPage() {
  return (
    <StatsCard
      title="Utilisateurs Total"
      value={1250}
      change={12}  // +12% vs semaine dernière
      icon={<Users className="h-6 w-6" />}
      color="blue"
    />
  );
}
```

### Exemple 2: Avec valeur négative
```tsx
<StatsCard
  title="Scripts en Attente"
  value={5}
  change={-3}  // -3% vs semaine dernière
  icon={<FileText className="h-6 w-6" />}
  color="orange"
/>
```

### Exemple 3: Sans changement
```tsx
<StatsCard
  title="Sources Actives"
  value={24}
  icon={<Newspaper className="h-6 w-6" />}
  color="green"
/>
```

### Couleurs disponibles
- `color="blue"` - Bleu (défaut)
- `color="green"` - Vert
- `color="purple"` - Violet
- `color="orange"` - Orange
- `color="red"` - Rouge

---

## ViralityBadge

Affiche un badge coloré basé sur le score de viralité.

### Exemple 1: Badge avec label
```tsx
import { ViralityBadge } from '@/components/admin/ViralityBadge';

export default function NewsItem() {
  return (
    <ViralityBadge
      score={8.5}
      showLabel={true}
      size="md"
    />
  );
}
```

Affiche: "Très Élevée" (badge orange)

### Exemple 2: Badge avec score
```tsx
<ViralityBadge
  score={5.2}
  showLabel={false}
  size="sm"
/>
```

Affiche: "5.2x" (badge orange, petite taille)

### Exemple 3: Scores différents
```tsx
// Score très élevé
<ViralityBadge score={12} showLabel={true} />
// Affiche: "Extrême" (badge rouge)

// Score élevé
<ViralityBadge score={3.5} showLabel={true} />
// Affiche: "Élevée" (badge vert)

// Score bas
<ViralityBadge score={1.5} showLabel={true} />
// Affiche: "Basse" (badge gris)
```

### Tailles disponibles
- `size="sm"` - Petite (icône h-3 w-3)
- `size="md"` - Moyenne (icône h-4 w-4, défaut)
- `size="lg"` - Grande (icône h-5 w-5)

---

## NewsTable

Affiche un tableau des actualités virales avec actions.

### Utilisation de base
```tsx
import { NewsTable } from '@/components/admin/NewsTable';
import { useViralNews } from '@/hooks/useViralNews';

export default function NewsPage() {
  const { articles, loading } = useViralNews({
    region: 'FR',
    language: 'fr',
    minViralityScore: 2,
    page: 1,
    limit: 20,
  });

  const handleGenerateScript = async (articleId: string) => {
    try {
      await fetch('/api/admin/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ articleId }),
      });
      // Actualiser la liste
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  return (
    <NewsTable
      articles={articles}
      isLoading={loading}
      onGenerateScript={handleGenerateScript}
    />
  );
}
```

### Données attendues (ViralArticle)
```tsx
{
  id: "article-001",
  title: "Nouvelle stratégie...",
  source: "Bloomberg",
  region: "FR",
  language: "fr",
  interactions: 5230,
  viralityScore: 8.5,
  publishedAt: "2026-02-03T09:30:00Z",
  hasScript: false,
  url: "https://example.com/article/001"
}
```

### Colonnes affichées
| Colonne | Contenu | Statut |
|---------|---------|--------|
| Titre | Titre + date | Toujours |
| Source | Nom de la source | Toujours |
| Région | Badge couleur | Toujours |
| Viralité | Badge avec score | Toujours |
| Interactions | Nombre formaté | Toujours |
| Script | "✓ Généré" ou "-" | Conditionnel |
| Action | Bouton ou lien | Conditionnel |

---

## ScriptEditor

Éditeur complet pour créer/modifier un script vidéo.

### Utilisation de base
```tsx
import { ScriptEditor } from '@/components/admin/ScriptEditor';
import { useState, useEffect } from 'react';

export default function EditScriptPage({ scriptId }) {
  const [script, setScript] = useState(null);
  const [saveMessage, setSaveMessage] = useState(null);

  useEffect(() => {
    // Charger le script
    const loadScript = async () => {
      const res = await fetch(`/api/admin/scripts/${scriptId}`);
      setScript(await res.json());
    };
    loadScript();
  }, [scriptId]);

  const handleSave = async (data) => {
    const res = await fetch(`/api/admin/scripts/${scriptId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const updated = await res.json();
    setScript(updated);
    setSaveMessage('Script sauvegardé!');
  };

  const handleApprove = async () => {
    const res = await fetch(`/api/admin/scripts/${scriptId}/approve`, {
      method: 'POST',
    });
    const updated = await res.json();
    setScript(updated);
  };

  const handlePublish = async () => {
    const res = await fetch(`/api/admin/scripts/${scriptId}/publish`, {
      method: 'POST',
    });
    const updated = await res.json();
    setScript(updated);
  };

  return (
    <ScriptEditor
      script={script}
      isLoading={!script}
      onSave={handleSave}
      onApprove={handleApprove}
      onPublish={handlePublish}
    />
  );
}
```

### Structure du script
```tsx
interface VideoScript {
  id: "script-001",
  articleId: "article-001",
  title: "Titre du script",
  hook: "L'accroche pour attirer l'attention",
  scriptText: "Le texte complet du script...",
  wordCount: 1240,
  estimatedDuration: 8,  // minutes
  status: "draft",  // draft | reviewed | approved | published
  createdAt: "2026-02-03T11:00:00Z",
  updatedAt: "2026-02-03T11:00:00Z",
  articleTitle: "Titre de l'article source"
}
```

### Fonctionnalités automatiques
- **Compteur de mots**: Mis à jour en temps réel
- **Durée estimée**: Calculée à partir du contenu (~150 mots/min)
- **Aperçu formaté**: Affichage du contenu formaté
- **Badge de statut**: Couleur selon le statut
- **Actions conditionnelles**: Approuver/Publier selon le statut

### Statuts et actions disponibles
| Statut | Actions Disponibles |
|--------|-------------------|
| draft | Sauvegarder, Approuver |
| reviewed | Sauvegarder |
| approved | Sauvegarder, Publier vers Actualités |
| published | Aucune (lecture seule) |

---

## Hooks

### useAdminStats()

Récupère et rafraîchit automatiquement les statistiques.

```tsx
import { useAdminStats } from '@/hooks/useAdminStats';

export default function DashboardPage() {
  const { stats, loading, error } = useAdminStats();

  if (loading) return <div>Chargement...</div>;
  if (error) return <div>Erreur: {error}</div>;

  return (
    <div>
      <p>Utilisateurs: {stats.users.total}</p>
      <p>Articles: {stats.news.scrapedToday}</p>
      <p>Sources: {stats.system.sourcesActive}</p>
    </div>
  );
}
```

**Objet retourné:**
```tsx
{
  stats: AdminStats | null,
  loading: boolean,
  error: string | null
}
```

**Auto-refresh:** Toutes les 5 minutes

---

### useViralNews(params)

Récupère les actualités virales avec filtres et pagination.

```tsx
import { useViralNews } from '@/hooks/useViralNews';

export default function NewsPage() {
  const [filters, setFilters] = useState({
    region: 'FR',
    language: 'fr',
    minViralityScore: 2,
    page: 1,
    limit: 20,
  });

  const { articles, total, loading, error, refetch } = useViralNews(filters);

  const handleRefresh = async () => {
    await refetch();
  };

  return (
    <div>
      <button onClick={handleRefresh}>Actualiser</button>
      <p>{total} articles trouvés</p>
      {articles.map(article => (
        <div key={article.id}>{article.title}</div>
      ))}
    </div>
  );
}
```

**Objet retourné:**
```tsx
{
  articles: ViralArticle[],
  total: number,
  loading: boolean,
  error: string | null,
  refetch: () => Promise<void>
}
```

**Paramètres (optionnels):**
```tsx
{
  region?: string;           // "FR", "US", "EU", "ASIA"
  language?: string;         // "fr", "en", "de", "es"
  minViralityScore?: number; // 0.0 - 15.0
  page?: number;             // 1+
  limit?: number;            // 1-100 (défaut: 20)
}
```

---

### useVideoScripts(params)

Gestion CRUD complète des scripts vidéo.

```tsx
import { useVideoScripts } from '@/hooks/useVideoScripts';

export default function ScriptsPage() {
  const [filters, setFilters] = useState({
    status: 'draft',
    page: 1,
    limit: 20,
  });

  const {
    scripts,
    total,
    loading,
    error,
    createScript,
    updateScript,
    deleteScript,
    refetch,
  } = useVideoScripts(filters);

  const handleCreateScript = async () => {
    try {
      const newScript = await createScript('article-001', {
        title: 'Mon Script',
        hook: 'L\'accroche',
        scriptText: 'Le contenu',
      });
      console.log('Script créé:', newScript);
    } catch (err) {
      console.error('Erreur:', err);
    }
  };

  const handleUpdateScript = async (scriptId) => {
    try {
      const updated = await updateScript(scriptId, {
        title: 'Nouveau Titre',
      });
      console.log('Script mis à jour:', updated);
    } catch (err) {
      console.error('Erreur:', err);
    }
  };

  const handleDeleteScript = async (scriptId) => {
    try {
      await deleteScript(scriptId);
      console.log('Script supprimé');
    } catch (err) {
      console.error('Erreur:', err);
    }
  };

  return (
    <div>
      <button onClick={handleCreateScript}>Créer</button>
      {scripts.map(script => (
        <div key={script.id}>
          <h3>{script.title}</h3>
          <button onClick={() => handleUpdateScript(script.id)}>Éditer</button>
          <button onClick={() => handleDeleteScript(script.id)}>Supprimer</button>
        </div>
      ))}
    </div>
  );
}
```

**Objet retourné:**
```tsx
{
  scripts: VideoScript[],
  total: number,
  loading: boolean,
  error: string | null,
  createScript: (articleId: string, data: Partial<VideoScript>) => Promise<VideoScript>,
  updateScript: (id: string, data: Partial<VideoScript>) => Promise<VideoScript>,
  deleteScript: (id: string) => Promise<void>,
  refetch: () => Promise<void>
}
```

**Paramètres (optionnels):**
```tsx
{
  status?: 'draft' | 'reviewed' | 'approved' | 'published';
  page?: number;  // 1+
  limit?: number; // 1-100 (défaut: 20)
}
```

---

## Composition Complète - Dashboard Principal

```tsx
'use client';

import { useAdminStats } from '@/hooks/useAdminStats';
import { StatsCard } from '@/components/admin/StatsCard';
import {
  Users,
  Newspaper,
  FileText,
  TrendingUp,
} from 'lucide-react';

export default function AdminDashboard() {
  const { stats, loading, error } = useAdminStats();

  if (loading) return <div>Chargement...</div>;
  if (error) return <div>Erreur: {error}</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Tableau de Bord</h1>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <StatsCard
          title="Utilisateurs Total"
          value={stats?.users.total || 0}
          change={stats?.users.newThisWeek || 0}
          icon={<Users className="h-6 w-6" />}
          color="blue"
        />

        <StatsCard
          title="Utilisateurs Pro"
          value={stats?.users.pro || 0}
          icon={<TrendingUp className="h-6 w-6" />}
          color="green"
        />

        <StatsCard
          title="Articles Scrapés (Aujourd'hui)"
          value={stats?.news.scrapedToday || 0}
          icon={<Newspaper className="h-6 w-6" />}
          color="orange"
        />

        <StatsCard
          title="Scripts Générés"
          value={stats?.news.scriptsGenerated || 0}
          icon={<FileText className="h-6 w-6" />}
          color="blue"
        />
      </div>
    </div>
  );
}
```

---

## Composition Complète - Page Actualités

```tsx
'use client';

import { useState } from 'react';
import { useViralNews } from '@/hooks/useViralNews';
import { NewsTable } from '@/components/admin/NewsTable';

export default function NewsPage() {
  const [region, setRegion] = useState<string>();
  const [language, setLanguage] = useState<string>();
  const [minViralityScore, setMinViralityScore] = useState<number>();

  const { articles, total, loading, error, refetch } = useViralNews({
    region,
    language,
    minViralityScore,
  });

  const handleGenerateScript = async (articleId: string) => {
    try {
      await fetch('/api/admin/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ articleId }),
      });
      refetch();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Actualités Virales</h1>

      <div className="grid gap-4 md:grid-cols-3">
        <select
          value={region || ''}
          onChange={(e) => setRegion(e.target.value || undefined)}
          className="rounded-lg border px-4 py-2"
        >
          <option value="">Toutes les régions</option>
          <option value="FR">France</option>
          <option value="US">États-Unis</option>
        </select>

        <select
          value={language || ''}
          onChange={(e) => setLanguage(e.target.value || undefined)}
          className="rounded-lg border px-4 py-2"
        >
          <option value="">Toutes les langues</option>
          <option value="fr">Français</option>
          <option value="en">Anglais</option>
        </select>

        <select
          value={minViralityScore || ''}
          onChange={(e) => setMinViralityScore(e.target.value ? Number(e.target.value) : undefined)}
          className="rounded-lg border px-4 py-2"
        >
          <option value="">Tous les niveaux</option>
          <option value="2">2x+</option>
          <option value="5">5x+</option>
          <option value="10">10x+</option>
        </select>
      </div>

      <NewsTable
        articles={articles}
        isLoading={loading}
        onGenerateScript={handleGenerateScript}
      />

      {error && <div className="text-red-600">Erreur: {error}</div>}
    </div>
  );
}
```

---

## Points d'Attention

1. **Types**: Toujours importer les types depuis `/types/admin.ts`
2. **Hooks**: Créent automatiquement les appels API
3. **Composants**: Acceptent les données, pas les hooks
4. **Erreurs**: Toujours afficher les messages d'erreur
5. **Loading**: Afficher des loaders pendant le chargement
6. **Events**: Les actions comme "générer" doivent appeler `refetch()`

---

**Dernière mise à jour**: 3 Février 2026
