import os, asyncio
import logging
from typing import List, Dict
from app.workers.celery_app import celery
from app.services.ingest_helpers import (
    detect_language, split_text, parse_bytes_by_ext,
    add_context_to_chunks, embed_texts
)
from app.db.session import get_db

logger = logging.getLogger(__name__)

# Global event loop for this worker process (solo pool = 1 process)
# Created once and reused across all tasks to avoid "Event loop is closed" errors
_worker_loop = None


def run_async_safe(coro):
    """
    Safely run an async coroutine in a Celery worker with a persistent event loop.

    For solo pool workers, we maintain ONE event loop for the entire worker process.
    This prevents "Event loop is closed" errors with Redis async connections.
    """
    global _worker_loop

    try:
        logger.debug(f"[DEBUG] run_async_safe: Current _worker_loop = {_worker_loop}")

        # Create the loop once for this worker process
        if _worker_loop is None:
            logger.info("[DEBUG] Creating NEW persistent event loop for Celery worker (first time)")
            _worker_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_worker_loop)
            logger.debug(f"[DEBUG] Created new loop: {id(_worker_loop)}, is_closed={_worker_loop.is_closed()}")
        elif _worker_loop.is_closed():
            logger.warning("[DEBUG] Event loop was closed! Creating a new one...")
            _worker_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_worker_loop)
            logger.debug(f"[DEBUG] Created replacement loop: {id(_worker_loop)}, is_closed={_worker_loop.is_closed()}")
        else:
            logger.debug(f"[DEBUG] Reusing existing loop: {id(_worker_loop)}, is_closed={_worker_loop.is_closed()}")

        # Run the coroutine using the persistent loop
        logger.debug(f"[DEBUG] Running coroutine: {coro}")
        result = _worker_loop.run_until_complete(coro)
        logger.debug(f"[DEBUG] Coroutine completed successfully")
        return result

    except Exception as e:
        logger.error(f"[DEBUG] Error in async task: {type(e).__name__}: {e}", exc_info=True)
        raise




@celery.task(bind=True, name="app.workers.ingest.process_document")
def process_document_task(self, document_id: str):
    db = get_db()

    doc = db.table("knowledge_documents").select(
        "id,title,bucket_id,object_name"
    ).eq("id", document_id).single().execute().data
    if not doc:
        raise RuntimeError("Document not found")

    bucket_id = doc["bucket_id"]
    object_name    = doc["object_name"]

    db.table("knowledge_documents").update({"status":"processing"}).eq("id", document_id).execute()

    try:
        data = db.storage.from_(bucket_id).download(object_name)

        content = parse_bytes_by_ext(data, os.path.splitext(object_name)[1].lower())

        lang_code, tsconfig = detect_language(content)
        db.table("knowledge_documents").update({"lang_code":lang_code,"tsconfig":tsconfig}).eq("id", document_id).execute()

        chunks = split_text(content, 1024, 128)


        # Run async from a sync Celery task
        chunks_ctx = run_async_safe(add_context_to_chunks(chunks, document_text=content, concurrency=8))

        rows: List[Dict] = []

        for idx, (txt, start, end) in enumerate(chunks_ctx):
            rows.append({
                "document_id": document_id,
                "chunk_index": idx,
                "content": txt,
                "start_char": start,
                "end_char": end,
                "token_count": len(txt.split()),
                "metadata": {},
            })


        
        if rows:
            db.table("knowledge_chunks").delete().eq("document_id", document_id).execute()

            B = 100
            nb_rows = len(rows)
            for batch_start in range(0, nb_rows, B):
                batch_end = min(batch_start + B, nb_rows)
                batch_rows = rows[batch_start:batch_end]
                batch_contents = [r["content"] for r in batch_rows]

                embs = embed_texts(batch_contents)

                for i, e in enumerate(embs):
                    batch_rows[i]["embedding"] = e

                db.table("knowledge_chunks").insert(batch_rows).execute()
        
        db.table("knowledge_documents").update({
            "status":"indexed",
            "last_ingested_at":"now()",
        }).eq("id", document_id).execute()

    except Exception as e:
        logger.exception(f"Error processing document {document_id}: {e}")
        db.table("knowledge_documents").update({
            "status":"failed"
        }).eq("id", document_id).execute()
        raise


