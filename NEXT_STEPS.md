# 🎯 PROCHAINES ÉTAPES - MIGRATION ENTERPRISE

Votre repo a été nettoyé et tout est prêt pour la migration! Voici le plan d'action:

---

## ✅ TERMINÉ

- [x] Nettoyage du repo (~120 fichiers temporaires supprimés)
- [x] Commit des suppressions
- [x] Création des fichiers enterprise (README, LICENSE, DEPLOYMENT.md)
- [x] Script de migration automatisé créé

---

## 🚀 ÉTAPE 1: CRÉER LE REPO ENTERPRISE (5 minutes)

### Option A: Script automatisé (Recommandé)

```bash
# Depuis la racine du projet (là où vous êtes maintenant)
./.enterprise_setup/MIGRATE_TO_ENTERPRISE.sh
```

Le script va tout faire automatiquement:
- Créer le nouveau repo sur GitHub (si gh CLI installé)
- Copier le code
- Appliquer les customisations enterprise
- Créer un commit propre
- Pousser vers GitHub

### Option B: Manuel

Si vous préférez faire à la main, consultez:
```bash
cat .enterprise_setup/README.md
```

---

## 📦 CONTENU DU DOSSIER .enterprise_setup/

Tous les fichiers sont prêts dans ce dossier:

```
.enterprise_setup/
├── README.md                    # Guide d'utilisation
├── MIGRATE_TO_ENTERPRISE.sh     # Script automatisé ⭐
├── README_ENTERPRISE.md         # README pour repo enterprise
├── DEPLOYMENT.md                # Guide déploiement
└── LICENSE                      # Licence propriétaire
```

---

## 🔐 APRÈS LA MIGRATION ENTERPRISE

Une fois le repo enterprise créé sur GitHub, configurez:

### 1. Branch Protection
Settings → Branches → Add rule sur `main`:
- ✅ Require 2 PR reviews
- ✅ Require status checks
- ✅ Restrict force push

### 2. Secrets GitHub
Settings → Secrets → New repository secret:

**Production:**
- `SUPABASE_URL_PROD`
- `SUPABASE_SERVICE_KEY_PROD`
- `STRIPE_SECRET_KEY_LIVE`
- `STRIPE_WEBHOOK_SECRET`
- `META_APP_SECRET`

**CI/CD:**
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

### 3. Collaborators
Settings → Collaborators → Add people

### 4. Security
Settings → Security:
- ✅ Enable Dependabot
- ✅ Enable secret scanning
- ✅ Enable CodeQL

---

## 🔓 ÉTAPE 2: NETTOYER CE REPO POUR OPEN-SOURCE

**Une fois le repo enterprise créé et vérifié**, on pourra nettoyer ce repo actuel pour la version open-source.

Ça impliquera:

### À supprimer:
- ❌ `backend/app/routers/stripe.py`
- ❌ `backend/app/services/stripe_service.py`
- ❌ `backend/app/routers/subscriptions.py` (garder juste `/models`)
- ❌ `frontend/app/pricing/`
- ❌ `frontend/app/dashboard/settings/billing/`
- ❌ Google Auth (remplacer par API key)

### À modifier:
- 📝 `backend/app/core/security.py` - Auth par API key
- 📝 `backend/app/services/credits_service.py` - Crédits illimités
- 📝 `frontend/components/sidebar-new.tsx` - Retirer "Billing"
- 📝 `frontend/components/user-credits-indicator.tsx` - Afficher "Unlimited"

### À ajouter:
- ✅ Licence AGPL v3
- ✅ README open-source
- ✅ Script `seed_demo_user.py` (créer users sans auth)
- ✅ Documentation self-hosting
- ✅ `start.sh` - Démarrage en une commande

---

## 📊 RÉSUMÉ DES 2 REPOS

```
┌─────────────────────────────────────┐
│  REPO ACTUEL                        │
│  socialsync-ai                      │
│                                     │
│  État: Nettoyé, prêt pour migration│
│  Contient: Code complet avec Stripe│
└─────────────┬───────────────────────┘
              │
              │ MIGRATION
              ▼
┌─────────────────────────────────────┐
│  NOUVEAU REPO                       │
│  socialsync-ai-enterprise          │
│                                     │
│  🔐 PRIVÉ                           │
│  ✅ Stripe + paiements             │
│  ✅ Google Auth                     │
│  ✅ Crédits limités                │
│  ✅ Pages billing                   │
│  © Propriétaire                     │
└─────────────────────────────────────┘

              │ APRÈS
              ▼
┌─────────────────────────────────────┐
│  REPO ACTUEL (nettoyé)             │
│  socialsync-ai                      │
│                                     │
│  🔓 PUBLIC                          │
│  ❌ Pas de Stripe                   │
│  ✅ API Key auth                    │
│  ✅ Crédits illimités               │
│  ❌ Pas de billing                  │
│  📜 AGPL v3                         │
└─────────────────────────────────────┘
```

---

## ⏱️ TIMELINE

| Étape | Durée | Action |
|-------|-------|--------|
| 1 | 5 min | Exécuter script de migration enterprise |
| 2 | 10 min | Configurer repo GitHub (settings, secrets) |
| 3 | 5 min | Vérifier que tout est OK |
| 4 | 2-3h | Nettoyer repo actuel pour open-source |
| **TOTAL** | **~3h** | Migration complète |

---

## 🎬 ACTIONS IMMÉDIATES

**Prêt à commencer?**

1. **Vérifiez votre environnement:**
```bash
git --version  # Git installé?
gh --version   # GitHub CLI installé? (optionnel)
```

2. **Lancez la migration:**
```bash
./.enterprise_setup/MIGRATE_TO_ENTERPRISE.sh
```

3. **Suivez les instructions** affichées par le script

---

## 📞 BESOIN D'AIDE?

Si vous avez des questions ou rencontrez des problèmes:

1. **Consultez la doc:**
   ```bash
   cat .enterprise_setup/README.md
   ```

2. **Vérifiez l'état:**
   ```bash
   git status
   git log --oneline -5
   ```

3. **Testez localement** avant de pousser:
   ```bash
   docker-compose up -d
   ```

---

## ✅ CHECKLIST FINALE

Avant de lancer la migration, vérifiez:

- [ ] Vous avez un compte GitHub
- [ ] Vous êtes prêt à créer un repo privé
- [ ] Vous avez lu `.enterprise_setup/README.md`
- [ ] Vous comprenez la différence enterprise vs open-source
- [ ] Le repo actuel est clean (`git status`)

**Tout est OK? Alors lancez:**
```bash
./.enterprise_setup/MIGRATE_TO_ENTERPRISE.sh
```

---

Bonne migration! 🚀🚀🚀
