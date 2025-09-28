# Plan de Migration - Social Sync AI Design

## Objectif
Remplacer le design et l'architecture des pages existantes du frontend par celles du dossier `social-sync-ai/`, tout en conservant les fonctionnalités actuelles.

## Architecture Actuelle (Frontend)

### Structure des pages existantes :
- **Dashboard** : `/dashboard/page.tsx` - Vue d'ensemble avec métriques
- **Inbox** : `/dashboard/inbox/page.tsx` - Conversations unifiées
- **Social Accounts** : `/dashboard/social-accounts/page.tsx` - Gestion des comptes
- **Calendar** : `/dashboard/calendar/page.tsx` - Planification
- **Media** : `/dashboard/media/page.tsx` - Gestion des médias
- **AI Studio** : `/dashboard/ai-studio/` - Outils IA
  - Data : `/dashboard/ai-studio/data/page.tsx`
  - Prompt Tuning : `/dashboard/ai-studio/prompt-tuning/page.tsx`
  - QA Examples : `/dashboard/ai-studio/qa-examples/page.tsx`
- **Design** : `/dashboard/design/page.tsx` - Studio de design
- **Ads** : `/dashboard/ads/page.tsx` - Gestion des publicités

### Fonctionnalités à conserver :
1. **Authentification Supabase** avec Google OAuth
2. **Sidebar persistante** avec états expanded/collapsed
3. **Services API** existants (SocialAccounts, Conversations, Analytics)
4. **Protection des routes** avec AuthGuard
5. **Gestion d'état** avec Zustand
6. **Composants UI** shadcn/ui existants

## Nouvelles Pages à Intégrer (Social Sync AI)

### Pages identifiées :
1. **Playground** - Nouvelle page
2. **Activity** - Remplacement probable du Dashboard
3. **Chat** - Remplacement probable d'Inbox
4. **Data** - Remplacement probable d'AI Studio Data
5. **FAQ** - Nouvelle page
6. **Analytics** - Remplacement probable des métriques
7. **Connect AI** - Remplacement probable d'AI Studio
8. **Chat Interface** - Interface de chat améliorée
9. **Custom Domains** - Nouvelle fonctionnalité

## Stratégie de Migration

### Phase 1 : Exploration et Documentation
- [ ] Accéder au dossier social-sync-ai
- [ ] Lire la documentation dans social-sync-ai/docs
- [ ] Analyser chaque composant et page
- [ ] Identifier les correspondances avec l'architecture actuelle

### Phase 2 : Migration Page par Page
Pour chaque page :
1. Analyser la nouvelle structure
2. Identifier les fonctionnalités à conserver
3. Intégrer le nouveau design
4. Tester les fonctionnalités
5. Documenter les changements dans un fichier `*-modif.md`

### Phase 3 : Tests et Validation
- Vérifier que toutes les fonctionnalités sont conservées
- Tester l'authentification et les services API
- Valider la responsivité et l'accessibilité
- S'assurer que la sidebar fonctionne correctement

## Notes Importantes

### Conventions à Respecter :
- **Répondre en français** selon les règles utilisateur
- **Simplicité** : Éviter la sur-ingénierie
- **Types explicites** avec TypeScript
- **Noms descriptifs** pour variables/fonctions
- **Gestion d'erreurs** explicite
- **Pas de commentaires superflus**

### Architecture Technique :
- **Next.js 14** avec App Router
- **Tailwind v4** + shadcn/ui
- **Supabase** pour l'authentification
- **Zustand** pour l'état global
- **API services** pour les données backend

## Prochaines Étapes

1. **Attendre l'accès au dossier social-sync-ai**
2. **Lire la documentation complète**
3. **Commencer la migration page par page**
4. **Documenter chaque modification**

---

*Ce plan sera mis à jour au fur et à mesure de la progression de la migration.*