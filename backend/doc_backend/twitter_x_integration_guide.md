# Guide d'Intégration Twitter/X

## Configuration Twitter/X OAuth 2.0

### 1. Création de l'application Twitter

1. Aller sur https://developer.twitter.com/en/portal/dashboard
2. Créer un nouveau projet ou utiliser un projet existant
3. Créer une nouvelle app dans le projet :
   - **App name**: SocialSync
   - **Description**: Application SocialSync pour gérer les comptes Twitter/X
   - **Website URL**: https://votre-site.com
   - **Callback URL**: `http://localhost:8000/api/social-accounts/connect/twitter/callback`

### 2. Configuration OAuth 2.0

1. Dans les paramètres de l'app, aller dans **User authentication settings**
2. **App type**: Web App
3. **App permissions**: 
   - Read and write (pour publier des tweets)
   - Read users (pour récupérer le profil)
4. **Callback URI**: `http://localhost:8000/api/social-accounts/connect/twitter/callback`
5. **Website URL**: https://votre-site.com

### 3. Variables d'environnement à ajouter

Ajouter dans votre fichier `.env` :

```env
# Twitter/X
TWITTER_CLIENT_ID=votre_client_id_twitter
TWITTER_CLIENT_SECRET=votre_client_secret_twitter
TWITTER_REDIRECT_URI=http://localhost:8000/api/social-accounts/connect/twitter/callback
```

### 4. Scopes autorisés

L'intégration Twitter demande les scopes suivants :
- `tweet.read` : Pour lire les tweets
- `tweet.write` : Pour publier des tweets
- `users.read` : Pour récupérer les informations du profil utilisateur
- `offline.access` : Pour obtenir un refresh token (accès permanent)

### 5. Points importants pour Twitter/X

- Twitter utilise OAuth 2.0 avec Basic Authentication pour l'échange de tokens
- Les tokens expirent après 2 heures par défaut
- Le refresh token permet de renouveler l'accès sans re-autorisation
- L'API v2 est utilisée pour les profils et tweets
- Certaines fonctionnalités nécessitent un plan payant (Essential+, Elevated, etc.)

### 6. URLs de l'API Twitter

- **Authorization**: `https://twitter.com/i/oauth2/authorize`
- **Token exchange**: `https://api.twitter.com/2/oauth2/token`
- **User profile**: `https://api.twitter.com/2/users/me`
- **Tweet publication**: `https://api.twitter.com/2/tweets`

### 7. Limitations selon le plan

**Plan gratuit** (limité) :
- 1,500 tweets publiés par mois
- Lecture limitée

**Plan Essential ($100/mois)** :
- Accès complet aux APIs v2
- Publication sans limite de volume raisonnable
- Accès aux DMs

**Plan Elevated** :
- Accès aux APIs premium
- Metriques avancées

### 8. Test de l'intégration

1. Démarrer le backend FastAPI : `uvicorn app.main:app --reload --port 8000`
2. Aller sur la page comptes dans le frontend
3. Cliquer sur "Connecter un Nouveau Profil"
4. Sélectionner X (Twitter)
5. Autoriser l'application sur Twitter
6. Vérifier que le compte apparaît dans la liste

**Note** : Twitter utilise la valeur `'twitter'` dans l'ENUM (déjà présent)

## Fonctionnalités supportées

- ✅ Authentification OAuth 2.0
- ✅ Récupération du profil utilisateur (nom, username, photo)
- ✅ Tokens avec refresh automatique
- 🔄 Publication de tweets (à implémenter)
- 🔄 Lecture des DMs (à implémenter - nécessite plan payant)
- 🔄 Réponse aux mentions (à implémenter)

## Troubleshooting

- **403 Forbidden** : Vérifier que les scopes sont bien configurés dans l'app Twitter
- **Invalid client** : Vérifier les Client ID/Secret
- **Redirect URI mismatch** : Vérifier que l'URL de callback correspond exactement
- **Rate limits** : Twitter a des limites strictes, implémenter un système de retry
