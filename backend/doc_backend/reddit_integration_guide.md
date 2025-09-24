# Guide d'Intégration Reddit

## Configuration Reddit OAuth

### 1. Création de l'application Reddit

1. Aller sur https://www.reddit.com/prefs/apps
2. Cliquer sur "Create App" ou "Create Another App"
3. Remplir les informations :
   - **Name**: SocialSync
   - **App type**: Web app
   - **Description**: Application SocialSync pour gérer les comptes Reddit
   - **About URL**: https://votre-site.com
   - **Redirect URI**: `http://localhost:8000/api/social-accounts/connect/reddit/callback`

### 2. Variables d'environnement à ajouter

Ajouter dans votre fichier `.env` :

```env
# Reddit
REDDIT_CLIENT_ID=votre_client_id_reddit
REDDIT_CLIENT_SECRET=votre_client_secret_reddit
REDDIT_REDIRECT_URI=http://localhost:8000/api/social-accounts/connect/reddit/callback
```

### 3. Scopes autorisés

L'intégration Reddit demande les scopes suivants :
- `identity` : Pour obtenir l'identité de l'utilisateur
- `read` : Pour lire les posts et commentaires
- `submit` : Pour soumettre de nouveaux posts
- `edit` : Pour éditer les posts et commentaires
- `privatemessages` : Pour gérer les messages privés
- `modposts` : Pour modérer les posts (si l'utilisateur est modérateur)

### 4. Points importants pour Reddit

- Reddit nécessite un `User-Agent` unique et descriptif
- **Les tokens Reddit expirent après 1 jour (24 heures)**
- Reddit supporte les refresh tokens pour les tokens permanents
- L'authentification basic est requise pour l'échange de tokens
- **Pas de contrôle sur la durée** : Reddit détermine la période de validité

### 5. URLs de l'API Reddit

- **Authorization**: `https://www.reddit.com/api/v1/authorize`
- **Token exchange**: `https://www.reddit.com/api/v1/access_token`
- **User profile**: `https://oauth.reddit.com/api/v1/me`

### 6. Test de l'intégration

1. Démarrer le backend FastAPI : `uvicorn app.main:app --reload --port 8000`
2. Aller sur la page comptes dans le frontend
3. Cliquer sur "Connecter un Nouveau Profil"
4. Sélectionner Reddit
5. Autoriser l'application sur Reddit
6. Vérifier que le compte apparaît dans la liste

## Fonctionnalités supportées

- ✅ Authentification OAuth2
- ✅ Récupération du profil utilisateur
- ✅ Tokens de 24 heures (par défaut Reddit)
- ✅ Refresh token disponible pour renouvellement
- 🔄 Publication de posts (à implémenter)
- 🔄 Lecture des messages privés (à implémenter)
- 🔄 Réponse aux commentaires (à implémenter)

## Gestion des tokens

### Durée de vie
- **Token d'accès** : 24 heures (défini par Reddit)
- **Refresh token** : Permanent (jusqu'à révocation utilisateur)
- **Pas de personnalisation** : Reddit contrôle la durée

### Renouvellement
- **Manuel** : Via le refresh token quand nécessaire
- **Interface** : Bouton "Re-auth" si token expiré
- **Automatique** : Possible mais pas implémenté (simplicité)
