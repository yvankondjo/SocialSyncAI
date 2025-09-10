from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Dict, Any
from uuid import UUID
from supabase import Client
from app.core.security import get_current_user_id
from app.services.content_service import content_service
from app.schemas.content import Content, ContentCreate, ContentUpdate
from app.db.session import get_authenticated_db

router = APIRouter(prefix="/content", tags=["content"])

@router.post("/", response_model=Content)
async def create_new_content(
    content: ContentCreate,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    user_id = UUID(current_user_id)
    return await content_service.create_content(db=db, content=content, user_id=user_id)

@router.get("/", response_model=List[Content])
async def read_user_content(
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    user_id = UUID(current_user_id)
    return await content_service.get_all_content_for_user(db=db, user_id=user_id)

@router.get("/{content_id}", response_model=Content)
async def read_content_by_id(
    content_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    # TODO: Ajouter une vérification que l'utilisateur a le droit de voir ce contenu
    return await content_service.get_content_by_id(db=db, content_id=content_id)

@router.put("/{content_id}", response_model=Content)
async def update_existing_content(
    content_id: UUID,
    content: ContentUpdate,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    # TODO: Ajouter une vérification que l'utilisateur a le droit de modifier ce contenu
    return await content_service.update_content(db=db, content_id=content_id, content=content)

@router.delete("/{content_id}", status_code=204)
async def delete_existing_content(
    content_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    # TODO: Ajouter une vérification que l'utilisateur a le droit de supprimer ce contenu
    await content_service.delete_content(db=db, content_id=content_id)
    return