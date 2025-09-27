"""
RAG Agent PRD2 - Format JSON strict et escalade automatique
Implémente les règles de sortie et l'escalade selon le PRD2
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError
from openai import OpenAI
import os
from app.db.session import get_db
from app.services.find_answers_prd2 import get_find_answers_service
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)

# Configuration LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL
)


class AIResponse(BaseModel):
    """Format JSON strict de réponse selon PRD2"""
    response: str
    confidence: float


class EscalationResult(BaseModel):
    """Résultat d'une escalade"""
    escalated: bool
    escalation_id: Optional[str] = None
    reason: str


class RAGAgentPRD2:
    """Agent RAG avec format JSON strict et escalade selon PRD2"""
    
    def __init__(self, user_id: str, system_prompt: str = None, model_name: str = "anthropic/claude-3.5-haiku"):
        self.user_id = user_id
        self.model_name = model_name
        self.db = get_db()
        self.find_answers_service = get_find_answers_service(user_id)
        
        # System prompt avec règles PRD2
        base_system_prompt = """
RÈGLES DE SORTIE STRICTES :
- Si tu réponds à l'utilisateur, renvoie UNIQUEMENT :
  {"response":"<texte>", "confidence": <float 0..1>}
- Si tu dois utiliser un outil, utilise le tool-calling natif. 
  Le tour suivant DOIT être la réponse finale JSON ci-dessus.
- Ne mélange jamais tool-call et JSON final dans le même tour.
- Si on te renvoie "JSON_INVALID", renvoie uniquement le JSON corrigé.

Tu es un assistant IA spécialisé dans le support client. Tu peux utiliser l'outil find_answers pour chercher des réponses dans la base de connaissances.
"""
        
        if system_prompt:
            self.system_prompt = f"{base_system_prompt}\n\n{system_prompt}"
        else:
            self.system_prompt = base_system_prompt
    
    def check_ai_settings(self) -> bool:
        """Vérifier si l'IA est activée globalement pour l'utilisateur"""
        try:
            result = self.db.table("ai_settings").select("is_active").eq("user_id", self.user_id).single().execute()
            return result.data.get("is_active", True) if result.data else True
        except:
            return True
    
    def check_conversation_ai_mode(self, conversation_id: str) -> bool:
        """Vérifier si l'IA est activée pour cette conversation"""
        try:
            result = self.db.table("conversations").select("ai_mode").eq("id", conversation_id).single().execute()
            return result.data.get("ai_mode", "ON") == "ON" if result.data else True
        except:
            return True
    
    def parse_or_fix_json(self, response_text: str) -> Optional[AIResponse]:
        """Parse ou corrige le JSON de réponse (avec 1 retry)"""
        try:
            # Première tentative
            response_json = json.loads(response_text.strip())
            return AIResponse(**response_json)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"JSON invalide, tentative de correction: {e}")
            
            # Retry avec demande de correction
            try:
                correction_prompt = f"""
Le JSON suivant est invalide: {response_text}

Erreur: {str(e)}

Renvoie UNIQUEMENT le JSON corrigé au format:
{{"response":"<texte>", "confidence": <float 0..1>}}
"""
                correction_response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": correction_prompt}],
                    temperature=0.0,
                    max_tokens=200
                )
                
                corrected_text = correction_response.choices[0].message.content.strip()
                corrected_json = json.loads(corrected_text)
                return AIResponse(**corrected_json)
                
            except Exception as retry_error:
                logger.error(f"Échec correction JSON après retry: {retry_error}")
                return None
    
    def create_escalation(self, conversation_id: str, message_id: str, confidence: float, reason: str) -> str:
        """Créer une escalade et mettre la conversation en mode OFF"""
        try:
            # Créer l'escalade
            escalation_data = {
                "user_id": self.user_id,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "confidence": confidence,
                "reason": reason,
                "notified": False
            }
            
            escalation_result = self.db.table("support_escalations").insert(escalation_data).execute()
            escalation_id = escalation_result.data[0]["id"] if escalation_result.data else None
            
            # Mettre la conversation en mode OFF
            self.db.table("conversations").update({
                "ai_mode": "OFF",
                "updated_at": "now()"
            }).eq("id", conversation_id).execute()
            
            logger.info(f"Escalade créée: {escalation_id} pour conversation {conversation_id}")
            return escalation_id
            
        except Exception as e:
            logger.error(f"Erreur création escalade: {e}")
            return None
    
    def find_answers_tool(self, question: str) -> Dict[str, Any]:
        """Tool pour rechercher des réponses dans les FAQs"""
        try:
            answer = self.find_answers_service.find_answers(question)
            return {
                "status": answer.status,
                "answer": answer.answer,
                "faq_id": answer.faq_id,
                "matched_question": answer.matched_question_text,
                "reason": answer.reason
            }
        except Exception as e:
            return {
                "status": "error",
                "reason": f"Erreur recherche: {str(e)}"
            }
    
    def call_llm_with_tools(self, messages: List[Dict[str, str]], conversation_id: str = None) -> Dict[str, Any]:
        """Appel LLM avec gestion des tools"""
        try:
            # Définir les tools disponibles
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "find_answers",
                        "description": "Recherche des réponses dans la base de connaissances FAQ",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "La question de l'utilisateur"
                                }
                            },
                            "required": ["question"]
                        }
                    }
                }
            ]
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2
            )
            
            response_message = response.choices[0].message
            
            # Si le LLM veut utiliser un tool
            if response_message.tool_calls:
                # Exécuter le tool
                tool_results = []
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "find_answers":
                        args = json.loads(tool_call.function.arguments)
                        result = self.find_answers_tool(args["question"])
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                
                # Ajouter les résultats des tools et redemander une réponse finale
                extended_messages = messages + [
                    {"role": "assistant", "content": response_message.content or "", "tool_calls": [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in response_message.tool_calls
                    ]}
                ] + tool_results
                
                # Demander la réponse finale JSON
                final_response = client.chat.completions.create(
                    model=self.model_name,
                    messages=extended_messages,
                    temperature=0.2,
                    max_tokens=500
                )
                
                return {
                    "content": final_response.choices[0].message.content,
                    "tool_used": True
                }
            else:
                # Réponse directe
                return {
                    "content": response_message.content,
                    "tool_used": False
                }
                
        except Exception as e:
            logger.error(f"Erreur appel LLM: {e}")
            return {
                "content": '{"response": "Désolé, une erreur technique s\'est produite.", "confidence": 0.05}',
                "tool_used": False
            }
    
    def process_message(self, user_message: str, conversation_id: str, message_id: str = None) -> Dict[str, Any]:
        """Traite un message utilisateur selon les règles PRD2"""
        
        # Gate 1: IA globale désactivée
        if not self.check_ai_settings():
            return {
                "response": None,
                "escalated": False,
                "reason": "IA globalement désactivée"
            }
        
        # Gate 2: IA désactivée pour cette conversation
        if not self.check_conversation_ai_mode(conversation_id):
            return {
                "response": None,
                "escalated": False,
                "reason": "IA désactivée pour cette conversation"
            }
        
        try:
            # Préparer les messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Appel LLM avec tools
            llm_result = self.call_llm_with_tools(messages, conversation_id)
            response_text = llm_result["content"]
            
            # Parser le JSON de réponse
            ai_response = self.parse_or_fix_json(response_text)
            
            if not ai_response:
                # JSON invalide même après retry
                return {
                    "response": "Désolé, une erreur technique s'est produite.",
                    "escalated": False,
                    "reason": "JSON invalide après retry",
                    "confidence": 0.05
                }
            
            # Vérifier le seuil d'escalade
            if ai_response.confidence < 0.10:
                escalation_id = self.create_escalation(
                    conversation_id=conversation_id,
                    message_id=message_id or "unknown",
                    confidence=ai_response.confidence,
                    reason=f"Confiance faible: {ai_response.confidence}"
                )
                
                return {
                    "response": "Transfert à un agent humain.",
                    "escalated": True,
                    "escalation_id": escalation_id,
                    "confidence": ai_response.confidence,
                    "reason": "Confiance inférieure au seuil 0.10"
                }
            
            # Réponse normale
            return {
                "response": ai_response.response,
                "escalated": False,
                "confidence": ai_response.confidence,
                "tool_used": llm_result.get("tool_used", False)
            }
            
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")
            return {
                "response": "Désolé, une erreur technique s'est produite.",
                "escalated": False,
                "confidence": 0.05,
                "reason": f"Erreur: {str(e)}"
            }


def create_rag_agent_prd2(user_id: str, system_prompt: str = None, model_name: str = "anthropic/claude-3.5-haiku") -> RAGAgentPRD2:
    """Factory pour créer un agent RAG PRD2"""
    return RAGAgentPRD2(user_id=user_id, system_prompt=system_prompt, model_name=model_name)