# 🤖 SocialSync AI - Open Source Edition

**AI-Powered Social Media Management & Automation Platform**

SocialSync AI est une plateforme open-source de gestion intelligente des réseaux sociaux. Automatisez vos réponses, gérez vos messages et commentaires, et créez du contenu avec l'aide de l'IA.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

## ✨ Fonctionnalités

### 🤖 Automation IA
- **Réponses automatiques** aux DMs Instagram et messages WhatsApp
- **Analyse de sentiment** et triage intelligent des conversations
- **Règles personnalisables** pour contrôler quand l'IA répond
- **Mode de sécurité** avec guardrails configurables

### 💬 Gestion des Conversations
- **Inbox unifié** pour Instagram DMs et WhatsApp Business
- **Réponses manuelles ou assistées par IA**
- **Escalade** des conversations importantes
- **Historique complet** des échanges

### 📝 Commentaires Instagram
- **Monitoring automatique** des commentaires sur vos posts
- **Réponses IA contextuelles** basées sur votre base de connaissances
- **Règles de filtre** pour ignorer certains types de commentaires
- **Dashboard de gestion** avec statistiques

### 📚 Base de Connaissances
- **Documents FAQ** pour entraîner l'IA
- **RAG (Retrieval Augmented Generation)** pour réponses précises
- **Topic modeling** automatique avec BERTopic
- **Support multi-formats** (texte, PDF, etc.)

### 📅 Planification de Posts
- **Calendrier de publication** pour Instagram
- **Brouillons et aperçus**
- **Planification multi-posts**
- **Gestion des médias**

### 🎨 AI Studio
- **Génération de contenu** assistée par IA
- **Réécriture et amélioration** de textes
- **Suggestions de hashtags**
- **Tonalité personnalisable**

### 📊 Analytics
- **Statistiques d'engagement** en temps réel
- **Performance des posts** et commentaires
- **Métriques de conversations**
- **Rapports d'utilisation IA**

## 🚀 Démarrage Rapide

### Prérequis

- **Docker** et **Docker Compose**
- **Compte Supabase** (gratuit) - [supabase.com](https://supabase.com)
- **Clés API** :
  - OpenRouter ou OpenAI (pour l'IA)
  - Meta Developer Account (pour Instagram/WhatsApp)
  - Google Gemini (optionnel, pour embeddings)

### Installation

1. **Clonez le repo**

```bash
git clone https://github.com/votre-username/socialsync-ai.git
cd socialsync-ai
```

2. **Configurez les variables d'environnement**

```bash
# Backend
cp backend/.env.example backend/.env
# Éditez backend/.env avec vos clés

# Frontend
cp frontend/.env.example frontend/.env.local
# Éditez frontend/.env.local avec vos clés
```

3. **Lancez avec Docker Compose**

```bash
docker-compose up -d
```

4. **Créez votre premier utilisateur**

```bash
# Configurez vos credentials Supabase
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Créez des utilisateurs de test
python scripts/seed_users.py
```

5. **Accédez à l'application**

- Frontend : [http://localhost:3000](http://localhost:3000)
- API Backend : [http://localhost:8000](http://localhost:8000)
- API Docs : [http://localhost:8000/docs](http://localhost:8000/docs)

📖 **Guide complet** : Voir [SEEDING.md](SEEDING.md) pour créer des données de test

## 📁 Structure du Projet

```
socialsync-ai/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── routers/     # Endpoints REST
│   │   ├── services/    # Logique métier
│   │   ├── workers/     # Celery tasks
│   │   └── schemas/     # Modèles Pydantic
│   └── requirements.txt
├── frontend/            # Application Next.js
│   ├── app/            # App Router (Next.js 14)
│   ├── components/     # Composants React
│   ├── lib/           # Utilitaires
│   └── package.json
├── supabase/
│   └── migrations/    # Migrations DB
├── scripts/           # Scripts de seed
│   ├── seed_users.py
│   └── seed_social_accounts.py
├── docker-compose.yml
└── README.md
```

## 🛠️ Stack Technique

### Backend
- **FastAPI** - API REST moderne et rapide
- **Python 3.10+** - Language principal
- **Celery** - Queue de tâches asynchrones
- **Redis** - Cache et message broker
- **Supabase** - Base de données PostgreSQL + Auth

### Frontend
- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage statique
- **Tailwind CSS** - Styles utilitaires
- **shadcn/ui** - Composants UI
- **Zustand** - State management

### IA & ML
- **LangChain** - Orchestration LLM
- **OpenRouter** - Gateway multi-LLM
- **Google Gemini** - Embeddings (optionnel)
- **BERTopic** - Topic modeling
- **ChromaDB** - Vector database pour RAG

### Infrastructure
- **Docker** - Containerisation
- **PostgreSQL** - Base de données principale
- **Redis** - Cache et queues
- **Supabase** - Backend-as-a-Service

## 🔧 Configuration

### Variables d'Environnement Backend

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# LLM (choisissez l'un ou l'autre)
OPENROUTER_API_KEY=your-openrouter-key
OPENAI_API_KEY=your-openai-key

# Meta (Instagram/WhatsApp)
INSTAGRAM_ACCESS_TOKEN=your-ig-token
WHATSAPP_ACCESS_TOKEN=your-wa-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-id

# Redis
REDIS_URL=redis://redis:6379/0

# Embeddings (optionnel)
GOOGLE_API_KEY=your-gemini-key
```

### Variables d'Environnement Frontend

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

📖 **Documentation complète** : Voir `.env.example` pour toutes les options

## 📚 Documentation

- **[SEEDING.md](SEEDING.md)** - Guide de création de données de test
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guide de déploiement en production *(à venir)*
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guide de contribution *(à venir)*

## 🤝 Contribution

Les contributions sont les bienvenues ! SocialSync AI est sous licence **AGPL v3** - toute modification doit être partagée avec la communauté.

### Comment contribuer ?

1. **Fork** le projet
2. **Créez une branche** : `git checkout -b feature/amazing-feature`
3. **Commitez** : `git commit -m 'feat: add amazing feature'`
4. **Push** : `git push origin feature/amazing-feature`
5. **Ouvrez une Pull Request**

### Standards de code

- **Backend** : Suivez PEP 8, utilisez Black pour le formatting
- **Frontend** : ESLint + Prettier configurés
- **Commits** : Convention Conventional Commits

## 📝 Licence

Ce projet est sous licence **GNU Affero General Public License v3.0 (AGPL-3.0)**.

**Ce que cela signifie :**
- ✅ Vous pouvez utiliser, modifier et distribuer ce code
- ✅ Vous pouvez l'utiliser commercialement
- ⚠️ **Toute modification doit être partagée** sous la même licence
- ⚠️ Si vous hébergez une version modifiée, vous devez **partager le code source**

La licence AGPL garantit que SocialSync AI reste open-source pour toujours.

## 🎯 Roadmap

- [ ] Support pour Facebook Pages
- [ ] Support pour Twitter/X
- [ ] Support pour LinkedIn
- [ ] Webhooks personnalisables
- [ ] Marketplace de plugins
- [ ] Support multi-tenant
- [ ] Interface d'administration
- [ ] Rapports analytiques avancés

## 🐛 Support & Issues

- **Bugs** : [Ouvrir une issue](https://github.com/votre-username/socialsync-ai/issues)
- **Questions** : [Discussions](https://github.com/votre-username/socialsync-ai/discussions)
- **Sécurité** : security@socialsync.ai

## 🌟 Remerciements

- **FastAPI** pour l'excellent framework
- **Next.js** pour la Developer Experience
- **Supabase** pour le BaaS
- **LangChain** pour l'orchestration LLM
- **shadcn/ui** pour les composants

## ⭐ Star le Projet

Si SocialSync AI vous est utile, donnez-nous une ⭐ sur GitHub !

---

**Fait avec ❤️ par la communauté open-source**

*Version Open-Source • Crédits Illimités • Licence AGPL v3*
