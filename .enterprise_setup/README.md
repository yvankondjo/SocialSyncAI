# Enterprise Migration Guide

Ce dossier contient tout le nécessaire pour migrer le code vers le nouveau repo enterprise.

## 📦 Contenu

- **MIGRATE_TO_ENTERPRISE.sh** - Script automatisé de migration
- **README_ENTERPRISE.md** - README pour le repo enterprise
- **DEPLOYMENT.md** - Guide de déploiement production
- **LICENSE** - Licence propriétaire

## 🚀 Utilisation

### Méthode 1: Script automatisé (Recommandé)

```bash
# Depuis la racine du projet
./.enterprise_setup/MIGRATE_TO_ENTERPRISE.sh
```

Le script va:
1. ✅ Vérifier les prérequis (git, gh CLI optionnel)
2. ✅ Vous demander votre username GitHub
3. ✅ Créer le nouveau repo (si gh CLI disponible)
4. ✅ Copier tout le code
5. ✅ Remplacer README, LICENSE, ajouter DEPLOYMENT.md
6. ✅ Créer un commit initial propre
7. ✅ Pousser vers GitHub

**Durée**: ~2 minutes

### Méthode 2: Manuel

Si vous préférez faire manuellement:

1. **Créer le repo sur GitHub:**
   - Aller sur https://github.com/new
   - Nom: `socialsync-ai-enterprise`
   - Visibilité: **Private**
   - Ne pas initialiser avec README/License

2. **Copier le code:**
```bash
cd ~/projects
git clone https://github.com/YOUR_USERNAME/socialsync-ai socialsync-ai-enterprise
cd socialsync-ai-enterprise
```

3. **Fresh start (recommandé):**
```bash
# Supprimer historique git
rm -rf .git

# Nouveau repo
git init
git branch -M main
```

4. **Appliquer customisations enterprise:**
```bash
# Depuis racine du repo enterprise
cp ../socialsync-ai/.enterprise_setup/README_ENTERPRISE.md ./README.md
cp ../socialsync-ai/.enterprise_setup/DEPLOYMENT.md ./DEPLOYMENT.md
cp ../socialsync-ai/.enterprise_setup/LICENSE ./LICENSE

# Remplacer YOUR_USERNAME dans README
sed -i 's/YOUR_USERNAME/votre-username/g' README.md
```

5. **Commit et push:**
```bash
git add .
git commit -m "Initial commit - Enterprise Edition"
git remote add origin https://github.com/YOUR_USERNAME/socialsync-ai-enterprise.git
git push -u origin main
```

## 📋 Checklist Post-Migration

### GitHub Settings

Aller sur: `https://github.com/YOUR_USERNAME/socialsync-ai-enterprise/settings`

**Général:**
- [ ] Description: "SocialSync AI - Enterprise SaaS Edition"
- [ ] Website: https://socialsync.ai
- [ ] Topics: `saas`, `social-media`, `ai`, `automation`, `stripe`

**Branches:**
- [ ] Branch protection sur `main`:
  - Require pull request reviews (2 approvals)
  - Require status checks to pass
  - Require conversation resolution
  - Do not allow force pushes
  - Restrict who can push

**Secrets:**

Ajouter dans Settings → Secrets and variables → Actions:

```
SUPABASE_URL_PROD=https://xxx.supabase.co
SUPABASE_SERVICE_KEY_PROD=eyJhbGc...
SUPABASE_ANON_KEY_PROD=eyJhbGc...
STRIPE_SECRET_KEY_LIVE=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
META_APP_SECRET=xxx
SENTRY_DSN=https://...
DOCKER_USERNAME=xxx
DOCKER_PASSWORD=xxx
```

**Collaborators:**
- [ ] Ajouter team members
- [ ] Définir permissions (Admin/Write/Read)

**Security:**
- [ ] Enable Dependabot alerts
- [ ] Enable secret scanning
- [ ] Enable code scanning (CodeQL)

### Documentation

- [ ] Mettre à jour README.md avec infos spécifiques
- [ ] Vérifier tous les liens
- [ ] Ajouter screenshots si possible
- [ ] Compléter DEPLOYMENT.md avec infrastructure réelle

### CI/CD

- [ ] Créer `.github/workflows/test.yml`
- [ ] Créer `.github/workflows/deploy.yml`
- [ ] Tester le pipeline

### Deployment

- [ ] Créer environnement de staging
- [ ] Déployer version de test
- [ ] Configurer monitoring (Sentry, Uptime)
- [ ] Tester intégration Stripe
- [ ] Vérifier webhooks

## ⚠️ Important

**Ce repo contient:**
- ✅ Intégration Stripe (paiements)
- ✅ Google Auth + Supabase
- ✅ Système de crédits avec limites
- ✅ Pages billing/pricing
- ✅ Subscription management

**NE PAS:**
- ❌ Rendre public par erreur
- ❌ Commit des secrets/clés API
- ❌ Partager le code source
- ❌ Utiliser clés de test en production

## 🔐 Licence

Le repo enterprise est sous **licence propriétaire**.
Voir [LICENSE](LICENSE) pour les détails.

## 📞 Support

Questions? Contact:
- Email: dev@socialsync.ai
- Slack: #enterprise-migration

---

**Prochaine étape:** Une fois l'enterprise créé, vous pourrez nettoyer le repo actuel pour l'open-source.
