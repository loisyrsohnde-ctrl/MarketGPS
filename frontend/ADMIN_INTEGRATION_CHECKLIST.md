# Checklist d'Intégration - Admin Dashboard

Checklist pour intégrer complètement le dashboard admin avec votre backend.

## 1. Dépendances

- [ ] `lucide-react` est installé (`npm list lucide-react`)
  ```bash
  npm install lucide-react
  ```
- [ ] `next@13+` est disponible
- [ ] `tailwindcss` est configuré
- [ ] `typescript` est configuré

## 2. Structure de Dossiers

Vérifiez que tous les fichiers sont créés:

### Pages
- [ ] `/app/admin/layout.tsx`
- [ ] `/app/admin/page.tsx`
- [ ] `/app/admin/news/page.tsx`
- [ ] `/app/admin/scripts/page.tsx`
- [ ] `/app/admin/scripts/[id]/page.tsx`
- [ ] `/app/admin/users/page.tsx`
- [ ] `/app/admin/settings/page.tsx`

### Composants
- [ ] `/components/admin/AdminSidebar.tsx`
- [ ] `/components/admin/StatsCard.tsx`
- [ ] `/components/admin/ViralityBadge.tsx`
- [ ] `/components/admin/NewsTable.tsx`
- [ ] `/components/admin/ScriptEditor.tsx`
- [ ] `/components/admin/index.ts`

### Hooks
- [ ] `/hooks/useAdminStats.ts`
- [ ] `/hooks/useViralNews.ts`
- [ ] `/hooks/useVideoScripts.ts`

### Types
- [ ] `/types/admin.ts`

### Documentation
- [ ] `ADMIN_DASHBOARD_README.md`
- [ ] `ADMIN_API_EXAMPLES.md`
- [ ] `ADMIN_IMPLEMENTATION_SUMMARY.md`
- [ ] `ADMIN_INTEGRATION_CHECKLIST.md`

## 3. API Backend à Implémenter

### Authentication
- [ ] `GET /api/admin/auth/check`
  - Vérifie si l'utilisateur est un admin
  - Retour: `{ isAdmin: boolean, userId: string, email: string }`

- [ ] `POST /api/auth/logout`
  - Déconnecte l'utilisateur
  - Retour: `{ success: boolean }`

### Dashboard Stats
- [ ] `GET /api/admin/stats`
  - Retourne les statistiques du système
  - Voir exemple dans `ADMIN_API_EXAMPLES.md`

### Actualités Virales
- [ ] `GET /api/admin/news`
  - Query params: `region`, `language`, `minViralityScore`, `page`, `limit`
  - Retour: tableau d'articles avec pagination

- [ ] `POST /api/admin/scripts/generate`
  - Body: `{ articleId: string }`
  - Génère un script pour un article
  - Retour: `VideoScript`

### Scripts Vidéo
- [ ] `GET /api/admin/scripts`
  - Query params: `status`, `page`, `limit`
  - Retour: tableau de scripts avec pagination

- [ ] `GET /api/admin/scripts/[id]`
  - Retourne un script spécifique
  - Retour: `VideoScript`

- [ ] `POST /api/admin/scripts`
  - Body: `{ articleId, title, hook, scriptText }`
  - Crée un nouveau script
  - Retour: `VideoScript`

- [ ] `PUT /api/admin/scripts/[id]`
  - Body: `{ title?, hook?, scriptText? }`
  - Met à jour un script
  - Retour: `VideoScript`

- [ ] `POST /api/admin/scripts/[id]/approve`
  - Change le statut à "approved"
  - Retour: `VideoScript`

- [ ] `POST /api/admin/scripts/[id]/publish`
  - Publie vers les actualités
  - Change le statut à "published"
  - Retour: `VideoScript`

- [ ] `DELETE /api/admin/scripts/[id]`
  - Supprime un script
  - Retour: `204 No Content`

### Utilisateurs
- [ ] `GET /api/admin/users`
  - Query params: `plan`, `search`, `page`, `limit`
  - Retour: tableau d'utilisateurs avec pagination

### Paramètres
- [ ] `GET /api/admin/settings`
  - Retourne les paramètres système

- [ ] `PUT /api/admin/settings`
  - Body: `{ minViralityScore?, maxArticlesPerDay?, scriptGenerationModel?, notificationsEnabled?, maintenanceMode? }`
  - Met à jour les paramètres
  - Retour: paramètres mis à jour

## 4. Configuration Frontend

### Environnement
- [ ] Vérifier `next.config.js` supporta `/api/admin/*`
- [ ] Vérifier que les cors sont configurés si nécessaire
- [ ] Vérifier que l'authentification est partagée

### Middleware (optionnel)
- [ ] Créer un middleware pour vérifier l'authentification admin
- [ ] Ajouter logging des actions admin si nécessaire

### Styling
- [ ] Vérifier que Tailwind supporte les classes utilisées
- [ ] Vérifier le dark mode fonctionnel
- [ ] Tester les responsivités

## 5. Tests Manuels

### Pages
- [ ] Dashboard principal charge correctement
- [ ] Stats s'affichent avec les bonnes valeurs
- [ ] Filtres des actualités fonctionnent
- [ ] Pagination fonctionne
- [ ] Édition de script fonctionne
- [ ] Approbation et publication de script fonctionnent
- [ ] Suppression de script fonctionne (avec confirmation)
- [ ] Utilisateurs s'affichent correctement
- [ ] Paramètres se sauvegardent

### Navigation
- [ ] Sidebar affiche les bons liens
- [ ] Liens actifs sont mis en évidence
- [ ] Bouton déconnexion fonctionne
- [ ] Redirection login fonctionne si non-autorisé

### Dark Mode
- [ ] Les couleurs s'adaptent en dark mode
- [ ] Contrastes suffisants en dark mode
- [ ] Toggle dark mode fonctionne partout

### Responsive
- [ ] Layout s'adapte sur mobile (si possible)
- [ ] Tableaux scrollent horizontalement
- [ ] Modales se ferment correctement

## 6. Sécurité

- [ ] Authentification vérifiée à chaque requête API
- [ ] Autorisations admin vérifiées au backend
- [ ] CSRF tokens si nécessaire
- [ ] SQL injection prévenue (paramètres préparés)
- [ ] XSS prévenu (échappement HTML)
- [ ] Taux de limitation sur les endpoints API
- [ ] Logs des actions administrateur

## 7. Performance

- [ ] Lazy loading des pages (si besoin)
- [ ] Images optimisées avec Next.js Image
- [ ] Caching des stats (5 min)
- [ ] Pas de n+1 queries au backend
- [ ] Pagination efficace
- [ ] Temps de chargement < 2s pour les pages

## 8. Monitoring & Logs

- [ ] Logs des erreurs frontend
- [ ] Logs des actions admin au backend
- [ ] Monitoring des erreurs API
- [ ] Alertes pour les actions sensibles

## 9. Documentation

- [ ] Documentation README écrite
- [ ] Exemples API documentés
- [ ] Commentaires dans le code
- [ ] Types TypeScript documentés
- [ ] Guide d'intégration fourni

## 10. Déploiement

### Staging
- [ ] Déployer et tester en staging
- [ ] Vérifier l'authentification
- [ ] Vérifier les performances
- [ ] Vérifier les logs

### Production
- [ ] Vérifier les secrets/env vars
- [ ] Vérifier les permissions utilisateurs
- [ ] Vérifier les endpoints API
- [ ] Vérifier les logs
- [ ] Déployer et monitorer

## 11. Après Déploiement

- [ ] Vérifier que le dashboard est accessible
- [ ] Tester les principales fonctionnalités
- [ ] Vérifier les logs pour les erreurs
- [ ] Monitorer les performances
- [ ] Recueillir le feedback utilisateur

## Points d'Attention

### ⚠️ Critique
- [ ] Authentification obligatoire
- [ ] Vérifications des permissions au backend
- [ ] Validation des inputs
- [ ] Gestion des erreurs

### ⚠️ Important
- [ ] Performance des requêtes
- [ ] Caching stratégique
- [ ] Messages d'erreur explicites
- [ ] Logs des actions sensibles

### ⚠️ Nice to Have
- [ ] Graphiques avancés
- [ ] Export de données
- [ ] Webhooks
- [ ] Real-time updates

## Commandes Utiles

```bash
# Build
npm run build

# Dev
npm run dev

# Lint
npm run lint

# Test (si configuré)
npm test

# Type check
tsc --noEmit
```

## Troubleshooting

### Le dashboard ne charge pas
- [ ] Vérifier que `/api/admin/auth/check` fonctionne
- [ ] Vérifier l'authentification utilisateur
- [ ] Vérifier les logs du navigateur (F12)

### Les stats n'affichent pas
- [ ] Vérifier que `/api/admin/stats` existe
- [ ] Vérifier le format de la réponse
- [ ] Vérifier les logs du navigateur

### Les filtres ne fonctionnent pas
- [ ] Vérifier les query parameters
- [ ] Vérifier le backend traite les filtres
- [ ] Vérifier le format des données retournées

### Dark mode ne fonctionne pas
- [ ] Vérifier que `dark:` classes sont en place
- [ ] Vérifier la configuration Tailwind
- [ ] Vérifier le script de détection du dark mode

## Support

Pour des questions, consultez:
1. `ADMIN_DASHBOARD_README.md` - Documentation complète
2. `ADMIN_API_EXAMPLES.md` - Exemples API
3. `ADMIN_IMPLEMENTATION_SUMMARY.md` - Résumé technique
4. Code source avec commentaires

---

**Progress**: [ ] 0% - Complèter cette checklist pour une intégration réussie
