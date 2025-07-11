# SocialSync AI Backend

Backend API pour SocialSync AI, construit avec FastAPI et Supabase.

## Configuration

### 1. Installation des dépendances

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configuration de Supabase

1. Créez un projet sur [Supabase Cloud](https://supabase.com/dashboard)
2. Copiez le fichier `.env.example` vers `.env`
3. Remplissez les variables d'environnement avec vos clés Supabase

### 3. Création du schéma de base de données

1. Allez dans l'éditeur SQL de votre projet Supabase
2. Exécutez le contenu du fichier `schema.sql`
3. Cela créera toutes les tables, indexes, et politiques RLS nécessaires

## Structure de la base de données

### Tables principales

- **users** : Utilisateurs de l'application
- **organizations** : Organisations/entreprises
- **social_accounts** : Comptes de réseaux sociaux
- **content** : Contenu publié/planifié
- **analytics** : Métriques d'engagement
- **ai_insights** : Insights générés par l'IA

### Fonctionnalités

- **UUID** comme clés primaires
- **Row Level Security (RLS)** activé
- **Triggers** pour `updated_at` automatique
- **Extension pgvector** pour les embeddings IA
- **Index** optimisés pour les performances

## Démarrage du serveur

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Une fois le serveur démarré, la documentation interactive est disponible sur :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## Endpoints principaux

### Users
- `POST /users/` - Créer un utilisateur
- `GET /users/{user_id}` - Récupérer un utilisateur
- `GET /users/` - Lister les utilisateurs
- `PUT /users/{user_id}` - Mettre à jour un utilisateur

### Organizations
- `POST /organizations/` - Créer une organisation
- `GET /organizations/{org_id}` - Récupérer une organisation

### Social Accounts
- `POST /social-accounts/` - Créer un compte social
- `GET /organizations/{org_id}/social-accounts` - Lister les comptes d'une organisation

## Sécurité

- **Row Level Security** : Les utilisateurs ne peuvent accéder qu'à leurs propres données
- **Variables d'environnement** : Les clés sensibles sont stockées dans `.env`
- **CORS** : Configuré pour autoriser le frontend Next.js

## Tests

Pour tester l'API, vous pouvez utiliser :

1. **Swagger UI** : Interface web interactive
2. **curl** : Commandes en ligne de commande
3. **Postman** : Client API graphique

Exemple avec curl :

```bash
# Test de santé
curl http://localhost:8000/health

# Créer un utilisateur
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "password123"
  }'
``` 