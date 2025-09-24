# Architecture Simplifiée - Gestion des Messages et RAG

## Vue d'ensemble

L'architecture a été simplifiée pour supprimer la gestion d'historique complexe et utiliser l'agent RAG avec son PostgresSaver intégré.

## Composants Principaux

### 1. MessageBatcher (Simplifié)
- **Rôle** : Grouper les messages entrants dans des batches de 15 secondes
- **Fonctionnalités** :
  - Ajout de messages au batch Redis
  - Gestion des timers de batch
  - Groupement des messages par type (texte, image, audio)
  - Suppression de toute gestion d'historique

### 2. RAGMessageConverter
- **Rôle** : Convertir les messages groupés au format RAG et gérer l'intégration
- **Fonctionnalités** :
  - Conversion des messages groupés au format RAG
  - Gestion du cache des agents RAG par utilisateur
  - Génération de réponses via l'agent RAG
  - Récupération de l'historique depuis PostgresSaver

### 3. BatchScanner (Mis à jour)
- **Rôle** : Traiter les batches dus et générer des réponses
- **Fonctionnalités** :
  - Récupération des conversations dues
  - Traitement des messages groupés
  - Utilisation du RAGMessageConverter pour les réponses
  - Envoi des réponses via les plateformes

### 4. RAGAgent (Avec user_id)
- **Rôle** : Agent RAG avec gestion d'historique par utilisateur
- **Fonctionnalités** :
  - Recherche dans les documents de l'utilisateur spécifique
  - Gestion d'historique via PostgresSaver
  - Génération de réponses contextuelles

## Flux de Données

```
Message Entrant
    ↓
MessageBatcher.add_message_to_batch()
    ↓ (Timer 15s)
BatchScanner._process_due_conversations()
    ↓
MessageBatcher.process_batch_for_conversation()
    ↓ (Groupement)
RAGMessageConverter.generate_response_with_rag()
    ↓
RAGAgent.invoke() (avec user_id)
    ↓ (PostgresSaver pour historique)
Réponse Générée
    ↓
Envoi via Plateforme
```

## Avantages de la Nouvelle Architecture

### ✅ **Simplicité**
- Suppression de la gestion d'historique complexe
- Un seul point de gestion d'historique (PostgresSaver)
- Code plus maintenable

### ✅ **Performance**
- Moins de requêtes Redis
- Cache des agents RAG par utilisateur
- Groupement efficace des messages

### ✅ **Sécurité**
- Isolation des données par utilisateur
- Chaque agent RAG ne voit que ses documents

### ✅ **Flexibilité**
- Facile d'ajouter de nouveaux types de messages
- Conversion modulaire des formats
- Gestion d'erreurs améliorée

## Structure des Messages Groupés

```json
{
  "message_data": {
    "role": "user",
    "content": "Texte groupé ou [array de contenu multimédia]"
  },
  "message_ids": ["id1", "id2", "id3"],
  "external_message_id": "last_external_id",
  "message_count": 3
}
```

## Configuration

### Variables d'Environnement
- `REDIS_URL` : URL Redis pour le batching
- `SUPABASE_DB_*` : Configuration base de données
- `OPENROUTER_API_KEY` : Clé API pour l'agent RAG

### Paramètres
- `batch_window_seconds` : 15 secondes (délai de groupement)
- `cache_ttl_hours` : 1 heure (TTL Redis)
- `max_tokens` : 6000 (limite tokens RAG)

## Migration

### Supprimé
- Table `conversations_message_groups` (plus utilisée)
- Méthodes de gestion d'historique dans MessageBatcher
- Cache Redis complexe pour l'historique

### Ajouté
- RAGMessageConverter pour l'intégration RAG
- Gestion d'historique via PostgresSaver
- Cache des agents RAG par utilisateur

## Utilisation

```python
# Le système fonctionne automatiquement
# Les messages sont groupés et traités via RAG

# Pour accéder à l'historique d'une conversation
history = await rag_message_converter.get_conversation_history(
    user_id="user_123",
    conversation_id="conv_456"
)

# Pour forcer la suppression d'un agent du cache
rag_message_converter.clear_user_agent("user_123")
```

Cette architecture simplifiée offre une meilleure performance, une maintenance plus facile et une intégration RAG plus robuste.
