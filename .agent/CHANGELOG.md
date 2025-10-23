# Changelog - SocialSync AI

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.4.0] - 2025-10-23

### 🔒 Major: RAG Agent Silent Error Handling & Guardrails

**Breaking Changes:**
- ⚠️ `RAGAgentState.messages` now uses `add_messages` reducer instead of `operator.add`
- ⚠️ `_call_llm()` returns `AIMessage` instead of `RAGAgentResponse`

### Added

#### Silent Error Handling System
- ✅ **Guardrail PRE-check** with silent blocking
  - Checks OpenAI Moderation API + custom rules before LLM call
  - Sets `should_respond=False` and `error_message="GUARDRAIL_PRE_BLOCKED"`
  - No user-facing message generated
  - Logs decision in `ai_decisions` table
- ✅ **Guardrail POST-check** with message removal
  - Checks OpenAI Moderation on generated AI response
  - Removes AI message + triggering user message from context via `RemoveMessage`
  - Prevents context pollution (messages stay out of LLM history)
  - Sets `should_respond=False` and `error_message="GUARDRAIL_POST_BLOCKED"`
- ✅ **Retry logic** with exponential backoff
  - 3 automatic retries on LLM errors (API down, rate limit, etc.)
  - Exponential backoff: 2s, 4s, 8s
  - Silent failure after max retries (`should_respond=False`)
  - Logs: `[LLM RETRY] Attempt X/3 failed`
- ✅ **Error handler node** for all error types
  - Central node for all guardrail blocks and LLM errors
  - Categorizes errors (PRE/POST guardrail, LLM error)
  - Logs silently, no user-facing messages
  - Logs: `[SILENT FAILURE] {type}`

#### State Management
- ✅ Added `should_respond: bool = True` to `RAGAgentState`
  - Controls whether AI should generate a response
  - Set to `False` by guardrails/errors to prevent generation
- ✅ Added `retry_count: int = 0` to `RAGAgentState`
  - Tracks number of LLM retry attempts
  - Max 3 retries before silent failure

#### Graph Structure
- ✅ New decision functions:
  - `_check_llm_result()`: Routes to error/tool_call/end
  - `_check_should_respond()`: Routes to blocked/ok after POST-check
- ✅ New error handler node routes:
  - `guardrails_pre_check` → `error_handler` (if blocked)
  - `llm` → `error_handler` (if error after retries)
  - `guardrails_post_check` → `error_handler` (if response flagged)

### Fixed

#### Critical Bug: RemoveMessage Not Working
- 🚨 **CRITICAL:** Changed `messages` reducer from `operator.add` to `add_messages`
  - `RemoveMessage` **REQUIRES** `add_messages` reducer to work
  - Without this, message removal would silently fail
  - Impact: Messages now get auto-assigned UUIDs
  - Impact: Deduplication by ID enabled
  - **File:** `backend/app/services/rag_agent.py` line 13, 144
- ✅ Added safety checks for message IDs before removal
  - Validates `message.id` exists before creating `RemoveMessage`
  - Logs warning if ID missing: `[GUARDRAILS POST] Message has no ID`

### Changed

#### LLM Response Format
- ⚠️ `_call_llm()` now returns `AIMessage` instead of `RAGAgentResponse`
  - Old: `return {"messages": [RAGAgentResponse(...)]}`
  - New: `return {"messages": [AIMessage(content=response.response)]}`
  - Required for LangGraph message compatibility

#### Error Behavior
- ✅ LLM errors no longer generate "Désolé..." messages
  - Old: `return {"messages": [AIMessage(content="Désolé, une erreur...")]}`
  - New: `return {"should_respond": False, "error_message": "LLM_ERROR:..."}`
- ✅ Credit limit errors also silent
  - Returns `should_respond=False` instead of error message

### Documentation

#### New Files
- ✅ `.agent/System/RAG_AGENT_ERROR_HANDLING.md`
  - Complete technical documentation
  - Architecture diagrams
  - Testing procedures
  - 50+ sections
- ✅ `/workspace/RAG_AGENT_SILENT_ERROR_HANDLING.md`
  - Detailed implementation guide
  - Configuration examples
  - Logging patterns
- ✅ `/workspace/RAG_AGENT_ERROR_FLOW_SUMMARY.md`
  - ASCII flow diagrams for 4 scenarios
  - Before/after comparisons
- ✅ `/workspace/CRITICAL_FIXES_AND_VALIDATION.md`
  - Bug fix report
  - Validation results
  - Testing checklist

#### Test Files
- ✅ `backend/test_rag_logic_validation.py` (✅ 7/7 PASS)
  - State validation
  - Graph structure
  - Decision functions
  - Message IDs generation
- ✅ `backend/test_rag_real_scenarios.py` (⚠️ requires credentials)
  - Integration tests with Supabase
  - Guardrails with real rules
  - OpenAI Moderation tests
- ✅ `backend/test_rag_retry_logic.py` (⚠️ partial)
  - Retry behavior validation
  - Credit limit handling

### Testing Status

| Component | Status | Notes |
|-----------|--------|-------|
| Logic validation | ✅ 7/7 PASS | All tests passing |
| State management | ✅ Validated | Fields present, correct types |
| Graph structure | ✅ Validated | 7 nodes, correct routing |
| Message IDs | ✅ Validated | Auto-generated UUIDs |
| Guardrails logic | ✅ Validated | Routes correctly |
| **Guardrails + OpenAI** | ⚠️ **Manual test required** | Need OPENAI_API_KEY |
| **Retry with real API** | ⚠️ **Manual test required** | Need API down simulation |
| **Production readiness** | ⚠️ **70%** | Code ready, needs integration tests |

### Migration Notes

⚠️ **BREAKING CHANGE**: If you have code that:
1. Depends on duplicate messages in state → Behavior changed (now deduplicated)
2. Parses `RAGAgentResponse.confidence` from messages → Now returns `AIMessage`
3. Expects error messages like "Désolé..." → Now silent failure

### Deployment Checklist

Before production:
- [ ] Test guardrails PRE with real Supabase rules
- [ ] Test guardrails POST with OpenAI Moderation
- [ ] Test retry logic with API down simulation
- [ ] Test message IDs persistence with checkpointer
- [ ] Verify `ai_decisions` table receives entries
- [ ] Verify logs show `[SILENT FAILURE]` correctly
- [ ] Test regression (existing features still work)

---

## [2.3.0] - 2025-10-23

### 🧹 Refactoring: AutomationService Architecture Unification

**Breaking Changes:** None (fully backwards compatible)

### Changed

#### AutomationService Refactored
- ✅ **Unified architecture** for conversations AND comments
  - Added `context_type` parameter ("chat" or "comment")
  - Added `comment_id` parameter for comment automation checks
  - New method: `_check_comment_automation()` for comment rules
  - Existing method: `_check_conversation_automation()` unchanged
- ✅ **Eliminated code duplication** in `workers/comments.py`
  - Removed 45 lines of direct `monitoring_rules` checks
  - Now uses `AutomationService.should_auto_reply(context_type="comment")`
  - 78% code reduction (45 lines → 10 lines)

### Removed
- ❌ **Deleted dead code:** `backend/app/services/auto_reply_service.py`
  - 76 lines removed
  - 0 imports found in codebase (never used)
  - Replaced by `ai_settings` + `AutomationService`
- ❌ **Cleaned up database:** `auto_reply_settings` table
  - Migration created: `20251023_drop_auto_reply_settings.sql`
  - Table was orphaned (no active usage)

### Fixed
- ✅ Fixed `routers/automation.py` signature
  - Removed obsolete `message_content` parameter
  - Added explicit `context_type="chat"`
  - Fixed `toggle_conversation_automation()` to update DB directly

### Added

#### Documentation
- ✅ `.agent/System/AUTOMATION_SERVICE.md` - Complete architecture guide
  - Architecture before/after diagrams
  - Flow decision for chats and comments
  - Usage examples (batch_scanner, workers, routers)
  - Difference with AIDecisionService
  - Validation tests checklist
- ✅ `AUTOMATION_REFACTORING_SUMMARY.md` - Refactoring summary
  - Detailed changelist
  - Metrics (111 lines removed, architecture 10x cleaner)
  - Test results (100% passing)

#### Testing
- ✅ `backend/test_automation_refactoring.py` - Automated validation
  - 8 tests covering imports, signatures, methods
  - Verifies code mort deleted
  - Checks migration created
  - Validates documentation updated

### Database Migrations
- ✅ `migrations/20251023_drop_auto_reply_settings.sql`
  - Idempotent (uses IF EXISTS)
  - Removes orphaned table

### Performance
- **No impact** - Refactoring only (same logic, cleaner code)
- **Maintenance improvement** - Single source of truth for automation checks

### Architecture Benefits
- ✅ **DRY principle** - Don't Repeat Yourself (logic centralized)
- ✅ **Easier testing** - Test AutomationService once, workers reuse
- ✅ **Consistency** - Same service for DMs and comments
- ✅ **Maintainability** - Change automation logic in one place

### Related Documentation
- See `.agent/System/AUTOMATION_SERVICE.md` for complete architecture
- See `AUTOMATION_REFACTORING_SUMMARY.md` for detailed changelist

---

## [2.2.0] - 2025-10-21

### 🎉 Major Release: Topic Modeling + Gemini Optimization

**Breaking Changes:** None (fully backwards compatible)

### Added

#### Topic Modeling System (BERTopic + Gemini)
- ✅ **Automatic clustering** of user conversations with BERTopic
  - UMAP dimension reduction
  - HDBSCAN clustering algorithm
  - c-TF-IDF topic extraction
  - Min cluster size: 10 messages
- ✅ **Gemini embeddings** (768 dimensions, task_type='clustering')
  - Optimized for topic modeling
  - 100% free (Gemini quota: 15M/month)
  - Batch processing (100 messages max)
- ✅ **Topic naming** with Gemini 2.5 Flash
  - Descriptive labels (2-4 words)
  - Batch processing (10-20 topics per call)
  - Fallback to keyword-based labels
- ✅ **Incremental learning** with merge_models
  - Biweekly refit (every 2 days)
  - Merge old + new models
  - Preserve historical knowledge
- ✅ **Multi-tenant architecture**
  - Isolated per user_id
  - RLS policies on all tables
  - Separate model storage per user

#### Database Schema
- ✅ New table: `message_embeddings`
  - vector(768) for Gemini embeddings
  - IVFFlat index for similarity search
  - Unique constraint per message
- ✅ New table: `bertopic_models`
  - Model version tracking
  - Storage path references
  - Active model flag (one per user)
  - JSONB metadata (topic labels, hyperparams)
- ✅ Updated table: `topic_analysis`
  - Now populated by BERTopic
  - Gemini-generated labels
  - Sample messages per topic

#### Celery Tasks
- ✅ New queue: `topics` for topic modeling
- ✅ Daily inference task (3:00 AM UTC)
  - Transform new messages with active model
  - Update topic_analysis table
  - ~10-15s per user
- ✅ Biweekly refit task (4:00 AM UTC, every 2 days)
  - Merge new data with existing model
  - Upload new version to Supabase Storage
  - ~40-120s per user
- ✅ Manual fit task
  - One-time initial model creation
  - Triggered when user enables topic modeling

#### Supabase Storage
- ✅ New bucket: `bertopic-models`
  - Private access with RLS
  - safetensors format (4x faster than pickle)
  - Versioned model files per user

#### Infrastructure Optimization
- ✅ **Refactored embed_texts()** function
  - Added `task_type` parameter (configurable)
  - Supports: clustering, retrieval_document, classification, etc.
  - Reused across RAG + topic modeling
- ✅ **97% cost reduction** vs OpenAI
  - Embeddings: $0.20/mo → FREE ✅
  - Topic naming: $2.50/mo → $0.08/mo
  - Storage: 50% reduction (768d vs 1536d)

### Documentation
- ✅ `.agent/System/TOPIC_MODELING.md` - Complete system documentation
- ✅ `TOPIC_MODELING_GEMINI_REFACTOR.md` - Refactoring details
- ✅ `TOPIC_MODELING_PERFORMANCE.md` - Performance guide & scaling
- ✅ Updated README.md with V2.2 statistics

### Performance
- **Daily inference:** 10-15s per user (150-200 users max with 50min timeout)
- **Biweekly refit:** 40-120s per user (50-70 users max with 90min timeout)
- **Embeddings latency:** 150-400ms per batch of 100 messages
- **Topic naming latency:** 1-2s for 20 topics (batch)

### Related Issues
- Closes #topic-modeling
- Implements `.agent/Tasks/CLUSTERING.md`

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
