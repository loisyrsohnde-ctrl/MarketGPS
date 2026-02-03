# Admin Dashboard API Examples

Exemples de réponses pour les endpoints API requis par le dashboard admin.

## Stats Endpoint

### GET /api/admin/stats

Récupère les statistiques du dashboard principal.

**Réponse (200)**:
```json
{
  "users": {
    "total": 1250,
    "pro": 450,
    "free": 800,
    "newToday": 15,
    "newThisWeek": 89
  },
  "news": {
    "scrapedToday": 342,
    "viralCount": 28,
    "scriptsGenerated": 12
  },
  "system": {
    "lastPipelineRun": "2026-02-03T10:45:00Z",
    "sourcesActive": 24
  }
}
```

---

## News Endpoints

### GET /api/admin/news

Récupère les actualités virales avec support de filtres et pagination.

**Query Parameters**:
- `region` (optional): "FR", "US", "EU", "ASIA"
- `language` (optional): "fr", "en", "de", "es"
- `minViralityScore` (optional): nombre min de viralité
- `page` (optional): numéro de page (défaut: 1)
- `limit` (optional): nombre de résultats (défaut: 20)

**Réponse (200)**:
```json
{
  "articles": [
    {
      "id": "article-001",
      "title": "Nouvelle stratégie de trading révolutionne le marché",
      "source": "Bloomberg",
      "region": "FR",
      "language": "fr",
      "interactions": 5230,
      "viralityScore": 8.5,
      "publishedAt": "2026-02-03T09:30:00Z",
      "hasScript": false,
      "url": "https://example.com/article/001"
    },
    {
      "id": "article-002",
      "title": "Les crypto-monnaies rebondissent fortement",
      "source": "Reuters",
      "region": "US",
      "language": "en",
      "interactions": 12450,
      "viralityScore": 12.3,
      "publishedAt": "2026-02-03T08:15:00Z",
      "hasScript": true,
      "url": "https://example.com/article/002"
    }
  ],
  "total": 128,
  "page": 1,
  "limit": 20,
  "pages": 7
}
```

### POST /api/admin/scripts/generate

Génère un script vidéo pour un article donné.

**Body**:
```json
{
  "articleId": "article-001"
}
```

**Réponse (201)**:
```json
{
  "id": "script-001",
  "articleId": "article-001",
  "title": "Stratégie de Trading pour Débutants",
  "hook": "Découvrez la stratégie qui fait gagner les traders professionnels...",
  "scriptText": "Bonjour à tous! Vous avez entendu parler de cette nouvelle stratégie...",
  "wordCount": 1240,
  "estimatedDuration": 8,
  "status": "draft",
  "createdAt": "2026-02-03T11:00:00Z",
  "updatedAt": "2026-02-03T11:00:00Z",
  "articleTitle": "Nouvelle stratégie de trading révolutionne le marché"
}
```

---

## Scripts Endpoints

### GET /api/admin/scripts

Récupère les scripts vidéo avec filtres et pagination.

**Query Parameters**:
- `status` (optional): "draft", "reviewed", "approved", "published"
- `page` (optional): numéro de page (défaut: 1)
- `limit` (optional): nombre de résultats (défaut: 20)

**Réponse (200)**:
```json
{
  "scripts": [
    {
      "id": "script-001",
      "articleId": "article-001",
      "title": "Stratégie de Trading pour Débutants",
      "hook": "Découvrez la stratégie qui fait gagner les traders...",
      "scriptText": "Bonjour à tous!...",
      "wordCount": 1240,
      "estimatedDuration": 8,
      "status": "draft",
      "createdAt": "2026-02-03T11:00:00Z",
      "updatedAt": "2026-02-03T11:00:00Z",
      "articleTitle": "Nouvelle stratégie de trading..."
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

### GET /api/admin/scripts/[id]

Récupère un script spécifique.

**Réponse (200)**:
```json
{
  "id": "script-001",
  "articleId": "article-001",
  "title": "Stratégie de Trading pour Débutants",
  "hook": "Découvrez la stratégie qui fait gagner les traders...",
  "scriptText": "Bonjour à tous!...",
  "wordCount": 1240,
  "estimatedDuration": 8,
  "status": "draft",
  "createdAt": "2026-02-03T11:00:00Z",
  "updatedAt": "2026-02-03T11:00:00Z",
  "articleTitle": "Nouvelle stratégie de trading..."
}
```

### POST /api/admin/scripts

Crée un nouveau script.

**Body**:
```json
{
  "articleId": "article-001",
  "title": "Mon Script",
  "hook": "L'accroche...",
  "scriptText": "Le contenu du script..."
}
```

**Réponse (201)**:
```json
{
  "id": "script-new-001",
  "articleId": "article-001",
  "title": "Mon Script",
  "hook": "L'accroche...",
  "scriptText": "Le contenu du script...",
  "wordCount": 450,
  "estimatedDuration": 3,
  "status": "draft",
  "createdAt": "2026-02-03T12:00:00Z",
  "updatedAt": "2026-02-03T12:00:00Z",
  "articleTitle": "Nouvelle stratégie de trading..."
}
```

### PUT /api/admin/scripts/[id]

Met à jour un script.

**Body** (tous les champs optionnels):
```json
{
  "title": "Nouveau Titre",
  "hook": "Nouvelle accroche",
  "scriptText": "Nouveau contenu..."
}
```

**Réponse (200)**:
```json
{
  "id": "script-001",
  "articleId": "article-001",
  "title": "Nouveau Titre",
  "hook": "Nouvelle accroche",
  "scriptText": "Nouveau contenu...",
  "wordCount": 1250,
  "estimatedDuration": 8,
  "status": "draft",
  "createdAt": "2026-02-03T11:00:00Z",
  "updatedAt": "2026-02-03T13:30:00Z",
  "articleTitle": "Nouvelle stratégie de trading..."
}
```

### POST /api/admin/scripts/[id]/approve

Approuve un script (change le statut à "approved").

**Réponse (200)**:
```json
{
  "id": "script-001",
  "articleId": "article-001",
  "title": "Stratégie de Trading pour Débutants",
  "hook": "Découvrez la stratégie...",
  "scriptText": "Bonjour à tous!...",
  "wordCount": 1240,
  "estimatedDuration": 8,
  "status": "approved",
  "createdAt": "2026-02-03T11:00:00Z",
  "updatedAt": "2026-02-03T14:00:00Z",
  "articleTitle": "Nouvelle stratégie de trading..."
}
```

### POST /api/admin/scripts/[id]/publish

Publie un script vers les actualités (change le statut à "published").

**Réponse (200)**:
```json
{
  "id": "script-001",
  "articleId": "article-001",
  "title": "Stratégie de Trading pour Débutants",
  "hook": "Découvrez la stratégie...",
  "scriptText": "Bonjour à tous!...",
  "wordCount": 1240,
  "estimatedDuration": 8,
  "status": "published",
  "createdAt": "2026-02-03T11:00:00Z",
  "updatedAt": "2026-02-03T14:05:00Z",
  "articleTitle": "Nouvelle stratégie de trading...",
  "publishedUrl": "https://marketgps.com/news/script-001"
}
```

### DELETE /api/admin/scripts/[id]

Supprime un script.

**Réponse (204)**: Pas de contenu

---

## Users Endpoints

### GET /api/admin/users

Récupère les utilisateurs avec filtres et pagination.

**Query Parameters**:
- `plan` (optional): "free", "pro", "enterprise"
- `search` (optional): recherche par email ou nom
- `page` (optional): numéro de page (défaut: 1)
- `limit` (optional): nombre de résultats (défaut: 20)

**Réponse (200)**:
```json
{
  "users": [
    {
      "id": "user-001",
      "email": "trader@example.com",
      "name": "Jean Dupont",
      "plan": "pro",
      "createdAt": "2025-10-15T08:30:00Z",
      "lastLogin": "2026-02-03T09:00:00Z",
      "isActive": true
    },
    {
      "id": "user-002",
      "email": "investor@example.com",
      "name": "Marie Martin",
      "plan": "free",
      "createdAt": "2026-01-20T10:15:00Z",
      "lastLogin": "2026-02-01T14:30:00Z",
      "isActive": true
    }
  ],
  "total": 1250,
  "page": 1,
  "limit": 20,
  "pages": 63
}
```

---

## Settings Endpoints

### GET /api/admin/settings

Récupère les paramètres du système.

**Réponse (200)**:
```json
{
  "minViralityScore": 2,
  "maxArticlesPerDay": 1000,
  "scriptGenerationModel": "gpt-4",
  "notificationsEnabled": true,
  "maintenanceMode": false
}
```

### PUT /api/admin/settings

Met à jour les paramètres du système.

**Body** (tous les champs optionnels):
```json
{
  "minViralityScore": 2.5,
  "maxArticlesPerDay": 500,
  "scriptGenerationModel": "gpt-3.5-turbo",
  "notificationsEnabled": true,
  "maintenanceMode": false
}
```

**Réponse (200)**:
```json
{
  "minViralityScore": 2.5,
  "maxArticlesPerDay": 500,
  "scriptGenerationModel": "gpt-3.5-turbo",
  "notificationsEnabled": true,
  "maintenanceMode": false,
  "updatedAt": "2026-02-03T14:15:00Z"
}
```

---

## Authentication Endpoints

### GET /api/admin/auth/check

Vérifie si l'utilisateur est authentifié et autorisé admin.

**Réponse (200)**:
```json
{
  "isAdmin": true,
  "userId": "user-admin-001",
  "email": "admin@marketgps.com"
}
```

**Réponse (401)**: Non authentifié ou pas admin

### POST /api/auth/logout

Déconnecte l'utilisateur.

**Réponse (200)**:
```json
{
  "success": true
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid parameters",
  "details": "region must be one of: FR, US, EU, ASIA"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "You must be logged in as an admin"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "resource": "Script with ID script-invalid not found"
}
```

### 500 Server Error
```json
{
  "error": "Server error",
  "message": "An unexpected error occurred",
  "requestId": "req-12345"
}
```

---

## Notes

- Les timestamps sont en ISO 8601 (UTC)
- Les IDs sont des chaînes alphanumériques uniques
- La pagination est basée sur des pages (pas un curseur)
- Les scores de viralité sont des nombres décimaux (ex: 8.5)
- Les durées estimées sont en minutes
- Les compteurs de mots sont en nombres entiers
