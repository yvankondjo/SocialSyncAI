# 🤖 RAG System

**File:** `backend/app/services/rag_agent.py`

---

## Architecture

**LangGraph state machine** pour conversations RAG avec:
- **pg_vector (Supabase)** - Recherche vectorielle
- **PostgreSQL** - Checkpoints + données
- **Google Gemini** - Embeddings (text-embedding-004, 768 dims)

---

## Data Ingestion

### 1. Upload Document

```
User uploads PDF/TXT/MD
↓
backend/app/routers/knowledge_documents.py
↓
Stored in Supabase Storage bucket "kb"
↓
Entry created in table: knowledge_documents
```

### 2. Generate Embeddings

**File:** `backend/app/services/ingest_helpers.py`

```python
# 1. Extract text from document
text = extract_text(file_path)

# 2. Chunk text (1000 chars, 200 overlap)
chunks = chunk_text(text, chunk_size=1000, overlap=200)

# 3. Generate embeddings via Google Gemini
embeddings = embed_texts(chunks)  # Returns List[List[float]]

# 4. Store in PostgreSQL
for chunk, embedding in zip(chunks, embeddings):
    db.table("knowledge_chunks").insert({
        "user_id": user_id,
        "document_id": document_id,
        "content": chunk,
        "embedding": embedding  # vector(768)
    })
```

**Table:** `knowledge_chunks`
- `id` - UUID
- `user_id` - UUID (RLS)
- `document_id` - FK → knowledge_documents
- `content` - text
- `embedding` - vector(768) **[pg_vector]**
- `tsv` - tsvector (for BM25)

**Index:** `CREATE INDEX idx_kc_embed ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);`

---

## Vector Search

### Hybrid Search (BM25 + Vector)

**File:** `backend/app/services/retriever.py`

```python
retriever = Retriever(user_id)

# Hybrid search
results = retriever.retrieve_from_knowledge_chunks(
    query="refund policy",
    k=5,
    type='hybrid'  # or 'vector' or 'text'
)
```

**Supabase Function:** `hybrid_knowledge_chunks_search_v2()`

```sql
-- Combines BM25 (text) + vector similarity
-- Uses Reciprocal Rank Fusion (RRF)
SELECT
    c.id,
    c.content,
    1.0 / (rrf_k + bm25_rank) + 1.0 / (rrf_k + vector_rank) AS score
FROM knowledge_chunks c
WHERE c.user_id = p_user_id
ORDER BY score DESC
LIMIT match_count;
```

---

## LangGraph Agent

### State

```python
class State(TypedDict):
    messages: List[BaseMessage]  # Conversation
    conversation_history: List[Dict]  # DB history
    retry_count: int
```

### Graph Flow

```
__start__
  ↓
check_conversation_state (load history from DB)
  ↓
retrieve_context (hybrid search if needed)
  ↓
call_llm (generate response)
  ↓
has tool_calls? ──Yes→ tool_execution ──→ call_llm (loop)
  ↓ No
__end__
```

### Tools Available

**File:** `backend/app/services/rag_agent.py`

```python
# 1. search_knowledge
@tool
def search_knowledge(query: str) -> str:
    results = retriever.retrieve_from_knowledge_chunks(query, k=5, type='hybrid')
    return format_results(results)

# 2. find_answers (FAQ)
@tool
def find_answers(question: str) -> str:
    answer = faq_service.find_answer(question)
    return answer or "No FAQ found"

# 3. escalation
@tool
def escalation(message: str, confidence: float, reason: str) -> EscalationResult:
    escalation_id = escalation_service.create_escalation(message, confidence, reason)
    # Disables AI for conversation (ai_mode=OFF)
    return EscalationResult(escalated=True, escalation_id=escalation_id)
```

---

**File:** `backend/app/services/rag_agent.py:608`


**Why?**
- `structured_llm` forces JSON output → blocks tool calls
- `llm_with_tools` allows both text AND tool calls

---

## Checkpoints

### PostgreSQL Persistence

**Tables:**
- `checkpoints` - State snapshots
- `checkpoint_writes` - Write operations
- `checkpoint_blobs` - Serialized data

```python
checkpointer = PostgresSaver.from_conn_string(SUPABASE_DB_URL)
graph = workflow.compile(checkpointer=checkpointer)

# Invoke with thread_id
response = graph.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config={"configurable": {"thread_id": conversation_id}}
)
```

**Result:** Conversation state persists across worker restarts

---

## Example Flow

```
User: "What is your refund policy?"
  ↓
RAG Agent: retrieve_context()
  ↓
Retriever: hybrid_search("refund policy") → 5 chunks
  ↓
LLM: Generate response using chunks as context
  ↓
AI: "Our refund policy is 30 days..."
```

---

## Key Files

| File | Purpose |
|------|---------|
| `services/rag_agent.py` | LangGraph agent |
| `services/retriever.py` | Vector search |
| `services/find_answers.py` | FAQ search |
| `services/ingest_helpers.py` | Document chunking + embeddings |
| `routers/knowledge_documents.py` | Upload API |

**SQL:** `/workspace/supabase/migrations/20251018192723_remote_schema.sql`
- `hybrid_knowledge_chunks_search_v2()`
- `vector_knowledge_chunks_search_v2()`
- `text_knowledge_chunks_search_v2()`

---

**Last Updated:** 2025-10-30
