# 📚 Knowledge Base

Vector-powered knowledge management with **pg_vector** (Supabase) and hybrid search (BM25 + Vector).

---

## Overview

Upload documents (PDF/TXT/MD/DOCX) that AI uses to answer customer questions:
- **Vector Search** - pg_vector (PostgreSQL extension)
- **Hybrid Search** - BM25 (keyword) + Vector (semantic)
- **Embeddings** - Google Gemini text-embedding-004 (768 dims, FREE)
- **Chunking** - 1000 chars, 200 overlap
- **Multilingual** - French, English, Spanish

---

## Architecture

### Stack

- **Storage:** Supabase Storage bucket `kb`
- **Database:** PostgreSQL with pg_vector extension
- **Embeddings:** Google Gemini API (FREE)
- **Search:** SQL functions (`hybrid_knowledge_chunks_search_v2`)

### Why Hybrid Search?

**BM25 (Keyword):**
- Exact term matching
- Good for specific words ("refund policy")

**Vector (Semantic):**
- Understands meaning
- Catches synonyms ("get money back" → "refund")

**Hybrid = Best of both:**
```sql
-- Reciprocal Rank Fusion (RRF)
final_score = 1/(rrf_k + bm25_rank) + 1/(rrf_k + vector_rank)
```

### Why Google Gemini Embeddings?

| Provider | Model | Dims | Cost/1M | Quality |
|----------|-------|------|---------|---------|
| OpenAI | text-embedding-3-small | 1536 | $0.02 | ⭐⭐⭐⭐ |
| **Google** | **text-embedding-004** | **768** | **FREE** | **⭐⭐⭐⭐⭐** |

**Benefits:**
- FREE (vs $0.02/1M OpenAI)
- 768 dims (50% less storage than OpenAI's 1536)
- Excellent multilingual support
- High MTEB score (67.3 vs 62.5 ada-002)

---

## Document Ingestion

**File:** `backend/app/routers/knowledge_documents.py`

```
1. User uploads PDF/TXT/MD
   ↓
2. Store in Supabase Storage bucket "kb"
   ↓
3. Extract text
   ↓
4. Chunk text (1000 chars, 200 overlap)
   ↓
5. Generate embeddings via Gemini
   ↓
6. Store in knowledge_chunks table:
   - content: text
   - embedding: vector(768)
   - tsv: tsvector (for BM25)
```

**Table:** `knowledge_chunks`
```sql
CREATE TABLE knowledge_chunks (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    document_id uuid REFERENCES knowledge_documents(id),
    content text NOT NULL,
    embedding vector(768),  -- pg_vector
    tsv tsvector,  -- for BM25
    created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_kc_embed ON knowledge_chunks
USING hnsw (embedding vector_cosine_ops);
```

---

## Vector Search

**File:** `backend/app/services/retriever.py`

```python
retriever = Retriever(user_id)

# Hybrid search (BM25 + vector)
results = retriever.retrieve_from_knowledge_chunks(
    query="refund policy",
    k=5,
    type='hybrid'  # or 'vector' or 'text'
)
```

**Supabase SQL Function:**
```sql
-- /workspace/supabase/migrations/20251018192723_remote_schema.sql
CREATE FUNCTION hybrid_knowledge_chunks_search_v2(
    p_user_id uuid,
    query_text text,
    query_embedding vector(768),
    query_lang text DEFAULT 'simple',
    match_count int DEFAULT 10,
    rrf_k int DEFAULT 10
) RETURNS json AS $$
    -- BM25 text search
    WITH text_results AS (
        SELECT id, ts_rank(tsv, query) AS rank_text
        FROM knowledge_chunks
        WHERE user_id = p_user_id AND tsv @@ query::tsquery
    ),
    -- Vector similarity search
    vector_results AS (
        SELECT id, -(embedding <#> query_embedding) AS rank_vec
        FROM knowledge_chunks
        WHERE user_id = p_user_id
    )
    -- Reciprocal Rank Fusion
    SELECT c.*,
           1.0/(rrf_k + t.rank_text) + 1.0/(rrf_k + v.rank_vec) AS score
    FROM knowledge_chunks c
    JOIN text_results t ON c.id = t.id
    JOIN vector_results v ON c.id = v.id
    ORDER BY score DESC
    LIMIT match_count;
$$ LANGUAGE sql;
```

---

## FAQ Management

**File:** `backend/app/services/find_answers.py`

**Table:** `faq_qa`
```sql
CREATE TABLE faq_qa (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    questions text[] NOT NULL,  -- Multiple phrasings
    answer text NOT NULL,
    is_active boolean DEFAULT true
);
```

**Usage:**
```python
find_answers = FindAnswers(user_id)
answer = find_answers.find_answers("What are your business hours?")
# Returns: Answer object with content, grade (full/partial/no-answer)
```

---

## Configuration

**File:** `backend/app/core/config.py`

```python
# Chunking
CHUNK_SIZE = 1000  # chars
CHUNK_OVERLAP = 200  # chars

# Search
HYBRID_SEARCH_K = 5  # top-k results
SIMILARITY_THRESHOLD = 0.6  # min cosine similarity

# Storage
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx']
```

---

## Key Files

| File | Purpose |
|------|---------|
| `routers/knowledge_documents.py` | Upload API |
| `services/retriever.py` | Hybrid search |
| `services/find_answers.py` | FAQ search |
| `services/ingest_helpers.py` | Chunking + embeddings |
| `supabase/migrations/20251018192723_remote_schema.sql` | SQL functions |

---

**Last Updated:** 2025-10-30
