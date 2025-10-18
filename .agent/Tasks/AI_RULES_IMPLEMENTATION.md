# AI Rules - Simple AI Control (IMPLEMENTED ✅)

**Date d'implémentation**: 2025-10-18
**Statut**: ✅ COMPLETED

---

## Vue d'ensemble

Feature permettant un **contrôle simple de l'IA** via des instructions textuelles et des exemples de messages à ignorer.

**Objectif**: Donner aux utilisateurs un moyen simple de définir des garde-fous pour l'IA, sans avoir à configurer des patterns regex complexes.

---

## Fonctionnalités implémentées

### 1. Tables DB (Migration Supabase)

**Fichier**: `/workspace/supabase/migrations/20251018050034_add_ai_rules_simple.sql`

#### Table `ai_rules`
- Stocke les règles AI par utilisateur (UNIQUE constraint sur user_id)
- Champs:
  - `instructions` (TEXT): Instructions textuelles libres
  - `ignore_examples` (TEXT[]): Array d'exemples de messages à NE PAS répondre
  - `ai_control_enabled` (BOOLEAN): Master toggle (si FALSE, IA ne répond JAMAIS)
  - `created_at`, `updated_at`

#### Table `ai_decisions`
- Log des décisions IA pour traçabilité
- Champs:
  - `decision` (TEXT): "respond", "ignore", "escalate"
  - `confidence` (NUMERIC): Score de confiance 0.000-1.000
  - `reason` (TEXT): Raison lisible de la décision
  - `matched_rule` (TEXT): Règle qui a été matchée
  - `message_text` (TEXT): Message analysé
  - `snapshot_json` (JSONB): Contexte debug

**RLS**: Activé sur les 2 tables avec policies appropriées.

---

### 2. Service AI Decision

**Fichier**: `/workspace/backend/app/services/ai_decision_service.py`

**Classe**: `AIDecisionService`

**Méthode principale**: `check_message(message_text: str) -> Tuple[AIDecision, float, str, str]`

**Logique de décision**:
1. Vérifier si AI Control activé → si NON: IGNORE
2. Vérifier similarité avec `ignore_examples` → si > 70%: IGNORE
3. Vérifier mots-clés d'escalation ("remboursement", "urgent", "avocat", etc.) → ESCALATE
4. Sinon → RESPOND (défaut)

**Méthode de log**: `log_decision(...)` pour tracer toutes les décisions en DB.

---

### 3. Endpoints API

**Fichier**: `/workspace/backend/app/routers/ai_rules.py`

**Routes implémentées**:

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/ai-rules` | Récupérer les règles de l'utilisateur |
| `POST` | `/api/ai-rules` | Créer/Mettre à jour les règles (UPSERT) |
| `PATCH` | `/api/ai-rules` | Mise à jour partielle des règles |
| `PATCH` | `/api/ai-rules/toggle` | Toggle AI Control ON/OFF |
| `POST` | `/api/ai-rules/check-message` | Tester un message (dry-run) |
| `GET` | `/api/ai-rules/decisions` | Historique des décisions (paginé) |
| `GET` | `/api/ai-rules/decisions/stats` | Stats (count RESPOND/IGNORE/ESCALATE) |

**Authentification**: JWT via `get_authenticated_db` (RLS automatique).

---

### 4. Intégration dans le flux de messages

**Fichier modifié**: `/workspace/backend/app/services/batch_scanner.py`

**Point d'injection**: Après le check automation (ligne ~200), AVANT `generate_smart_response`.

**Workflow**:
```python
# 1. Check automation (existant)
if not automation_check["should_reply"]:
    return

# 2. CHECK AI RULES (NOUVEAU)
decision, confidence, reason, matched_rule = ai_decision_service.check_message(message_text)

# Log la décision
ai_decision_service.log_decision(...)

# 3. Appliquer la décision
if decision == AIDecision.IGNORE:
    logger.info("Message ignoré")
    return  # Pas de réponse

if decision == AIDecision.ESCALATE:
    logger.info("Message escaladé")
    # TODO: Créer escalation dans support_escalations
    return  # Pas de réponse auto

# 4. Si RESPOND → continuer normalement
await generate_smart_response(...)
```

---

## Schemas Pydantic

**Fichier**: `/workspace/backend/app/schemas/ai_rules.py`

**Schemas principaux**:
- `AIDecision` (Enum): RESPOND, IGNORE, ESCALATE
- `AIRulesCreate`: Pour créer des règles
- `AIRulesUpdate`: Pour mise à jour partielle
- `AIRulesResponse`: Réponse API
- `CheckMessageRequest/Response`: Pour tester un message
- `AIDecisionResponse`: Historique des décisions

---

## Tests

**Fichier**: `/workspace/backend/tests/test_ai_rules.py`

**Tests implémentés**:

### Tests unitaires (AIDecisionService)
- ✅ AI Control désactivé → IGNORE
- ✅ Message similaire à exemple → IGNORE
- ✅ Mot-clé "remboursement" → ESCALATE
- ✅ Mot-clé "urgent" → ESCALATE
- ✅ Mot-clé "avocat" → ESCALATE
- ✅ Message normal → RESPOND
- ✅ Similarité de texte (difflib)
- ✅ Log de décisions

### Tests d'intégration (API)
- ⏸️ Skipped (nécessitent DB Supabase)
- Endpoints: GET, POST, PATCH, toggle, check-message, decisions, stats

### Tests E2E
- ⏸️ Skipped (nécessitent environnement complet)
- Message ignoré, escaladé, répondu, similaire à exemple

**Lancer les tests**:
```bash
cd backend
pytest tests/test_ai_rules.py -v
```

---

## Migration DB

**Appliquer la migration**:

```bash
cd /workspace
supabase db push
```

**Vérifier**:
```bash
supabase migration list
```

**Rollback si nécessaire**:
```sql
DROP TABLE IF EXISTS public.ai_decisions;
DROP TABLE IF EXISTS public.ai_rules;
```

---

## Cas d'usage

### Exemple 1: Éviter les spams
```json
{
  "instructions": "- Évite les spams\n- Ne réponds pas aux messages agressifs",
  "ignore_examples": [
    "Clique ici pour gagner",
    "Promo limitée",
    "Tu es un robot pourri"
  ],
  "ai_control_enabled": true
}
```

Si un message arrive: "CLIQUE ICI POUR GAGNER 1000€ !!!"
→ Similarité > 70% avec "Clique ici pour gagner"
→ **Décision: IGNORE**

---

### Exemple 2: Escalader les demandes urgentes
```json
{
  "instructions": "- Escalade les demandes urgentes ou de remboursement",
  "ignore_examples": [],
  "ai_control_enabled": true
}
```

Si un message arrive: "Je veux être REMBOURSÉ IMMÉDIATEMENT !"
→ Mot-clé "remboursement" détecté
→ **Décision: ESCALATE**

---

### Exemple 3: Désactiver l'IA complètement
```json
{
  "instructions": null,
  "ignore_examples": [],
  "ai_control_enabled": false
}
```

**Tout message** → **Décision: IGNORE**
L'IA ne répond JAMAIS automatiquement.

---

## Limitations et améliorations futures

### Limitations actuelles
- Similarité basique (SequenceMatcher de difflib)
- Mots-clés d'escalation hardcodés dans le code
- Pas de support multilingue avancé
- Pas d'escalation automatique vers `support_escalations` (TODO)

### Améliorations possibles
- Utiliser embeddings (OpenAI/sentence-transformers) pour similarité sémantique
- Permettre aux utilisateurs de définir leurs propres mots-clés d'escalation
- Support multilingue via détection automatique
- Intégration avec système d'escalation existant
- Dashboard analytics des décisions IA
- Machine learning pour améliorer les décisions

---

## Architecture

```
┌─────────────────┐
│ Incoming Message│
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Automation Check    │ (existant)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ AI Rules Check      │ (NOUVEAU)
│ - Check enabled?    │
│ - Check similarity? │
│ - Check keywords?   │
└────────┬────────────┘
         │
         ├─ IGNORE ──────► [No response]
         │
         ├─ ESCALATE ────► [Create escalation + No auto response]
         │
         ▼ RESPOND
┌─────────────────────┐
│ Generate AI Response│
└─────────────────────┘
```

---

## Logs

Les logs incluent le tag `[AI_CONTROL]` pour faciliter le debugging:

```
🛡️ [AI_CONTROL] Message ignoré pour whatsapp:123:456 - AI Control désactivé
🛡️ [AI_CONTROL] Message escaladé pour instagram:789:012 - Mot-clé: avocat
🛡️ [AI_CONTROL] AI autorisée à répondre - Aucune règle bloquante
```

---

## Conclusion

Feature **AI Rules** implémentée avec succès ✅

- ✅ Migration DB créée et prête
- ✅ Service AIDecisionService opérationnel
- ✅ API REST complète (7 endpoints)
- ✅ Intégration dans batch_scanner
- ✅ Tests unitaires complets
- ✅ Documentation à jour

**Prochaines étapes**:
1. Appliquer la migration DB: `supabase db push`
2. Tester les endpoints via Swagger (`/docs`)
3. Implémenter le frontend (UI simple comme spécifié)
4. Connecter l'escalation au système `support_escalations`

---

*Dernière mise à jour: 2025-10-18*
