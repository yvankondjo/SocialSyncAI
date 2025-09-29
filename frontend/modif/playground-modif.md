# Migration Playground Pages - Documentation des Modifications

## Vue d'Ensemble
Création complète des pages Playground pour les tests de modèles IA. Deux pages principales : Playground principal pour les tests individuels et Compare pour la comparaison côte à côte des modèles.

## Fichiers Créés

### Structure Playground
- **Page principale**: `/app/playground/page.tsx` + `loading.tsx`
- **Page Compare**: `/app/playground/compare/page.tsx` + `loading.tsx`

## Playground Principal - Interface de Test ✨

### Fonctionnalités Principales
- ✨ **Configuration en temps réel**: Paramètres de modèle avec preview immédiat
- ✨ **Chat interface**: Interface de test complète avec historique
- ✨ **Agent management**: Statut d'agent et sauvegarde de configuration
- ✨ **Instructions système**: Personnalisation des prompts système

### Architecture Playground
```typescript
interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

// Configuration state
const [model, setModel] = useState("gpt-4o")
const [temperature, setTemperature] = useState([0.7])
const [maxTokens, setMaxTokens] = useState([2048])
const [systemInstruction, setSystemInstruction] = useState(string)
const [agentStatus, setAgentStatus] = useState("trained")
```

### Layout à Deux Panneaux
- **Panneau gauche (384px)**: Configuration et paramètres
- **Panneau droit**: Interface de chat avec messages et input

### Fonctionnalités de Configuration
- ✨ **Sélection de modèle**: 5 modèles disponibles (GPT-4o, GPT-4, GPT-3.5, Gemini Pro, Claude 3)
- ✨ **Contrôles avancés**:
  - Temperature slider (0-2) avec labels dynamiques (Precise → Creative)
  - Max Tokens slider (256-4096)
  - System prompt personnalisable

### Système de Tabs
- **Configure & Test**: Configuration principale
- **Compare**: Lien vers la page de comparaison

### Agent Management
- ✨ **Statut d'agent**: Badge "trained" avec indicateur visuel
- ✨ **Sauvegarde**: Bouton "Save to Agent" pour persister la configuration
- ✨ **AI Actions**: Section pour les actions personnalisées (placeholder)

### Interface de Chat
- ✨ **Messages temps réel**: Simulation de réponses IA avec délai réaliste
- ✨ **Typing indicator**: Animation pendant la génération de réponse
- ✨ **Timestamps**: Affichage des heures de message
- ✨ **Refresh**: Bouton pour réinitialiser la conversation
- ✨ **Branding**: "Powered by SocialSync AI"

## Playground Compare - Comparaison de Modèles ✨

### Fonctionnalités Principales
- ✨ **Comparaison côte à côte**: Deux modèles testés simultanément
- ✨ **Métriques de performance**: Latence et tokens pour chaque réponse
- ✨ **Interface unifiée**: Input partagé pour des tests équitables
- ✨ **Export de données**: Sauvegarde des résultats de comparaison

### Architecture Compare
```typescript
interface Conversation {
  messages: Message[]
  totalLatency: number
  totalTokens: number
}

const [conversations, setConversations] = useState<{
  left: Conversation
  right: Conversation
}>({
  left: { messages: [], totalLatency: 0, totalTokens: 0 },
  right: { messages: [], totalLatency: 0, totalTokens: 0 }
})
```

### Sélection de Modèles
- ✨ **Modèle A (Gauche)** et **Modèle B (Droite)**
- ✨ **Validation**: Empêche la sélection du même modèle des deux côtés
- ✨ **Swap function**: Bouton pour échanger les modèles rapidement

### Métriques de Performance
- ✨ **Latence par message**: Temps de réponse individuel affiché
- ✨ **Latence moyenne**: Calcul automatique par modèle
- ✨ **Compteur de tokens**: Suivi de la consommation de tokens
- ✨ **Métriques totales**: Agrégation des statistiques

### Simulation Réaliste
```typescript
const generateMockResponse = (userInput: string, model: string): string => {
  const responses = {
    "gpt-4o": [
      "As GPT-4o, I can provide you with a comprehensive analysis...",
      "I understand your query completely. Let me break this down systematically...",
    ],
    "gpt-3.5-turbo": [
      "Thanks for your question! Here's a quick and efficient response...",
      "I can help with that. Here's a straightforward answer...",
    ],
    // ... autres modèles
  }
}
```

### Fonctionnalités d'Export
- ✨ **Export JSON**: Données complètes de comparaison
- ✨ **Métriques incluses**: Latence moyenne, tokens totaux, configuration
- ✨ **Timestamp**: Date et heure de la comparaison
- ✨ **Download automatique**: Fichier généré et téléchargé

### Actions de Contrôle
- ✨ **Reset**: Réinitialisation des deux conversations
- ✨ **Swap**: Échange des modèles sélectionnés
- ✨ **Export**: Sauvegarde des résultats

## Design et UX

### Layout Responsive
- **Playground**: Layout à deux colonnes avec panneau de configuration fixe
- **Compare**: Grid 2x2 avec sélection de modèles et interface de comparaison
- **Mobile adaptation**: Responsive design pour différentes tailles d'écran

### Interface de Chat Unifiée
```typescript
const renderMessage = (message: Message) => (
  <div className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
    {message.role === "assistant" && (
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
        <Bot className="w-4 h-4 text-primary" />
      </div>
    )}
    <div className="max-w-[70%] space-y-1">
      <div className="px-4 py-3 rounded-lg bg-muted">
        <p className="text-sm leading-relaxed">{message.content}</p>
      </div>
      <div className="text-xs text-muted-foreground">
        {formatTime(message.timestamp)}
        {message.latency && <span>{message.latency}ms</span>}
        {message.tokens && <span>{message.tokens} tokens</span>}
      </div>
    </div>
  </div>
)
```

### Indicateurs Visuels
- **Agent status**: Badge coloré pour le statut d'entraînement
- **Model badges**: "Model A" et "Model B" pour la comparaison
- **Performance metrics**: Affichage des métriques en temps réel
- **Loading states**: Animations de typing et spinners

## États de Chargement

### Loading States Complets
- **Configuration panel**: Skeletons pour tous les contrôles
- **Chat interface**: Messages et input avec placeholders
- **Comparison grids**: Structure préservée avec métriques
- **Performance areas**: Zones de métriques avec skeletons

### Animations
- **Typing indicator**: Points animés pendant la génération
- **Spinner states**: Indicateurs de chargement sur les boutons
- **Smooth transitions**: Animations fluides entre les états

## Simulation et Mock Data

### Réponses Différenciées par Modèle
```typescript
// Chaque modèle a des patterns de réponse distincts
"gpt-4o": "Comprehensive analysis with advanced reasoning...",
"gpt-3.5-turbo": "Quick and efficient response...",
"gemini-pro": "Multi-angle analysis with structured approach...",
"claude-3": "Thoughtful and nuanced response...",
```

### Métriques Réalistes
- **Latence variable**: 500-2500ms selon le modèle simulé
- **Tokens réalistes**: 50-150 tokens par réponse
- **Calculs automatiques**: Moyennes et totaux mis à jour en temps réel

## Intégration Future avec l'API

### Endpoints Playground
```typescript
// Configuration management
GET /api/playground/config
POST /api/playground/config
{
  model: string,
  temperature: number,
  maxTokens: number,
  systemInstruction: string
}

// Chat testing
POST /api/playground/chat
{
  messages: Message[],
  config: PlaygroundConfig
}

// Model comparison
POST /api/playground/compare
{
  leftModel: string,
  rightModel: string,
  message: string
}
```

### Agent Integration
```typescript
// Save configuration to agent
POST /api/agents/:id/config
{
  model: string,
  temperature: number,
  maxTokens: number,
  systemPrompt: string,
  status: "trained" | "training" | "draft"
}
```

## Fonctionnalités Avancées

### Configuration Dynamique
- **Real-time updates**: Changements appliqués immédiatement
- **Validation**: Vérification des paramètres avant envoi
- **Persistence**: Sauvegarde automatique des préférences
- **Presets**: Configurations prédéfinies pour différents cas d'usage

### Comparaison Avancée
- **Parallel processing**: Requêtes simultanées aux deux modèles
- **Performance tracking**: Métriques détaillées par modèle
- **Statistical analysis**: Comparaison des performances moyennes
- **Export formats**: JSON, CSV pour analyse externe

### Testing Features
- **Conversation history**: Historique complet des tests
- **Context preservation**: Maintien du contexte entre les messages
- **Error handling**: Gestion des erreurs de modèle
- **Rate limiting**: Gestion des limites d'API

## Performance et Optimisation

### Optimisations Interface
- **Lazy loading**: Chargement à la demande des composants
- **Memoization**: Cache des calculs de métriques
- **Debounced inputs**: Optimisation des changements de configuration
- **Virtual scrolling**: Pour les longues conversations

### Simulation Optimisée
- **Realistic delays**: Délais variables selon le modèle
- **Memory management**: Nettoyage des anciennes conversations
- **State optimization**: Gestion efficace des états multiples

## Tests Recommandés

### Playground Principal
- [ ] Configuration des paramètres de modèle
- [ ] Interface de chat avec messages bidirectionnels
- [ ] Sauvegarde de configuration vers agent
- [ ] System prompt personnalisable
- [ ] Refresh et reset des conversations
- [ ] Responsive design et navigation

### Playground Compare
- [ ] Sélection de modèles avec validation
- [ ] Comparaison côte à côte avec input partagé
- [ ] Métriques de performance en temps réel
- [ ] Export des données de comparaison
- [ ] Swap et reset des modèles
- [ ] Interface responsive sur mobile

### Intégration
- [ ] Connexion avec l'API de modèles IA
- [ ] Gestion des erreurs et timeouts
- [ ] Persistence des configurations
- [ ] Performance avec de longues conversations

Ces pages Playground offrent une interface complète pour tester et comparer les modèles IA avec des fonctionnalités avancées de configuration et d'analyse de performance, essentielles pour optimiser les performances du chatbot.