# Configuration de l'Escalade vers un Humain

Ce document explique comment configurer le système d'escalade avec envoi d'emails via Resend.

## 🚀 Configuration Requise

### 1. Compte Resend
1. Allez sur [resend.com](https://resend.com) et créez un compte
2. Vérifiez votre domaine (your-app.vercel.app)
3. Récupérez votre API key dans les paramètres

### 2. Variables d'Environnement

Ajoutez ces variables à votre fichier `.env` :

```bash
# Clé API Resend (obligatoire)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Configuration des emails
FROM_EMAIL=noreply@your-app.vercel.app
SUPPORT_EMAIL=support@yourdomain.com

# Configuration des liens sécurisés
JWT_SECRET_KEY=votre-cle-jwt-super-secrete
FRONTEND_URL=https://your-app.vercel.app
LINK_EXPIRATION_HOURS=24
```

**🔄 Changement important :** Contrairement à ce qui était prévu initialement, l'email d'escalade est envoyé **au client/utilisateur** (pas à l'équipe support). L'utilisateur reçoit une notification lui indiquant qu'un humain va prendre en charge sa conversation.

### 3. Générer une Clé JWT Sécurisée

```bash
# En Python :
import secrets
print(secrets.token_hex(32))  # Copiez cette valeur
```

## 📧 Fonctionnement du Système

### Flux d'Escalade

1. **Client demande aide humaine** → Via l'interface de chat avec l'IA
2. **IA détecte la demande** → Appelle l'outil d'escalation
3. **Création de l'escalade** → Enregistrement en base + désactivation IA
4. **Génération du lien sécurisé** → Token JWT pour l'équipe de support (expire dans 24h)
5. **Envoi d'email** → Template HTML envoyé **à l'équipe de support**
6. **Équipe de support** → Reçoit l'email avec le lien pour accéder à la conversation du client

### Template d'Email

L'email envoyé à l'équipe de support contient :
- 📧 Alerte "Customer Support Request"
- 📝 Raison de l'escalade ({{ reason }})
- 🔗 Lien sécurisé vers la conversation du client
- ⏰ Expiration du lien (24h)

## 🛠️ Utilisation dans le Code

### Créer une Escalade

```python
from app.services.escalation import Escalation

escalation_service = Escalation(user_id, conversation_id)
escalation_id = await escalation_service.create_escalation(
    message="Je ne comprends pas cette réponse",
    confidence=85.5,
    reason="Demande complexe nécessitant expertise humaine"
)
```

### Vérifier un Lien d'Escalade

```python
from app.services.link_service import LinkService

link_service = LinkService()
payload = link_service.verify_conversation_token(token_from_url)

if payload:
    # Token valide, accès autorisé
    conversation_id = payload['conversation_id']
    user_id = payload['user_id']
else:
    # Token invalide ou expiré
    return "Lien expiré ou invalide"
```

## 🔒 Sécurité

- **Liens temporaires** : Expiration automatique après 24h
- **JWT signé** : Impossible de falsifier les tokens
- **Vérification d'accès** : Seul l'utilisateur propriétaire peut accéder
- **Logs complets** : Traçabilité des accès

## 📊 Monitoring

### Métriques à Surveiller

1. **Taux de succès d'envoi** : Emails délivrés vs échoués
2. **Temps de réponse** : Délai entre escalade et première réponse
3. **Satisfaction client** : Feedback sur la qualité du support
4. **Fréquence d'escalade** : Taux d'escalades par conversation

### Dashboard Resend

- Taux d'ouverture des emails
- Clics sur les liens de conversation
- Erreurs de livraison
- Géolocalisation des ouvertures

## 🐛 Dépannage

### Email Non Reçu

1. Vérifiez la configuration Resend
2. Vérifiez les variables d'environnement
3. Consultez les logs du serveur
4. Testez avec l'API Resend directement

### Lien Expiré

1. Les liens expirent après 24h (configurable)
2. Vérifiez la variable `LINK_EXPIRATION_HOURS`
3. Les utilisateurs doivent répondre rapidement

### Erreur JWT

1. Vérifiez `JWT_SECRET_KEY`
2. Assurez-vous qu'elle est identique partout
3. Les tokens sont sensibles à la casse

## 🚀 Déploiement sur Vercel

### Variables d'Environnement Vercel

```bash
# Dans le dashboard Vercel > Project Settings > Environment Variables
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JWT_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@your-app.vercel.app
SUPPORT_EMAIL=support@yourdomain.com
FRONTEND_URL=https://your-app.vercel.app
LINK_EXPIRATION_HOURS=24
```

### Domain Setup

1. Vérifiez votre domaine sur Resend
2. Ajoutez les enregistrements DNS si nécessaire
3. Testez l'envoi d'email

## 🧪 Test du Système

### Test Automatique

```bash
cd backend
python test_escalation.py
```

### Test Manuel via API

```bash
# 1. Créer une escalade de test
curl -X POST "http://localhost:8000/support/escalations/test" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "votre_conversation_id",
    "message": "Message de test",
    "confidence": 85.0,
    "reason": "Test du système"
  }'

# 2. Vérifier que l'escalade est créée
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/support/escalations"

# 3. Vérifier les logs pour les emails envoyés
```

### Vérifications Post-Test

- ✅ L'escalade est créée en base (`support_escalations`)
- ✅ La conversation a `ai_mode = "OFF"`
- ✅ Un email est envoyé à l'équipe de support (vérifiez Resend dashboard)
- ✅ Le lien JWT permet à l'équipe de support d'accéder à la conversation du client
- ✅ Le template HTML contient la raison de l'escalade
- ✅ Le lien expire dans 24h

## ⚖️ Conformité Légal (RGPD/CAN-SPAM)

Ces emails sont des **notifications transactionnelles** (demandes de support client), donc :
- Pas de lien de désinscription obligatoire
- Catégorisés comme "service communications"
- Exemptés des règles marketing

**Cependant**, si vous voulez ajouter des liens de désinscription, les endpoints existent déjà dans le code.

## 📈 Optimisations Futures

- **Webhook Resend** : Recevoir les événements d'email
- **Templates dynamiques** : Différents templates selon le type d'escalade
- **Analytics avancés** : Temps de réponse moyen, satisfaction
- **Auto-réponse** : Accusés de réception automatiques
- **Escalade intelligente** : Routage selon l'expertise requise
