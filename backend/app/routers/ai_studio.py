"""
AI Studio API Router
Endpoints for AI-assisted content creation
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from pydantic import BaseModel
from typing import Optional
import time

from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
from app.services.content_creation_agent import ContentCreationAgent, CONTENT_CREATION_SYSTEM_PROMPT
from app.deps.runtime_prod import CHECKPOINTER_POSTGRES
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/ai-studio", tags=["ai-studio"])


class ContentCreationRequest(BaseModel):
    """Request for AI content creation"""
    thread_id: str
    message: str
    model: Optional[str] = "openai/gpt-4o"
    system_prompt: Optional[str] = None


class ContentCreationResponse(BaseModel):
    """Response from AI content creation"""
    response: str
    response_time: float
    scheduled_posts: list = []
    previews: list = []


@router.post("/create", response_model=ContentCreationResponse)
async def create_content(
    request_data: ContentCreationRequest,
    req: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create social media content with AI assistance

    The AI can help you:
    - Generate post ideas and copy
    - Preview posts for different platforms
    - Schedule posts for future publication
    - Optimize content for engagement
    """
    try:
        start_time = time.time()

        agent = ContentCreationAgent(
            user_id=current_user_id,
            supabase_client=db,
            model_name=request_data.model,
            system_prompt=request_data.system_prompt or CONTENT_CREATION_SYSTEM_PROMPT,
            checkpointer=CHECKPOINTER_POSTGRES,
            max_iterations=10
        )

        config = {
            "configurable": {
                "thread_id": request_data.thread_id,
                "user_id": current_user_id,
                "checkpoint_ns": f"user:{current_user_id}:ai_studio"
            }
        }

        result = agent.invoke(request_data.message, config)

        messages_list = result.get("messages", [])
        if not messages_list:
            raise HTTPException(status_code=500, detail="No response from AI agent")

        ai_message = None
        for msg in reversed(messages_list):
            if hasattr(msg, 'content') and not hasattr(msg, 'tool_calls'):
                ai_message = msg
                break

        if not ai_message:
            ai_message = messages_list[-1]

        response_text = ai_message.content if hasattr(ai_message, 'content') else str(ai_message)
        response_time = time.time() - start_time

        scheduled_posts = [post.model_dump() for post in result.get("scheduled_posts", [])]
        previews = [preview.model_dump() for preview in result.get("previews", [])]

        return ContentCreationResponse(
            response=response_text,
            response_time=response_time,
            scheduled_posts=scheduled_posts,
            previews=previews
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating content: {str(e)}")


@router.get("/system-prompt")
async def get_system_prompt():
    """Get the default system prompt for content creation"""
    return {"system_prompt": CONTENT_CREATION_SYSTEM_PROMPT}


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    return {
        "platforms": [
            {
                "id": "instagram",
                "name": "Instagram",
                "description": "Visual storytelling with photos and videos",
                "max_chars": 2200,
                "supports_media": True,
                "best_practices": [
                    "Use high-quality images",
                    "Include relevant hashtags",
                    "First 125 characters are most important"
                ]
            },
            {
                "id": "twitter",
                "name": "Twitter",
                "description": "Short, engaging updates and conversations",
                "max_chars": 280,
                "supports_media": True,
                "best_practices": [
                    "Be concise and punchy",
                    "Use threads for longer content",
                    "Include images for better engagement"
                ]
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp",
                "description": "Direct, personal messaging",
                "max_chars": 65536,
                "supports_media": True,
                "best_practices": [
                    "Keep messages scannable",
                    "Use emojis appropriately",
                    "Consider breaking long messages"
                ]
            },
            {
                "id": "facebook",
                "name": "Facebook",
                "description": "Community engagement and updates",
                "max_chars": 63206,
                "supports_media": True,
                "best_practices": [
                    "40-80 characters get best engagement",
                    "Ask questions to drive interaction",
                    "Mix personal and promotional content"
                ]
            }
        ]
    }
