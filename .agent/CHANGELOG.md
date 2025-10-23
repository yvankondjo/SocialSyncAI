# Changelog - SocialSync AI

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2025-10-20

### 🎉 Major Release: Vision AI + Multi-Platform Architecture

**Breaking Changes:** None (backwards compatible)

### Added

#### Vision AI Context Enrichment
- ✅ AI can now see post images for contextual responses
- ✅ Enriched context includes:
  - Post image (Vision AI)
  - Post caption
  - Music title (placeholder, needs API integration)
  - Comment thread (up to 10 recent comments)
  - Current comment being responded to

#### Granular AI Controls
- ✅ `ai_enabled_for_comments` flag in `monitoring_rules` table
- ✅ `ai_enabled_for_conversations` flag in `ai_settings` table
- ✅ Frontend toggles in two locations:
  - MonitoringRulesPanel: "AI auto-replies on comments"
  - AI Settings page: "AI auto-replies for DMs/Chats"
- ✅ Backend enforcement in workers (fail-safe defaults)

#### Conversation Detection
- ✅ New `CommentTriageService` class
- ✅ Three detection rules:
  - @mentions check (skip if mentioning other users)
  - Reply-to-others check (skip if replying to other users)
  - Direct question check (respond only to questions)
- ✅ New triage type: 'user_conversation'

#### Multi-Platform Architecture
- ✅ Unified `BasePlatformConnector` interface
- ✅ Instagram connector fully implemented
- ✅ Facebook connector ready (needs OAuth)
- ✅ Twitter connector template provided
- ✅ Platform-agnostic comment schema

#### Debug Tools
- ✅ `/api/debug/comments/force-poll` - Force immediate polling
- ✅ `/api/debug/comments/comment-context/{id}` - View AI context
- ✅ `/api/debug/comments/test-should-respond` - Test conversation detection
- ✅ `/api/debug/comments/monitored-posts-status` - View monitoring status

#### Documentation
- ✅ `.agent/System/comment-monitoring-unified-api.md` (2000+ lines)
- ✅ `.agent/SOP/add-new-social-platform.md` (1000+ lines)
- ✅ `COMMENT_SYSTEM_IMPLEMENTATION_SUMMARY.md` (500+ lines)
- ✅ `QUICK_TEST_GUIDE.md` (300+ lines)

### Changed

#### Database Schema
- **monitored_posts**
  - Added `music_title VARCHAR(500)` - Music context for AI

- **monitoring_rules**
  - Added `ai_enabled_for_comments BOOLEAN DEFAULT TRUE`

- **ai_settings**
  - Added `ai_enabled_for_conversations BOOLEAN DEFAULT TRUE`

- **comments**
  - Added `like_count INTEGER DEFAULT 0`
  - Added `author_avatar_url TEXT`
  - Added `ai_reply_text TEXT`
  - Updated triage constraint to include 'user_conversation'

#### Backend Workers
- **comments.py** (~500 lines modified)
  - Fixed async/sync issues for Celery compatibility
  - Fixed `platform_page_id` → `account_id` field name
  - Added AI flag check before processing
  - Added conversation detection logic
  - Built enriched Vision AI context
  - Integrated RAGAgent with multimodal support

- **batch_scanner.py** (~10 lines modified)
  - Added conversation AI flag check

#### Services
- **instagram_connector.py**
  - Added `parent_id` and `like_count` to API calls
  - Updated comment normalization

- **comment_triage.py** (**NEW FILE**)
  - Conversation detection service
  - Three rule-based filters
  - LLM fallback for edge cases

#### Frontend
- **MonitoringRulesPanel.tsx**
  - Added "AI auto-replies on comments" toggle
  - Updated hasChanges logic

- **AI Settings page**
  - Added "Conversation AI Controls" card
  - Added "AI auto-replies for DMs/Chats" toggle
  - Updated state initialization

### Fixed

- ❌ → ✅ Comments not appearing in UI (polling was broken)
- ❌ → ✅ Missing `platform_page_id` causing connection errors
- ❌ → ✅ Async/sync mismatch in Celery tasks
- ❌ → ✅ Missing `parent_id` for thread support
- ❌ → ✅ AI responding to user-to-user conversations (spam)
- ❌ → ✅ No context for AI (couldn't see images, threads)
- ❌ → ✅ No granular AI controls (all-or-nothing)

### Database Migrations

1. **20251020_add_comment_fields.sql**
   - Added `like_count`, `author_avatar_url`, `ai_reply_text` to comments table

2. **20251020_add_user_conversation_triage.sql**
   - Added 'user_conversation' triage type to comments constraint

3. **20251020_add_ai_control_flags.sql**
   - Added `ai_enabled_for_comments` to monitoring_rules
   - Added `ai_enabled_for_conversations` to ai_settings
   - Professional, idempotent migration with verification

### Performance

- Adaptive polling frequency (5min → 15min → 30min based on post age)
- Cursor-based pagination (no duplicate fetches)
- Indexed queries for fast lookups
- Rate limit awareness (Instagram: 200 req/hour)

### Security

- Fail-safe AI controls (default TRUE, continue on config errors)
- No PII in logs
- Secure token handling
- HMAC webhook validation

---

## [1.5.0] - 2025-10-19

### Added
- **AI Studio** - AI-assisted content creation and scheduling
- Conversation preview before scheduling
- Model selection in UI

### Changed
- Improved scheduled posts UI
- Better error handling for post publishing

---

## [1.4.0] - 2025-10-18

### Added
- **AI Rules** - Simple IA control (instructions + ignore examples)
- **AI Moderation & Escalation** - OpenAI Moderation API + Email alerts
- **Comment Polling** - Adaptive polling for Instagram comments

### Changed
- Enhanced AI decision logging
- Improved escalation email templates

---

## [1.3.0] - 2025-10-18

### Added
- **Scheduled Posts** - Publication planifiée multi-plateformes
- Automatic retry on failure
- Post status tracking

---

## [1.2.0] - 2025-10-15

### Added
- Instagram integration (OAuth + webhooks)
- Media upload to Supabase Storage
- Basic analytics dashboard

---

## [1.1.0] - 2025-10-10

### Added
- WhatsApp Business API integration
- Message batching (Redis, 2s window)
- RAG agent for auto-replies

---

## [1.0.0] - 2025-10-01

### Initial Release
- User authentication (Supabase Auth)
- Credit system
- Basic inbox
- Subscription management (Stripe)

---

## Upgrade Guide

### From 1.x to 2.0

**Database:**
```bash
# Run migrations in order
psql < supabase/migrations/20251020_add_comment_fields.sql
psql < supabase/migrations/20251020_add_user_conversation_triage.sql
psql < supabase/migrations/20251020_add_ai_control_flags.sql
```

**Backend:**
- Restart Celery workers to load new code
- No config changes required (backwards compatible)

**Frontend:**
- Clear browser cache
- No breaking UI changes

**Testing:**
- Follow `QUICK_TEST_GUIDE.md` to verify all features work

---

## Versioning Scheme

- **Major (X.0.0)** - Breaking changes, major features
- **Minor (1.X.0)** - New features, backwards compatible
- **Patch (1.0.X)** - Bug fixes, minor improvements

---

**Next Version Preview (2.1.0):**
- Music metadata fetching from Instagram API
- Facebook OAuth completion
- Twitter integration
- Advanced analytics dashboard

---

*For detailed implementation notes, see `.agent/Tasks/COMMENT_MONITORING_V2.md`*
