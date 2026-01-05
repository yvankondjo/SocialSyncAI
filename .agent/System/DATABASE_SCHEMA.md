# Database Schema - SocialSync AI

## Vue d'ensemble

Base de données: **PostgreSQL 15+** (Supabase)
Extensions: `pgvector`, `pg_trgm`, `unaccent`

## Tables principales

### 1. Authentification & Utilisateurs

#### `users`
Table Supabase Auth (gérée automatiquement)
- `id` (UUID, PK)
- `email`
- `created_at`
- `updated_at`

---

### 2. Subscriptions & Credits

#### `user_subscriptions`
Abonnements utilisateurs
```sql
id UUID PK
user_id UUID FK → users(id)
plan_name TEXT  -- 'free', 'starter', 'pro', 'enterprise'
stripe_subscription_id TEXT
status TEXT  -- 'active', 'canceled', 'past_due'
current_period_start TIMESTAMPTZ
current_period_end TIMESTAMPTZ
storage_limit_mb NUMERIC(10,2)
storage_used_mb NUMERIC(10,2) DEFAULT 0
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

#### `user_credits`
Crédits consommables par utilisateur
```sql
user_id UUID PK FK → users(id)
credits_remaining INT DEFAULT 0
credits_total INT
last_reset_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

#### `credit_transactions`
Historique des transactions de crédits
```sql
id UUID PK
user_id UUID FK → users(id)
amount INT  -- Négatif = débit, Positif = crédit
reason TEXT  -- 'message_sent', 'image_processed', 'subscription_renewed'
metadata JSONB
created_at TIMESTAMPTZ
```

#### `products` & `prices`
Catalog Stripe (synchronisé via webhooks)

---

### 3. Social Accounts & Conversations

#### `social_accounts`
Comptes sociaux connectés (OAuth)
```sql
id UUID PK
user_id UUID FK → users(id)
platform TEXT  -- 'whatsapp', 'instagram', 'linkedin', etc.
account_id TEXT  -- ID externe (ex: phone_number_id, ig_user_id)
account_name TEXT
access_token TEXT  -- Chiffré
refresh_token TEXT  -- Chiffré
token_expires_at TIMESTAMPTZ
scopes TEXT[]
metadata JSONB  -- Infos spécifiques plateforme
status TEXT DEFAULT 'active'  -- 'active', 'expired', 'revoked'
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

UNIQUE(user_id, platform, account_id)
```

**Index**:
- `idx_social_accounts_user` ON (user_id)
- `idx_social_accounts_platform` ON (platform, account_id)

---

#### `customers`
Contacts/clients (personnes qui écrivent)
```sql
id UUID PK
social_account_id UUID FK → social_accounts(id)
platform_customer_id TEXT  -- ID externe (wa_id, ig_user_id)
name TEXT
username TEXT
phone_number TEXT
email TEXT
profile_pic_url TEXT
metadata JSONB
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

UNIQUE(social_account_id, platform_customer_id)
```

---

#### `conversations`
Fils de discussion avec un contact
```sql
id UUID PK
social_account_id UUID FK → social_accounts(id)
customer_id UUID FK → customers(id)
platform TEXT  -- 'whatsapp', 'instagram'
status TEXT DEFAULT 'active'  -- 'active', 'archived', 'escalated'
last_message_at TIMESTAMPTZ
assignee_user_id UUID FK → users(id)  -- Assigné à quel agent support
metadata JSONB
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

UNIQUE(social_account_id, customer_id)
```

**Index**:
- `idx_conversations_social_account` ON (social_account_id, last_message_at DESC)
- `idx_conversations_status` ON (status, last_message_at DESC)

---

#### `conversation_messages`
Messages d'une conversation
```sql
id UUID PK
conversation_id UUID FK → conversations(id) ON DELETE CASCADE
direction TEXT  -- 'inbound', 'outbound'
platform_message_id TEXT  -- ID externe
sender_id TEXT  -- wa_id ou ig_user_id
text TEXT
message_type TEXT  -- 'text', 'image', 'audio', 'video', 'unsupported'
media_url TEXT  -- URL Supabase Storage
metadata JSONB  -- Contient attachments, context, etc.

-- Nouveaux champs (à ajouter)
triage TEXT  -- 'ignore', 'escalate', 'auto_reply'
confidence NUMERIC(4,3)
ai_decision_id UUID FK → ai_decisions(id)

delivered_at TIMESTAMPTZ
read_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

UNIQUE(conversation_id, platform_message_id)
```

**Index**:
- `idx_messages_conversation` ON (conversation_id, created_at DESC)
- `idx_messages_platform` ON (platform_message_id)

---

### 4. Support & Escalations

#### `support_escalations`
Cas escaladés vers humain
```sql
id UUID PK
user_id UUID FK → users(id)
conversation_id UUID FK → conversations(id)
reason TEXT  -- 'customer_request', 'low_confidence', 'manual_escalation'
status TEXT DEFAULT 'open'  -- 'open', 'in_progress', 'resolved'
assigned_to UUID FK → users(id)
resolved_at TIMESTAMPTZ
notes TEXT
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

---

### 5. Knowledge Base & RAG

#### `knowledge_documents`
Documents uploadés pour la base de connaissance
```sql
id UUID PK
user_id UUID FK → users(id)
title TEXT
bucket_id TEXT  -- 'kb'
object_name TEXT  -- Chemin dans Supabase Storage
storage_object_id UUID
tsconfig REGCONFIG  -- 'pg_catalog.french', 'pg_catalog.english', etc.
lang_code TEXT  -- 'fr', 'en', 'es'
status TEXT  -- 'processing', 'indexed', 'failed'
file_size_bytes BIGINT
last_ingested_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

**Index**:
- `idx_knowledge_docs_user` ON (user_id, created_at DESC)
- `idx_knowledge_docs_status` ON (status)

---

#### `knowledge_chunks`
Chunks de documents avec embeddings
```sql
id UUID PK
document_id UUID FK → knowledge_documents(id) ON DELETE CASCADE
chunk_index INT
content TEXT
tsv TSVECTOR  -- Full-text search
tsconfig REGCONFIG
lang_code TEXT
embedding VECTOR(1536)  -- OpenAI text-embedding-3-small
start_char INT
end_char INT
token_count INT
metadata JSONB
created_at TIMESTAMPTZ

UNIQUE(document_id, chunk_index)
```

**Index**:
- `idx_chunks_document` ON (document_id, chunk_index)
- `idx_chunks_embedding` USING ivfflat (embedding vector_cosine_ops)
- `idx_chunks_tsv` USING gin (tsv)

---

#### `faq_qa`
Questions-réponses structurées
```sql
id UUID PK
user_id UUID FK → users(id)
question TEXT
answer TEXT
category TEXT
keywords TEXT[]
tsv TSVECTOR
tsconfig REGCONFIG
lang_code TEXT
embedding VECTOR(1536)
text_size_bytes BIGINT
enabled BOOLEAN DEFAULT true
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

**Index**:
- `idx_faq_user` ON (user_id, enabled)
- `idx_faq_embedding` USING ivfflat (embedding vector_cosine_ops)
- `idx_faq_tsv` USING gin (tsv)

---

### 6. AI Configuration

#### `ai_models`
Modèles IA disponibles
```sql
id UUID PK
name TEXT  -- 'gpt-4o', 'gpt-4o-mini', 'claude-3-sonnet'
provider TEXT  -- 'openai', 'anthropic'
description TEXT
input_cost_per_1k NUMERIC(10,6)
output_cost_per_1k NUMERIC(10,6)
context_window INT
is_active BOOLEAN DEFAULT true
created_at TIMESTAMPTZ
```

---

#### `ai_settings`
Configuration IA par utilisateur
```sql
id UUID PK
user_id UUID FK → users(id) UNIQUE
model_id UUID FK → ai_models(id)
system_prompt TEXT
temperature NUMERIC(3,2) DEFAULT 0.7
max_tokens INT DEFAULT 500
doc_lang TEXT[]  -- Langues des documents indexés
reply_lang TEXT  -- Langue de réponse par défaut
ai_enabled_for_conversations BOOLEAN DEFAULT TRUE  -- ✨ NEW (V2.0): Contrôle AI pour DMs/chats
auto_reply_enabled BOOLEAN DEFAULT true  -- Toggle AI Control
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

---

### 7. Analytics

#### `analytics`
Métriques temps réel par utilisateur
```sql
id UUID PK
user_id UUID FK → users(id)
total_messages INT DEFAULT 0
total_conversations INT DEFAULT 0
auto_replies_sent INT DEFAULT 0
avg_response_time_seconds INT
last_calculated_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

---

#### `analytics_history`
Snapshots historiques (daily)
```sql
id UUID PK
user_id UUID FK → users(id)
date DATE
messages_count INT
conversations_count INT
auto_replies_count INT
avg_response_time_seconds INT
created_at TIMESTAMPTZ

UNIQUE(user_id, date)
```

**Index**:
- `idx_analytics_history_user_date` ON (user_id, date DESC)

---

### 8. Webhooks

#### `webhook_events`
Log des webhooks reçus (audit trail)
```sql
id UUID PK
platform TEXT  -- 'whatsapp', 'instagram', 'stripe'
event_type TEXT
payload JSONB
processed BOOLEAN DEFAULT false
error TEXT
created_at TIMESTAMPTZ
```

**Index**:
- `idx_webhooks_platform` ON (platform, created_at DESC)
- `idx_webhooks_processed` ON (processed, created_at)

---

### 9. LangGraph State (Checkpointing)

#### `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`
Tables gérées par LangGraph pour persister l'état de l'agent
(Pas à modifier manuellement)

---

## 10. Scheduled Posts (✅ IMPLEMENTED 2025-10-18)

#### `scheduled_posts`
Posts programmés pour publication automatique
```sql
id UUID PK
user_id UUID FK → users(id)
channel_id UUID FK → social_accounts(id)
platform TEXT CHECK (platform IN ('whatsapp', 'instagram'))
content_json JSONB  -- {text: string, media: [{type, url}]}
publish_at TIMESTAMPTZ NOT NULL
rrule TEXT  -- Récurrence (iCal format) - Optionnel pour v1
status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'publishing', 'published', 'failed', 'cancelled'))
platform_post_id TEXT
error_message TEXT
retry_count INT DEFAULT 0
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

**Index**:
- `idx_scheduled_posts_publish` ON (publish_at, status) WHERE status IN ('queued', 'publishing')
- `idx_scheduled_posts_user` ON (user_id, created_at DESC)
- `idx_scheduled_posts_channel` ON (channel_id, created_at DESC)
- `idx_scheduled_posts_platform` ON (platform, status)

**RLS Policies**:
- Users can CRUD their own scheduled_posts (user_id = auth.uid())

---

#### `post_runs`
Historique des tentatives d'exécution
```sql
id UUID PK
scheduled_post_id UUID FK → scheduled_posts(id) ON DELETE CASCADE
started_at TIMESTAMPTZ
finished_at TIMESTAMPTZ
status TEXT CHECK (status IN ('success', 'failed'))
error TEXT
created_at TIMESTAMPTZ DEFAULT NOW()
```

**Index**:
- `idx_post_runs_scheduled_post` ON (scheduled_post_id, created_at DESC)

**RLS Policies**:
- Users can SELECT runs for their posts (via JOIN to scheduled_posts)
- Service role can INSERT/UPDATE runs (worker context)

---

## 11. AI Rules (✅ IMPLEMENTED 2025-10-18)

#### `ai_rules`
Règles de contrôle IA simple (instructions + ignore examples)
```sql
id UUID PK
user_id UUID FK → users(id) UNIQUE
instructions TEXT  -- Instructions textuelles libres (ex: "Évite les spams")
ignore_examples TEXT[]  -- Exemples de messages à NE PAS répondre
ai_control_enabled BOOLEAN DEFAULT true  -- Master toggle (si false, IA ne répond jamais)
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

**Index**:
- `idx_ai_rules_user` ON (user_id)

**RLS Policies**:
- Users can CRUD their own ai_rules (user_id = auth.uid())

**Contraintes**:
- UNIQUE(user_id) - Un seul set de règles par utilisateur

---

#### `ai_decisions`
Log des décisions IA pour traçabilité
```sql
id UUID PK
user_id UUID FK → users(id)
message_id UUID  -- FK optionnel vers conversation_messages
decision TEXT CHECK (decision IN ('respond', 'ignore', 'escalate'))
confidence NUMERIC(4,3)  -- 0.000 à 1.000
reason TEXT  -- Raison lisible de la décision
matched_rule TEXT  -- Règle qui a été matchée
message_text TEXT  -- Le message analysé (tronqué à 500 chars)
snapshot_json JSONB  -- Contexte debug
created_at TIMESTAMPTZ DEFAULT NOW()
```

**Index**:
- `idx_ai_decisions_user` ON (user_id, created_at DESC)
- `idx_ai_decisions_message` ON (message_id)
- `idx_ai_decisions_decision` ON (decision, created_at DESC)

**RLS Policies**:
- Users can SELECT their own ai_decisions (user_id = auth.uid())
- Service role can INSERT ai_decisions (workers)

---

## Tables à ajouter (Features futures)

---

### Commentaires

#### `monitored_posts` ✨ NEW (V2.0)
Posts actifs sous monitoring pour commentaires
```sql
id UUID PK
user_id UUID FK → users(id)
social_account_id UUID FK → social_accounts(id)
platform TEXT  -- 'instagram', 'facebook', 'twitter'
platform_post_id TEXT  -- ID externe du post
caption TEXT
media_url TEXT  -- URL de l'image/video
music_title VARCHAR(500)  -- ✨ NEW: Titre de la musique (pour contexte AI)
posted_at TIMESTAMPTZ
source TEXT  -- 'scheduled', 'imported', 'manual'
monitoring_enabled BOOLEAN DEFAULT TRUE
monitoring_started_at TIMESTAMPTZ
monitoring_ends_at TIMESTAMPTZ
last_check_at TIMESTAMPTZ
next_check_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

UNIQUE(platform, platform_post_id)
```

**Index**:
- `idx_monitored_posts_next_check` ON (next_check_at) WHERE monitoring_enabled = TRUE
- `idx_monitored_posts_user` ON (user_id)
- `idx_monitored_posts_account` ON (social_account_id)

---

#### `monitoring_rules` ✨ NEW (V2.0)
Règles de monitoring par utilisateur/compte
```sql
id UUID PK
user_id UUID FK → users(id)
social_account_id UUID FK → social_accounts(id)  -- NULL = règles globales
auto_monitor_enabled BOOLEAN DEFAULT TRUE
auto_monitor_count INT DEFAULT 5 CHECK (auto_monitor_count BETWEEN 1 AND 20)
monitoring_duration_days INT DEFAULT 7 CHECK (monitoring_duration_days BETWEEN 1 AND 30)
ai_enabled_for_comments BOOLEAN DEFAULT TRUE  -- ✨ NEW: Contrôle AI granulaire
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

---

#### `comments`
Commentaires sur posts monitorés
```sql
id UUID PK
monitored_post_id UUID FK → monitored_posts(id)
platform_comment_id TEXT
parent_id TEXT  -- ID du commentaire parent (pour threads)
author_name TEXT
author_id TEXT
author_avatar_url TEXT  -- ✨ NEW
text TEXT
created_at TIMESTAMPTZ
like_count INTEGER DEFAULT 0  -- ✨ NEW
triage TEXT CHECK (triage IN ('respond', 'ignore', 'escalate', 'user_conversation'))  -- ✨ UPDATED
ai_decision_id UUID FK → ai_decisions(id)
replied_at TIMESTAMPTZ
ai_reply_text TEXT  -- ✨ NEW: Copie de la réponse AI envoyée

UNIQUE(monitored_post_id, platform_comment_id)
```

**Index**:
- `idx_comments_monitored_post` ON (monitored_post_id)
- `idx_comments_triage` ON (triage)
- `idx_comments_created_at` ON (created_at DESC)

---

#### `comment_checkpoint` ✨ NEW (V2.0)
État de pagination pour chaque post
```sql
id UUID PK
monitored_post_id UUID FK → monitored_posts(id)
last_cursor TEXT  -- Curseur de pagination Instagram
last_check_at TIMESTAMPTZ
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

UNIQUE(monitored_post_id)
```

---

### Triage IA (Features avancées)

#### `ai_triage_rules_advanced` (TODO)
```sql
id UUID PK
message_id UUID FK → conversation_messages(id)
triage TEXT  -- 'ignore', 'escalate', 'auto_reply'
confidence NUMERIC(4,3)
rule_id UUID FK → ai_rules(id)
reason TEXT
snapshot_json JSONB
created_at TIMESTAMPTZ
```

---

### Analytics avancées

#### `kpi_2h`
```sql
id UUID PK
tenant_id UUID FK → users(id)
window_start TIMESTAMPTZ
window_end TIMESTAMPTZ
messages_count INT
comments_count INT
frt_p50_seconds INT
auto_reply_rate NUMERIC(4,3)
escalate_count INT
ignored_count INT
posts_active INT
updated_at TIMESTAMPTZ

UNIQUE(tenant_id, window_start)
```

---

### Clustering

#### `clusters`
```sql
id UUID PK
tenant_id UUID FK → users(id)
scope TEXT  -- 'global', 'post'
scope_ref UUID  -- NULL pour global, post_id pour per-post
algo TEXT  -- 'hdbscan'
label TEXT  -- Titre du cluster (TF-IDF ou LLM)
size INT
created_at TIMESTAMPTZ
```

#### `cluster_items`
```sql
id UUID PK
cluster_id UUID FK → clusters(id) ON DELETE CASCADE
message_id UUID FK → conversation_messages(id)
comment_id UUID FK → comments(id)
created_at TIMESTAMPTZ

CHECK (message_id IS NOT NULL OR comment_id IS NOT NULL)
```

---

## Row Level Security (RLS)

Toutes les tables principales ont des policies RLS activées:
- `users` peuvent uniquement accéder à leurs propres données
- Filtrage automatique par `user_id` / `tenant_id`
- Pas besoin de `WHERE user_id = ...` dans les requêtes (géré par RLS)

**Exemple policy**:
```sql
CREATE POLICY "Users can view own social_accounts"
ON social_accounts FOR SELECT
USING (auth.uid() = user_id);
```

---

## Migrations

**Migrations récentes**:
- `20251016150443_remote_schema.sql` - Schema initial
- `20251018042910_add_scheduled_posts.sql` - Scheduled posts feature ✅
- `20251018050034_add_ai_rules_simple.sql` - AI Rules (simple control) ✅

Pour ajouter une migration:
1. Créer fichier `supabase/migrations/YYYYMMDDHHMMSS_description.sql`
2. Appliquer: `supabase db push`
3. Voir SOP: `.agent/SOP/ADD_MIGRATION.md`

---

*Schéma documenté: 2025-10-18*
