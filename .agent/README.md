# SocialSync AI - Documentation Index

## Vue d'ensemble
SocialSync AI est une plateforme de gestion multi-réseaux sociaux avec IA conversationnelle. Elle permet de connecter plusieurs comptes sociaux (WhatsApp, Instagram, etc.), gérer les conversations entrantes, et répondre automatiquement via un agent RAG.

## Structure de la documentation

### 📋 Tasks/
PRD et plans d'implémentation pour chaque fonctionnalité. Chaque fichier contient:
- Objectifs et contexte
- Spécifications techniques
- Plan d'exécution
- Critères d'acceptation (DoD)

**Fichiers disponibles:**
- `SCHEDULED_POSTS.md` - Publication planifiée multi-plateformes (PRD)
- `SCHEDULED_POSTS_IMPLEMENTATION.md` - Publication planifiée (IMPLEMENTED ✅)
- `AI_STUDIO_IMPLEMENTATION.md` - AI-assisted content creation and scheduling (IMPLEMENTED ✅)
- `AI_RULES_IMPLEMENTATION.md` - Contrôle IA simple (IMPLEMENTED ✅)
- `AI_RULES_MODERATION_IMPLEMENTATION.md` - OpenAI Moderation + Email Escalation (IMPLEMENTED ✅)
- `COMMENT_POLLING_IMPLEMENTATION.md` - Polling commentaires avec AI scope controls (IMPLEMENTED ✅)
- `COMMENT_MONITORING_V2.md` - Vision AI + Multi-Platform Comment System (IMPLEMENTED ✅ 2025-10-20)
- `TRIAGE_SYSTEM.md` - Triage intelligent des messages (IGNORE/ESCALATE/AUTO_REPLY)
- `ANALYTICS_KPI.md` - Analytics et KPIs toutes les 2h
- `CLUSTERING.md` - Topic Modeling BERTopic + Gemini (IMPLEMENTED ✅ 2025-10-21)

### 🏗️ System/
Documentation de l'état actuel du système.

**Fichiers disponibles:**
- `ARCHITECTURE.md` - Architecture globale et flux de données
- `TECH_STACK.md` - Technologies utilisées
- `DATABASE_SCHEMA.md` - Schéma de base de données Supabase
- `INTEGRATIONS.md` - Intégrations existantes (WhatsApp, Instagram)
- `CELERY_WORKERS.md` - Configuration des workers et queues (deprecated - voir CELERY_ARCHITECTURE.md)
- `CELERY_ARCHITECTURE.md` - Architecture Celery complète (V2.0 - Post-Migration Batch Scanner)
- `TOPIC_MODELING.md` - Topic Modeling BERTopic + Gemini (2025-10-21)
- `AUTOMATION_SERVICE.md` - Service d'automation unifié (chats + commentaires) (2025-10-23)
- `RAG_AGENT_ERROR_HANDLING.md` - **NEW** - Gestion silencieuse erreurs & guardrails (V2.4 - 2025-10-23)
- `comment-monitoring-unified-api.md` - API unifiée système de monitoring commentaires multi-plateformes

### 📝 SOP/
Procédures standardisées pour les tâches récurrentes.

**Fichiers disponibles:**
- `ADD_MIGRATION.md` - Comment ajouter une migration Supabase
- `ADD_ROUTE.md` - Comment ajouter une nouvelle route API
- `ADD_PLATFORM.md` - Comment intégrer une nouvelle plateforme sociale
- `add-new-social-platform.md` - Guide complet intégration multi-plateformes (4-6h par plateforme)
- `DOCKER_SETUP.md` - **NEW** - Configuration Docker Compose complète (Dev + Prod)
- `DEPLOY.md` - Procédure de déploiement
- `TESTING.md` - Stratégies de tests

## État actuel du projet

### ✅ Fonctionnalités implémentées
- **Connexion OAuth** multi-plateformes (WhatsApp, Instagram)
- **Inbox intelligent** avec batching Redis (2s window)
- **Agent RAG** pour réponses automatiques
- **Système de crédits** et quotas par plan
- **Webhooks** avec validation HMAC
- **Media handling** (images, audio) vers Supabase Storage
- **Background processing** avec Celery + Redis
- **Analytics basiques** (métriques temps réel)
- **Scheduled Posts** ✅ (2025-10-18) - Publication planifiée avec retry automatique
- **AI Studio** ✅ (2025-10-19) - AI-assisted content creation, preview, and scheduling
- **AI Rules** ✅ (2025-10-18) - Contrôle IA simple (instructions + ignore examples)
- **AI Moderation & Escalation** ✅ (2025-10-18) - OpenAI Moderation API + Email escalation automatique
- **Comment Polling** ✅ (2025-10-18) - Polling adaptatif commentaires Instagram avec AI scope controls (chats vs comments)
- **Comment Monitoring V2** ✅ (2025-10-20) - Vision AI + Multi-Platform Architecture
  - ✅ Vision AI (AI voit les images des posts pour contexte)
  - ✅ Contrôles AI granulaires (comments séparés des conversations)
  - ✅ Détection conversations (ignore @mentions, user-to-user)
  - ✅ Architecture multi-plateformes (Instagram ✅, Facebook/Twitter 🚧)
  - ✅ Documentation API complète + guides intégration
- **Topic Modeling** ✅ (2025-10-21) - BERTopic + Gemini Analytics
  - ✅ Clustering automatique (UMAP + HDBSCAN)
  - ✅ Embeddings Gemini (768d, task_type='clustering')
  - ✅ Topic naming avec Gemini 2.5 Flash (batch)
  - ✅ Merge models incrémental (every 2 days)
  - ✅ 100% économie coûts (vs OpenAI)
- **RAG Agent Error Handling** ✅ (2025-10-23) - Silent Failure Mode (V2.4)
  - ✅ Gestion silencieuse des erreurs (pas de "Désolé...")
  - ✅ Guardrails PRE/POST avec suppression messages
  - ✅ Retry automatique 3x avec exponential backoff
  - ✅ RemoveMessage avec add_messages reducer
  - ⚠️ Tests manuels requis avant production

### 🎯 Fonctionnalités planifiées
Voir `Tasks/` pour les PRDs de chaque feature à développer

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Workers & Beat (REQUIRED)

**⚠️ IMPORTANT:** Celery Beat est REQUIS pour que les DMs/chats fonctionnent !

```bash
cd backend

# Méthode 1: Workers séparés (production)
# Terminal 1: Worker Ingest (DMs/chats)
celery -A app.workers.celery_app worker -l info -Q ingest -n ingest@%h

# Terminal 2: Worker Scheduler (posts planifiés)
celery -A app.workers.celery_app worker -l info -Q scheduler -n scheduler@%h

# Terminal 3: Worker Comments (commentaires)
celery -A app.workers.celery_app worker -l info -Q comments -n comments@%h

# Terminal 4: Worker Topics (topic modeling)
celery -A app.workers.celery_app worker -l info -Q topics -n topics@%h

# Terminal 5: Celery Beat (REQUIS - UN SEUL)
celery -A app.workers.celery_app beat -l info

# Méthode 2: Combined (dev seulement)
celery -A app.workers.celery_app worker --beat -l info -Q ingest,scheduler,comments,topics
```

**Voir:** `.agent/SOP/DOCKER_SETUP.md` pour Docker Compose

### Debug Tools (NEW)
```bash
# Force immediate comment polling (bypass schedule)
curl -X POST http://localhost:8000/api/debug/comments/force-poll

# View AI context for a comment (includes images, thread)
curl http://localhost:8000/api/debug/comments/comment-context/{comment_id}

# Test conversation detection rules
curl -X POST http://localhost:8000/api/debug/comments/test-should-respond \
  -H "Content-Type: application/json" \
  -d '{"comment": {...}, "post": {...}}'
```

## 🎯 Features Clés (V2.0 - 2025-10-20)

### Vision AI pour Commentaires
L'IA peut maintenant **voir les images des posts** et répondre avec contexte visuel complet :
- 📸 Image du post (Vision AI)
- 📝 Caption du post
- 🎵 Titre de la musique
- 💬 Thread complet (10 derniers commentaires)

### Contrôles AI Granulaires
Deux toggles indépendants pour un contrôle précis :
- **Comments Toggle** → Dashboard → Comment Monitoring → "AI auto-replies on comments"
- **Conversations Toggle** → Dashboard → AI Settings → "AI auto-replies for DMs/Chats"

### Détection de Conversations
L'IA ne spam plus les conversations user-to-user :
- ❌ Ignore `@mentions` d'autres utilisateurs
- ❌ Ignore réponses à d'autres users
- ✅ Répond seulement aux questions directes

### Architecture Multi-Plateformes
Système unifié pour toutes les plateformes :
- ✅ Instagram (production ready)
- 🚧 Facebook (connector prêt, needs OAuth)
- 🚧 Twitter (template fourni, 4-6h)
- 🚧 TikTok (awaiting API access)

**Guide intégration:** `.agent/SOP/add-new-social-platform.md`

---

## Ressources externes

**Documentation technique:**
- [RAG_AGENT_SILENT_ERROR_HANDLING.md](/workspace/RAG_AGENT_SILENT_ERROR_HANDLING.md) - **NEW** - Doc technique complète V2.4 (50+ sections)
- [RAG_AGENT_ERROR_FLOW_SUMMARY.md](/workspace/RAG_AGENT_ERROR_FLOW_SUMMARY.md) - **NEW** - Diagrammes flux erreurs (4 scénarios)
- [CRITICAL_FIXES_AND_VALIDATION.md](/workspace/CRITICAL_FIXES_AND_VALIDATION.md) - **NEW** - Bug critique corrigé + validation
- [AUTOMATION_REFACTORING_SUMMARY.md](/workspace/AUTOMATION_REFACTORING_SUMMARY.md) - Refactorisation AutomationService V2.3
- [CELERY_REDIS_COURS_COMPLET.md](/workspace/CELERY_REDIS_COURS_COMPLET.md) - Cours complet Celery + Redis (15-20 min)
- [BATCH_SCANNER_MIGRATION.md](/workspace/BATCH_SCANNER_MIGRATION.md) - Migration batch scanner → Celery
- [AUDIT_CORRECTIFS_COMPLETE.md](/workspace/AUDIT_CORRECTIFS_COMPLETE.md) - Rapport audit architecture (4 correctifs)
- [TOPIC_MODELING_GEMINI_REFACTOR.md](/workspace/TOPIC_MODELING_GEMINI_REFACTOR.md) - Refactorisation Gemini (97% économie)
- [TOPIC_MODELING_PERFORMANCE.md](/workspace/backend/TOPIC_MODELING_PERFORMANCE.md) - Guide performance & scaling
- [PLATFORM_INTEGRATION_GUIDE.md](/workspace/PLATFORM_INTEGRATION_GUIDE.md) - Guide intégration plateformes
- [COMMENT_SYSTEM_IMPLEMENTATION_SUMMARY.md](/workspace/COMMENT_SYSTEM_IMPLEMENTATION_SUMMARY.md) - Résumé V2.0
- [QUICK_TEST_GUIDE.md](/workspace/QUICK_TEST_GUIDE.md) - Guide de test (10-15 min)

**Services externes:**
- [Supabase Dashboard](https://supabase.com/dashboard)
- [Meta Business Suite](https://business.facebook.com/)
- [Flower (Celery Monitoring)](http://localhost:5555) - Requis: Docker Compose

## Convention de mise à jour

Après l'implémentation d'une fonctionnalité majeure:
1. ✅ Marquer la task comme complète dans `Tasks/[FEATURE].md`
2. 📝 Mettre à jour `System/` si l'architecture a évolué
3. 🔄 Ajouter une SOP si une procédure récurrente émerge
4. 📊 Mettre à jour ce README si nécessaire

---

## 📊 Statistiques du Projet (V2.4)

**Version actuelle:** 2.4 (RAG Agent Silent Error Handling)
**Dernière mise à jour:** 2025-10-23
**Changelog complet:** [CHANGELOG.md](.agent/CHANGELOG.md)

**Architecture Changes (V2.4):**
- ✅ RAG Agent gestion silencieuse erreurs & guardrails
- ✅ Bug critique corrigé (operator.add → add_messages)
- ✅ RemoveMessage fonctionnel (contexte LLM propre)
- ✅ Retry automatique 3x avec exponential backoff
- ✅ Tests logique 7/7 PASS
- ⚠️ Tests manuels requis avant production

**Architecture Changes (V2.3):**
- ✅ AutomationService unifié (conversations + commentaires)
- ✅ Code mort supprimé (auto_reply_service.py)
- ✅ Architecture DRY (Don't Repeat Yourself)
- ✅ 78% réduction code duplication (workers/comments.py)
- ✅ Tests automatiques 100% passants

**Architecture Changes (V2.2):**
- ✅ Topic Modeling BERTopic + Gemini (clustering automatique)
- ✅ Embeddings Gemini 768d (task_type='clustering')
- ✅ Topic naming Gemini 2.5 Flash (batch processing)
- ✅ Merge models incrémental (every 2 days)
- ✅ 97% économie coûts embeddings (vs OpenAI)

**Architecture Changes (V2.1):**
- ✅ Batch Scanner migré vers Celery (DMs/chats)
- ✅ API Versions unifiées (v23.0 → META_GRAPH_VERSION)
- ✅ Services patterns standardisés (RuntimeError)
- ✅ HMAC Webhooks réactivé (sécurité)
- ✅ Docker Compose complet (Beat + workers)

**Code Stats (V2.4):**
- Backend: ~200 lignes modifiées (rag_agent.py)
- Bug critique: operator.add → add_messages (RemoveMessage fix)
- Documentation: 4 nouveaux fichiers
  - `.agent/System/RAG_AGENT_ERROR_HANDLING.md` (doc technique)
  - `RAG_AGENT_SILENT_ERROR_HANDLING.md` (50+ sections)
  - `RAG_AGENT_ERROR_FLOW_SUMMARY.md` (diagrammes visuels)
  - `CRITICAL_FIXES_AND_VALIDATION.md` (rapport validation)
- Tests: 3 nouveaux scripts (logic, scenarios, retry)

**Code Stats (V2.3):**
- Backend: -111 lignes (code mort + duplication supprimée)
- Migrations: 1 nouveau fichier SQL (drop auto_reply_settings)
- Documentation: 2 nouveaux fichiers
  - `.agent/System/AUTOMATION_SERVICE.md` (architecture complète)
  - `AUTOMATION_REFACTORING_SUMMARY.md` (résumé refactorisation)
- Tests: 1 nouveau script (test_automation_refactoring.py)

**Plateformes supportées:**
- ✅ Instagram (production)
- ✅ WhatsApp (production)
- 🚧 Facebook (connector prêt)
- 🚧 Twitter (template fourni)
- 🚧 TikTok (en attente API)

---
*Dernière mise à jour: 2025-10-23 - V2.4 (RAG Agent Silent Error Handling)*
