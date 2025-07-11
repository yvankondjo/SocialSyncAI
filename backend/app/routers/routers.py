from fastapi import APIRouter
from app.routers import users, organizations, social_accounts

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(social_accounts.router, prefix="/social-accounts", tags=["social-accounts"]) 