from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class KnowledgeDocument(BaseModel):
    id: UUID
    title: str
    storage_object_id: UUID
    user_id: UUID
    bucket_id: str
    object_name: str
    tsconfig: str
    lang_code: str
    status: str
    last_ingested_at: Optional[datetime] = None
    last_embedded_at: Optional[datetime] = None
    embed_model: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True