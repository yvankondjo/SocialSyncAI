from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from supabase import Client
from app.db.session import get_authenticated_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.core.security import get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        # TODO: Ajouter vérification rôle admin quand système de rôles implémenté
        # Pour l'instant, permettre la création mais logger l'action
        print(f"User {current_user_id} is creating a new user account")

        result = db.table("users").insert({
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active
        }).execute()

        if result.data:
            return User(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        # Vérifier que l'utilisateur ne peut voir que son propre profil
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied: can only view own profile")

        # RLS applique automatiquement user_id = auth.uid(), donc pas besoin de .eq("id", user_id)
        result = db.table("users").select("*").single().execute()
        if result.data:
            return User(**result.data)
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[User])
async def list_users(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        # TODO: Ajouter vérification rôle admin quand système de rôles implémenté
        # Pour l'instant, interdire l'accès à la liste des utilisateurs
        raise HTTPException(status_code=403, detail="Access denied: admin privileges required")

        # Code pour admin (quand système de rôles sera implémenté):
        # result = db.table("users").select("*").range(offset, offset + limit - 1).execute()
        # return [User(**user) for user in result.data]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        # Vérifier que l'utilisateur ne peut modifier que son propre profil
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied: can only update own profile")

        update_data = {k: v for k, v in user_update.model_dump(exclude_unset=True).items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        # RLS applique automatiquement user_id = auth.uid(), donc pas besoin de .eq("id", user_id)
        result = db.table("users").update(update_data).execute()

        if result.data:
            return User(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="User not found or no changes made")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))