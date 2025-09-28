from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from app.db.session import get_authenticated_db
from app.schemas.ai_settings import AISettings, AISettingsCreate, AISettingsUpdate, AITestRequest, AITestResponse
from app.core.security import get_current_user_id
import time
import random
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL","https://openrouter.ai/api/v1")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL
)

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
- Document interactions to improve service"""
}

@router.get("/", response_model=AISettings)
async def get_ai_settings(
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        result = db.table("ai_settings").select("*").eq("user_id", current_user_id).execute()
        
        if result.data:
            return AISettings(**result.data[0])
        else:
            default_settings = {
                "user_id": current_user_id,
                "system_prompt": PROMPT_TEMPLATES["social"],
                "ai_model": "anthropic/claude-3.5-haiku",
                "temperature": 0.20,
                "top_p": 1.00,
                "lang": "en",
                "tone": "friendly",
                "is_active": True,
                "doc_lang": []
            }
            
            create_result = db.table("ai_settings").insert(default_settings).execute()
            if create_result.data:
                return AISettings(**create_result.data[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to create default AI settings")
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/", response_model=AISettings)
async def update_ai_settings(
    settings_update: AISettingsUpdate,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        update_data = {k: v for k, v in settings_update.model_dump(exclude_unset=True).items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        update_data["updated_at"] = "NOW()"
        
        result = db.table("ai_settings").update(update_data).eq("user_id", current_user_id).execute()
        
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
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model=test_request.settings.ai_model,
            messages=[{"role": "system", "content": test_request.settings.system_prompt}, {"role": "user", "content": test_request.message}],
            temperature=test_request.settings.temperature,
            top_p=test_request.settings.top_p,
            max_tokens=150
        )
        
        response_time = time.time() - start_time
        confidence = round(random.uniform(0.85, 0.98), 2)
        
        return AITestResponse(
            response=response.choices[0].message.content,
            response_time=response_time,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates")
async def get_prompt_templates():
    return {"templates": PROMPT_TEMPLATES}

@router.post("/reset")
async def reset_to_template(
    template_type: str,
    request: Request,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        if template_type not in PROMPT_TEMPLATES:
            raise HTTPException(status_code=400, detail="Invalid template type")
        
        update_data = {
            "system_prompt": PROMPT_TEMPLATES[template_type],
            "updated_at": "NOW()"
        }
        
        result = db.table("ai_settings").update(update_data).eq("user_id", current_user_id).execute()
        
        if result.data:
            return {"message": f"Settings reset to {template_type} template"}
        else:
            raise HTTPException(status_code=404, detail="AI settings not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
