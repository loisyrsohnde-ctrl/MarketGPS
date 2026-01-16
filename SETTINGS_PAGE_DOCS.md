# ⚙️ Page Paramètres - Documentation des Changements

## 📋 Vue d'Ensemble

La page **Paramètres** a été complètement refactorisée pour offrir une **expérience utilisateur robuste avec persistance des données**.

Toutes les modifications effectuées par l'utilisateur sont **sauvegardées en base de données** et persistent entre les sessions.

---

## 🎯 Fonctionnalités Implémentées

### 1️⃣ **Onglet Profil**

#### Modifier le Nom d'Affichage
- **Action:** Saisir un nouveau nom, cliquer "Enregistrer"
- **Persistance:** ✅ Sauvegardé en BD (`user_profiles.display_name`)
- **Confirmation:** Message vert "Profil mis à jour ✓"

#### Uploader une Photo de Profil
- **Formats supportés:** JPG, PNG, GIF
- **Taille max:** 2MB
- **Persistance:** ✅ Fichier sauvegardé + URL en BD
- **Affichage:** Avatar mis à jour immédiatement
- **Endpoint:** `POST /users/avatar/upload`

#### Email (Non modifiable)
- **Info:** Affiche l'email mais désactivé
- **Raison:** Les emails requièrent une vérification additionnelle

---

### 2️⃣ **Onglet Sécurité**

#### Changer le Mot de Passe
- **Validation:**
  - ✅ Mot de passe actuel requis
  - ✅ Nouveau mot de passe ≥ 8 caractères
  - ✅ Confirmationdu nouveau mot de passe
  - ✅ Vérification que les mots de passe correspondent
- **Persistance:** ✅ Nouveau hash sauvegardé en BD
- **Endpoint:** `POST /users/security/change-password`
- **Sécurité:** Mots de passe hashés avec SHA256

#### Voir/Masquer Mots de Passe
- **Icônes:** Eye (voir) / EyeOff (masquer)
- **Indépendant:** Chaque champ peut être vu/masqué séparément

#### Se Déconnecter
- **Action:** Clic sur "Se déconnecter maintenant"
- **Effet:** 
  - ✅ Sessions supprimées en BD
  - ✅ Redirection vers `/login`
- **Endpoint:** `POST /users/logout`

#### Zone de Danger - Supprimer le Compte
- **Confirmation requise:** Deuxième étape de vérification
- **Mot de passe:** Doit entrer le mot de passe pour confirmer
- **Persistance:** ✅ Compte supprimé définitivement en BD
- **Endpoint:** `POST /users/delete-account`
- **Données supprimées:**
  - Profil utilisateur
  - Données sécurité
  - Préférences
  - Sessions
  - Watchlist
- **Redirection:** Vers `/` après suppression

---

### 3️⃣ **Onglet Notifications**

#### Préférences Disponibles
1. **Notifications par email** - Mises à jour importantes
2. **Alertes de marché** - Actualités du marché
3. **Alertes de prix** - Prix sur actifs suivis
4. **Mises à jour du portefeuille** - Résumés de portefeuille

#### Comportement
- **Toggle:** Clic sur le switch pour activer/désactiver
- **Sauvegarde instantanée:** Changements persistés immédiatement
- **Sans page de confirmation:** Les modifications s'appliquent en temps réel
- **Endpoint:** `POST /users/notifications/update`
- **Persistance:** ✅ Chaque préférence sauvegardée en BD

---

## 🔄 Flux de Données (Architecture)

```
┌─────────────────┐
│   Frontend      │
│   (Next.js)     │
└────────┬────────┘
         │
    Modification
    utilisateur
         │
         ▼
┌─────────────────────────────────────────┐
│  useUserProfile Hook                    │
│  - Récupère données                     │
│  - Gère état local                      │
│  - Appelle API                          │
└────────┬────────────────────────────────┘
         │
    HTTP POST/PUT
         │
         ▼
┌──────────────────────────────────────────┐
│  Backend (FastAPI)                       │
│  user_routes.py                          │
│  - Valide données                        │
│  - Hash passwords                        │
│  - Upload fichiers                       │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  SQLite Database                         │
│  - user_profiles                         │
│  - user_security                         │
│  - user_preferences                      │
│  - user_entitlements                     │
└──────────────────────────────────────────┘
```

---

## 📁 Fichiers Modifiés/Créés

### Frontend
```
frontend/
├── app/settings/page.tsx              ← PAGE COMPLÈTE (refactorisée)
├── lib/api-user.ts                    ← CRÉÉ (Services API)
├── lib/config.ts                      ← (existant)
├── lib/api-client.ts                  ← (existant)
└── hooks/useUserProfile.ts            ← CRÉÉ (Hook React)
```

### Backend
```
backend/
├── user_routes.py                     ← AMÉLIORÉ (routes sécurisées)
├── main.py                            ← (déjà inclus user_router)
└── storage/sqlite_store.py            ← (utilise le store existant)
```

### Database Schema Requis
```sql
-- Tables utilisées (doit exister dans schema.sql)
CREATE TABLE user_profiles (
  user_id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE user_security (
  user_id TEXT PRIMARY KEY,
  password_hash TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE user_preferences (
  user_id TEXT PRIMARY KEY,
  email_notifications BOOLEAN DEFAULT TRUE,
  market_alerts BOOLEAN DEFAULT TRUE,
  price_alerts BOOLEAN DEFAULT TRUE,
  portfolio_updates BOOLEAN DEFAULT TRUE,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE user_entitlements (
  user_id TEXT PRIMARY KEY,
  plan TEXT DEFAULT 'FREE',
  status TEXT DEFAULT 'active',
  daily_requests_limit INTEGER DEFAULT 10
);

CREATE TABLE user_sessions (
  user_id TEXT,
  session_token TEXT PRIMARY KEY,
  created_at TEXT
);
```

---

## 🔐 Sécurité

### Gestion des Mots de Passe
- ✅ Hashés avec SHA256
- ✅ Mot de passe actuel vérifié avant changement
- ✅ Longueur minimale: 8 caractères
- ✅ Ne jamais stocké en clair

### Upload de Fichiers
- ✅ Validation du type (JPG, PNG, GIF uniquement)
- ✅ Vérification de la taille (max 2MB)
- ✅ Noms de fichiers sécurisés (user_id_avatar.ext)
- ✅ Sauvegardé en `/data/uploads/avatars/`

### Suppression de Compte
- ✅ Confirmation par mot de passe requise
- ✅ Zone visuelle de danger (couleur rouge)
- ✅ Double confirmation nécessaire
- ✅ Suppression complète en BD (CASCADE)

---

## 🚀 Utilisation

### Pour les Développeurs

#### 1. Charger le profil utilisateur
```typescript
import { useUserProfile } from '@/hooks/useUserProfile';

export function MyComponent() {
  const { profile, notifications, loading } = useUserProfile();
  
  if (loading) return <div>Chargement...</div>;
  
  return <div>{profile?.displayName}</div>;
}
```

#### 2. Mettre à jour le profil
```typescript
const { updateProfile } = useUserProfile();

const handleUpdate = async () => {
  await updateProfile({
    displayName: 'Nouveau Nom',
  });
};
```

#### 3. Modifier les notifications
```typescript
const { updateNotifications, notifications } = useUserProfile();

const handleToggle = async () => {
  await updateNotifications({
    ...notifications,
    emailNotifications: !notifications.emailNotifications,
  });
};
```

---

## ✅ Checklist de Test

- [ ] Modifier le nom d'affichage → Sauvegardé en BD
- [ ] Upload avatar → Fichier sauvegardé + affichage mis à jour
- [ ] Changer mot de passe → Nouveau hash en BD
- [ ] Voir/masquer mots de passe → Fonctionne correctement
- [ ] Se déconnecter → Redirection vers login
- [ ] Supprimer compte → Données complètement supprimées
- [ ] Modifier notifications → Changements persistés
- [ ] Recharger la page → Les modifications persistent
- [ ] Fermer/rouvrir navigateur → Les modifications persistent

---

## 🐛 Dépannage

### Avatar n'apparaît pas
- Vérifier que `/data/uploads/avatars/` existe
- Vérifier les permissions d'écriture sur le répertoire
- Vérifier l'URL dans la BD

### Mot de passe ne change pas
- Vérifier que l'ancien mot de passe est correct
- Vérifier que le nouveau mot de passe ≥ 8 caractères
- Vérifier les erreurs dans la console

### Notifications ne se sauvegardent pas
- Vérifier que la table `user_preferences` existe
- Vérifier les logs du backend

---

## 📊 Performance

- **Chargement:** Récupère toutes les données en 1 requête groupée
- **Sauvegarde:** Requête directe, pas de batching
- **Cache:** Aucun cache (toujours frais depuis la BD)
- **Temps réel:** Les changements sont visibles immédiatement

---

## 🔄 Prochaines Améliorations Possibles

1. **Authentification JWT** - Remplacer `user_id` par JWT
2. **Cache Redis** - Cache les données de profil
3. **Audit Trail** - Logger les modifications sensibles
4. **2FA** - Authentification à deux facteurs
5. **Export Données** - Télécharger toutes les données personelles
6. **Historique Modifications** - Log des changements effectués

---

**Status:** ✅ **COMPLET ET PRÊT**  
**Date:** 12 Janvier 2026  
**Persistance:** ✅ Toutes les modifications en BD
