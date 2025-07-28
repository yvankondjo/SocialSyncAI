from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.session import get_db
from app.schemas import User, UserCreate, UserUpdate

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: UserCreate, db=Depends(get_db)):
    try:
        # Note: In a real app, password should be hashed before saving.
        # Supabase Auth handles this automatically if you use its auth functions.
        # Here we are inserting directly, so password handling is simplified.
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
async def get_user(user_id: str, db=Depends(get_db)):
    try:
        result = db.table("users").select("*").eq("id", user_id).single().execute()
        if result.data:
            return User(**result.data)
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[User])
async def list_users(limit: int = 10, offset: int = 0, db=Depends(get_db)):
    try:
        result = db.table("users").select("*").range(offset, offset + limit - 1).execute()
        return [User(**user) for user in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, db=Depends(get_db)):
    try:
        update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()}
        if 'role' in update_data and update_data['role']:
            update_data['role'] = update_data['role'].value

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = db.table("users").update(update_data).eq("id", user_id).execute()
        
        if result.data:
            return User(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="User not found or no changes made")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 