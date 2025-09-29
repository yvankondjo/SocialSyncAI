# Documentation d'implémentation PRD2 - Confidence Score & Escalade Humain

## Vue d'ensemble

Cette documentation détaille l'implémentation complète du PRD2 qui introduit :
- **Format JSON strict** pour toutes les réponses finales du LLM
- **Escalade automatique** vers un humain si confidence < 0.10
- **Gestion FAQ avec questions[]** (liste de formulations multiples)
- **Contrôles IA** globaux et par conversation
- **Service find_answers piloté par LLM** (sans embeddings)

## 🗃️ Modifications de la base de données

### Migration 004 - PRD2

**Fichier**: `backend/migrations/migration_004_prd2_confidence_escalation.sql`

#### A. FAQ - Passage de `question` à `questions[]`

```sql
-- Ajouter la colonne questions[] 
ALTER TABLE faq_qa
  ADD COLUMN IF NOT EXISTS questions TEXT[] NOT NULL DEFAULT '{}'::text[];

-- Migrer les données existantes
UPDATE faq_qa 
SET questions = ARRAY[question] 
WHERE question IS NOT NULL AND questions = '{}'::text[];

-- Supprimer l'ancienne colonne et le full-text search
DROP TRIGGER IF EXISTS trg_faq_tsv_update ON faq_qa;
ALTER TABLE faq_qa DROP COLUMN IF EXISTS content;
ALTER TABLE faq_qa DROP COLUMN IF EXISTS question;
ALTER TABLE faq_qa DROP COLUMN IF EXISTS tsv;
```

**Impact** : Chaque FAQ peut maintenant avoir plusieurs formulations de questions au lieu d'une seule.

#### B. Contrôle IA par conversation

```sql
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS ai_mode TEXT NOT NULL DEFAULT 'ON'
  CHECK (ai_mode IN ('ON', 'OFF'));
```

**Impact** : Permet de désactiver l'IA pour une conversation spécifique après escalade.

#### C. Table des escalades

```sql
CREATE TABLE IF NOT EXISTS support_escalations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  message_id UUID NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  reason TEXT,
  notified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Impact** : Traçabilité complète des escalades avec lien vers la conversation et le message déclencheur.

## 📊 Schémas Pydantic mis à jour

### Fichier: `backend/app/schemas/faq_qa_service.py`

#### Nouveaux schémas FAQ

```python
class FAQQA(BaseModel):
    questions: List[str] = Field(default_factory=list)  # Changement majeur
    # ... autres champs

class FAQQuestionsAddRequest(BaseModel):
    items: List[str] = Field(..., min_items=1)

class FAQQuestionsUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., description="[{index: int, value: str}]")

class FAQQuestionsDeleteRequest(BaseModel):
    indexes: List[int] = Field(..., min_items=1)
```

#### Schémas pour escalades et contrôle IA

```python
class SupportEscalation(BaseModel):
    id: UUID
    conversation_id: UUID
    confidence: float
    reason: Optional[str] = None
    notified: bool = False

class ConversationAIModeRequest(BaseModel):
    mode: str = Field(..., description="ON ou OFF")
```

## 🛣️ Nouvelles routes API

### 1. Routes FAQ - Gestion des questions multiples

#### POST `/api/faq-qa/{faq_id}/questions:add`
**Objectif** : Ajouter des questions à une FAQ existante

```python
@router.post("/{faq_id}/questions:add")
async def add_faq_questions(
    faq_id: UUID,
    request: FAQQuestionsAddRequest,  # {"items": ["Question 1", "Question 2"]}
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
```

**Exemple d'utilisation** :
```bash
curl -X POST "/api/faq-qa/123e4567-e89b-12d3-a456-426614174000/questions:add" \
  -H "Content-Type: application/json" \
  -d '{"items": ["Comment puis-je faire X?", "Quelle est la procédure pour X?"]}'
```

**Réponse** :
```json
{
  "message": "2 questions ajoutées avec succès",
  "questions": ["Question existante", "Comment puis-je faire X?", "Quelle est la procédure pour X?"]
}
```

#### POST `/api/faq-qa/{faq_id}/questions:update`
**Objectif** : Mettre à jour des questions spécifiques par index

```python
@router.post("/{faq_id}/questions:update")
async def update_faq_questions(
    faq_id: UUID,
    request: FAQQuestionsUpdateRequest,
    # ...
):
```

**Exemple d'utilisation** :
```bash
curl -X POST "/api/faq-qa/123e4567-e89b-12d3-a456-426614174000/questions:update" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"index": 0, "value": "Nouvelle formulation pour la question 1"},
      {"index": 2, "value": "Nouvelle formulation pour la question 3"}
    ]
  }'
```

**Logique** :
- Validation que tous les index sont dans les bornes
- Mise à jour atomique de toutes les questions spécifiées
- Retour de la liste complète mise à jour

#### POST `/api/faq-qa/{faq_id}/questions:delete`
**Objectif** : Supprimer des questions par index (1..n éléments)

```python
@router.post("/{faq_id}/questions:delete")
async def delete_faq_questions(
    faq_id: UUID,
    request: FAQQuestionsDeleteRequest,  # {"indexes": [0, 2, 4]}
    # ...
):
```

**Logique critique** :
- Validation des bornes pour tous les index
- Suppression en ordre décroissant pour éviter les décalages d'index
- Vérification qu'il reste au moins une question après suppression
- Support des index non contigus

### 2. Route contrôle IA par conversation

#### PATCH `/api/conversations/{conversation_id}/ai_mode`
**Objectif** : Activer/désactiver l'IA pour une conversation spécifique

```python
@router.patch("/{conversation_id}/ai_mode")
async def update_conversation_ai_mode(
    conversation_id: str,
    request: ConversationAIModeRequest,  # {"mode": "OFF"}
    # ...
):
```

**Cas d'usage** :
- Après escalade automatique → mode "OFF"
- Réactivation manuelle par l'agent → mode "ON"
- Interface UI avec bannière "Escaladée au support"

### 3. Routes support - Gestion des escalades

#### GET `/api/support/escalations`
**Objectif** : Lister toutes les escalades de l'utilisateur

```python
@router.get("/escalations", response_model=List[SupportEscalation])
async def get_user_escalations(
    current_user_id: str = Depends(get_current_user_id),
    # ...
):
```

#### POST `/api/support/escalations/{escalation_id}/notify`
**Objectif** : Marquer une escalade comme notifiée et déclencher l'email

```python
@router.post("/escalations/{escalation_id}/notify")
async def notify_escalation(
    escalation_id: str,
    # ...
):
```

**Processus** :
1. Vérification que l'escalade appartient à l'utilisateur
2. Marquage `notified = true`
3. Déclenchement de l'envoi d'email (TODO à implémenter)

## 🔧 Service find_answers PRD2

### Fichier: `backend/app/services/find_answers_prd2.py`

#### Principe architectural

Le nouveau service **abandonne complètement les embeddings** et utilise uniquement le LLM pour la sélection :

1. **Récupération** : Toutes les FAQs actives du tenant
2. **Pagination** : Division en lots de 20-50 FAQs pour éviter un contexte trop long
3. **Sélection LLM** : Pour chaque lot, le LLM choisit la meilleure correspondance
4. **Agrégation** : Sélection du meilleur résultat parmi tous les lots

#### Implémentation détaillée

```python
class FindAnswersService:
    def __init__(self, user_id: str, batch_size: int = 30):
        self.user_id = user_id
        self.batch_size = batch_size
    
    def find_answers(self, question: str) -> Answer:
        # 1. Récupérer toutes les FAQs actives
        faqs = self.get_active_faqs()
        
        # 2. Diviser en lots
        batches = self.create_batches(faqs)
        
        # 3. Traiter chaque lot avec le LLM
        batch_results = []
        for batch in batches:
            result = self.process_batch(batch, question)
            if result:
                batch_results.append(result)
        
        # 4. Sélectionner le meilleur résultat
        best_match = self.find_best_across_batches(batch_results)
        
        # 5. Retourner un objet Answer structuré
        return self.build_answer(best_match, faqs)
```

#### Format de prompt LLM

```python
prompt = f"""Tu es un assistant spécialisé dans la recherche de FAQs.

Voici une question utilisateur: "{user_question}"

Voici une liste de FAQs disponibles:
{json.dumps(faqs_context, ensure_ascii=False, indent=2)}

Réponds UNIQUEMENT avec un JSON dans ce format:
{{
  "best_match": {{
    "faq_id": "uuid",
    "matched_question_index": 0,
    "matched_question_text": "texte exact",
    "confidence_local": 0.85,
    "reason": "explication courte"
  }}
}}

OU si aucune FAQ ne correspond:
{{
  "no_match": {{
    "reason": "explication courte"
  }}
}}
"""
```

#### Objet Answer retourné

```python
class Answer(BaseModel):
    faq_id: Optional[str] = None
    answer: Optional[str] = None
    matched_question_index: Optional[int] = None
    matched_question_text: Optional[str] = None
    reason: str
    status: str  # "match" | "no_match"
```

**Important** : Cet objet Answer n'est PAS la réponse finale à l'utilisateur, mais sert de contexte au LLM génératif principal.

## 🤖 Agent RAG PRD2

### Fichier: `backend/app/services/rag_agent_prd2.py`

#### Règles de sortie strictes

L'agent implémente les règles PRD2 :

```python
base_system_prompt = """
RÈGLES DE SORTIE STRICTES :
- Si tu réponds à l'utilisateur, renvoie UNIQUEMENT :
  {"response":"<texte>", "confidence": <float 0..1>}
- Si tu dois utiliser un outil, utilise le tool-calling natif. 
  Le tour suivant DOIT être la réponse finale JSON ci-dessus.
- Ne mélange jamais tool-call et JSON final dans le même tour.
- Si on te renvoie "JSON_INVALID", renvoie uniquement le JSON corrigé.
"""
```

#### Gestion des Gates IA

```python
def process_message(self, user_message: str, conversation_id: str, message_id: str = None):
    # Gate 1: IA globale désactivée
    if not self.check_ai_settings():
        return {"response": None, "reason": "IA globalement désactivée"}
    
    # Gate 2: IA désactivée pour cette conversation
    if not self.check_conversation_ai_mode(conversation_id):
        return {"response": None, "reason": "IA désactivée pour cette conversation"}
    
    # ... traitement normal
```

#### Parsing JSON avec retry

```python
def parse_or_fix_json(self, response_text: str) -> Optional[AIResponse]:
    try:
        # Première tentative
        response_json = json.loads(response_text.strip())
        return AIResponse(**response_json)
    except (json.JSONDecodeError, ValidationError):
        # Retry automatique avec correction LLM
        return self.retry_json_correction(response_text)
```

#### Escalade automatique

```python
# Vérifier le seuil d'escalade
if ai_response.confidence < 0.10:
    escalation_id = self.create_escalation(
        conversation_id=conversation_id,
        message_id=message_id,
        confidence=ai_response.confidence,
        reason=f"Confiance faible: {ai_response.confidence}"
    )
    
    return {
        "response": "Transfert à un agent humain.",
        "escalated": True,
        "escalation_id": escalation_id
    }
```

#### Gestion des tools

Le système supporte le tool-calling natif :

1. **Premier appel LLM** : Peut décider d'utiliser `find_answers`
2. **Exécution du tool** : Récupération des données FAQ
3. **Second appel LLM** : DOIT produire la réponse JSON finale

## 🧪 Tests complets

### Tests unitaires (`backend/tests/test_prd2_features.py`)

#### Tests JSON parsing
- ✅ JSON valide → OK
- ✅ JSON invalide → retry "JSON_INVALID" → OK  
- ✅ JSON invalide après retry → erreur contrôlée

#### Tests seuil escalade
- ✅ `confidence = 0.09` → escalade + `ai_mode='OFF'`
- ✅ `confidence = 0.10` → pas d'escalade

#### Tests tool-calling
- ✅ Présence de `.tool_calls` → aucun parsing JSON tenté

#### Tests FAQ operations
- ✅ Add multiples questions
- ✅ Update par index (validation bornes)
- ✅ Delete 1..n indexes (indexes non contigus)

### Tests d'intégration

#### Tests Gates IA
- ✅ `ai_settings.is_active=false` → LLM non appelé
- ✅ `conversations.ai_mode='OFF'` → LLM non appelé pour ce thread

#### Tests escalade
- ✅ Insertion `support_escalations` + mutation `ai_mode='OFF'`
- ✅ Email marqué `notified=true` (optionnel)

### Tests E2E simulés

#### Scénario normal
1. Message utilisateur → tool-call (find_answers) 
2. → JSON final `{response, confidence=0.42}` 
3. → message livré

#### Scénario escalade
1. Message utilisateur → JSON final `{..., confidence=0.05}` 
2. → escalade + mute + bannière UI

### Tests routes API (`backend/tests/test_routers/test_faq_prd2_routes.py`)

- ✅ Routes FAQ questions:add/update/delete
- ✅ Route conversation ai_mode
- ✅ Routes support escalations
- ✅ Validation des erreurs et cas limites

## 🔒 Sécurité et RLS

### Row Level Security (RLS)

Toutes les nouvelles tables respectent le principe RLS :

```sql
-- support_escalations
CREATE POLICY "Users manage their escalations" ON support_escalations 
FOR ALL USING (auth.uid() = user_id);

-- ai_settings  
CREATE POLICY "Users manage their ai_settings" ON ai_settings 
FOR ALL USING (auth.uid() = user_id);
```

### Validation des données

- **FAQ questions** : Validation des index pour update/delete
- **AI mode** : Validation stricte "ON" | "OFF"
- **Escalades** : Vérification appartenance utilisateur
- **Limites** : Taille maximale `questions[]` pour éviter inflation prompts

## 📈 Observabilité

### Logs recommandés

```python
# JSON invalide + retry
logger.warning(f"JSON invalide, tentative de correction: {e}")

# Escalades
logger.info(f"Escalade créée: {escalation_id} pour conversation {conversation_id}")

# Performance find_answers
logger.info(f"Traitement de {len(faqs)} FAQs en {len(batches)} lots")
```

### Métriques à surveiller

- **% escalades** : Ratio escalades / messages totaux
- **Temps moyen find_answers** : Performance par lot
- **Taille moyenne prompt** : Optimisation batch_size
- **Taux retry JSON** : Qualité des réponses LLM

## 🚀 Déploiement

### Ordre d'exécution

1. **Migration SQL** : `migration_004_prd2_confidence_escalation.sql`
2. **Déploiement backend** : Nouvelles routes et services
3. **Tests** : Validation suite complète
4. **Configuration** : Variables d'environnement LLM
5. **Monitoring** : Activation logs et métriques

### Variables d'environnement requises

```bash
OPENROUTER_API_KEY=your_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### Points d'attention

- **Batch size** : Ajuster selon la taille moyenne des FAQs
- **Seuil escalade** : 0.10 par défaut, configurable si nécessaire
- **Performance** : Surveiller temps de réponse avec lots multiples
- **Coûts LLM** : Optimiser taille des prompts et fréquence d'appels

## 📋 Critères d'acceptation - Validation

- ✅ Le LLM ne sort **jamais** autre chose que `{response, confidence}` pour la réponse finale
- ✅ `confidence < 0.10` → `conversations.ai_mode='OFF'` + ligne `support_escalations` créée
- ✅ `find_answers` fonctionne **sans embeddings**, via LLM, avec lots si nécessaire
- ✅ FAQ : **add/update/delete (multi)** opérationnels avec validation complète
- ✅ `ai_settings.is_active=false` → IA muette globalement
- ✅ Suite de **tests verte** avec couverture unitaire, intégration et E2E

## 🔄 Évolutions futures

### Phase 2 - Améliorations

- **Email automatique** : Implémentation complète envoi notifications escalade
- **UI avancée** : Interface de gestion des escalades avec filtres et recherche
- **Analytics** : Dashboard de performance IA et taux d'escalade
- **Optimisations** : Cache LLM pour réponses fréquentes, batch size dynamique

### Phase 3 - Extensions

- **Multi-langues** : Support escalades dans différentes langues
- **Règles métier** : Escalades conditionnelles selon contexte client
- **Intégrations** : Webhooks vers systèmes de ticketing externes
- **IA adaptative** : Ajustement automatique du seuil selon performance

---

Cette implémentation respecte intégralement les spécifications du PRD2 et fournit une base solide pour les évolutions futures du système d'IA conversationnelle avec escalade humaine.
