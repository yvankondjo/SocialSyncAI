# Endpoints API Backend SocialSync - Référence Complète

## 🌐 Vue d'ensemble de l'API

**Base URL** : `http://localhost:8000` (ou votre URL de production)
**Version** : v1.0.0
**Authentification** : JWT Bearer Token (Supabase)

## 🔐 Authentification et Sécurité

### Headers Requis
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Récupération du Token
```typescript
// Via Supabase Client
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;
```

## 📱 Gestion des Comptes de Réseaux Sociaux

### Base Path : `/api/social-accounts`

#### 1. Obtenir l'URL d'Autorisation OAuth
```http
GET /api/social-accounts/connect/{platform}
```

**Paramètres :**
- `platform` : `instagram`, `tiktok`, `youtube`, `twitter`, `reddit`, `facebook`, `linkedin`, `whatsapp`

**Réponse :**
```json
{
  "authorization_url": "https://api.instagram.com/oauth/authorize?..."
}
```

**Utilisation :**
```typescript
const response = await fetch(`/api/social-accounts/connect/instagram`);
const { authorization_url } = await response.json();
window.location.href = authorization_url;
```

#### 2. Gérer le Callback OAuth
```http
GET /api/social-accounts/connect/{platform}/callback?code={code}&state={state}
```

**Paramètres Query :**
- `code` : Code d'autorisation OAuth
- `state` : JWT sécurisé avec user_id et expiration

**Comportement :**
- Redirection automatique vers `/dashboard/accounts?success=true&platform={platform}`
- En cas d'erreur : `/dashboard/accounts?error={message}&platform={platform}`

#### 3. Lister les Comptes Connectés
```http
GET /api/social-accounts/
```

**Réponse :**
```json
[
  {
    "id": "acc_123",
    "platform": "instagram",
    "account_id": "178414123456789",
    "username": "monentreprise",
    "display_name": "Mon Entreprise",
    "profile_url": "https://instagram.com/monentreprise",
    "access_token": "IGQWR...",
    "refresh_token": "IGQWR...",
    "token_expires_at": "2024-12-20T10:00:00Z",
    "is_active": true,
    "user_id": "user_456",
    "created_at": "2024-12-19T10:00:00Z",
    "updated_at": "2024-12-19T10:00:00Z"
  }
]
```

#### 4. Supprimer un Compte
```http
DELETE /api/social-accounts/{account_id}
```

## 💬 Gestion des Conversations et Messages

### Base Path : `/api/conversations`

#### 1. Lister les Conversations
```http
GET /api/conversations?channel={channel}&limit={limit}
```

**Paramètres Query :**
- `channel` (optionnel) : `whatsapp`, `instagram`, `all`
- `limit` (optionnel) : `50` (max 100)

**Réponse :**
```json
{
  "conversations": [
    {
      "id": "conv_123",
      "channel": "instagram",
      "customer_name": "Jean Dupont",
      "customer_identifier": "user_789",
      "last_message_at": "2024-12-19T15:30:00Z",
      "last_message_snippet": "Bonjour, j'ai une question...",
      "unread_count": 2,
      "social_account_id": "acc_123"
    }
  ],
  "total": 1
}
```

#### 2. Récupérer les Messages d'une Conversation
```http
GET /api/conversations/{conversation_id}/messages?limit={limit}
```

**Paramètres Query :**
- `limit` (optionnel) : `100` (max 200)

**Réponse :**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "conversation_id": "conv_123",
      "direction": "inbound",
      "content": "Bonjour, j'ai une question sur vos produits",
      "created_at": "2024-12-19T15:30:00Z",
      "sender_id": "user_789",
      "is_from_agent": false
    }
  ],
  "total": 1
}
```

#### 3. Envoyer un Message
```http
POST /api/conversations/{conversation_id}/messages
```

**Body :**
```json
{
  "content": "Bonjour ! Comment puis-je vous aider ?",
  "message_type": "text"
}
```

**Réponse :**
```json
{
  "id": "msg_124",
  "conversation_id": "conv_123",
  "direction": "outbound",
  "content": "Bonjour ! Comment puis-je vous aider ?",
  "created_at": "2024-12-19T15:35:00Z",
  "sender_id": "user_456",
  "is_from_agent": true
}
```

#### 4. Marquer une Conversation comme Lue
```http
PATCH /api/conversations/{conversation_id}/read
```

**Réponse :**
```json
{
  "success": true
}
```

## 📸 API Instagram

### Base Path : `/api/instagram`

#### 1. Valider les Credentials
```http
POST /api/instagram/validate-credentials
```

**Body :**
```json
{
  "access_token": "IGQWR...",
  "page_id": "178414123456789"
}
```

**Réponse :**
```json
{
  "valid": true,
  "page_name": "Mon Entreprise",
  "page_id": "178414123456789",
  "permissions": ["instagram_basic", "instagram_manage_comments"]
}
```

#### 2. Envoyer un Message Direct
```http
POST /api/instagram/send-dm
```

**Body :**
```json
{
  "access_token": "IGQWR...",
  "page_id": "178414123456789",
  "recipient_ig_id": "user_789",
  "text": "Bonjour ! Comment puis-je vous aider ?"
}
```

**Réponse :**
```json
{
  "success": true,
  "message_id": "msg_123"
}
```

#### 3. Publier un Post
```http
POST /api/instagram/publish-post
```

**Body :**
```json
{
  "access_token": "IGQWR...",
  "page_id": "178414123456789",
  "image_url": "https://example.com/image.jpg",
  "caption": "Nouveau produit disponible ! 🎉"
}
```

**Réponse :**
```json
{
  "success": true,
  "post_id": "post_123",
  "container_id": "container_456"
}
```

#### 4. Publier une Story
```http
POST /api/instagram/publish-story
```

**Body :**
```json
{
  "access_token": "IGQWR...",
  "page_id": "178414123456789",
  "image_url": "https://example.com/story.jpg"
}
```

**Réponse :**
```json
{
  "success": true,
  "story_id": "story_123",
  "container_id": "container_789"
}
```

#### 5. Répondre à un Commentaire
```http
POST /api/instagram/reply-comment
```

**Body :**
```json
{
  "access_token": "IGQWR...",
  "page_id": "178414123456789",
  "comment_id": "comment_123",
  "text": "Merci pour votre commentaire ! 😊"
}
```

**Réponse :**
```json
{
  "success": true,
  "reply_id": "reply_123"
}
```

#### 6. Envoyer des Messages en Lot
```http
POST /api/instagram/send-dm-batch
```

**Body :**
```json
{
  "access_token": "IGQWR...",
  "page_id": "178414123456789",
  "recipients": ["user_789", "user_790"],
  "text": "Nouvelle offre spéciale ! 🎁"
}
```

**Réponse :**
```json
{
  "success": true,
  "sent_count": 2,
  "failed_count": 0,
  "results": [
    {
      "recipient": "user_789",
      "success": true,
      "message_id": "msg_123"
    }
  ]
}
```

#### 7. Récupérer les Conversations
```http
GET /api/instagram/conversations
```

**Réponse :**
```json
{
  "conversations": [
    {
      "id": "conv_123",
      "participants": ["user_789"],
      "last_message": "Bonjour !",
      "unread_count": 1
    }
  ]
}
```

#### 8. Webhook Instagram
```http
POST /api/instagram/webhook
```

**Headers :**
```http
X-Hub-Signature-256: sha256=...
X-Hub-Signature: sha1=...
```

**Body :** Payload Meta Webhook (messages, comments, mentions)

## 📱 API WhatsApp

### Base Path : `/api/whatsapp`

#### 1. Valider les Credentials
```http
POST /api/whatsapp/validate-credentials
```

**Body :**
```json
{
  "access_token": "EAA...",
  "phone_number_id": "123456789"
}
```

**Réponse :**
```json
{
  "valid": true,
  "phone_number": "+33123456789",
  "business_name": "Mon Entreprise",
  "permissions": ["messages", "messaging"]
}
```

#### 2. Envoyer un Message Texte
```http
POST /api/whatsapp/send-text
```

**Body :**
```json
{
  "to": "+33123456789",
  "text": "Bonjour ! Comment puis-je vous aider ?"
}
```

**Réponse :**
```json
{
  "messaging_product": "whatsapp",
  "contacts": [
    {
      "input": "+33123456789",
      "wa_id": "33123456789"
    }
  ],
  "messages": [
    {
      "id": "msg_123"
    }
  ],
  "message_type": "text"
}
```

#### 3. Envoyer un Template
```http
POST /api/whatsapp/send-template
```

**Body :**
```json
{
  "to": "+33123456789",
  "template_name": "hello_world",
  "language_code": "fr_FR",
  "components": [
    {
      "type": "body",
      "parameters": [
        {
          "type": "text",
          "text": "Jean"
        }
      ]
    }
  ]
}
```

#### 4. Envoyer un Média
```http
POST /api/whatsapp/send-media
```

**Body :**
```json
{
  "to": "+33123456789",
  "media_type": "image",
  "media_url": "https://example.com/image.jpg",
  "caption": "Voici notre nouveau produit !"
}
```

#### 5. Envoyer en Lot
```http
POST /api/whatsapp/send-batch
```

**Body :**
```json
{
  "messages": [
    {
      "to": "+33123456789",
      "text": "Message 1"
    },
    {
      "to": "+33123456790",
      "text": "Message 2"
    }
  ]
}
```

#### 6. Profil Business
```http
GET /api/whatsapp/business-profile
```

**Réponse :**
```json
{
  "business_name": "Mon Entreprise",
  "phone_number": "+33123456789",
  "address": "123 Rue de la Paix, Paris",
  "description": "Description de l'entreprise"
}
```

#### 7. Webhook WhatsApp
```http
POST /api/whatsapp/webhook
```

**Headers :**
```http
X-Hub-Signature-256: sha256=...
X-Hub-Signature: sha1=...
```

**Body :** Payload Meta Webhook (messages, status updates)

## 📊 API Analytics

### Base Path : `/api/analytics`

#### 1. Synchroniser les Analytics d'un Contenu
```http
POST /api/analytics/sync/{content_id}
```

**Réponse :**
```json
{
  "content_id": "content_123",
  "sync_status": "completed",
  "metrics": {
    "likes": 150,
    "shares": 25,
    "comments": 12,
    "impressions": 5000
  }
}
```

#### 2. Synchroniser les Analytics Utilisateur
```http
POST /api/analytics/sync/user/{user_id}?days={days}
```

**Paramètres Query :**
- `days` (optionnel) : `7` (défaut)

**Réponse :**
```json
{
  "message": "Analytics sync started in background",
  "user_id": "user_456",
  "period_days": 7
}
```

#### 3. Historique des Analytics
```http
GET /api/analytics/history/{content_id}?days={days}
```

**Paramètres Query :**
- `days` (optionnel) : `30` (défaut)

**Réponse :**
```json
{
  "content_id": "content_123",
  "history": [
    {
      "recorded_at": "2024-12-19T10:00:00Z",
      "platform": "instagram",
      "likes": 150,
      "shares": 25,
      "comments": 12,
      "impressions": 5000,
      "reach": 3500,
      "clicks": 45,
      "conversions": 3,
      "engagement_rate": 0.075
    }
  ]
}
```

#### 4. Tendances Analytics
```http
GET /api/analytics/trends/{user_id}?days={days}
```

**Paramètres Query :**
- `days` (optionnel) : `30` (défaut)

**Réponse :**
```json
{
  "user_id": "user_456",
  "period_days": 30,
  "trends": [
    {
      "date": "2024-12-19",
      "total_likes": 150,
      "total_shares": 25,
      "total_comments": 12,
      "total_impressions": 5000,
      "avg_engagement_rate": 0.075
    }
  ]
}
```

## 🌐 Widget Web

### Base Path : `/api/web-widget`

#### 1. Configuration du Widget
```http
GET /api/web-widget/config/{widget_id}
```

**Réponse :**
```json
{
  "widget_id": "widget_123",
  "organization_id": "org_456",
  "name": "Support Chat",
  "primary_color": "#3B82F6",
  "logo_url": "https://example.com/logo.png",
  "welcome_message": "Bonjour ! Comment puis-je vous aider ?",
  "enabled": true
}
```

#### 2. Envoyer un Message via Widget
```http
POST /api/web-widget/messages
```

**Body :**
```json
{
  "widget_id": "widget_123",
  "visitor_id": "visitor_789",
  "message": "Bonjour, j'ai une question",
  "visitor_info": {
    "name": "Jean Dupont",
    "email": "jean@example.com"
  }
}
```

#### 3. Fichiers Statiques
```http
GET /api/web-widget/static/{filename}
```

**Fichiers disponibles :**
- `widget.js` - Script d'intégration
- `widget.css` - Styles du widget
- `widget.html` - Template HTML

#### 4. Webhook Widget
```http
POST /api/web-widget/webhook
```

**Body :** Événements du widget (nouveaux messages, statuts)

## 🔧 Endpoints Utilitaires

### 1. Vérification de Santé
```http
GET /health
```

**Réponse :**
```json
{
  "status": "healthy",
  "service": "socialsyncai-api"
}
```

### 2. Versions des APIs
```http
GET /api/versions
```

**Réponse :**
```json
{
  "whatsapp": {
    "graph_api_version": "v23.0",
    "base_url": "https://graph.facebook.com/v23.0",
    "webhook_compatible": true,
    "notes": "Cohérent avec les webhooks Meta"
  },
  "instagram": {
    "graph_api_version": "v23.0",
    "base_url": "https://graph.instagram.com/v23.0",
    "webhook_compatible": true,
    "notes": "Cohérent avec les webhooks Meta"
  },
  "api_info": {
    "socialsync_version": "1.0.0",
    "last_updated": "2024-12-19",
    "compatibility": "Toutes les APIs utilisent la même version v23.0"
  }
}
```

## 📝 Gestion des Erreurs

### Codes d'Erreur Communs

#### 400 - Bad Request
```json
{
  "detail": "Invalid request data"
}
```

#### 401 - Unauthorized
```json
{
  "detail": "Non authentifié"
}
```

#### 403 - Forbidden
```json
{
  "detail": "Access denied"
}
```

#### 404 - Not Found
```json
{
  "detail": "Platform not supported"
}
```

#### 500 - Internal Server Error
```json
{
  "detail": "Erreur lors de la récupération des conversations: Database connection failed"
}
```

### Gestion des Erreurs dans le Frontend

```typescript
try {
  const response = await fetch('/api/conversations');
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `Erreur ${response.status}`);
  }
  return await response.json();
} catch (error) {
  console.error('Erreur API:', error);
  // Gérer l'erreur dans l'UI
}
```

## 🔄 Webhooks et Intégrations

### Configuration des Webhooks

#### Instagram
- **URL** : `https://votre-domaine.com/api/instagram/webhook`
- **Verify Token** : Configuré dans les paramètres Meta
- **Champs** : `messages`, `mentions`, `comments`

#### WhatsApp
- **URL** : `https://votre-domaine.com/api/whatsapp/webhook`
- **Verify Token** : Configuré dans les paramètres Meta
- **Champs** : `messages`, `message_deliveries`, `message_reads`

### Validation des Webhooks

```typescript
// Vérification de la signature Meta
const signature = request.headers['x-hub-signature-256'];
const expectedSignature = crypto
  .createHmac('sha256', appSecret)
  .update(JSON.stringify(body))
  .digest('hex');

if (signature !== `sha256=${expectedSignature}`) {
  throw new Error('Invalid webhook signature');
}
```

## 🚀 Utilisation dans le Frontend

### Client API Centralisé

```typescript
// lib/api.ts
export const api = {
  get: (endpoint: string) => apiCall(endpoint, { method: "GET" }),
  post: (endpoint: string, data: unknown) => 
    apiCall(endpoint, { method: "POST", body: JSON.stringify(data) }),
  put: (endpoint: string, data: unknown) => 
    apiCall(endpoint, { method: "PUT", body: JSON.stringify(data) }),
  delete: (endpoint: string) => apiCall(endpoint, { method: "DELETE" }),
};

// Utilisation
const conversations = await api.get('/conversations?channel=instagram');
const message = await api.post(`/conversations/${id}/messages`, { content: 'Hello' });
```

### Hooks React avec React Query

```typescript
// Hooks personnalisés
const { conversations, loading, error } = useConversations();
const { messages, sendMessage } = useMessages(conversationId);

// Mutations
const sendMessageMutation = useMutation({
  mutationFn: (content: string) => 
    api.post(`/conversations/${conversationId}/messages`, { content }),
  onSuccess: () => {
    queryClient.invalidateQueries(['messages', conversationId]);
  },
});
```

Cette documentation couvre tous les endpoints API disponibles dans le backend SocialSync, fournissant une référence complète pour l'intégration dans votre nouveau projet.





