# Transformation Open-Source - SocialSync AI

**Date**: 2025-10-29
**Version**: 3.0 (Open-Source Edition)
**Licence**: AGPL v3.0

## Vue d'ensemble

SocialSync AI a été transformé d'une application SaaS commerciale en une **plateforme open-source complète** sous licence AGPL v3. Cette transformation élimine toutes les barrières commerciales tout en conservant 100% des fonctionnalités d'automatisation IA.

## Changements Majeurs

### 🗑️ Fonctionnalités Supprimées

#### 1. Intégration de Paiement (Stripe)
**Fichiers supprimés:**
- `backend/app/routers/stripe.py` - Endpoints Stripe (webhooks, checkout)
- `backend/app/routers/subscriptions.py` - Gestion des abonnements
- `backend/app/services/stripe_service.py` - Logique métier Stripe (986 lignes)
- `backend/app/schemas/stripe_models.py` - Modèles Pydantic Stripe
- `backend/app/schemas/subscription.py` - Modèles d'abonnement complets

**Impact:**
- Plus de webhooks Stripe à gérer
- Plus de logique de checkout/billing
- Plus de gestion d'abonnements
- Simplification du code backend (-4665 lignes)

#### 2. Pages de Facturation (Frontend)
**Dossiers supprimés:**
- `frontend/app/pricing/page.tsx` - Page de tarification publique
- `frontend/app/dashboard/settings/billing/` - Interface de gestion billing

**Impact:**
- Navigation simplifiée dans le dashboard
- Plus de références aux plans/pricing
- UX plus directe et claire

#### 3. OAuth Google
**Modifications:**
- `frontend/app/auth/page.tsx` - Remplacé OAuth Google par email/password
- Suppression de `signInWithOAuth()` Supabase
- Formulaire de connexion standard avec Input email + password

**Avant:**
```tsx
const handleGoogleSignIn = async () => {
  await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: `${window.location.origin}/auth/callback` }
  })
}
```

**Après:**
```tsx
const handleEmailSignIn = async (e: React.FormEvent) => {
  await supabase.auth.signInWithPassword({ email, password })
}
```

### ♾️ Système de Crédits Illimité

#### Modification de `credits_service.py`

**Fichier**: `backend/app/services/credits_service.py`

**Changements:**
- Réduit de 613 lignes à 180 lignes (-70%)
- Toutes les méthodes retournent `True` ou valeurs illimitées
- Pas de vérification de quotas
- Pas de déduction de crédits

**Méthodes principales:**

```python
async def check_credits_available(self, user_id: str, cost: float, operation: str = "unknown") -> bool:
    """VERSION OPEN-SOURCE: Retourne toujours True (crédits illimités)"""
    logger.info(f"[OPEN-SOURCE] Credits check for user {user_id}: {cost} credits for {operation} - UNLIMITED MODE")
    return True

async def deduct_credits(self, user_id: str, amount: float, operation: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """VERSION OPEN-SOURCE: Ne fait rien, retourne simplement un résultat simulé"""
    return {
        "success": True,
        "user_id": user_id,
        "amount": amount,
        "operation": operation,
        "remaining_balance": float('inf'),  # Infini
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "unlimited"
    }

async def get_feature_access(self, user_id: str, feature: str) -> bool:
    """VERSION OPEN-SOURCE: Tous les utilisateurs ont accès à toutes les fonctionnalités"""
    return True
```

**Impact sur l'application:**
- Aucune limite d'utilisation IA
- Aucune limite de stockage
- Aucune restriction de fonctionnalités
- Tous les utilisateurs sont "premium"

#### Schéma Simplifié

**Fichier**: `backend/app/schemas/subscription.py`

```python
class StorageUsage(BaseModel):
    """Modèle pour l'utilisation du stockage"""
    used_mb: float = 0.0
    quota_mb: float = float('inf')  # Illimité en open-source
    percentage: float = 0.0

class StorageQuotaExceededError(Exception):
    """
    NOTE: En version open-source, cette exception ne devrait jamais être levée
    car le stockage est illimité.
    """
    pass
```

### 📚 Nouvelle Documentation & Tooling

#### 1. README.md Open-Source

**Fichier**: `/workspace/README.md`

**Contenu:**
- Badge AGPL v3
- Guide d'installation avec Docker
- Configuration Supabase complète
- Stack technique détaillé
- Roadmap publique
- Section contribution
- Explication licence AGPL

**Structure:**
```markdown
# 🤖 SocialSync AI - Open Source Edition

## ✨ Fonctionnalités
- Automation IA
- Gestion des Conversations
- Commentaires Instagram
- Base de Connaissances (RAG)
- Planification de Posts
- AI Studio
- Analytics

## 🚀 Démarrage Rapide
1. Clonez le repo
2. Configurez les variables d'environnement
3. Lancez avec Docker Compose
4. Créez votre premier utilisateur
5. Accédez à l'application

## 🛠️ Stack Technique
- Backend: FastAPI, Python 3.10+, Celery, Redis
- Frontend: Next.js 14, TypeScript, Tailwind, shadcn/ui
- IA & ML: LangChain, OpenRouter, BERTopic, ChromaDB
- Infrastructure: Docker, PostgreSQL, Supabase

## 📝 Licence
AGPL v3.0 - Toute modification doit être partagée
```

#### 2. Guide de Seeding (SEEDING.md)

**Fichier**: `/workspace/SEEDING.md`

**Contenu complet:**
- Configuration Supabase (URL, service key)
- Guide étape par étape
- Script `seed_users.py` - Créer utilisateurs de test
- Script `seed_social_accounts.py` - Créer comptes sociaux fictifs
- Personnalisation des données
- Utilisation avec vrais comptes (OAuth flow)
- Dépannage complet
- Sécurité (ne jamais commit les clés)
- Commandes de nettoyage

**Exemple d'utilisation:**
```bash
# 1. Configuration
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# 2. Créer des utilisateurs
python scripts/seed_users.py
# Output: demo@socialsync.ai / Demo123456!

# 3. Créer des comptes sociaux
python scripts/seed_social_accounts.py
# Output: Instagram test account + WhatsApp test account
```

#### 3. Scripts de Seed

##### Script 1: `scripts/seed_users.py`

**Fonctionnalités:**
- Connexion Supabase avec service key
- Création utilisateurs via `admin.create_user()`
- Configuration métadonnées (full_name, username)
- Confirmation email automatique
- Création enregistrement `user_credits` (999999 crédits)
- Affichage credentials de connexion

**Users par défaut:**
```python
TEST_USERS = [
    {
        "email": "demo@socialsync.ai",
        "password": "Demo123456!",
        "full_name": "Demo User",
        "username": "demo_user"
    },
    {
        "email": "test@socialsync.ai",
        "password": "Test123456!",
        "full_name": "Test User",
        "username": "test_user"
    }
]
```

##### Script 2: `scripts/seed_social_accounts.py`

**Fonctionnalités:**
- Demande email utilisateur (interactif)
- Récupération user_id depuis Supabase Auth
- Création comptes sociaux fictifs
- Tokens marqués comme `is_test_account: true`

**Comptes par défaut:**
```python
TEST_SOCIAL_ACCOUNTS = [
    {
        "platform": "instagram",
        "platform_user_id": "17841400000000001",  # ID fictif
        "username": "demo_instagram",
        "access_token": "FAKE_IG_TOKEN_FOR_TESTING_DO_NOT_USE_IN_PRODUCTION"
    },
    {
        "platform": "whatsapp",
        "platform_user_id": "102200000000001",  # ID fictif
        "username": "+1234567890",
        "access_token": "FAKE_WA_TOKEN_FOR_TESTING_DO_NOT_USE_IN_PRODUCTION"
    }
]
```

**Note importante:**
Les tokens fictifs ne fonctionnent pas avec les vraies APIs. Pour utiliser de vrais comptes, connectez-les via le dashboard (OAuth flow normal).

#### 4. Licence AGPL v3

**Fichier**: `/workspace/LICENSE`

**Points clés de l'AGPL v3:**

1. **Disponibilité du Code Source (Section 13)**
   - Si vous hébergez une version modifiée, vous DEVEZ fournir le code source
   - Les utilisateurs qui interagissent avec votre serveur doivent pouvoir accéder au code
   - Pas de "tivoization" - pas de restrictions techniques sur les modifications

2. **Copyleft Fort**
   - Toute modification doit être sous AGPL v3
   - Pas de "dual licensing" possible
   - Force le partage des améliorations

3. **Utilisation Commerciale**
   - ✅ Vous pouvez utiliser commercialement
   - ✅ Vous pouvez héberger et facturer
   - ⚠️ Vous devez partager votre code si vous modifiez
   - ⚠️ Vos clients peuvent redistribuer gratuitement

4. **Différence vs GPL**
   - GPL: obligation de partager seulement si vous distribuez
   - AGPL: obligation de partager même si vous hébergez seulement (SaaS)

**Pourquoi AGPL ?**
- Garantit que SocialSync AI reste open-source forever
- Empêche les forks propriétaires fermés
- Force les contributions back à la communauté
- Protège contre l'appropriation par les géants tech

## Architecture Post-Transformation

### Backend Simplifié

**Routers restants:**
```python
# backend/app/main.py
app.include_router(social_accounts.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(instagram.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(automation.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(knowledge_documents.router, prefix="/api")
app.include_router(faq_qa.router, prefix="/api")
app.include_router(ai_settings.router, prefix="/api")
app.include_router(media.router, prefix="/api")
# Plus de subscriptions.router ni stripe.router
app.include_router(support.router, prefix="/api")
app.include_router(scheduled_posts.router, prefix="/api")
app.include_router(ai_rules.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(ai_studio.router, prefix="/api")
app.include_router(instagram_profiles.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
```

**Services simplifiés:**
- `credits_service.py` - Mode illimité (180 lignes vs 613)
- Plus de `stripe_service.py`
- Schemas subscription minimalistes

### Frontend Simplifié

**Pages restantes:**
```
frontend/app/
├── auth/
│   ├── page.tsx           # Email/Password login (modifié)
│   └── callback/
│       └── page.tsx       # Auth callback
├── dashboard/
│   ├── page.tsx           # Dashboard principal
│   ├── conversations/     # Inbox
│   ├── knowledge-base/    # RAG documents
│   ├── scheduled-posts/   # Planification
│   ├── ai-studio/         # Content creation
│   ├── monitoring/        # Comment monitoring
│   ├── analytics/         # Stats & KPIs
│   └── settings/
│       ├── ai-settings/   # Config IA
│       ├── accounts/      # Comptes sociaux
│       └── profile/       # Profil user
│       # Plus de billing/
└── # Plus de pricing/
```

## Migration Enterprise → Open-Source

### Étapes Réalisées

1. ✅ **Préservation Enterprise**
   - Repo privé créé : `socialsync-ai-enterprise`
   - Toutes les features commerciales préservées
   - Toolkit de migration dans `.enterprise_setup/`

2. ✅ **Nettoyage Stripe**
   - Suppression de 5 fichiers backend Stripe
   - Suppression de 2 pages frontend billing
   - Nettoyage imports et dépendances

3. ✅ **Crédits Illimités**
   - Réécriture `credits_service.py` (-70% code)
   - Toutes les checks retournent `True`
   - Balance toujours `float('inf')`

4. ✅ **Auth Simplifiée**
   - Page login redessinée (email/password)
   - Suppression OAuth Google
   - Instructions seed dans l'UI

5. ✅ **Documentation Complète**
   - README.md open-source (272 lignes)
   - SEEDING.md guide complet (220 lignes)
   - Scripts Python documentés

6. ✅ **Licence AGPL v3**
   - Fichier LICENSE ajouté
   - Badges dans README
   - Explication copyleft

7. ✅ **Commit Git Propre**
   - Message descriptif complet
   - 19 fichiers modifiés
   - +1083 / -4665 lignes

### Statistiques

```
Files changed: 19
Insertions: 1,083
Deletions: 4,665
Net reduction: -3,582 lignes

Suppressions:
- .enterprise_setup/ (5 fichiers)
- Stripe integration (4 fichiers backend)
- Billing/pricing pages (2 dossiers frontend)
- NEXT_STEPS.md

Ajouts:
- LICENSE (AGPL v3)
- SEEDING.md (guide complet)
- scripts/seed_users.py
- scripts/seed_social_accounts.py
- README.md (open-source edition)

Modifications:
- backend/app/services/credits_service.py (-70% code)
- backend/app/schemas/subscription.py (minimal)
- backend/app/main.py (cleanup imports)
- frontend/app/auth/page.tsx (email/password)
```

## Démarrage Rapide Open-Source

### Prérequis

1. **Docker & Docker Compose**
2. **Compte Supabase** (gratuit)
3. **Clés API**:
   - OpenRouter ou OpenAI (LLM)
   - Meta Developer (Instagram/WhatsApp)
   - Google Gemini (optionnel, embeddings)

### Installation (5 étapes)

```bash
# 1. Clone
git clone https://github.com/votre-username/socialsync-ai.git
cd socialsync-ai

# 2. Configuration
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Éditez avec vos clés

# 3. Lancement
docker-compose up -d

# 4. Seed users
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
python scripts/seed_users.py

# 5. Connexion
# http://localhost:3000
# Email: demo@socialsync.ai
# Password: Demo123456!
```

### Premiers pas

1. **Dashboard** - Voir l'interface
2. **Paramètres > Comptes Sociaux** - Connecter Instagram/WhatsApp
3. **Base de Connaissances** - Uploader des FAQs
4. **Conversations** - Tester les réponses IA
5. **Monitoring** - Activer les auto-replies commentaires

## Différences Enterprise vs Open-Source

| Feature | Enterprise | Open-Source |
|---------|-----------|-------------|
| **Prix** | Abonnement Stripe | Gratuit |
| **Crédits** | Limités par plan | Illimités ∞ |
| **Auth** | Google OAuth + Email | Email/Password only |
| **Billing** | Pages pricing/billing | Aucune |
| **Stripe** | Webhooks, checkout | Supprimé |
| **Support** | Email premium | Community GitHub |
| **Licence** | Propriétaire | AGPL v3 |
| **Code Source** | Privé | Public |
| **Hébergement** | Géré | Self-hosted |
| **Mises à jour** | Automatiques | Git pull |

## Contribution Open-Source

### Comment contribuer

1. **Fork** le projet
2. **Créez une branche**: `git checkout -b feature/amazing-feature`
3. **Commitez**: `git commit -m 'feat: add amazing feature'`
4. **Push**: `git push origin feature/amazing-feature`
5. **Ouvrez une Pull Request**

### Standards

- **Backend**: PEP 8, Black formatting
- **Frontend**: ESLint + Prettier
- **Commits**: Conventional Commits
- **Tests**: pytest (backend), Jest (frontend)
- **Documentation**: Mettre à jour .agent/ si architecture change

### Obligations AGPL v3

Si vous forkez et hébergez une version modifiée:
1. ✅ Vous DEVEZ partager votre code source
2. ✅ Licence AGPL v3 obligatoire
3. ✅ Lien vers le code dans l'UI
4. ✅ Pas de "tivoization"

## Roadmap Open-Source

### V3.1 (Q1 2025)
- [ ] Support Facebook Pages
- [ ] Support Twitter/X
- [ ] Interface d'administration multi-tenant
- [ ] Webhooks personnalisables

### V3.2 (Q2 2025)
- [ ] Marketplace de plugins
- [ ] Templates d'automation
- [ ] Rapports analytiques avancés
- [ ] Export/Import configurations

### V3.3 (Q3 2025)
- [ ] Support LinkedIn
- [ ] Support TikTok
- [ ] Multi-langue (i18n)
- [ ] Thèmes personnalisables

## Support & Communauté

**Issues**: [GitHub Issues](https://github.com/votre-username/socialsync-ai/issues)
**Discussions**: [GitHub Discussions](https://github.com/votre-username/socialsync-ai/discussions)
**Sécurité**: security@socialsync.ai

## Fichiers de Référence

- `/workspace/README.md` - README principal open-source
- `/workspace/SEEDING.md` - Guide de seeding complet
- `/workspace/LICENSE` - Texte AGPL v3
- `/workspace/scripts/seed_users.py` - Script création users
- `/workspace/scripts/seed_social_accounts.py` - Script comptes sociaux
- `backend/app/services/credits_service.py` - Service crédits illimités
- `frontend/app/auth/page.tsx` - Login email/password

## Historique des Versions

**V3.0 (2025-10-29)** - Transformation Open-Source
- Suppression Stripe, billing, OAuth Google
- Crédits illimités pour tous
- Licence AGPL v3
- Scripts de seed
- Documentation complète

**V2.4 (2025-10-23)** - RAG Agent Silent Error Handling
**V2.3 (2025-10-22)** - Automation Service Unified
**V2.2 (2025-10-21)** - Topic Modeling BERTopic + Gemini
**V2.1 (2025-10-20)** - Comment Monitoring V2 (Vision AI)
**V2.0 (2025-10-18)** - AI Studio + Scheduled Posts

---

**Version**: 3.0 (Open-Source Edition)
**Licence**: AGPL v3.0
**Dernière mise à jour**: 2025-10-29

---

## Related Documentation

- `.agent/README.md` - Index de toute la documentation
- `.agent/System/ARCHITECTURE.md` - Architecture système complète
- `.agent/System/TECH_STACK.md` - Stack technique détaillé
- `.agent/SOP/DOCKER_SETUP.md` - Configuration Docker Compose
