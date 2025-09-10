# Configuration SocialSync

## Variables d'environnement à configurer

Pour que l'application fonctionne correctement, vous devez configurer les variables d'environnement suivantes :

### 1. Variables Frontend (.env.local)
```bash
# Configuration API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Configuration Supabase (À REMPLACER PAR VOS VALEURS)
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_clé_anon_supabase

# Configuration Frontend
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

### 2. Variables Backend (.env)
```bash
# Configuration Supabase Backend
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_ROLE_KEY=votre_clé_service_role
SUPABASE_JWT_SECRET=votre_secret_jwt

# Configuration Frontend URL
FRONTEND_URL=http://localhost:3000
```

## Comment obtenir les clés Supabase

1. **Allez sur** [https://supabase.com](https://supabase.com)
2. **Créez un nouveau projet** ou utilisez un projet existant
3. **Allez dans Settings > API**
4. **Copiez les valeurs suivantes :**
   - `Project URL` → `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` → `SUPABASE_SERVICE_ROLE_KEY`
   - `JWT Secret` → `SUPABASE_JWT_SECRET`

## Configuration OAuth Google

1. **Allez dans Authentication > Providers**
2. **Activez Google**
3. **Ajoutez votre domaine** dans les authorized domains
4. **Configurez l'URL de redirection** : `https://votre-domaine.com/auth/callback`

## Démarrage de l'application

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Test de connexion

1. **Allez sur** `http://localhost:3000`
2. **Cliquez sur** "Continuer avec Google"
3. **Connectez-vous** avec `yvankondjo8@gmail.com`
4. **Vous devriez être redirigé** vers le dashboard

## Fonctionnalités configurées

✅ **Authentification sécurisée** avec Google OAuth
✅ **Protection des routes** dashboard
✅ **Connexion aux comptes sociaux** (Instagram, WhatsApp, etc.)
✅ **Inbox multi-plateformes** avec envoi de messages
✅ **Dashboard dynamique** avec KPIs temps réel
✅ **Logos officiels** des plateformes
✅ **Gestion d'erreurs** améliorée
