from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from app.db.session import get_authenticated_db
from app.schemas.ai_settings import (
    AISettings,
    AISettingsCreate,
    AISettingsUpdate,
    AITestRequest,
    AITestResponse,
    AIResponse,
)
from app.schemas.ai_decisions import (
    CheckMessageRequest,
    CheckMessageResponse,
    AIDecisionResponse,
    AIDecision,
)
from app.services.ai_decision_service import AIDecisionService
from app.core.security import get_current_user_id
import time
import random
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.services.rag_agent import RAGAgent
from app.deps.runtime_test import CHECKPOINTER_REDIS
from langchain_core.messages import HumanMessage
from typing import List, Optional
from datetime import datetime

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

router = APIRouter(prefix="/ai-settings", tags=["ai-settings"])

# Templates de prompts par secteur
PROMPT_TEMPLATES = {
    "social": """You are an AI assistant specialized in social media management for {{brand_name}}.

Your responsibilities:
- Create engaging and viral content for social media
- Analyze trending hashtags and topics
- Optimize posts for each platform (Instagram, TikTok, Facebook, Twitter)
- Propose growth and engagement strategies
- Respond in {{lang}} with a {{tone}} tone
- Provide creative and authentic advice""",
    "ecommerce": """You are an AI expert in e-commerce for {{brand_name}}.

Your responsibilities:
- Optimize product descriptions to increase conversions
- Analyze customer buying behavior
- Propose pricing and promotion strategies
- Create targeted marketing campaigns
- Improve customer experience and purchase journey
- Respond in {{lang}} with a {{tone}} tone
- Provide data-driven sales insights""",
    "support": """You are an AI assistant dedicated to customer support for {{brand_name}}.

Your responsibilities:
- Quickly resolve customer issues
- Provide accurate and empathetic responses
- Escalate complex cases to human team
- Maintain high customer satisfaction levels
- Follow company procedures and policies
- Respond in {{lang}} with a {{tone}} tone
- Document interactions to improve service""",
}


@router.get("/", response_model=AISettings)
async def get_ai_settings(
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        result = (
            db.table("ai_settings").select("*").eq("user_id", current_user_id).execute()
        )

        if result.data:
            return AISettings(**result.data[0])
        else:
            default_settings = {
                "user_id": current_user_id,
                "system_prompt": PROMPT_TEMPLATES["social"],
                "ai_model": "openai/gpt-4o",
                "temperature": 0.20,
                "top_p": 1.00,
                "lang": "en",
                "tone": "friendly",
                "is_active": True,
                "doc_lang": [],
                # Consolidated fields from ai_rules
                "ai_control_enabled": True,
                "ai_enabled_for_conversations": True,
                "ai_enabled_for_chats": True,
                "ai_enabled_for_comments": True,
                "flagged_keywords": [],
                "flagged_phrases": [],
                "instructions": None,
                "ignore_examples": [],
            }

            create_result = db.table("ai_settings").insert(default_settings).execute()
            if create_result.data:
                return AISettings(**create_result.data[0])
            else:
                raise HTTPException(
                    status_code=400, detail="Failed to create default AI settings"
                )

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        print(f"ERROR in get_ai_settings: {error_detail}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.put("/", response_model=AISettings)
async def update_ai_settings(
    settings_update: AISettingsUpdate,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        update_data = {
            k: v
            for k, v in settings_update.model_dump(exclude_unset=True).items()
            if v is not None
        }

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        update_data["updated_at"] = "NOW()"

        result = (
            db.table("ai_settings")
            .update(update_data)
            .eq("user_id", current_user_id)
            .execute()
        )

        if result.data:
            return AISettings(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="AI settings not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test", response_model=AITestResponse)
async def test_ai_response(
    test_request: AITestRequest,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        print("=== AI TEST REQUEST DEBUG ===")
        print(f"User ID: {current_user_id}")
        print(f"Thread ID: {test_request.thread_id}")
        print(f"Message: {test_request.message}")
        print(f"Settings: {test_request.settings.model_dump()}")

        start_time = time.time()
        print(f"Creating RAGAgent with model: {test_request.settings.ai_model}")

        agent = RAGAgent(
            user_id=current_user_id,
            conversation_id=test_request.thread_id,
            model_name=test_request.settings.ai_model,
            system_prompt=test_request.settings.system_prompt,
            checkpointer=CHECKPOINTER_REDIS,
            test_mode=True,
        )
        print("RAGAgent created successfully")

        config = {
            "configurable": {
                "thread_id": test_request.thread_id,
                "user_id": current_user_id,
                "checkpoint_ns": f"user:{current_user_id}:test",
            }
        }
        print(f"Invoking graph with config: {config}")

        messages = agent.graph.invoke(
            {"messages": [HumanMessage(content=test_request.message)]}, config=config
        )

        print(f"Graph invocation completed. Messages keys: {list(messages.keys())}")
        print(f"Messages type: {type(messages)}")

        response_time = time.time() - start_time
        print(f"Response time: {response_time}s")

        messages_list = messages.get("messages", [])
        print(f"Messages list length: {len(messages_list)}")

        if not messages_list:
            print("ERROR: No messages in response")
            raise HTTPException(
                status_code=400, detail="No messages returned from AI agent"
            )

        reponse = messages_list[-1]
        print(f"Last message type: {type(reponse)}")
        print(f"Last message content preview: {reponse.content[:100]}")

        try:
            ai_response = AIResponse.model_validate_json(reponse.content)
            response_text = ai_response.response
            confidence = ai_response.confidence
            print(f"Parsed JSON response - confidence: {confidence}")
        except Exception as json_error:
            print(f"Failed to parse as JSON: {json_error}, using raw content")
            response_text = reponse.content
            # Since we now use llm_with_tools (for escalation), the LLM returns plain text
            # We use a default confidence of 0.85 (high confidence for successful responses)
            confidence = 0.85
            print(f"Using default confidence: {confidence}")

        result = AITestResponse(
            response=response_text, response_time=response_time, confidence=confidence
        )
        print(
            f"Returning result: response_length={len(result.response)}, confidence={result.confidence}"
        )
        return result

    except HTTPException:
        print("HTTPException caught, re-raising")
        raise
    except Exception as e:
        print(f"Unexpected error in test_ai_response: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates")
async def get_prompt_templates():
    return {"templates": PROMPT_TEMPLATES}


@router.post("/reset")
async def reset_to_template(
    template_type: str,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        if template_type not in PROMPT_TEMPLATES:
            raise HTTPException(status_code=400, detail="Invalid template type")

        update_data = {
            "system_prompt": PROMPT_TEMPLATES[template_type],
            "updated_at": "NOW()",
        }

        result = (
            db.table("ai_settings")
            .update(update_data)
            .eq("user_id", current_user_id)
            .execute()
        )

        if result.data:
            return {"message": f"Settings reset to {template_type} template"}
        else:
            raise HTTPException(status_code=404, detail="AI settings not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/toggle", response_model=AISettings)
async def toggle_ai_control(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Toggle AI control ON/OFF (master switch)
    Toggles ai_control_enabled between true and false
    """
    try:
        # Get current value
        existing = (
            db.table("ai_settings")
            .select("ai_control_enabled")
            .eq("user_id", current_user_id)
            .execute()
        )

        if not existing.data:
            # Create default settings with AI disabled
            default_settings = {
                "user_id": current_user_id,
                "system_prompt": PROMPT_TEMPLATES["social"],
                "ai_model": "openai/gpt-4o",
                "temperature": 0.20,
                "top_p": 1.00,
                "lang": "en",
                "tone": "friendly",
                "is_active": True,
                "ai_control_enabled": False,
                "ai_enabled_for_chats": True,
                "ai_enabled_for_comments": True,
                "doc_lang": [],
            }
            result = db.table("ai_settings").insert(default_settings).execute()
        else:
            # Toggle existing value
            current_value = existing.data[0].get("ai_control_enabled", True)
            result = (
                db.table("ai_settings")
                .update(
                    {
                        "ai_control_enabled": not current_value,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("user_id", current_user_id)
                .execute()
            )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to toggle AI control")

        return AISettings(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-message", response_model=CheckMessageResponse)
async def check_message(
    request: CheckMessageRequest,
    context_type: str = "chat",
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Test if AI should respond to a message (dry-run)
    Does NOT log the decision to ai_decisions table

    Args:
        context_type: "chat" or "comment" for granular control
    """
    try:
        service = AIDecisionService(current_user_id)
        decision, confidence, reason, matched_rule = service.check_message(
            request.message_text, context_type=context_type
        )

        return CheckMessageResponse(
            decision=decision,
            confidence=confidence,
            reason=reason,
            should_respond=(decision == AIDecision.RESPOND),
            matched_rule=matched_rule if matched_rule else None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/decisions", response_model=List[AIDecisionResponse])
async def get_decisions_history(
    limit: int = 50,
    offset: int = 0,
    decision_filter: Optional[str] = None,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get history of AI decisions for current user

    Args:
        limit: Max number of results (default 50, max 100)
        offset: Pagination offset
        decision_filter: Filter by decision type (respond, ignore, escalate)
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100

        # Build query
        query = db.table("ai_decisions").select("*").eq("user_id", current_user_id)

        # Apply decision filter if provided
        if decision_filter:
            if decision_filter not in ["respond", "ignore", "escalate"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid decision_filter. Must be: respond, ignore, or escalate",
                )
            query = query.eq("decision", decision_filter)

        # Apply pagination and ordering
        result = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return [AIDecisionResponse(**item) for item in result.data]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/decisions/stats")
async def get_decisions_stats(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get statistics on AI decisions
    Returns count of RESPOND, IGNORE, ESCALATE decisions
    """
    try:
        # Count by decision type
        all_decisions = (
            db.table("ai_decisions")
            .select("decision")
            .eq("user_id", current_user_id)
            .execute()
        )

        stats = {
            "respond": 0,
            "ignore": 0,
            "escalate": 0,
            "total": len(all_decisions.data),
        }

        for item in all_decisions.data:
            decision = item.get("decision")
            if decision in stats:
                stats[decision] += 1

        # Calculate percentages
        total = stats["total"]
        if total > 0:
            stats["respond_pct"] = round((stats["respond"] / total) * 100, 1)
            stats["ignore_pct"] = round((stats["ignore"] / total) * 100, 1)
            stats["escalate_pct"] = round((stats["escalate"] / total) * 100, 1)
        else:
            stats["respond_pct"] = 0.0
            stats["ignore_pct"] = 0.0
            stats["escalate_pct"] = 0.0

        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
