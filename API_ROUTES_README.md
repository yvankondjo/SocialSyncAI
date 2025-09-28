# 📚 Documentation des Routes API - SocialSyncAI

## 🎯 Vue d'ensemble

Ce document répertorie toutes les routes API développées dans le backend SocialSyncAI, organisées par modules fonctionnels. Il inclut les routes actuellement incluses dans `main.py` et celles qui ne le sont pas encore.

## 📋 Routes Actuellement Incluses dans main.py

### 🏠 Routes Principales (main.py)
```python
# Routes de base
GET  /                    # Page d'accueil
GET  /health             # Vérification de santé
GET  /api/versions       # Versions des APIs externes
GET  /api/health         # Santé du système complet
GET  /api/metrics        # Métriques détaillées
```

### 📊 Analytics (`/api/analytics`)
```python
POST /api/analytics/sync/{content_id}           # Synchroniser analytics d'un contenu
POST /api/analytics/sync/user/{user_id}         # Synchroniser analytics utilisateur (background)
GET  /api/analytics/history/{content_id}        # Historique analytics d'un contenu
GET  /api/analytics/trends/{user_id}            # Tendances analytics utilisateur
```

### 🔗 Comptes Sociaux (`/api/social-accounts`)
```python
GET  /api/social-accounts/connect/{platform}              # URL d'autorisation OAuth
GET  /api/social-accounts/connect/{platform}/callback     # Callback OAuth
GET  /api/social-accounts/                               # Lister les comptes sociaux
DELETE /api/social-accounts/{account_id}                  # Supprimer un compte social
```


### 📱 WhatsApp (`/api/whatsapp`)
```python
# Envoi de messages
POST /api/whatsapp/validate-credentials     # Valider les credentials WhatsApp
POST /api/whatsapp/send-text               # Envoyer message texte
POST /api/whatsapp/send-template           # Envoyer template WhatsApp
POST /api/whatsapp/send-media              # Envoyer message avec média
POST /api/whatsapp/send-batch              # Envoyer messages en lot
GET  /api/whatsapp/business-profile        # Profil business WhatsApp

# Webhooks
GET  /api/whatsapp/webhook                 # Vérification webhook
POST /api/whatsapp/webhook                 # Gestionnaire webhook principal
POST /api/whatsapp/webhook-test            # Test webhook local
GET  /api/whatsapp/webhook-info            # Info configuration webhooks
```

### 📸 Instagram (`/api/instagram`)
```python
# Messages et publications
POST /api/instagram/validate-credentials   # Valider credentials Instagram
POST /api/instagram/send-dm                # Envoyer message direct
POST /api/instagram/publish-post           # Publier post feed
POST /api/instagram/publish-story          # Publier story
POST /api/instagram/reply-comment          # Répondre à commentaire
GET  /api/instagram/conversations          # Récupérer conversations
POST /api/instagram/send-batch-dm          # Messages directs en lot

# Utilitaires
GET  /api/instagram/health                 # Santé service Instagram
GET  /api/instagram/capabilities           # Fonctionnalités disponibles
GET  /api/instagram/setup-guide            # Guide configuration

# Webhooks
GET  /api/instagram/webhook                # Vérification webhook
POST /api/instagram/webhook                # Gestionnaire webhook principal
POST /api/instagram/webhook-test           # Test webhook local
GET  /api/instagram/webhook-info           # Info configuration webhooks
```

### 💬 Messaging Unifié (`/api/messaging`)
```python
POST /api/messaging/send                   # Envoyer message unifié
POST /api/messaging/send-bulk              # Envoyer messages en lot
POST /api/messaging/broadcast              # Diffuser sur plusieurs plateformes
POST /api/messaging/send-smart             # Envoi intelligent avec détection auto
GET  /api/messaging/capabilities/{platform} # Capacités d'une plateforme
GET  /api/messaging/capabilities           # Capacités de toutes les plateformes
GET  /api/messaging/health                 # Santé service messaging
GET  /api/messaging/detect-platform/{recipient} # Détecter plateforme destinataire
```

### 💭 Conversations (`/api/conversations`)
```python
GET  /api/conversations                    # Lister conversations utilisateur
GET  /api/conversations/{conversation_id}/messages # Messages d'une conversation
POST /api/conversations/{conversation_id}/messages # Envoyer message dans conversation
POST /api/conversations/send-message       # Envoyer message (nouvelle signature)
PATCH /api/conversations/{conversation_id}/read # Marquer conversation comme lue
```

### 🤖 Automation (`/api/automation`)
```python
PATCH /api/automation/conversations/{conversation_id}/toggle # Activer/désactiver automation
POST /api/automation/conversations/{conversation_id}/check   # Vérifier règles automation
GET  /api/automation/keyword-rules         # Récupérer règles mots-clés
POST /api/automation/keyword-rules         # Créer règle mots-clés
PATCH /api/automation/keyword-rules/{rule_id} # Modifier règle mots-clés
DELETE /api/automation/keyword-rules/{rule_id} # Supprimer règle mots-clés
```

### 🌐 Widget Web (`/api/widget`)
```python
POST /api/widget/create                    # Créer widget chat IA
GET  /api/widget/preview/{widget_id}       # Aperçu HTML du widget
PUT  /api/widget/update/{widget_id}        # Mettre à jour configuration widget
GET  /api/widget/analytics/{widget_id}     # Analytics du widget
POST /api/widget/chat                      # Traiter message chat (endpoint widget)
POST /api/widget/validate-domain           # Valider domaine autorisé
GET  /api/widget/user-widgets              # Widgets d'un utilisateur
GET  /api/widget/templates                 # Templates de widgets disponibles
GET  /api/widget/embed-code/{widget_id}    # Code embed du widget
PUT  /api/widget/status/{widget_id}        # Mettre à jour statut widget
DELETE /api/widget/delete/{widget_id}      # Supprimer widget
GET  /api/widget/health                    # Santé service widgets
GET  /api/widget/setup-guide               # Guide d'installation
```

### ⚙️ Processus (`/api/functions/v1`)
```python
POST /api/functions/v1/process             # Traiter document (tâche d'ingestion)
```

### 📚 Documents de Connaissance (`/api/knowledge_documents`)
```python
GET    /api/knowledge_documents/           # Lister documents de connaissance
GET    /api/knowledge_documents/{document_id} # Récupérer document spécifique
DELETE /api/knowledge_documents/{document_id} # Supprimer document
```

### ❓ FAQ Q&A (`/api/faq-qa`)
```python
GET    /api/faq-qa/                        # Lister FAQ Q&A
GET    /api/faq-qa/{faq_id}                # Récupérer FAQ spécifique
POST   /api/faq-qa/                        # Créer nouvelle FAQ
PUT    /api/faq-qa/{faq_id}                # Mettre à jour FAQ
PATCH  /api/faq-qa/{faq_id}                # Mise à jour partielle FAQ
PATCH  /api/faq-qa/{faq_id}/toggle         # Activer/désactiver FAQ
DELETE /api/faq-qa/{faq_id}                # Supprimer FAQ définitivement
```

### 🧠 Paramètres IA (`/api/ai-settings`)
```python
GET    /api/ai-settings/                   # Récupérer paramètres IA utilisateur
PUT    /api/ai-settings/                   # Mettre à jour paramètres IA
POST   /api/ai-settings/test               # Tester réponse IA
GET    /api/ai-settings/templates          # Récupérer templates de prompts
POST   /api/ai-settings/reset              # Réinitialiser vers template
```

## 🚫 Routes NON Incluses dans main.py

### 👥 Utilisateurs (`/api/users`)
```python
POST /api/users/                           # Créer utilisateur (admin)
GET  /api/users/{user_id}                  # Récupérer profil utilisateur
GET  /api/users/                           # Lister utilisateurs (admin)
PUT  /api/users/{user_id}                  # Modifier profil utilisateur
```


## 🔧 Comment Intégrer les Routes Manquantes

### 1. Ajouter les imports dans main.py

```python
# Dans backend/app/main.py, ajouter :
from app.routers import users
```

### 2. Inclure les routers dans l'application

```python
# Dans backend/app/main.py, après les autres includes :
app.include_router(users.router, prefix="/api")
```

### 3. Vérifier les dépendances

Assurez-vous que tous les services et schémas nécessaires sont disponibles :
- `app.schemas.user`

## 📊 Statistiques des Routes

| Module | Routes Incluses | Routes Manquantes | Total |
|--------|----------------|-------------------|-------|
| Analytics | 4 | 0 | 4 |
| Social Accounts | 4 | 0 | 4 |
| WhatsApp | 8 | 0 | 8 |
| Instagram | 12 | 0 | 12 |
| Messaging | 8 | 0 | 8 |
| Conversations | 5 | 0 | 5 |
| Automation | 6 | 0 | 6 |
| Web Widget | 12 | 0 | 12 |
| Process | 1 | 0 | 1 |
| Knowledge Documents | 3 | 0 | 3 |
| FAQ Q&A | 7 | 0 | 7 |
| AI Settings | 5 | 0 | 5 |
| **Users** | **0** | **4** | **4** |
| **TOTAL** | **75** | **4** | **79** |

## 🎯 Fonctionnalités Principales par Module

### 📊 Analytics
- Synchronisation automatique des métriques
- Historique des performances
- Tendances et analyses
- Support multi-plateformes

### 🔗 Social Accounts
- OAuth pour toutes les plateformes majeures
- Gestion des tokens d'accès
- Profils business
- Sécurité RLS

### 📱 WhatsApp & Instagram
- Envoi de messages (texte, média, templates)
- Webhooks pour réception
- Gestion des conversations
- Support batch

### 💬 Messaging Unifié
- API unifiée pour toutes les plateformes
- Détection automatique de plateforme
- Envoi en lot et broadcast
- Gestion des capacités

### 🤖 Automation & IA
- Règles de mots-clés
- Réponses automatiques
- Configuration IA personnalisée
- Templates de prompts

### 🌐 Widget Web
- Chat IA intégrable
- Personnalisation complète
- Analytics détaillées
- Sécurité par domaine

## 🚀 Prochaines Étapes

1. **Intégrer les routes manquantes** dans `main.py`
2. **Tester toutes les routes** avec des données réelles
3. **Documenter les schémas** de requêtes/réponses
4. **Ajouter la validation** des paramètres
5. **Implémenter la pagination** pour les listes
6. **Ajouter la gestion d'erreurs** centralisée

## 📝 Notes Importantes

- Toutes les routes utilisent l'authentification Supabase
- La sécurité RLS est appliquée automatiquement
- Les webhooks nécessitent une configuration spécifique
- Certaines routes sont en mode développement (mocked data)
- La documentation OpenAPI est générée automatiquement via FastAPI

---

*Dernière mise à jour : 19 décembre 2024*
