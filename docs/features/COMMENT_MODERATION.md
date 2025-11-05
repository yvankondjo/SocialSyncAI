# 💭 Comment Moderation

AI auto-replies to Instagram post comments with adaptive polling.

---

## Flow

```
Celery Beat → poll_all_monitored_posts (every 5 min)
  ↓
For each monitored post:
  - Fetch new comments from Instagram API
  - Adjust next poll interval based on post age
  ↓
For each comment:
  - Skip if from post owner
  - Triage: RESPOND / IGNORE / ESCALATE
  - If RESPOND: generate reply via RAG agent
  - Post reply via Instagram API
```

---

## Adaptive Polling

**Why not webhooks?** Instagram doesn't provide comment webhooks for regular posts.

**Table:** `monitored_posts`
```sql
post_age_hours int
next_poll_at timestamptz
poll_interval_minutes int
```

**Intervals:**
```python
if post_age_hours < 24:  poll_interval = 5   # Fresh
elif post_age_hours < 72: poll_interval = 15  # Recent
else: poll_interval = 30                       # Old
```

**Result:** 80% fewer API calls vs fixed 5-min polling.

---

## Triage System

**File:** `backend/app/services/comment_triage.py`

### 1. Owner Loop Prevention
```python
if comment.username == post_owner_username:
    return "IGNORE"
```

### 2. Guardrails
```python
if keyword in comment.text.lower():  # flagged_keywords
    return "IGNORE"
```

### 3. OpenAI Moderation
```python
result = openai.Moderation.create(input=comment.text)
if result.flagged:  # hate, harassment, violence
    return "IGNORE"
```

### 4. AI Decision
```python
decision = rag_agent.triage(comment, post_context)
return decision  # "RESPOND", "IGNORE", "ESCALATE"
```

---

## Multimodal Context

LLM sees:
```python
{
    "post_image_url": "https://...",
    "post_caption": "New product! 🚀",
    "comment_text": "Looks amazing!",
    "comment_author": "@user123"
}
```

Response:
```
"Thank you @user123! We're excited too! 🎉"
```

---

## Components

**Worker:** `backend/app/workers/comments.py`
```python
@celery_app.task
def poll_all_monitored_posts():
    # Celery Beat: every 5 min
    # Fetches comments for monitored posts
    # Adjusts next_poll_at dynamically
```

**Triage:** `backend/app/services/comment_triage.py`
```python
def triage_comment(comment, post) -> TriageDecision:
    # Returns: RESPOND / IGNORE / ESCALATE
```

---

## Configuration

**Table:** `ai_settings`
```python
{
    "ai_enabled_for_comments": true,
    "flagged_keywords": ["spam"],
    "auto_reply_enabled": true
}
```

**Table:** `monitored_posts`
```sql
CREATE TABLE monitored_posts (
    id uuid PRIMARY KEY,
    user_id uuid,
    post_id text,
    is_monitoring boolean DEFAULT true,
    next_poll_at timestamptz,
    poll_interval_minutes int DEFAULT 5
);
```

---

## Key Files

| File | Purpose |
|------|---------|
| `workers/comments.py` | Polling + processing |
| `services/comment_triage.py` | Triage logic |
| `services/rag_agent.py` | Response generation |

---

**Last Updated:** 2025-10-30
