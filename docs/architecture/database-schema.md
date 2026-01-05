# Database Schema

**Complete PostgreSQL database structure for SocialSync AI.**

This document describes all tables, columns, relationships, and indexes in the database.

---

## Table of Contents

- [Schema overview](#schema-overview)
- [Core tables](#core-tables)
  - [users](#users)
  - [social_accounts](#social_accounts)
  - [conversations](#conversations)
  - [messages](#messages)
- [AI and Knowledge Base](#ai-and-knowledge-base)
  - [knowledge_documents](#knowledge_documents)
  - [faq_qa](#faq_qa)
  - [ai_settings](#ai_settings)
- [Comment Monitoring](#comment-monitoring)
  - [monitored_posts](#monitored_posts)
  - [comments](#comments)
- [Billing and Credits](#billing-and-credits)
  - [user_credits](#user_credits)
  - [customers](#customers)
- [System tables](#system-tables)
  - [webhook_events](#webhook_events)
  - [support_escalations](#support_escalations)
- [Indexes and constraints](#indexes-and-constraints)
- [Row Level Security](#row-level-security)

---

## Schema overview

**SocialSync AI uses PostgreSQL with pgvector extension.**

**Total tables:** 28

**Key features:**
- Multi-tenant with Row Level Security (RLS)
- Vector embeddings for semantic search (pgvector)
- Real-time updates via Supabase subscriptions
- Automatic timestamp management via triggers

**Key relationships:**
- Users → Social Accounts (one-to-many)
- Social Accounts → Conversations (one-to-many)
- Conversations → Messages (one-to-many)
- Users → Knowledge Documents (one-to-many)
- Users → Monitored Posts (one-to-many)
- Monitored Posts → Comments (one-to-many)

**Database diagram:**

```
users ──┬── social_accounts ──┬── conversations ── conversation_messages
        │                     └── monitored_posts ── comments
        ├── knowledge_documents ── knowledge_chunks
        ├── faq_qa
        ├── ai_settings
        ├── ai_decisions
        ├── bertopic_models ── topic_analysis
        ├── user_credits ── credit_transactions
        ├── customers ── subscriptions
        └── support_escalations
```

---

## Core tables

### users

**Stores user accounts and profiles.**

Managed by Supabase Auth. Extended with custom columns.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key (from Supabase Auth) |
| `email` | text | NO | User email address |
| `created_at` | timestamptz | NO | Account creation timestamp |
| `updated_at` | timestamptz | NO | Last profile update |
| `full_name` | text | YES | Display name |
| `avatar_url` | text | YES | Profile picture URL |
| `subscription_status` | text | YES | Stripe subscription status: `active`, `canceled`, `past_due` |
| `subscription_tier` | text | YES | Plan: `free`, `pro`, `enterprise` |

**Indexes:**
- Primary key: `id`
- Unique: `email`

**Row Level Security:** Users can only read/update their own row.

---

### social_accounts

**Connected Instagram, WhatsApp, and Messenger accounts.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `platform` | text | NO | Platform: `instagram`, `whatsapp`, `messenger` |
| `platform_user_id` | text | NO | Platform-specific account ID |
| `username` | text | YES | Display name (e.g., Instagram handle) |
| `access_token` | text | NO | OAuth access token (encrypted) |
| `token_expires_at` | timestamptz | YES | Token expiry time |
| `is_active` | boolean | NO | Account enabled/disabled |
| `ai_mode` | text | NO | AI automation: `ON`, `OFF`, `REVIEW` |
| `created_at` | timestamptz | NO | Connection timestamp |
| `updated_at` | timestamptz | NO | Last sync timestamp |
| `profile_picture_url` | text | YES | Account avatar |
| `follower_count` | integer | YES | Followers/contacts count |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Unique: `(platform, platform_user_id)`
- Index: `user_id` (for fast user queries)

**Constraints:**
- `platform` must be one of: `instagram`, `whatsapp`, `messenger`
- `ai_mode` must be one of: `ON`, `OFF`, `REVIEW`

**Row Level Security:** Users can only access their own social accounts.

---

### conversations

**Message threads for each social account.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `social_account_id` | uuid | NO | Foreign key → `social_accounts.id` |
| `platform_thread_id` | text | NO | Platform-specific conversation ID |
| `participant_name` | text | YES | Name of the other person |
| `participant_id` | text | NO | Platform user ID of participant |
| `last_message_at` | timestamptz | YES | Timestamp of most recent message |
| `last_message_preview` | text | YES | First 100 characters of last message |
| `unread_count` | integer | NO | Number of unread messages (default: 0) |
| `ai_mode` | text | NO | AI automation: `ON`, `OFF`, `REVIEW` |
| `status` | text | NO | Conversation status: `open`, `closed`, `escalated` |
| `created_at` | timestamptz | NO | First message timestamp |
| `updated_at` | timestamptz | NO | Last activity timestamp |

**Indexes:**
- Primary key: `id`
- Foreign key: `social_account_id` → `social_accounts.id`
- Unique: `(social_account_id, platform_thread_id)`
- Index: `social_account_id` (for fast account queries)
- Index: `last_message_at DESC` (for inbox sorting)
- Index: `status` (for filtering)

**Constraints:**
- `ai_mode` must be one of: `ON`, `OFF`, `REVIEW`
- `status` must be one of: `open`, `closed`, `escalated`

**Row Level Security:** Users can access conversations for their own social accounts.

---

### messages

**Individual messages within conversations.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `conversation_id` | uuid | NO | Foreign key → `conversations.id` |
| `platform_message_id` | text | NO | Platform-specific message ID |
| `sender_type` | text | NO | Who sent: `user` (customer), `business` (you), `system` |
| `sender_id` | text | YES | Platform user ID of sender |
| `content` | text | YES | Message text content |
| `media_url` | text | YES | Attached image/video URL |
| `media_type` | text | YES | Media type: `image`, `video`, `audio`, `file` |
| `sent_at` | timestamptz | NO | Message timestamp |
| `delivered_at` | timestamptz | YES | Delivery confirmation time |
| `read_at` | timestamptz | YES | Read receipt time |
| `is_ai_generated` | boolean | NO | Generated by AI (default: false) |
| `ai_confidence` | float | YES | Confidence score 0-1 |
| `created_at` | timestamptz | NO | Database insert time |

**Indexes:**
- Primary key: `id`
- Foreign key: `conversation_id` → `conversations.id`
- Unique: `(conversation_id, platform_message_id)`
- Index: `conversation_id, sent_at DESC` (for conversation history)
- Index: `is_ai_generated` (for analytics)

**Constraints:**
- `sender_type` must be one of: `user`, `business`, `system`
- `ai_confidence` must be between 0 and 1

**Row Level Security:** Users can access messages for their own conversations.

---

## AI and Knowledge Base

### knowledge_documents

**Uploaded documents for AI knowledge base.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `title` | text | NO | Document title |
| `content` | text | NO | Full document text |
| `content_type` | text | NO | Type: `pdf`, `text`, `markdown`, `url` |
| `file_url` | text | YES | Original file URL (if uploaded) |
| `file_size` | integer | YES | File size in bytes |
| `embedding` | vector(1536) | YES | OpenAI embedding vector |
| `chunk_count` | integer | NO | Number of chunks created (default: 0) |
| `is_processed` | boolean | NO | Embeddings generated (default: false) |
| `created_at` | timestamptz | NO | Upload timestamp |
| `updated_at` | timestamptz | NO | Last modification |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Index: `user_id` (for user documents)
- Index: `is_processed` (for processing queue)
- **Vector index:** `embedding vector_cosine_ops` (for similarity search)

**Row Level Security:** Users can only access their own documents.

---

### faq_qa

**Frequently asked questions and answers.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `question` | text | NO | Question text |
| `answer` | text | NO | Answer text |
| `embedding` | vector(1536) | YES | Question embedding for similarity search |
| `category` | text | YES | Category: `shipping`, `returns`, `pricing`, etc. |
| `is_active` | boolean | NO | Enabled/disabled (default: true) |
| `usage_count` | integer | NO | Times used in responses (default: 0) |
| `created_at` | timestamptz | NO | Creation timestamp |
| `updated_at` | timestamptz | NO | Last edit |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Index: `user_id, is_active` (for active FAQs)
- **Vector index:** `embedding vector_cosine_ops` (for similarity search)

**Row Level Security:** Users can only access their own FAQs.

---

### ai_settings

**Per-user AI configuration.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `system_prompt` | text | YES | Custom AI instructions |
| `model` | text | NO | AI model: `gpt-4o`, `claude-3.5-sonnet`, etc. |
| `temperature` | float | NO | Creativity 0-1 (default: 0.7) |
| `max_tokens` | integer | NO | Max response length (default: 500) |
| `confidence_threshold` | float | NO | Min confidence for auto-reply (default: 0.8) |
| `escalation_enabled` | boolean | NO | Auto-escalate low confidence (default: true) |
| `created_at` | timestamptz | NO | Creation timestamp |
| `updated_at` | timestamptz | NO | Last update |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Unique: `user_id` (one config per user)

---

### monitored_posts

**Instagram posts being monitored for comments.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `social_account_id` | uuid | NO | Foreign key → `social_accounts.id` |
| `platform_post_id` | text | NO | Instagram media ID |
| `caption` | text | YES | Post caption |
| `media_url` | text | YES | Image/video URL |
| `is_active` | boolean | NO | Monitoring enabled (default: true) |
| `ai_moderation_enabled` | boolean | NO | Auto-reply to comments (default: false) |
| `last_checked_at` | timestamptz | YES | Last poll time |
| `created_at` | timestamptz | NO | Monitoring started |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Foreign key: `social_account_id` → `social_accounts.id`
- Unique: `(social_account_id, platform_post_id)`
- Index: `is_active, last_checked_at` (for polling)

**Row Level Security:** Users can only access their own monitored posts.

---

### comments

**Comments on monitored Instagram posts.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `monitored_post_id` | uuid | NO | Foreign key → `monitored_posts.id` |
| `platform_comment_id` | text | NO | Instagram comment ID |
| `username` | text | NO | Commenter's Instagram username |
| `user_id` | text | NO | Instagram user ID |
| `text` | text | NO | Comment text |
| `timestamp` | timestamptz | NO | Comment time |
| `is_replied` | boolean | NO | Replied to (default: false) |
| `reply_text` | text | YES | AI-generated reply |
| `created_at` | timestamptz | NO | Database insert time |

**Indexes:**
- Primary key: `id`
- Foreign key: `monitored_post_id` → `monitored_posts.id`
- Unique: `(monitored_post_id, platform_comment_id)`
- Index: `monitored_post_id, timestamp DESC` (for comment threads)
- Index: `is_replied` (for reply queue)

**Row Level Security:** Users can access comments on their own monitored posts.

---

## Billing and Credits

### user_credits

**AI usage credits for each user.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `credits_remaining` | integer | NO | Available credits |
| `credits_total` | integer | NO | Total credits allocated |
| `credits_used` | integer | NO | Credits consumed |
| `last_reset_at` | timestamptz | YES | Last monthly reset |
| `created_at` | timestamptz | NO | Record creation |
| `updated_at` | timestamptz | NO | Last credit change |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Unique: `user_id` (one record per user)

**Row Level Security:** Users can only view their own credits.

---

### customers

**Stripe customer mappings.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `stripe_customer_id` | text | NO | Stripe customer ID (starts with `cus_`) |
| `stripe_subscription_id` | text | YES | Active subscription ID |
| `created_at` | timestamptz | NO | Customer creation |
| `updated_at` | timestamptz | NO | Last sync |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Unique: `user_id`
- Unique: `stripe_customer_id`
- Index: `stripe_subscription_id`

**Row Level Security:** Users cannot directly access (backend only).

---

## System tables

### webhook_events

**Received webhook events log.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `platform` | text | NO | Source: `instagram`, `whatsapp`, `messenger`, `stripe` |
| `event_type` | text | NO | Event name (e.g., `message`, `comment`) |
| `payload` | jsonb | NO | Full webhook payload |
| `processed` | boolean | NO | Successfully processed (default: false) |
| `error_message` | text | YES | Error details if failed |
| `received_at` | timestamptz | NO | Webhook delivery time |
| `processed_at` | timestamptz | YES | Processing completion time |

**Indexes:**
- Primary key: `id`
- Index: `platform, event_type` (for analytics)
- Index: `processed, received_at` (for retry queue)
- Index: `received_at DESC` (for debugging)

**Retention:** Delete events older than 30 days (background job).

---

### support_escalations

**Cases escalated to human support.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | uuid | NO | Primary key |
| `user_id` | uuid | NO | Foreign key → `users.id` |
| `conversation_id` | uuid | NO | Foreign key → `conversations.id` |
| `message` | text | NO | Message that triggered escalation |
| `confidence` | float | NO | AI confidence score 0-100 |
| `reason` | text | NO | Why escalated |
| `notified` | boolean | NO | Email sent (default: false) |
| `resolved` | boolean | NO | Case resolved (default: false) |
| `created_at` | timestamptz | NO | Escalation time |
| `resolved_at` | timestamptz | YES | Resolution time |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id` → `users.id`
- Foreign key: `conversation_id` → `conversations.id`
- Index: `resolved, created_at DESC` (for support queue)

**Row Level Security:** Users can view their own escalations.

---

## Indexes and constraints

**Performance optimizations:**

1. **Foreign key indexes:** All foreign keys have indexes for fast joins
2. **Composite indexes:** Multi-column indexes for common queries
3. **Vector indexes:** pgvector indexes for similarity search (HNSW algorithm)
4. **Partial indexes:** Indexes on boolean columns with `WHERE` clause

**Example vector index:**
```sql
CREATE INDEX idx_knowledge_documents_embedding 
ON knowledge_documents 
USING hnsw (embedding vector_cosine_ops);
```

---

## Row Level Security

**All user data tables have RLS policies.**

**Example policy (social_accounts):**
```sql
-- Users can only see their own social accounts
CREATE POLICY "Users can view own social accounts"
ON social_accounts FOR SELECT
USING (auth.uid() = user_id);

-- Users can only insert their own social accounts
CREATE POLICY "Users can insert own social accounts"
ON social_accounts FOR INSERT
WITH CHECK (auth.uid() = user_id);
```

**Benefits:**
- Security at database level
- No accidental cross-user data leaks
- Simplifies application code

---

**Complete SQL migrations:** See `supabase/migrations/` for CREATE TABLE statements.

**Need to modify schema?** Update migration files and run `supabase db push`.
