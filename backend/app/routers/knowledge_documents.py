from app.db.session import get_authenticated_db
from fastapi import APIRouter, HTTPException, Depends, Request
from supabase import Client
from uuid import UUID
from typing import List
from app.schemas.knowledge_documents import KnowledgeDocument
router = APIRouter(prefix="/knowledge_documents", tags=["Knowledge Documents"])

@router.get("/", response_model=List[KnowledgeDocument])
async def get_knowledge_documents(
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    data = db.table("knowledge_documents").select("*").execute()
    return [KnowledgeDocument(**item) for item in data.data]

@router.get("/{document_id}", response_model=KnowledgeDocument)
async def get_knowledge_document(
    document_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    try: 
        data = db.table("knowledge_documents").select("*").eq("id", document_id).single().execute()
        return KnowledgeDocument(**data.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

  
@router.delete("/{document_id}")
async def delete_knowledge_document(
    document_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    try:
        print(f"🗑️ Deleting document: {document_id}")

        # First get the document to know bucket_id and object_name
        doc_res = db.table("knowledge_documents").select(
            "id,title,bucket_id,object_name"
        ).eq("id", document_id).single().execute()

        if doc_res.data is None:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_res.data
        bucket_id = document["bucket_id"]
        object_name = document["object_name"]

        # Delete from storage bucket if we have the info
        if bucket_id and object_name:
            try:
                storage_result = db.storage.from_(bucket_id).remove([object_name])
                print(f"🗑️ Deleted from storage:{storage_result}/{bucket_id}/{object_name}")
            except Exception as storage_error:
                print(f"⚠️ Warning: Could not delete from storage: {storage_error}")
                # Don't fail the whole operation if storage deletion fails

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

