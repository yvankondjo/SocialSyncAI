from app.db.session import get_authenticated_db
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from supabase import Client
from uuid import UUID
from typing import List
import logging
import uuid as uuid_lib
from app.schemas.knowledge_documents import KnowledgeDocument
from app.core.security import get_current_user_id
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge_documents", tags=["Knowledge Documents"])

@router.post("/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
    storage_service = Depends(get_storage_service)
):
    """
    Upload un document de connaissance avec vérification du quota de stockage.
    Le fichier est vérifié côté backend avant d'être uploadé au bucket.
    """
    try:
        # Vérifier le type de fichier
        allowed_extensions = ['.pdf', '.txt', '.md']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté. Seuls PDF, TXT et MD sont acceptés."
            )
        
        # Lire le fichier pour obtenir sa taille
        file_content = await file.read()
        file_size_bytes = len(file_content)
        
        # Vérifier la taille maximale (10 MB)
        max_size_bytes = 10 * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Fichier trop volumineux ({file_size_bytes / (1024 * 1024):.1f} MB). Maximum 10 MB."
            )
        
        # Vérifier le quota de stockage
        can_upload, usage = await storage_service.check_storage_available(current_user_id, file_size_bytes)
        
        if not can_upload:
            file_size_mb = file_size_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"Quota de stockage insuffisant. Disponible: {usage.available_mb:.2f} MB, Requis: {file_size_mb:.2f} MB"
            )
        
        # Générer un nom unique pour le fichier
        file_path = f"{uuid_lib.uuid4()}/{file.filename}"
        
        # Uploader vers le bucket Supabase
        upload_result = db.storage.from_("kb").upload(
            file_path,
            file_content,
            {
                "content-type": file.content_type or "application/octet-stream",
                "cache-control": "3600",
                "upsert": "false"
            }
        )
        
        logger.info(f"✅ Document uploadé: {file.filename} ({file_size_bytes} bytes) pour utilisateur {current_user_id}")
        
        return {
            "success": True,
            "message": f"Document {file.filename} uploadé avec succès",
            "file_path": file_path,
            "file_size_bytes": file_size_bytes,
            "storage_usage": {
                "used_mb": usage.used_mb,
                "quota_mb": usage.quota_mb,
                "available_mb": usage.available_mb
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")


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

        if doc_res.data is None or doc_res.data == []:
            raise HTTPException(status_code=404, detail="Document not found")
        print(f"🗑️ Document found: {doc_res.data}")
        document = doc_res.data
        bucket_id = document["bucket_id"]
        object_name = document["object_name"]
        print(f"🗑️ Bucket ID: {bucket_id}")
        print(f"🗑️ Object Name: {object_name}")

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

