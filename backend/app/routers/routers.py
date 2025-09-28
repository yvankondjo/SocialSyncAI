from fastapi import APIRouter
from app.routers import users, social_accounts, faq_qa, process, knowledge_documents, ai_settings

api_router = APIRouter()
api_router.include_router(users.router, prefix="", tags=["users"])
api_router.include_router(social_accounts.router, prefix="", tags=["social-accounts"])
api_router.include_router(knowledge_documents.router, prefix="", tags=["knowledge-documents"])
api_router.include_router(faq_qa.router, prefix="", tags=["faq-qa"])
api_router.include_router(ai_settings.router, prefix="", tags=["ai-settings"])
api_router.include_router(process.router, prefix="", tags=["process"])