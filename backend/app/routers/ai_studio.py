"""
AI Studio API Router
Endpoints for AI-assisted content creation
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from pydantic import BaseModel
from typing import Optional, List
import time
import logging

from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
from app.services.content_creation_agent import (
    ContentCreationAgent,
    CONTENT_CREATION_SYSTEM_PROMPT,
)
from app.deps.runtime_prod import CHECKPOINTER_POSTGRES
from app.schemas.ai_studio_settings import (
    AIStudioSettings,
    AIStudioSettingsUpdate,
    AIStudioSettingsCreate,
)
from app.schemas.ai_studio_conversations import (
    ConversationMetadata,
    ConversationMetadataUpdate,
    ConversationMessages,
    ConversationListResponse,
    MessageItem,
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)

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
    current_user_id: str = Depends(get_current_user_id),
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

        settings_result = (
            db.table("ai_studio_settings")
            .select("*")
            .eq("user_id", current_user_id)
            .execute()
        )

        if settings_result.data and len(settings_result.data) > 0:
            settings = settings_result.data[0]
            model_to_use = request_data.model or settings.get(
                "default_model", "openai/gpt-4o"
            )
            system_prompt_to_use = (
                CONTENT_CREATION_SYSTEM_PROMPT
                + "\n\n"
                + settings.get("default_system_prompt")
                if settings.get("default_system_prompt")
                else (
                    "" + "\n\n" + request_data.system_prompt
                    if request_data.system_prompt
                    else ""
                )
            )
        else:
            model_to_use = request_data.model or "openai/gpt-4o"
            system_prompt_to_use = (
                CONTENT_CREATION_SYSTEM_PROMPT + "\n\n" + request_data.system_prompt
                if request_data.system_prompt
                else ""
            )

        agent = ContentCreationAgent(
            user_id=current_user_id,
            model_name=model_to_use,
            system_prompt=system_prompt_to_use,
            checkpointer=CHECKPOINTER_POSTGRES,
            max_iterations=10,
        )

        config = {
            "configurable": {
                "thread_id": request_data.thread_id,
                "user_id": current_user_id,
            }
        }

        result = agent.invoke(request_data.message, config)

        messages_list = result.get("messages", [])
        if not messages_list:
            raise HTTPException(status_code=500, detail="No response from AI agent")

        ai_message = None
        for msg in reversed(messages_list):
            if isinstance(msg, AIMessage) and hasattr(msg, "content"):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    continue
                ai_message = msg
                break

        if not ai_message:
            ai_message = messages_list[-1]
            logger.warning(
                f"No AIMessage found, using last message: {type(ai_message)}"
            )

        response_text = (
            ai_message.content if hasattr(ai_message, "content") else str(ai_message)
        )
        response_time = time.time() - start_time

        scheduled_posts = [
            post.model_dump() for post in result.get("scheduled_posts", [])
        ]
        previews = [preview.model_dump() for preview in result.get("previews", [])]

        return ContentCreationResponse(
            response=response_text,
            response_time=response_time,
            scheduled_posts=scheduled_posts,
            previews=previews,
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
                    "First 125 characters are most important",
                ],
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
                    "Include images for better engagement",
                ],
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
                    "Consider breaking long messages",
                ],
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
                    "Mix personal and promotional content",
                ],
            },
        ]
    }


# =====================================================
# AI Studio Settings Endpoints
# =====================================================


@router.get("/settings", response_model=AIStudioSettings)
async def get_ai_studio_settings(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get AI Studio settings for current user
    Creates default settings if none exist
    """
    try:
        result = (
            db.table("ai_studio_settings")
            .select("*")
            .eq("user_id", current_user_id)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return AIStudioSettings(**result.data[0])

        default_settings = {
            "user_id": current_user_id,
            "default_system_prompt": None,
            "default_model": "openai/gpt-4o",
            "temperature": 0.70,
        }

        create_result = (
            db.table("ai_studio_settings").insert(default_settings).execute()
        )
        if create_result.data and len(create_result.data) > 0:
            return AIStudioSettings(**create_result.data[0])

        raise HTTPException(status_code=500, detail="Failed to create default settings")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AI Studio settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching settings: {str(e)}"
        )


@router.put("/settings", response_model=AIStudioSettings)
async def update_ai_studio_settings(
    settings_update: AIStudioSettingsUpdate,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Update AI Studio settings for current user
    """
    try:
        update_data = {
            k: v
            for k, v in settings_update.model_dump(exclude_unset=True).items()
            if v is not None
        }

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = (
            db.table("ai_studio_settings")
            .update(update_data)
            .eq("user_id", current_user_id)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return AIStudioSettings(**result.data[0])

        raise HTTPException(status_code=404, detail="Settings not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI Studio settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating settings: {str(e)}"
        )


# =====================================================
# Conversation Metadata Endpoints
# =====================================================


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 100,
    offset: int = 0,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    List all AI Studio conversations for current user
    Ordered by updated_at DESC
    """
    try:
        result = (
            db.table("ai_studio_conversation_metadata")
            .select("*")
            .eq("user_id", current_user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        conversations = (
            [ConversationMetadata(**conv) for conv in result.data]
            if result.data
            else []
        )

        count_result = (
            db.table("ai_studio_conversation_metadata")
            .select("*", count="exact")
            .eq("user_id", current_user_id)
            .execute()
        )

        total = count_result.count if count_result.count else 0

        return ConversationListResponse(conversations=conversations, total=total)

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error listing conversations: {str(e)}"
        )


@router.get("/conversations/{thread_id}/messages", response_model=ConversationMessages)
async def get_conversation_messages(
    thread_id: str,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get messages for a specific conversation from LangGraph checkpoints
    """
    try:
        metadata_result = (
            db.table("ai_studio_conversation_metadata")
            .select("*")
            .eq("thread_id", thread_id)
            .eq("user_id", current_user_id)
            .execute()
        )

        if not metadata_result.data or len(metadata_result.data) == 0:
            logger.info(
                f"No metadata found for thread {thread_id}, returning empty messages (new conversation)"
            )
            return ConversationMessages(
                thread_id=thread_id, messages=[], total_messages=0
            )

        agent = ContentCreationAgent(
            user_id=current_user_id,
            model_name="openai/gpt-4o",
            checkpointer=CHECKPOINTER_POSTGRES,
        )

        config = {"configurable": {"thread_id": thread_id, "user_id": current_user_id}}

        try:
            state = agent.graph.get_state(config)
            messages_raw = (
                state.values.get("messages", []) if state and state.values else []
            )
        except Exception as checkpoint_error:
            logger.warning(
                f"Could not retrieve checkpoint for thread {thread_id}: {checkpoint_error}"
            )
            messages_raw = []

        messages = []
        for msg in messages_raw:
            if isinstance(msg, (HumanMessage, AIMessage)):
                messages.append(
                    MessageItem(
                        role="user" if isinstance(msg, HumanMessage) else "assistant",
                        content=msg.content,
                        metadata=getattr(msg, "additional_kwargs", None),
                    )
                )
            elif isinstance(msg, SystemMessage):
                continue

        return ConversationMessages(
            thread_id=thread_id, messages=messages, total_messages=len(messages)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation messages: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error fetching messages: {str(e)}"
        )


@router.delete("/conversations/{thread_id}")
async def delete_conversation(
    thread_id: str,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Delete a conversation (metadata only, checkpoints remain for audit)
    """
    try:
        metadata_result = (
            db.table("ai_studio_conversation_metadata")
            .select("*")
            .eq("thread_id", thread_id)
            .eq("user_id", current_user_id)
            .execute()
        )

        if not metadata_result.data or len(metadata_result.data) == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db.table("ai_studio_conversation_metadata").delete().eq(
            "thread_id", thread_id
        ).eq("user_id", current_user_id).execute()

        return {"message": "Conversation deleted successfully", "thread_id": thread_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting conversation: {str(e)}"
        )


@router.patch("/conversations/{thread_id}", response_model=ConversationMetadata)
async def update_conversation(
    thread_id: str,
    update_data: ConversationMetadataUpdate,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Update conversation metadata (e.g., rename title)
    """
    try:
        metadata_result = (
            db.table("ai_studio_conversation_metadata")
            .select("*")
            .eq("thread_id", thread_id)
            .eq("user_id", current_user_id)
            .execute()
        )

        if not metadata_result.data or len(metadata_result.data) == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")

        update_dict = {
            k: v
            for k, v in update_data.model_dump(exclude_unset=True).items()
            if v is not None
        }

        if not update_dict:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = (
            db.table("ai_studio_conversation_metadata")
            .update(update_dict)
            .eq("thread_id", thread_id)
            .eq("user_id", current_user_id)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return ConversationMetadata(**result.data[0])

        raise HTTPException(status_code=500, detail="Failed to update conversation")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error updating conversation: {str(e)}"
        )
