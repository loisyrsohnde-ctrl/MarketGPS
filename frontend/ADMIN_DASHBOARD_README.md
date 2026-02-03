# Admin Dashboard MarketGPS

Dashboard administrateur complet pour la gestion de MarketGPS, avec support des actualités virales, scripts vidéo et gestion des utilisateurs.

## Structure

### Pages Admin (`/app/admin/`)

#### 1. Dashboard Principal (`/app/admin/page.tsx`)
Page d'accueil avec statistiques système:
- Nombre total d'utilisateurs (total, pro, free, nouveaux)
- Articles scrapés aujourd'hui
- Scripts générés
- Graphique d'activité hebdomadaire
- Distribution des plans
- Statut du pipeline de scraping
- Nombre de sources actives

#### 2. Actualités Virales (`/app/admin/news/page.tsx`)
Gestion des actualités virales avec:
- Tableau filtrable et paginé (20 par page)
- Filtres: région, langue, score de viralité minimum
- Affichage: titre, source, région, score viralité, interactions
- Bouton "Générer Script" pour créer automatiquement un script
- Badge "Script généré" si un script existe déjà
- Lien vers la page de modification du script

#### 3. Scripts Vidéo (`/app/admin/scripts/page.tsx`)
Gestion complète des scripts avec:
- Liste des scripts avec pagination
- Filtres par statut (brouillon, révision, approuvé, publié)
- Affichage: titre, article source, nombre de mots, durée estimée, date
- Actions: éditer, supprimer
- Confirmation avant suppression (modal)

#### 4. Édition de Script (`/app/admin/scripts/[id]/page.tsx`)
Éditeur complet de script avec:
- Affichage de l'article source
- Champ titre du script
- Éditeur pour l'accroche (hook)
- Textarea principal pour le script
- Compteur de mots en temps réel
- Calcul automatique de la durée estimée (~150 mots/minute)
- Aperçu formaté
- Affichage du statut
- Boutons: Sauvegarder, Approuver, Publier vers Actualités
- Messages de confirmation/erreur

#### 5. Utilisateurs (`/app/admin/users/page.tsx`)
Gestion des utilisateurs avec:
- Recherche par email
- Filtres par plan (tous, gratuit, pro, entreprise)
- Tableau avec: nom, email, plan, date inscription
- Affichage du dernier accès avec indicateur (aujourd'hui, hier, etc.)
- Badge de statut actif/inactif
- Pagination

#### 6. Paramètres (`/app/admin/settings/page.tsx`)
Configuration du système:
- Score de viralité minimum
- Nombre max d'articles par jour
- Modèle IA pour la génération (GPT-4, GPT-3.5, Claude)
- Activation/désactivation des notifications
- Mode maintenance

### Composants Admin (`/components/admin/`)

#### AdminSidebar
Navigation latérale avec:
- Logo et titre "Admin Panel"
- Liens actifs vers les pages principales
- Indicateur visuel de la page active
- Bouton déconnexion en bas
- Support dark mode

#### StatsCard
Carte de statistique générique:
```tsx
<StatsCard
  title="Titre"
  value={100}
  change={15}  // % changement
  icon={<IconComponent />}
  color="blue" // blue | green | purple | orange | red
/>
```

#### ViralityBadge
Badge coulé selon le niveau de viralité:
- Score > 10: Extrême (rouge)
- Score > 5: Très élevée (orange)
- Score > 2: Élevée (vert)
- Score < 2: Basse (gris)

Props:
```tsx
<ViralityBadge
  score={5.3}
  showLabel={true}
  size="md" // sm | md | lg
/>
```

#### NewsTable
Tableau des actualités virales avec:
- Colonnes: titre, source, région, viralité, interactions, script, actions
- Indicateur de chargement (skeleton)
- Message si aucune actualité
- Bouton "Générer Script" avec état de chargement
- Lien vers la page de modification si script existe

#### ScriptEditor
Éditeur complet de script avec:
- Affichage article source
- Champs: titre, hook, script complet
- Aperçu formaté en temps réel
- Compteur de mots
- Durée estimée
- Affichage du statut
- Actions: Sauvegarder, Approuver, Publier
- États de chargement pour chaque bouton

### Hooks (`/hooks/`)

#### useAdminStats()
Récupère les statistiques du dashboard:
```tsx
const { stats, loading, error } = useAdminStats();
// Refresh automatique toutes les 5 minutes
```

#### useViralNews(params?)
Récupère les actualités virales avec filtres:
```tsx
const { articles, total, loading, error, refetch } = useViralNews({
  region?: string;
  language?: string;
  minViralityScore?: number;
  page?: number;
  limit?: number;
});
```

#### useVideoScripts(params?)
Gestion CRUD complète des scripts:
```tsx
const {
  scripts,
  total,
  loading,
  error,
  createScript,
  updateScript,
  deleteScript,
  refetch
} = useVideoScripts({
  status?: 'draft' | 'reviewed' | 'approved' | 'published';
  page?: number;
  limit?: number;
});
```

### Types (`/types/admin.ts`)

#### AdminStats
```tsx
interface AdminStats {
  users: {
    total: number;
    pro: number;
    free: number;
    newToday: number;
    newThisWeek: number;
  };
  news: {
    scrapedToday: number;
    viralCount: number;
    scriptsGenerated: number;
  };
  system: {
    lastPipelineRun: string;
    sourcesActive: number;
  };
}
```

#### ViralArticle
```tsx
interface ViralArticle {
  id: string;
  title: string;
  source: string;
  region: string;
  language: string;
  interactions: number;
  viralityScore: number;
  publishedAt: string;
  hasScript: boolean;
  url?: string;
}
```

#### VideoScript
```tsx
interface VideoScript {
  id: string;
  articleId: string;
  title: string;
  hook: string;
  scriptText: string;
  wordCount: number;
  estimatedDuration: number;
  status: 'draft' | 'reviewed' | 'approved' | 'published';
  createdAt: string;
  updatedAt: string;
  articleTitle?: string;
}
```

#### User
```tsx
interface User {
  id: string;
  email: string;
  name: string;
  plan: 'free' | 'pro' | 'enterprise';
  createdAt: string;
  lastLogin: string;
  isActive: boolean;
}
```

## Design & Styles

- **Framework**: Next.js 13+ avec App Router
- **Styling**: Tailwind CSS
- **Dark Mode**: Support complet du dark mode avec classe `dark`
- **Icons**: Lucide React
- **Responsive**: Optimisé pour desktop (sidebar fixe, layout fluide)

## Couleurs

- **Primaire**: Bleu (`#3b82f6`)
- **Succès**: Vert (`#10b981`)
- **Danger**: Rouge (`#ef4444`)
- **Attention**: Orange (`#f97316`)
- **Info**: Bleu (`#0ea5e9`)

## Authentification

Le layout admin vérifie automatiquement l'authentification:
- Endpoint: `GET /api/admin/auth/check`
- Redirige vers `/login` si non autorisé
- Affiche un loader pendant la vérification

## API Endpoints Requis

### Stats
- `GET /api/admin/stats` - Récupère les statistiques

### Actualités
- `GET /api/admin/news?region=...&language=...&minViralityScore=...&page=...&limit=...`
- `POST /api/admin/scripts/generate` - Génère un script pour un article

### Scripts
- `GET /api/admin/scripts?status=...&page=...&limit=...`
- `GET /api/admin/scripts/[id]` - Récupère un script
- `POST /api/admin/scripts` - Crée un nouveau script
- `PUT /api/admin/scripts/[id]` - Met à jour un script
- `POST /api/admin/scripts/[id]/approve` - Approuve un script
- `POST /api/admin/scripts/[id]/publish` - Publie vers actualités
- `DELETE /api/admin/scripts/[id]` - Supprime un script

### Utilisateurs
- `GET /api/admin/users?plan=...&search=...&page=...&limit=...`

### Paramètres
- `GET /api/admin/settings` - Récupère les paramètres
- `PUT /api/admin/settings` - Met à jour les paramètres

### Authentification
- `GET /api/admin/auth/check` - Vérifie l'autorisation admin
- `POST /api/auth/logout` - Déconnecte l'utilisateur

## Installation

1. Tous les fichiers sont déjà créés dans la structure du projet
2. Assurez-vous que les dépendances sont installées:
   ```bash
   npm install lucide-react
   ```

3. Les composants et pages sont prêts à l'emploi

## Utilisation

### Importer les composants
```tsx
import { AdminSidebar, StatsCard, ViralityBadge } from '@/components/admin';
```

### Utiliser les hooks
```tsx
import { useAdminStats } from '@/hooks/useAdminStats';

function MyComponent() {
  const { stats, loading, error } = useAdminStats();
  // ...
}
```

## Notes

- Le sidebar est fixe avec `ml-64` pour le contenu principal
- Les pages utilisent `'use client'` car elles ont besoin d'interactivité
- Les modales de confirmation utilisent des états React simples
- Les formulaires n'utilisent pas de bibliothèque externe pour la validation
- Les images sont optimisées avec Next.js Image (si besoin)

## Future Enhancements

- Graphiques interactifs avec Chart.js ou Recharts
- Export de données (CSV, PDF)
- Logs d'actions administrateur
- Webhooks pour événements système
- Notifications en temps réel avec WebSocket
- Cache côté client avec SWR
