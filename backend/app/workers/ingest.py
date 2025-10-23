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




@celery.task(bind=True, name="app.workers.ingest.process_document")
def process_document_task(self, document_id: str):
    db = get_db()

    doc = db.table("knowledge_documents").select(
        "id,title,bucket_id,object_name"
    ).eq("id", document_id).single().execute().data
    if not doc:
        raise RuntimeError("Document introuvable")

    bucket_id = doc["bucket_id"]
    object_name    = doc["object_name"]

    # status -> processing
    db.table("knowledge_documents").update({"status":"processing"}).eq("id", document_id).execute()

    try:
        # 2) download
        data = db.storage.from_(bucket_id).download(object_name)

        # 3) parse
        content = parse_bytes_by_ext(data, os.path.splitext(object_name)[1].lower())

        # 4) langue
        lang_code, tsconfig = detect_language(content)
        db.table("knowledge_documents").update({"lang_code":lang_code,"tsconfig":tsconfig}).eq("id", document_id).execute()

        # 5) chunk
        chunks = split_text(content, 1024, 128)


        # run async depuis tâche sync
        chunks_ctx = asyncio.run(add_context_to_chunks(chunks, document_text=content, concurrency=8))

        # 7) préparer rows + embeddins
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
        
        # 9) status -> indexed
        db.table("knowledge_documents").update({
            "status":"indexed",
            "last_ingested_at":"now()",
        }).eq("id", document_id).execute()

    except Exception as e:
        print(f"❌ Erreur lors du traitement du document {document_id}: {e}")
        db.table("knowledge_documents").update({
            "status":"failed"
        }).eq("id", document_id).execute()
        raise


@celery.task(bind=True, name="app.workers.ingest.scan_redis_batches")
def scan_redis_batches_task(self):
    """
    Celery task to scan Redis for due message batches and process them.

    This replaces the asyncio loop in batch_scanner that runs in FastAPI process.
    Executes every 0.5s via Celery Beat for robust distributed processing.
    """
    try:
        # Import here to avoid circular dependencies
        from app.services.batch_scanner import batch_scanner

        logger.debug("[BATCH_SCAN] Starting Redis batch scan")

        # Run the async processing function
        asyncio.run(batch_scanner._process_due_conversations())

        logger.debug("[BATCH_SCAN] Batch scan completed successfully")

    except Exception as e:
        logger.error(f"[BATCH_SCAN] Error scanning Redis batches: {e}")
        # Don't raise - let Celery retry automatically
        # The next scheduled task will try again in 0.5s
