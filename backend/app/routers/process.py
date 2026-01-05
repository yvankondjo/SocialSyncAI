# app/routers/process.py
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.workers.ingest import process_document_task
router = APIRouter(prefix="/functions/v1", tags=["Ingestion"])

class ProcessDocumentRequest(BaseModel):
    document_id: str = Field(..., description="ID du document à traiter")

@router.post("/process")
async def process_document(request: ProcessDocumentRequest, authorization: Optional[str] = Header(None)):
    try:
        task = process_document_task.delay(request.document_id)
        return {"document_id": request.document_id, "job_id": task.id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
