# 🎨 Widget Chat IA SocialSync - Guide Complet

## Vue d'ensemble

Le **Widget Chat IA SocialSync** permet d'intégrer facilement un assistant IA sur n'importe quel site web. Les utilisateurs peuvent discuter avec une IA intelligente qui répond à leurs questions en temps réel.

## ✨ Fonctionnalités

### 🎯 **Widget JavaScript Intégrable**
- ✅ **Installation en 1 ligne** de code
- ✅ **Responsive** (mobile + desktop)
- ✅ **Personnalisable** (couleurs, position, textes)
- ✅ **Thèmes** light/dark
- ✅ **Animations** fluides

### 🤖 **IA Intégrée**
- ✅ **OpenAI GPT** (3.5-turbo, 4)
- ✅ **Anthropic Claude** 
- ✅ **Réponses intelligentes** personnalisées
- ✅ **Fallback responses** si l'IA est indisponible
- ✅ **Historique de conversation**

### 📊 **Analytics Avancées**
- ✅ **Nombre de conversations**
- ✅ **Temps de réponse IA**
- ✅ **Taux de résolution**
- ✅ **Questions fréquentes**
- ✅ **Satisfaction utilisateur**

## 🚀 Utilisation

### 1. **Créer un Widget**

```bash
curl -X POST "http://localhost:8000/api/widget/create" \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://mon-site.com",
    "widget_settings": {
      "theme": "light",
      "primary_color": "#007bff",
      "position": "bottom-right",
      "welcome_message": "Bonjour ! Comment puis-je vous aider ?",
      "company_name": "Mon Support",
      "ai_enabled": true,
      "ai_provider": "openai",
      "ai_model": "gpt-3.5-turbo"
    }
  }'
```

**Réponse :**
```json
{
  "success": true,
  "widget_id": "widget_123",
  "api_key": "wgt_abc123...",
  "embed_code": "<!-- Code à copier -->",
  "setup_instructions": { ... }
}
```

### 2. **Installer sur le Site Web**

Copiez le code fourni et collez-le **avant `</body>`** :

```html
<!-- SocialSync Chat Widget -->
<script>
  (function() {
    window.SocialSyncWidget = {
      widgetId: 'widget_123',
      apiKey: 'wgt_abc123...',
      apiUrl: 'http://localhost:8000'
    };
    
    var script = document.createElement('script');
    script.src = 'http://localhost:8000/static/widget/widget.js';
    script.async = true;
    
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'http://localhost:8000/static/widget/widget.css';
    
    document.head.appendChild(link);
    document.head.appendChild(script);
  })();
</script>
```

### 3. **Tester le Widget**

- ✅ Rechargez votre page
- ✅ Un bouton de chat apparaît en bas à droite
- ✅ Cliquez et testez une conversation
- ✅ L'IA répond automatiquement

## 🎨 Personnalisation

### **Couleurs et Thème**

```bash
curl -X PUT "http://localhost:8000/api/widget/update/widget_123" \
  -H "Content-Type: application/json" \
  -d '{
    "widget_settings": {
      "theme": "dark",
      "primary_color": "#28a745",
      "welcome_message": "🌙 Bonsoir ! Comment pouvons-nous vous aider ?"
    }
  }'
```

### **Position et Taille**

```json
{
  "position": "bottom-left",    // bottom-right, top-left, top-right
  "widget_size": "large",       // small, medium, large
  "auto_open": true,
  "auto_open_delay": 5000
}
```

### **Configuration IA**

```json
{
  "ai_provider": "openai",           // openai, anthropic
  "ai_model": "gpt-4",
  "ai_temperature": 0.7,             // 0.0 - 2.0
  "ai_max_tokens": 200,
  "ai_system_prompt": "Vous êtes un assistant commercial expert..."
}
```

## 📊 Analytics

### **Récupérer les Statistiques**

```bash
curl "http://localhost:8000/api/widget/analytics/widget_123?date_range=30d"
```

**Réponse :**
```json
{
  "widget_id": "widget_123",
  "total_conversations": 1247,
  "total_messages": 8934,
  "avg_response_time": 1.2,
  "ai_resolution_rate": 0.84,
  "user_satisfaction": 4.6,
  "top_questions": [
    {"question": "Quels sont vos horaires ?", "count": 89},
    {"question": "Comment puis-je annuler ?", "count": 67}
  ]
}
```

## 🛠️ Exemples d'Intégration

### **WordPress**
```php
// Dans functions.php
function add_socialsync_widget() {
    echo '<script>/* Code du widget */</script>';
}
add_action('wp_footer', 'add_socialsync_widget');
```

### **React.js**
```jsx
import { useEffect } from 'react';

function ChatWidget() {
  useEffect(() => {
    window.SocialSyncWidget = {
      widgetId: 'widget_123',
      apiKey: 'wgt_abc123...',
      apiUrl: 'http://localhost:8000'
    };
    
    const script = document.createElement('script');
    script.src = 'http://localhost:8000/static/widget/widget.js';
    document.head.appendChild(script);
    
    return () => {
      // Cleanup
      if (window.SocialSyncChatWidget) {
        window.SocialSyncChatWidget.destroy();
      }
    };
  }, []);
  
  return null;
}
```

### **Shopify**
```liquid
<!-- Dans theme.liquid avant </body> -->
{{ 'widget.css' | asset_url | stylesheet_tag }}
<script>
  // Code du widget
</script>
```

## 🔧 API Complète

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/widget/create` | POST | **Créer un nouveau widget** |
| `/api/widget/update/{id}` | PUT | **Mettre à jour la configuration** |
| `/api/widget/analytics/{id}` | GET | **Récupérer les statistiques** |
| `/api/widget/preview/{id}` | GET | **Aperçu HTML du widget** |
| `/api/widget/chat` | POST | **Traiter un message de chat** |
| `/api/widget/embed-code/{id}` | GET | **Récupérer le code embed** |
| `/api/widget/templates` | GET | **Templates de widgets** |
| `/api/widget/user-widgets` | GET | **Lister tous les widgets** |

## 🎭 Templates Prêts à l'Emploi

### **Template Minimal**
```json
{
  "theme": "light",
  "primary_color": "#6c757d", 
  "welcome_message": "Bonjour, comment puis-je vous aider ?",
  "company_name": "Support"
}
```

### **Template E-commerce**
```json
{
  "theme": "light",
  "primary_color": "#28a745",
  "welcome_message": "👋 Besoin d'aide pour votre commande ?",
  "ai_system_prompt": "Vous êtes un assistant e-commerce. Aidez avec les commandes, livraisons, retours..."
}
```

### **Template SaaS**
```json
{
  "theme": "dark",
  "primary_color": "#007bff",
  "welcome_message": "🚀 Questions sur notre plateforme ?",
  "ai_system_prompt": "Vous êtes un expert technique. Aidez avec l'utilisation de la plateforme..."
}
```

## 🔒 Sécurité

### **Domaines Autorisés**
```json
{
  "allowed_domains": ["https://mon-site.com", "https://www.mon-site.com"],
  "rate_limit": 10,  // messages par minute
  "max_conversation_length": 50
}
```

### **Validation des Domaines**
```bash
curl -X POST "http://localhost:8000/api/widget/validate-domain" \
  -d '{"widget_id": "widget_123", "domain": "https://test.com"}'
```

## 📱 Support Mobile

Le widget est **100% responsive** :
- ✅ **Détection automatique** mobile/desktop
- ✅ **Interface adaptée** pour mobile
- ✅ **Plein écran** sur petits écrans
- ✅ **Touch-friendly** boutons et interactions

## 🌍 Variables d'Environnement

```bash
# API Configuration
API_BASE_URL=http://localhost:8000
WIDGET_CDN_URL=http://localhost:8000/static/widget

# IA Configuration  
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 🎯 Cas d'Usage

### **Support Client**
- ✅ Réponses automatiques aux FAQ
- ✅ Collecte d'informations utilisateur
- ✅ Escalade vers agents humains

### **Lead Generation**
- ✅ Qualification des prospects
- ✅ Collecte d'emails/téléphones
- ✅ Recommandations produits

### **E-commerce**
- ✅ Assistance aux achats
- ✅ Suivi de commandes
- ✅ Support après-vente

### **SaaS/Tech**
- ✅ Aide technique
- ✅ Onboarding utilisateurs
- ✅ Documentation interactive

**Le widget est prêt à utiliser ! Testez-le dès maintenant sur votre site web.** 🚀
