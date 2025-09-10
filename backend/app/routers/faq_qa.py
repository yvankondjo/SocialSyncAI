from app.db.session import get_authenticated_db
from fastapi import APIRouter, HTTPException, Depends, Request
from supabase import Client
from uuid import UUID
from typing import List
from app.schemas.faq_qa_service import FAQQA, FAQQACreate, FAQQAUpdate, FAQQASearch

router = APIRouter(prefix="/faq-qa", tags=["FAQ Q&A"])


@router.get("/", response_model=List[FAQQA])
async def get_faq_qa_list(
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Récupère toutes les FAQ Q&A de l'utilisateur connecté"""
    try:
        data = db.table("faq_qa").select("*").execute()
        return [FAQQA(**item) for item in data.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la récupération des FAQ: {str(e)}")


@router.get("/{faq_id}", response_model=FAQQA)
async def get_faq_qa(
    faq_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Récupère une FAQ Q&A spécifique"""
    try:
        data = db.table("faq_qa").select("*").eq("id", faq_id).single().execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")
        return FAQQA(**data.data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la récupération de la FAQ: {str(e)}")


@router.post("/", response_model=FAQQA)
async def create_faq_qa(
    faq_data: FAQQACreate,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Crée une nouvelle FAQ Q&A"""
    print(f"Création d'une nouvelle FAQ Q&A: {faq_data}")
    try:
        # Récupérer l'utilisateur authentifié
        user_response = db.auth.get_user()
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Utilisateur non authentifié")
        print(f"Utilisateur authentifié: {user_response.user}")

        user_id = user_response.user.id
        print(f"ID de l'utilisateur: {user_id}")

        # Préparer les métadonnées avec les tags si présents
        metadata = faq_data.metadata.copy() if faq_data.metadata else {}

        # Gérer les tags depuis metadata.context si présent
        if "context" in metadata and isinstance(metadata["context"], list):
            tags = metadata["context"]
            print(f"Tags lors de la création: {tags}")
            # Vous pouvez traiter les tags ici (indexation, etc.)

        # Utiliser les propriétés calculées du schéma pour lang_code et tsconfig
        data = {
            "user_id": user_id,
            "title": faq_data.title,
            "question": faq_data.question,
            "answer": faq_data.answer,
            "lang_code": faq_data.lang_code,
            "tsconfig": faq_data.tsconfig,
            "metadata": metadata
        }

        result = db.table("faq_qa").insert(data).execute()
        return FAQQA(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création de la FAQ: {str(e)}")


@router.put("/{faq_id}", response_model=FAQQA)
async def update_faq_qa(
    faq_id: UUID,
    faq_data: FAQQAUpdate,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Met à jour une FAQ Q&A"""
    try:
        existing = db.table("faq_qa").select("*").eq("id", faq_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")

    
        update_data = {k: v for k, v in faq_data.model_dump().items() if v is not None}

        if hasattr(faq_data, 'language') and faq_data.language is not None:
            update_data["lang_code"] = faq_data.lang_code
            update_data["tsconfig"] = faq_data.tsconfig

        
        if "metadata" in update_data and update_data["metadata"]:
            metadata = update_data["metadata"]
            if "context" in metadata and isinstance(metadata["context"], list):
               
                tags = metadata["context"]
        update_data["updated_at"] = "now()"

        result = db.table("faq_qa").update(update_data).eq("id", faq_id).execute()
        return FAQQA(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la mise à jour de la FAQ: {str(e)}")


@router.patch("/{faq_id}", response_model=FAQQA)
async def patch_faq_qa(
    faq_id: UUID,
    faq_data: FAQQAUpdate,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Met à jour partiellement une FAQ Q&A"""
    try:
        existing = db.table("faq_qa").select("*").eq("id", faq_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")

        update_data = {k: v for k, v in faq_data.model_dump().items() if v is not None}
        if hasattr(faq_data, 'language') and faq_data.language is not None:
            update_data["lang_code"] = faq_data.lang_code
            update_data["tsconfig"] = faq_data.tsconfig


        if "metadata" in update_data and update_data["metadata"]:
            metadata = update_data["metadata"]
            if "context" in metadata and isinstance(metadata["context"], list):
                tags = metadata["context"]
               

        update_data["updated_at"] = "now()"

        result = db.table("faq_qa").update(update_data).eq("id", faq_id).execute()
        return FAQQA(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la mise à jour partielle de la FAQ: {str(e)}")


@router.patch("/{faq_id}/toggle")
async def toggle_faq_qa(
    faq_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Active/désactive une FAQ Q&A (soft delete avec toggle)"""
    try:
        # Vérifier que la FAQ existe
        existing = db.table("faq_qa").select("*").eq("id", faq_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")

        current_status = existing.data.get("is_active", True)
        new_status = not current_status

        # Soft delete/activate via is_active
        result = db.table("faq_qa").update({
            "is_active": new_status,
            "updated_at": "now()"
        }).eq("id", faq_id).execute()

        print(f"FAQ {faq_id} {'activée' if new_status else 'désactivée'}")
        return {
            "message": f"FAQ {'activée' if new_status else 'désactivée'} avec succès",
            "is_active": new_status
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors du toggle de la FAQ {faq_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur lors du toggle de la FAQ: {str(e)}")


@router.delete("/{faq_id}")
async def delete_faq_qa(
    faq_id: UUID,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Supprime définitivement une FAQ Q&A (hard delete)"""
    try:
        # Vérifier que la FAQ existe avant de la supprimer
        existing = db.table("faq_qa").select("*").eq("id", faq_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")

        # Suppression définitive (hard delete)
        db.table("faq_qa").delete().eq("id", faq_id).execute()
        print(f"FAQ {faq_id} supprimée définitivement")
        return {"message": "FAQ supprimée définitivement avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la suppression de la FAQ {faq_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur lors de la suppression de la FAQ: {str(e)}")


@router.post("/search", response_model=List[FAQQA])
async def search_faq_qa(
    search_data: FAQQASearch,
    request: Request,
    db: Client = Depends(get_authenticated_db)
):
    """Recherche full-text dans les FAQ Q&A"""
    try:
        # Recherche full-text avec ranking (sans filtre is_active car hard delete)
        query = f"""
        SELECT *, ts_rank(tsv, plainto_tsquery('simple', %s)) as rank
        FROM faq_qa
        WHERE tsv @@ plainto_tsquery('simple', %s)
        ORDER BY rank DESC
        LIMIT %s OFFSET %s
        """

        result = db.rpc('execute_sql', {
            'sql': query,
            'params': [
                search_data.query,
                search_data.query,
                search_data.limit,
                search_data.offset
            ]
        }).execute()

        return [FAQQA(**item) for item in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la recherche: {str(e)}")
