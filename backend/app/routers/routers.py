from fastapi import APIRouter
from app.routers import users, social_accounts, analytics

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(social_accounts.router, prefix="/social-accounts", tags=["social-accounts"]) 
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])