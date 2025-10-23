# RAG Agent - Silent Error Handling & Guardrails System

**Version:** 2.4
**Date:** 2025-10-23
**Status:** ✅ IMPLEMENTED (Tests manuels requis)

## 📋 Vue d'ensemble

Ce document décrit le système de gestion silencieuse des erreurs et des guardrails du RAG Agent, implémenté pour gérer les erreurs LLM, les messages inappropriés, et les blocages de sécurité sans générer de réponses utilisateur visibles.

## 🎯 Objectifs

### Problèmes Résolus

**AVANT (V2.3) :**
- ❌ Erreurs LLM généraient "Désolé, une erreur s'est produite..."
- ❌ Guardrails POST ne nettoyaient pas le contexte LLM
- ❌ Messages bloqués polluaient l'historique
- ❌ Pas de retry automatique sur erreurs transitoires

**APRÈS (V2.4) :**
- ✅ **Silence total** : Aucun message en cas de blocage/erreur
- ✅ **Contexte propre** : Messages flaggés retirés du contexte LLM
- ✅ **Retry silencieux** : 3 tentatives automatiques (exponential backoff)
- ✅ **Logging détaillé** : Toutes les erreurs dans logs techniques + DB
- ✅ **Base de données** : Décisions loggées dans `ai_decisions` table

---

## 🏗️ Architecture

### Nouveau LangGraph Flow

```
User Message
    ↓
┌─────────────────────┐
│ guardrails_pre_check│  → Flagged? → error_handler (silent)
└─────────┬───────────┘
          ↓ Pass
┌─────────────────────┐
│    LLM Call         │  → Error? → Retry 3x → error_handler (silent)
└─────────┬───────────┘
          ↓ Success
┌─────────────────────┐
│guardrails_post_check│  → Flagged? → Remove messages → error_handler
└─────────┬───────────┘
          ↓ Pass
      ┌───────┐
      │  END  │ (Response générée)
      └───────┘
```

### Nœuds du Graphe

1. **`guardrails_pre_check`** : Validation avant LLM
2. **`llm`** : Appel LLM avec retry logic
3. **`handle_tool_call`** : Exécution des tools (RAG, escalation)
4. **`guardrails_post_check`** : Validation après génération
5. **`error_handler`** : Gestion silencieuse de tous les blocages/erreurs

### State Management

```python
class RAGAgentState(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages]  # ⚠️ add_messages requis!

    # Nouveaux champs V2.4
    should_respond: bool = True      # Flag pour bloquer génération
    retry_count: int = 0             # Compteur retries LLM
    error_message: Optional[str]     # Message d'erreur technique
    guardrail_pre_result: Optional[dict]  # Résultat pre-check
```

**⚠️ CRITIQUE** : `add_messages` reducer est **REQUIS** pour que `RemoveMessage` fonctionne. L'utilisation de `operator.add` rendrait la suppression de messages impossible.

---

## 🔒 Guardrails

### 1. Guardrail PRE-check

**Timing :** AVANT que le message atteigne le LLM

**Vérifications :**
1. OpenAI Moderation API
2. Custom rules (`flagged_keywords`, `flagged_phrases`)
3. Scope check (chats vs comments enabled)

**Si bloqué :**
```python
{
    "should_respond": False,
    "error_message": "GUARDRAIL_PRE_BLOCKED: {reason}",
    "guardrail_pre_result": {
        "decision": "block",
        "reason": "Flagged keyword detected: 'spam'",
        "confidence": 0.95
    }
}
```

**Résultat :**
- ✅ Aucun appel LLM
- ✅ Aucun message AI généré
- ✅ Log dans `ai_decisions` table
- ✅ Log `[GUARDRAILS PRE] Message flagged and blocked`

---

### 2. Guardrail POST-check

**Timing :** APRÈS génération de la réponse AI

**Vérifications :**
1. OpenAI Moderation API sur la réponse générée

**Si bloqué :**
```python
{
    "messages": [
        RemoveMessage(id=ai_message.id),      # Supprime réponse AI
        RemoveMessage(id=user_message.id)     # Supprime question user
    ],
    "should_respond": False,
    "error_message": "GUARDRAIL_POST_BLOCKED: {reason}"
}
```

**Résultat :**
- ✅ Message AI retiré du contexte
- ✅ Message user qui l'a déclenché AUSSI retiré
- ✅ Contexte LLM propre (pas de pollution)
- ✅ Log `[GUARDRAILS POST] Removing triggering user message`

**Exemple :**

```python
# AVANT post-check
messages = [
    SystemMessage("You are helpful..."),
    HumanMessage("Question inappropriée"),  # À supprimer
    AIMessage("Réponse inappropriée")       # À supprimer
]

# APRÈS post-check (si flagged)
messages = [
    SystemMessage("You are helpful...")
    # Les 2 derniers messages supprimés
]
```

---

## 🔄 Retry Logic

### Configuration

```python
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
# Exponential backoff: 2s, 4s, 8s
```

### Cas d'usage

1. **API Down** : OpenRouter/OpenAI temporairement indisponible
2. **Rate Limit** : Trop de requêtes
3. **Network Error** : Timeout, connection error
4. **Model Error** : Erreur temporaire du modèle

### Flow

```python
Attempt 1 → Fail → Wait 2s
Attempt 2 → Fail → Wait 4s
Attempt 3 → Fail → Max retries reached
    ↓
{
    "should_respond": False,
    "error_message": "LLM_ERROR: {error}",
    "retry_count": 3
}
    ↓
error_handler (silent)
```

### Logs

```
[LLM RETRY] Attempt 1/3 failed: Connection timeout
[LLM RETRY] Attempt 2/3 failed: Connection timeout
[LLM RETRY] Success on attempt 3/3

OU

[LLM ERROR] Max retries (3) reached for user abc123: Connection timeout
[SILENT FAILURE] LLM error for user abc123: LLM_ERROR: Connection timeout
```

---

## 🚫 Error Handler

**Rôle :** Point final pour TOUS les blocages et erreurs

**Comportement :**
1. Categorise l'erreur (PRE/POST guardrail, LLM error)
2. Log dans logs techniques
3. **Ne génère AUCUN message utilisateur**
4. Termine silencieusement

**Code :**

```python
async def _error_handler(self, state: RAGAgentState) -> Dict[str, Any]:
    error_msg = state.error_message or "Unknown error"

    if "GUARDRAIL_PRE_BLOCKED" in error_msg:
        logger.info(f"[SILENT FAILURE] Pre-guardrail blocked")
    elif "GUARDRAIL_POST_BLOCKED" in error_msg:
        logger.info(f"[SILENT FAILURE] Post-guardrail blocked")
    elif "LLM_ERROR" in error_msg:
        logger.error(f"[SILENT FAILURE] LLM error: {error_msg}")

    return {}  # Silent - no messages generated
```

---

## 📊 Logging & Audit

### Base de données (`ai_decisions` table)

Toutes les décisions guardrails sont loggées :

```sql
INSERT INTO ai_decisions (
    user_id,
    message_id,
    decision,        -- 'ignore', 'respond', 'escalate'
    confidence,      -- 0.0 - 1.0
    reason,          -- "OpenAI Moderation: harassment"
    matched_rule,    -- "openai_moderation", "flagged_keyword:spam"
    message_text,    -- Premiers 500 caractères
    snapshot_json    -- Métadonnées
) VALUES (...);
```

### Logs techniques

**Guardrail PRE :**
```
[GUARDRAILS PRE] Message flagged and blocked: OpenAI Moderation: harassment
[SILENT FAILURE] Pre-guardrail blocked message for user abc123
```

**Guardrail POST :**
```
[GUARDRAILS POST] Generated response flagged: Violates: hate
[GUARDRAILS POST] Removing triggering user message from context
[SILENT FAILURE] Post-guardrail blocked response for user abc123
```

**LLM Retry :**
```
[LLM RETRY] Attempt 1/3 failed: Rate limit exceeded
[LLM RETRY] Success on attempt 2/3
```

---

## 🔧 Configuration

### Variables d'environnement

```bash
# OpenAI Moderation
OPENAI_API_KEY=sk-...
OPENAI_MODERATION_ENABLED=true  # Default: true

# LLM principal
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### AI Rules (Supabase)

```sql
-- Configuration par utilisateur
INSERT INTO ai_rules (
    user_id,
    ai_control_enabled,
    ai_enabled_for_chats,
    ai_enabled_for_comments,
    flagged_keywords,
    flagged_phrases
) VALUES (
    'user_123',
    true,                              -- Contrôle AI activé
    true,                              -- AI pour chats/DMs
    true,                              -- AI pour commentaires
    ARRAY['spam', 'viagra', 'scam'],   -- Keywords bloqués
    ARRAY['buy now', 'click here']     -- Phrases bloquées
);
```

---

## 🚨 Bug Critique Corrigé

### Problème Détecté (2025-10-23)

**Bug initial :**
- `RemoveMessage` utilisé avec `operator.add` reducer
- `RemoveMessage` **REQUIERT** `add_messages` reducer
- **Résultat** : Suppression de messages ne fonctionnerait PAS

**Correction appliquée :**

```python
# AVANT (ligne 144)
messages: Annotated[List[AnyMessage], operator.add]

# APRÈS
messages: Annotated[List[AnyMessage], add_messages]
```

**Impact :**
- ✅ Messages reçoivent automatiquement des UUIDs
- ✅ `RemoveMessage` fonctionne correctement
- ✅ Déduplication automatique
- ✅ Compatible checkpointer

---

## 🧪 Testing

### Tests Automatiques (✅ 7/7 PASS)

**Script :** `/workspace/backend/test_rag_logic_validation.py`

```bash
python test_rag_logic_validation.py

✅ TEST 1: RAGAgentState has required fields
✅ TEST 2: Graph has all 7 nodes
✅ TEST 3: Decision functions exist
✅ TEST 4: _check_llm_result routing logic
✅ TEST 5: _check_should_respond routing logic
✅ TEST 6: Messages use add_messages reducer
✅ TEST 7: Message IDs auto-generated
```

### Tests Manuels Requis (⚠️)

**1. Guardrail PRE avec vraies règles :**
```python
# Setup: Créer flagged_keywords dans ai_rules table
# Test: Envoyer message avec keyword
# Vérifier: should_respond=False, pas de message AI
```

**2. Guardrail POST avec OpenAI :**
```python
# Setup: OPENAI_API_KEY configurée
# Test: Message qui génère réponse inappropriée
# Vérifier: Messages user+AI supprimés du contexte
```

**3. Retry avec API down :**
```python
# Test: Simuler API down (couper réseau)
# Vérifier: 3 tentatives dans logs
# Vérifier: Exponential backoff (2s, 4s, 8s)
```

**4. Message IDs avec checkpointer :**
```python
# Test: Utiliser checkpointer réel
# Vérifier: Tous messages ont des IDs
# Vérifier: RemoveMessage fonctionne
```

---

## ⚠️ Breaking Changes

### 1. Reducer Change

**Impact :** `operator.add` → `add_messages`

**Risque :** Comportement différent sur duplicates
- **AVANT** : Messages simplement concaténés (peut dupliquer)
- **APRÈS** : Messages dédupliqués par ID

**Mitigation :** Tester toutes fonctionnalités RAG agent

### 2. Return Type LLM

**Impact :** `RAGAgentResponse` → `AIMessage`

```python
# AVANT
return {"messages": [RAGAgentResponse(response="...", confidence=0.9)]}

# APRÈS
return {"messages": [AIMessage(content="...")]}
```

**Risque :** Code qui parse `RAGAgentResponse.confidence`

**Mitigation :** Vérifier appelants de `_call_llm`

---

## 📊 Statut Production

| Composant | Status | Tests | Notes |
|-----------|--------|-------|-------|
| State management | ✅ | ✅ | Validation logique OK |
| Guardrail PRE | ✅ | ⚠️ | Besoin test avec vraies règles |
| Guardrail POST | ✅ | ⚠️ | Besoin test avec OpenAI |
| RemoveMessage | ✅ | ✅ | add_messages corrigé |
| Retry logic | ✅ | ⚠️ | Besoin test avec vraie API |
| Error handler | ✅ | ✅ | Routes correctement |
| Graph structure | ✅ | ✅ | 7 nœuds validés |

**Légende :**
- ✅ Testé et validé
- ⚠️ Logique OK, tests manuels requis
- ❌ Problème détecté

---

## 📚 Fichiers Associés

**Code source :**
- `backend/app/services/rag_agent.py` (modifications majeures)

**Tests :**
- `backend/test_rag_logic_validation.py` (✅ 7/7 PASS)
- `backend/test_rag_real_scenarios.py` (nécessite credentials)
- `backend/test_rag_retry_logic.py` (tests partiels)

**Documentation :**
- `/workspace/RAG_AGENT_SILENT_ERROR_HANDLING.md` (50+ sections)
- `/workspace/RAG_AGENT_ERROR_FLOW_SUMMARY.md` (diagrammes ASCII)
- `/workspace/CRITICAL_FIXES_AND_VALIDATION.md` (rapport validation)
- `/workspace/rag_agent_graph_new.mmd` (diagramme Mermaid)

---

## 🚀 Checklist Déploiement

### Pré-production

- [ ] Tests manuels guardrails PRE/POST
- [ ] Tests retry avec API down
- [ ] Tests checkpointer + message IDs
- [ ] Vérifier logs (`[SILENT FAILURE]`)
- [ ] Vérifier DB (`ai_decisions` table)
- [ ] Tests régression (fonctionnalités existantes)
- [ ] Code review

### Configuration

- [ ] `OPENAI_API_KEY` pour moderation
- [ ] Table `ai_rules` avec rules configurées
- [ ] Table `ai_decisions` pour logging
- [ ] Monitoring alertes sur `[LLM ERROR]`

### Post-déploiement

- [ ] Dashboard guardrails (blocages/jour)
- [ ] Monitoring retry rate
- [ ] Vérifier pas de spike silent failures
- [ ] Feedback utilisateurs (messages bloqués)

---

## 🎯 Prochaines Étapes

1. ✅ Tests manuels complets
2. 📊 Dashboard monitoring guardrails
3. 🔔 Alertes admin sur blocages fréquents
4. 📈 Métriques performance retry
5. 🔧 Fine-tuning seuils guardrails

---

## Related Documentation

- `.agent/System/AUTOMATION_SERVICE.md` - Service automation unifié
- `.agent/System/AI_MODERATION_SYSTEM.md` - Système moderation (si existe)
- `.agent/Tasks/AI_RULES_MODERATION_IMPLEMENTATION.md` - Implémentation modération V1

---

**Version:** 2.4
**Date:** 2025-10-23
**Auteur:** Claude
**Status:** ✅ IMPLEMENTED - Tests manuels requis avant production
