# 🔍 Guide d'Intégration LangSmith - SocialSyncAI

## 🎯 Pourquoi LangSmith ?

LangSmith est l'outil officiel de monitoring pour LangChain/LangGraph. Il offre :

- **Tracing complet** : Visualisation de chaque étape de tes agents RAG
- **Métriques détaillées** : Latence, tokens, coût par invocation
- **Monitoring des erreurs** : Stack traces et contexte complet
- **Optimisation** : A/B testing des prompts et modèles
- **Alertes** : Notifications sur les anomalies de performance

## 📋 Installation et Configuration

### 1. Installation des dépendances

```bash
pip install langsmith langchain
```

### 2. Configuration environnement

```bash
# .env
LANGCHAIN_API_KEY=lsv2_pt_your_key_here
LANGCHAIN_PROJECT=socialsync-ai-prod
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_TRACING_V2=true

# Optionnel - pour les environnements
LANGCHAIN_ENV=production
```

### 3. Obtenir une clé API LangSmith

1. **Créer un compte** : [smith.langchain.com](https://smith.langchain.com)
2. **Aller dans Settings** → API Keys
3. **Créer une clé** avec les permissions appropriées
4. **Copier la clé** dans ton `.env`

## 🔧 Intégration dans le Code

### 1. Configuration globale (optionnel)

```python
# app/__init__.py ou main.py
import os
from langsmith import Client

# Configuration automatique via variables d'environnement
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "socialsync-ai-prod")

# Client pour les opérations avancées
langsmith_client = Client()
```

### 2. Monitoring automatique

**LangSmith s'intègre automatiquement** avec ton agent RAG existant :

```python
# app/services/rag_agent.py - Pas de modification nécessaire !
from langchain_openai import ChatOpenAI

# LangSmith trace automatiquement :
# - Toutes les invocations LLM
# - Les appels aux tools (search_files)
# - Les erreurs et timeouts
# - Les métriques de tokens

llm = ChatOpenAI(
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url="https://openrouter.ai/api/v1",
    model="gpt-4o-mini"
)
```

## 📊 Métriques Collectées

### Métriques de base
- **Durée totale** d'exécution par conversation
- **Tokens input/output** par invocation
- **Coût estimé** par requête
- **Taux de succès** des recherches

### Métriques avancées
- **Latence par étape** : search → LLM → response
- **Utilisation des tools** : nombre d'appels search_files
- **Erreurs par type** : API, parsing, timeout
- **Modèles utilisés** : gpt-4o-mini, etc.

## 🎛️ Dashboard LangSmith

### 1. Accès au dashboard
- **URL** : [smith.langchain.com](https://smith.langchain.com)
- **Projet** : `socialsync-ai-prod`
- **Traces** : Visualisation des executions

### 2. Métriques clés à surveiller

#### Performance
```
- P95 latence totale < 30s
- Taux de succès > 95%
- Tokens moyens par requête < 4000
```

#### Qualité
```
- Erreurs de parsing < 1%
- Timeouts < 2%
- Coût moyen par conversation < 0.05€
```

#### Usage
```
- Requêtes par minute
- Utilisateurs actifs
- Modèles les plus utilisés
```

## 🚨 Alertes et Monitoring

### 1. Configuration des alertes

```python
# Exemple d'alerte sur les erreurs
from langsmith import Client

client = Client()

# Récupérer les runs échoués
failed_runs = client.list_runs(
    project_name="socialsync-ai-prod",
    filter="error is not null",
    limit=10
)

# Alert si > 5% d'erreurs
error_rate = len(failed_runs) / total_runs
if error_rate > 0.05:
    # Envoyer alerte (Slack, email, etc.)
    send_alert(f"High error rate: {error_rate*100".1f"}%")
```

### 2. Monitoring avec Prometheus/Grafana

```python
# Exporter les métriques
from prometheus_client import Counter, Histogram, Gauge

# Compteurs pour les métriques
CONVERSATIONS_PROCESSED = Counter(
    'conversations_processed_total',
    'Total conversations processed'
)

RESPONSE_TIME = Histogram(
    'conversation_response_time_seconds',
    'Time to process a conversation',
    buckets=[1, 5, 10, 30, 60, 120]
)

ERRORS = Counter(
    'conversation_errors_total',
    'Total errors by type',
    labelnames=['error_type']
)
```

## 🔍 Debugging avec LangSmith

### 1. Recherche de traces

```python
from langsmith import Client

client = Client()

# Trouver une conversation spécifique
runs = client.list_runs(
    project_name="socialsync-ai-prod",
    filter=f'metadata.conversation_id = "{conversation_id}"'
)

# Analyser les détails
for run in runs:
    print(f"Duration: {run.latency}")
    print(f"Tokens: {run.total_tokens}")
    print(f"Model: {run.model}")
    if run.error:
        print(f"Error: {run.error}")
```

### 2. Comparaison A/B

```python
# Comparer les performances entre modèles
comparison = client.evaluate(
    project_name="socialsync-ai-prod",
    experiment_name="model-comparison",
    runs=[
        {"model": "gpt-4o-mini", "run_id": "run_1"},
        {"model": "gpt-4o", "run_id": "run_2"}
    ]
)

print(f"gpt-4o-mini: {comparison['gpt-4o-mini']['avg_latency']}")
print(f"gpt-4o: {comparison['gpt-4o']['avg_latency']}")
```

## 📈 Optimisation avec les données

### 1. Analyse des coûts

```python
# Calculer le coût par utilisateur
costs = client.list_runs(
    project_name="socialsync-ai-prod",
    filter="status = 'completed'"
)

user_costs = {}
for run in costs:
    user_id = run.metadata.get('user_id')
    cost = run.total_cost or 0
    user_costs[user_id] = user_costs.get(user_id, 0) + cost

# Identifier les utilisateurs coûteux
high_cost_users = {k: v for k, v in user_costs.items() if v > 10}  # > 10€
```

### 2. Optimisation des prompts

```python
# A/B testing des prompts
experiments = client.list_experiments(
    project_name="socialsync-ai-prod"
)

for exp in experiments:
    print(f"Prompt A: {exp['prompt_a']['avg_tokens']}")
    print(f"Prompt B: {exp['prompt_b']['avg_tokens']}")
```

## 🎯 Recommandations pour Production

### 1. Configuration recommandée

```python
# Pour la production
os.environ.update({
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_PROJECT": "socialsync-ai-prod",
    "LANGCHAIN_ENV": "production",
    "LANGCHAIN_TRACING_SAMPLING_RATE": "0.1",  # 10% des traces
})

# Pour le développement
os.environ.update({
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_PROJECT": "socialsync-ai-dev",
    "LANGCHAIN_ENV": "development",
    "LANGCHAIN_TRACING_SAMPLING_RATE": "1.0",  # 100% des traces
})
```

### 2. Intégration avec tes métriques existantes

```python
# Complément au BatchScanner
class EnhancedBatchScanner(BatchScanner):
    def __init__(self):
        super().__init__()
        self.langsmith_client = Client()

    async def log_to_langsmith(self, conversation_data):
        """Logger dans LangSmith pour corrélation"""
        run = self.langsmith_client.create_run(
            name=f"conversation_{conversation_data['conversation_id']}",
            run_type="chain",
            inputs={"user_message": conversation_data["message"]},
            metadata={
                "platform": conversation_data["platform"],
                "user_id": conversation_data["user_id"],
                "conversation_id": conversation_data["conversation_id"]
            }
        )

        # Ajouter les résultats
        self.langsmith_client.update_run(
            run.id,
            outputs={"response": conversation_data["response"]},
            end_time=datetime.now()
        )
```

## 🚀 Avantages pour SocialSyncAI

1. **Monitoring complet** : De WhatsApp webhook à la réponse finale
2. **Optimisation RAG** : Améliorer la pertinence des réponses
3. **Réduction des coûts** : Identifier les requêtes inefficaces
4. **Débugging rapide** : Trouver les problèmes en quelques clics
5. **SLA monitoring** : S'assurer du respect des temps de réponse

## 💡 Prochaines étapes

1. **Tester l'intégration** sur quelques conversations
2. **Configurer les alertes** sur les métriques critiques
3. **Optimiser les prompts** basés sur les données
4. **Intégrer avec Grafana** pour un dashboard unifié
5. **Configurer la rétention** des traces (30 jours recommandé)

**LangSmith transformera ton monitoring d'un système basique à un observatoire complet de tes agents RAG !** 🎉
