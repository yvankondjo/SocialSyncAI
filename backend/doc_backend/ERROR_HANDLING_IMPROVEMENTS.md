# Améliorations de la Gestion d'Erreurs pour les LLMs

## Vue d'ensemble

Les services `FindAnswers` et `Retriever` ont été améliorés avec une gestion d'erreurs robuste et explicite, optimisée pour les interactions avec les LLMs (Large Language Models).

## Améliorations Apportées

### 1. Exceptions Personnalisées

#### FindAnswersError
```python
class FindAnswersError(Exception):
    def __init__(self, message: str, error_type: str = "UNKNOWN", details: dict = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)
```

#### RetrieverError
```python
class RetrieverError(Exception):
    def __init__(self, message: str, error_type: str = "UNKNOWN", details: dict = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)
```

### 2. Types d'Erreurs Définis

#### FindAnswers - Types d'erreurs
- `INVALID_USER_ID`: User ID manquant ou invalide
- `DATABASE_CONNECTION_ERROR`: Erreur de connexion à la base de données
- `MISSING_API_KEY`: Clé API manquante
- `LLM_INITIALIZATION_ERROR`: Erreur d'initialisation du LLM
- `INVALID_QUESTION`: Question vide ou invalide
- `QUESTION_RETRIEVAL_ERROR`: Erreur lors de la récupération des questions
- `OPENAI_API_ERROR`: Erreur de l'API OpenAI/OpenRouter
- `LLM_RESPONSE_VALIDATION_ERROR`: Erreur de validation de la réponse LLM
- `LLM_PROCESSING_ERROR`: Erreur de traitement LLM
- `UNICODE_ENCODING_ERROR`: Erreur d'encodage Unicode
- `ANSWER_PROCESSING_ERROR`: Erreur de traitement de la réponse
- `UNEXPECTED_ERROR`: Erreur inattendue

#### Retriever - Types d'erreurs
- `INVALID_USER_ID`: User ID manquant ou invalide
- `DATABASE_CONNECTION_ERROR`: Erreur de connexion à la base de données
- `EMBEDDING_INITIALIZATION_ERROR`: Erreur d'initialisation des embeddings
- `EMPTY_TEXTS_LIST`: Liste de textes vide
- `INVALID_TEXT_TYPE`: Type de texte invalide
- `EMBEDDING_ERROR`: Erreur d'embedding
- `INVALID_QUERY`: Requête vide ou invalide
- `INVALID_K_VALUE`: Valeur k invalide
- `INVALID_TYPE`: Type de recherche invalide
- `INVALID_QUERY_LANG`: Langue de requête invalide
- `EMBEDDING_GENERATION_ERROR`: Erreur de génération d'embedding
- `DATABASE_API_ERROR`: Erreur API de base de données
- `SEARCH_ERROR`: Erreur de recherche
- `INVALID_FAQ_WEIGHT`: Poids FAQ invalide
- `INVALID_DOC_WEIGHT`: Poids document invalide
- `FAQ_RETRIEVAL_ERROR`: Erreur de récupération FAQ
- `KNOWLEDGE_RETRIEVAL_ERROR`: Erreur de récupération de connaissances
- `RESULT_COMBINATION_ERROR`: Erreur de combinaison de résultats
- `UNEXPECTED_ERROR`: Erreur inattendue

### 3. Validation des Paramètres

Chaque fonction valide maintenant ses paramètres d'entrée :

```python
# Exemple de validation dans retrieve_from_knowledge_chunks
if not query or not query.strip():
    raise RetrieverError(
        "Query cannot be empty or only whitespace",
        error_type="INVALID_QUERY",
        details={"query": query}
    )

if k <= 0:
    raise RetrieverError(
        "Number of results (k) must be positive",
        error_type="INVALID_K_VALUE",
        details={"k": k}
    )
```

### 4. Gestion des Erreurs Spécifiques

Les erreurs sont maintenant capturées et transformées en exceptions explicites :

```python
try:
    result = self.llm.with_structured_output(_AnswerSchema).invoke(prompt)
except OpenAIError as e:
    raise FindAnswersError(
        f"OpenAI API error during answer generation: {str(e)}",
        error_type="OPENAI_API_ERROR",
        details={"question": question, "model": self.model_name, "original_error": str(e)}
    )
```

### 5. Détails Contextuels

Chaque erreur inclut des détails contextuels pour faciliter le débogage :

```python
{
    "error_type": "DATABASE_API_ERROR",
    "message": "Database API error during knowledge chunks search: ...",
    "details": {
        "query": "test query",
        "type": "hybrid",
        "user_id": "user123",
        "original_error": "..."
    }
}
```

## Avantages pour les LLMs

### 1. Messages d'Erreur Structurés
Les LLMs peuvent facilement comprendre le type d'erreur et ses causes.

### 2. Contexte Détaillé
Les détails fournis permettent aux LLMs de suggérer des solutions appropriées.

### 3. Types d'Erreurs Standardisés
Les types d'erreurs permettent aux LLMs de catégoriser et traiter les erreurs de manière cohérente.

### 4. Suggestions Automatiques
Les types d'erreurs peuvent être mappés à des suggestions spécifiques.

## Utilisation

### Gestion d'Erreurs Basique
```python
try:
    find_answers = FindAnswers(user_id="valid-user")
    answer = find_answers.find_answers("What is the meaning of life?")
except FindAnswersError as e:
    print(f"Erreur: {e.error_type} - {e.message}")
    print(f"Détails: {e.details}")
```

### Gestion d'Erreurs pour LLM
```python
def handle_error_for_llm(error):
    if isinstance(error, (FindAnswersError, RetrieverError)):
        return {
            "error": True,
            "error_type": error.error_type,
            "message": error.message,
            "details": error.details,
            "suggestions": get_error_suggestions(error.error_type)
        }
    return {"error": True, "message": str(error)}
```

## Tests

Exécutez les exemples de gestion d'erreurs :

```bash
python backend/app/services/error_examples.py
```

## Migration

Les changements sont rétrocompatibles. Le code existant continuera de fonctionner, mais bénéficiera maintenant d'une meilleure gestion d'erreurs.

## Recommandations

1. **Toujours capturer les exceptions spécifiques** avant les exceptions génériques
2. **Utiliser les types d'erreurs** pour implémenter une logique de récupération
3. **Logger les détails** pour faciliter le débogage
4. **Fournir des suggestions** basées sur le type d'erreur
