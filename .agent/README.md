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
- `AI_RULES_IMPLEMENTATION.md` - Contrôle IA simple (IMPLEMENTED ✅)
- `AI_RULES_MODERATION_IMPLEMENTATION.md` - OpenAI Moderation + Email Escalation (IMPLEMENTED ✅)
- `COMMENT_POLLING_IMPLEMENTATION.md` - Polling commentaires avec AI scope controls (IMPLEMENTED ✅)
- `TRIAGE_SYSTEM.md` - Triage intelligent des messages (IGNORE/ESCALATE/AUTO_REPLY)
- `ANALYTICS_KPI.md` - Analytics et KPIs toutes les 2h
- `CLUSTERING.md` - Clustering de messages et topics

### 🏗️ System/
Documentation de l'état actuel du système.

**Fichiers disponibles:**
- `ARCHITECTURE.md` - Architecture globale et flux de données
- `TECH_STACK.md` - Technologies utilisées
- `DATABASE_SCHEMA.md` - Schéma de base de données Supabase
- `INTEGRATIONS.md` - Intégrations existantes (WhatsApp, Instagram)
- `AGENT_ARCHITECTURE.md` - Architecture de l'agent RAG
- `CELERY_WORKERS.md` - Configuration des workers et queues

### 📝 SOP/
Procédures standardisées pour les tâches récurrentes.

**Fichiers disponibles:**
- `ADD_MIGRATION.md` - Comment ajouter une migration Supabase
- `ADD_ROUTE.md` - Comment ajouter une nouvelle route API
- `ADD_PLATFORM.md` - Comment intégrer une nouvelle plateforme sociale
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
- **AI Rules** ✅ (2025-10-18) - Contrôle IA simple (instructions + ignore examples)
- **AI Moderation & Escalation** ✅ (2025-10-18) - OpenAI Moderation API + Email escalation automatique
- **Comment Polling** ✅ (2025-10-18) - Polling adaptatif commentaires Instagram avec AI scope controls (chats vs comments)

### 🚧 En cours de développement
Voir `/workspace/RAPPORT_FINAL.md` pour la dernière session de développement

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

### Workers
```bash
cd backend
# Worker for ingest queue
celery -A app.workers.celery_app worker --loglevel=info -Q ingest

# Worker for scheduler queue (scheduled posts)
celery -A app.workers.celery_app worker --loglevel=info -Q scheduler

# Worker for comments queue (comment polling)
celery -A app.workers.celery_app worker --loglevel=info -Q comments

# Celery Beat for periodic tasks
celery -A app.workers.celery_app beat --loglevel=info

# Combined (dev only)
celery -A app.workers.celery_app worker --beat --loglevel=info -Q ingest,scheduler,comments
```

## Ressources externes
- [PLATFORM_INTEGRATION_GUIDE.md](/workspace/PLATFORM_INTEGRATION_GUIDE.md) - Guide détaillé d'intégration de plateformes
- [Supabase Dashboard](https://supabase.com/dashboard)
- [Meta Business Suite](https://business.facebook.com/)

## Convention de mise à jour

Après l'implémentation d'une fonctionnalité majeure:
1. ✅ Marquer la task comme complète dans `Tasks/[FEATURE].md`
2. 📝 Mettre à jour `System/` si l'architecture a évolué
3. 🔄 Ajouter une SOP si une procédure récurrente émerge
4. 📊 Mettre à jour ce README si nécessaire

---
*Dernière mise à jour: 2025-10-18*
