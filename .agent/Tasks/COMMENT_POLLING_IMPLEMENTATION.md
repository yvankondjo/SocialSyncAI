# Comment Polling System - Implementation Documentation

**Status**: ✅ IMPLEMENTED (2025-10-18)
**Related Docs**:
- [AI Moderation System](../System/AI_MODERATION_SYSTEM.md)
- [Celery Workers](../System/CELERY_WORKERS.md)
- [Database Schema](../System/DATABASE_SCHEMA.md)

---

## 📋 Overview

Système de polling adaptatif des commentaires Instagram avec modération IA et réponses automatiques.

**Objectifs:**
- Poller les commentaires publics sur posts programmés
- Modération automatique via OpenAI Moderation API
- Réponses automatiques via agent RAG
- Escalation email pour contenu problématique
- Contrôle granulaire IA (chats vs comments séparés)

---

## 🏗️ Architecture

### Flow de Données

```
┌──────────────────┐
│  Celery Beat     │ Déclenche toutes les 5 min
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│  poll_post_comments worker  │
├─────────────────────────────┤
│ 1. Query posts publiés      │
│ 2. Calculate interval       │
│ 3. Fetch via connector      │
│ 4. Save + enqueue           │
└────────┬────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  process_comment worker      │
├──────────────────────────────┤
│ 1. AIDecisionService         │
│    (context_type="comment")  │
│ 2. Switch on decision:       │
│    - ESCALATE → Email        │
│    - RESPOND → RAG + Reply   │
│    - IGNORE → No action      │
└──────────────────────────────┘
```

### Polling Adaptatif

**Stratégie selon âge du post:**
- **J+0 à J+2**: Toutes les 5 minutes (engagement élevé)
- **J+2 à J+5**: Toutes les 15 minutes (engagement moyen)
- **J+5 à J+7**: Toutes les 30 minutes (engagement faible)
- **J+7+**: Arrêt du polling (stop_at dépassé)

---

## 🗃️ Database Schema

### Table: `comments`

```sql
CREATE TABLE public.comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES scheduled_posts(id),
    platform_comment_id TEXT NOT NULL,
    parent_id UUID REFERENCES comments(id),

    -- Author
    author_name TEXT,
    author_id TEXT,

    -- Content
    text TEXT NOT NULL,

    -- AI Decision
    triage TEXT CHECK (triage IN ('respond', 'ignore', 'escalate')),
    ai_decision_id UUID REFERENCES ai_decisions(id),

    -- Status
    hidden BOOLEAN DEFAULT false,
    replied_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(post_id, platform_comment_id)
);
```

### Table: `comment_checkpoint`

```sql
CREATE TABLE public.comment_checkpoint (
    post_id UUID PRIMARY KEY REFERENCES scheduled_posts(id),
    last_cursor TEXT,        -- Pagination cursor (Instagram API)
    last_seen_ts TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Extension: `scheduled_posts`

```sql
ALTER TABLE scheduled_posts
ADD COLUMN last_check_at TIMESTAMPTZ,
ADD COLUMN next_check_at TIMESTAMPTZ,
ADD COLUMN stop_at TIMESTAMPTZ;  -- Auto-set to publish_at + 7 days
```

### Extension: `ai_rules` (Granular Control)

```sql
ALTER TABLE ai_rules
ADD COLUMN ai_enabled_for_chats BOOLEAN DEFAULT true,
ADD COLUMN ai_enabled_for_comments BOOLEAN DEFAULT true;
```

**Usage:**
- `ai_enabled_for_chats`: ON/OFF pour messages privés (DMs)
- `ai_enabled_for_comments`: ON/OFF pour commentaires publics
- Contrôle **indépendant** → Peut activer IA sur chats mais pas sur comments

---

## 🔧 Backend Implementation

### Services

#### PlatformConnector (Interface)

**Fichier**: `backend/app/services/platform_connector.py`

Interface abstraite pour futures plateformes:

```python
class PlatformConnector(ABC):
    @abstractmethod
    async def list_new_comments(
        post_platform_id: str,
        since_cursor: Optional[str]
    ) -> Tuple[List[Dict], Optional[str]]:
        """Fetch new comments. Returns (comments, next_cursor)"""
        pass

    @abstractmethod
    async def reply_to_comment(
        comment_platform_id: str,
        text: str
    ) -> Dict[str, Any]:
        """Reply to comment. Returns {success, reply_id, error}"""
        pass
```

#### InstagramConnector

**Fichier**: `backend/app/services/instagram_connector.py`

Implémentation Instagram:
- API: `GET /{media_id}/comments`
- Pagination avec cursor (`after` parameter)
- Normalise format commentaires
- Méthodes: `hide_comment()`, `delete_comment()`

#### AIDecisionService (Extended)

**Fichier**: `backend/app/services/ai_decision_service.py`

**Nouveau paramètre**: `context_type`

```python
def check_message(
    self,
    message_text: str,
    context_type: str = "chat"  # "chat" ou "comment"
) -> Tuple[AIDecision, float, str, str]:
    """
    Flow:
    1. Check ai_enabled_for_{chats|comments}
    2. Check ai_control_enabled (global)
    3. OpenAI Moderation
    4. Custom rules
    5. Fallback: RESPOND
    """
```

**Decision Flow avec context_type:**

```python
# Pour CHATS (DMs)
if context_type == "chat":
    if not rules.get("ai_enabled_for_chats"):
        return IGNORE

# Pour COMMENTS
if context_type == "comment":
    if not rules.get("ai_enabled_for_comments"):
        return IGNORE
```

---

### Workers

#### poll_post_comments

**Fichier**: `backend/app/workers/comments.py`
**Queue**: `comments`
**Schedule**: Toutes les 5 minutes (Celery Beat)

**Logic:**
```python
1. Query posts: status='published' AND stop_at > NOW()
2. Pour chaque post:
   - Si next_check_at > NOW() → Skip
   - Calculate interval adaptatif
   - connector.list_new_comments(since_cursor)
   - Save comments en DB
   - Enqueue process_comment.delay()
   - Update checkpoint + next_check_at
```

**Métriques retournées:**
```python
{
    "posts_checked": int,
    "comments_found": int,
    "errors": int
}
```

#### process_comment

**Fichier**: `backend/app/workers/comments.py`
**Queue**: `comments`
**Retry**: 3 fois, backoff 5 min

**Logic:**
```python
1. Fetch comment + post + user
2. AIDecisionService.check_message(text, context_type="comment")
3. Log decision dans ai_decisions
4. Switch on decision:
   - ESCALATE:
     * EmailEscalationService.generate_email() (LLM)
     * EmailEscalationService.send_email()
   - RESPOND:
     * RAGAgent.generate_response()
     * connector.reply_to_comment()
     * Update replied_at
   - IGNORE:
     * No action
5. Update triage + ai_decision_id
```

**Error Handling:**
- Max 3 retries avec exponential backoff
- Si échec final: triage=IGNORE, ai_decision_id=NULL

---

### Router API

**Fichier**: `backend/app/routers/comments.py`
**Prefix**: `/api/comments`

#### Endpoints

**GET /api/comments**
- **Query Params**:
  - `post_id` (optional): Filter par post
  - `triage` (optional): Filter par décision (respond, ignore, escalate)
  - `limit` (default 50, max 100)
  - `offset` (default 0)
- **Returns**: `CommentListResponse`
  ```json
  {
    "comments": [...],
    "total": 150,
    "limit": 50,
    "offset": 0
  }
  ```
- **Security**: Filtre automatique par user ownership (via posts)

**GET /api/comments/{comment_id}**
- **Returns**: `CommentInDB` avec détails complets
- **Security**: Vérifie ownership via post

---

## ⚙️ Configuration

### Celery

**Fichier**: `backend/app/workers/celery_app.py`

```python
# Route
task_routes = {
    "app.workers.comments.*": {"queue": "comments"}
}

# Beat Schedule
beat_schedule = {
    "poll-post-comments-every-5-minutes": {
        "task": "app.workers.comments.poll_post_comments",
        "schedule": 300.0,  # 5 minutes
        "options": {"expires": 290}
    }
}
```

### Démarrage Workers

**Production (Workers séparés):**
```bash
# Worker comments
celery -A app.workers.celery_app worker -Q comments --loglevel=info

# Celery Beat (1 seul process!)
celery -A app.workers.celery_app beat --loglevel=info
```

**Dev (Combined):**
```bash
celery -A app.workers.celery_app worker --beat -Q ingest,scheduler,comments --loglevel=info
```

---

## 🧪 Tests

### Tests Unitaires

**Fichier**: `backend/tests/test_comments_polling.py` (À créer)

**Cas de test:**
1. Calcul interval adaptatif (J+1, J+4, J+8)
2. Checkpoint cursor pagination
3. AIDecisionService avec context_type="comment"
4. AI disabled for comments mais enabled for chats
5. Process comment RESPOND flow
6. Process comment ESCALATE flow
7. Process comment IGNORE flow
8. Retry sur erreur API
9. Stop polling après J+7
10. Idempotence (pas de duplicatas)

### Tests E2E

**Fichier**: `backend/tests/test_comments_e2e.py` (À créer)

**Scénarios:**
1. Flow violence → ESCALATE → Email envoyé
2. Flow spam → IGNORE → Aucune action
3. Flow question → RESPOND → RAG → Reply Instagram
4. Polling 3 posts âges différents → Intervals corrects
5. Checkpoint après 2 polls → Pas de duplicatas

---

## 📊 Monitoring

### Logs Structurés

```python
[POLL] Checking 15 active posts for new comments
[POLL] Post abc123: found 3 new comments, next check in 5 minutes
[PROCESS] Processing comment xyz789 from @user123
[PROCESS] Comment xyz789 → Decision: RESPOND, confidence: 0.92
[PROCESS] Successfully replied to comment xyz789
```

### Métriques Celery

```bash
# Voir tasks actives
celery -A app.workers.celery_app inspect active

# Voir schedule
celery -A app.workers.celery_app inspect scheduled

# Stats
celery -A app.workers.celery_app inspect stats
```

---

## 🚀 Deployment Checklist

- [ ] Migration DB appliquée (20251018105442_add_comments_polling.sql)
- [ ] Variables d'env configurées (OPENAI_MODERATION_ENABLED, SMTP settings)
- [ ] Worker comments démarré
- [ ] Celery Beat démarré (1 seul process)
- [ ] Redis opérationnel
- [ ] Tests E2E passés
- [ ] Monitoring configuré (logs, métriques)
- [ ] Documentation frontend mise à jour

---

## 🐛 Troubleshooting

### Worker ne poll pas

**Symptômes**: Aucun log `[POLL]` toutes les 5 min

**Solutions:**
1. Vérifier Beat schedule:
   ```bash
   celery -A app.workers.celery_app inspect scheduled
   ```
2. Vérifier que Beat tourne:
   ```bash
   ps aux | grep celery | grep beat
   ```
3. Vérifier queue routing:
   ```bash
   celery -A app.workers.celery_app inspect active_queues
   ```

### Commentaires non sauvegardés

**Symptômes**: `comments_found=0` mais commentaires existent

**Solutions:**
1. Vérifier credentials Instagram dans social_accounts
2. Vérifier `platform_post_id` non NULL
3. Vérifier checkpoint cursor:
   ```sql
   SELECT * FROM comment_checkpoint WHERE post_id = 'xxx';
   ```
4. Vérifier logs connector: `[IG_CONNECTOR]`

### Réponses non envoyées

**Symptômes**: Decision=RESPOND mais replied_at NULL

**Solutions:**
1. Vérifier ai_enabled_for_comments=true
2. Vérifier RAG agent fonctionne
3. Vérifier InstagramService.reply_to_comment()
4. Check retry count (max 3)

---

## 📈 Performance

### Capacité

- **Posts actifs**: ~1000 posts simultanés
- **Commentaires/poll**: ~50 commentaires max par post
- **Processing time**: ~2-5s par commentaire (RAG + API)
- **Queue throughput**: ~100 commentaires/min (1 worker)

### Scaling

**Vertical:**
```bash
# Augmenter concurrency
celery -A app.workers.celery_app worker -Q comments --concurrency=10
```

**Horizontal:**
```bash
# Worker 1
celery -A app.workers.celery_app worker -Q comments --hostname=comments1@%h

# Worker 2
celery -A app.workers.celery_app worker -Q comments --hostname=comments2@%h
```

**Important**: Un seul Celery Beat process (pas de duplication)

---

## 🔗 Related Features

- **Scheduled Posts**: Posts programmés pour polling
- **AI Rules**: Contrôle granulaire chats vs comments
- **OpenAI Moderation**: Guardrails automatiques
- **Email Escalation**: Notifications contenu flaggé
- **RAG Agent**: Génération réponses automatiques

---

*Documentation créée: 2025-10-18*
*Dernière mise à jour: 2025-10-18*
