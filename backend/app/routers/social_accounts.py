from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import get_supabase_client
from app.schemas import SocialAccount, SocialAccountCreate, SocialAccountUpdate

router = APIRouter()

@router.post("/", response_model=SocialAccount)
async def create_social_account(account: SocialAccountCreate, supabase=Depends(get_supabase_client)):
    try:
        result = supabase.table("social_accounts").insert({
            "platform": account.platform.value,
            "account_id": account.account_id,
            "username": account.username,
            "display_name": account.display_name,
            "profile_url": account.profile_url,
            "is_active": account.is_active,
            "organization_id": account.organization_id
        }).execute()
        
        if result.data:
            return SocialAccount(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create social account")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 