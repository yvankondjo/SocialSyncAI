from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.supabase import get_supabase_client
from app.schemas import Organization, OrganizationCreate, OrganizationUpdate, SocialAccount

router = APIRouter()

@router.post("/", response_model=Organization)
async def create_organization(org: OrganizationCreate, supabase=Depends(get_supabase_client)):
    try:
        result = supabase.table("organizations").insert({
            "name": org.name,
            "description": org.description,
            "type": org.type.value,
            "website": org.website,
            "industry": org.industry,
            "owner_id": org.owner_id
        }).execute()
        
        if result.data:
            return Organization(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create organization")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{org_id}", response_model=Organization)
async def get_organization(org_id: str, supabase=Depends(get_supabase_client)):
    try:
        result = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
        if result.data:
            return Organization(**result.data)
        else:
            raise HTTPException(status_code=404, detail="Organization not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{org_id}/social-accounts", response_model=List[SocialAccount])
async def list_social_accounts_for_organization(org_id: str, supabase=Depends(get_supabase_client)):
    try:
        result = supabase.table("social_accounts").select("*").eq("organization_id", org_id).execute()
        return [SocialAccount(**account) for account in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 