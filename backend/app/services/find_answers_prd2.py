"""
Service find_answers selon PRD2 - piloté par LLM sans embeddings
Récupère toutes les FAQs actives et les passe à un LLM pour sélection
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI
import json
import os
from app.db.session import get_db

logger = logging.getLogger(__name__)

# Configuration LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL
)


class Answer(BaseModel):
    """Objet Answer retourné par find_answers"""
    faq_id: Optional[str] = None
    answer: Optional[str] = None
    matched_question_index: Optional[int] = None
    matched_question_text: Optional[str] = None
    reason: str
    status: str  # "match" | "no_match"


class FAQBatch(BaseModel):
    """Lot de FAQs pour traitement LLM"""
    faqs: List[Dict[str, Any]]
    batch_index: int


class LLMBatchResponse(BaseModel):
    """Réponse du LLM pour un lot"""
    best_match: Optional[Dict[str, Any]] = None
    no_match: Optional[Dict[str, str]] = None


class FindAnswersService:
    """Service find_answers piloté par LLM selon PRD2"""
    
    def __init__(self, user_id: str, batch_size: int = 30):
        self.user_id = user_id
        self.batch_size = batch_size
        self.db = get_db()
    
    def get_active_faqs(self) -> List[Dict[str, Any]]:
        """Récupère toutes les FAQs actives du user"""
        try:
            result = self.db.table("faq_qa").select(
                "id, answer, questions"
            ).eq("user_id", self.user_id).eq("is_active", True).execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Erreur récupération FAQs: {e}")
            return []
    
    def create_batches(self, faqs: List[Dict[str, Any]]) -> List[FAQBatch]:
        """Divise les FAQs en lots pour éviter un contexte trop long"""
        batches = []
        for i in range(0, len(faqs), self.batch_size):
            batch_faqs = faqs[i:i + self.batch_size]
            batches.append(FAQBatch(faqs=batch_faqs, batch_index=i // self.batch_size))
        return batches
    
    def process_batch(self, batch: FAQBatch, user_question: str) -> Optional[Dict[str, Any]]:
        """Traite un lot de FAQs avec le LLM"""
        try:
            # Construire le prompt pour le lot
            faqs_context = []
            for faq in batch.faqs:
                questions_str = " | ".join(faq["questions"])
                faqs_context.append({
                    "faq_id": faq["id"],
                    "questions": questions_str,
                    "answer": faq["answer"]
                })
            
            prompt = f"""Tu es un assistant spécialisé dans la recherche de FAQs.
            
Voici une question utilisateur: "{user_question}"

Voici une liste de FAQs disponibles:
{json.dumps(faqs_context, ensure_ascii=False, indent=2)}

Ta tâche:
1. Déterminer si l'une de ces FAQs peut répondre à la question utilisateur
2. Si oui, identifier la MEILLEURE correspondance avec:
   - L'ID de la FAQ
   - L'index de la question qui correspond le mieux (0-based)
   - Le texte exact de cette question
   - Un score de confiance local (0.0 à 1.0)
   - Une raison courte

Réponds UNIQUEMENT avec un JSON dans ce format:
{{
  "best_match": {{
    "faq_id": "uuid",
    "matched_question_index": 0,
    "matched_question_text": "texte exact",
    "confidence_local": 0.85,
    "reason": "explication courte"
  }}
}}

OU si aucune FAQ ne correspond:
{{
  "no_match": {{
    "reason": "explication courte"
  }}
}}
"""

            response = client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"Erreur traitement lot {batch.batch_index}: {e}")
            return None
    
    def find_best_across_batches(self, batch_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Trouve la meilleure correspondance parmi tous les lots"""
        best_match = None
        best_confidence = 0.0
        
        for result in batch_results:
            if result and "best_match" in result:
                match = result["best_match"]
                confidence = match.get("confidence_local", 0.0)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = match
        
        return best_match
    
    def find_answers(self, question: str) -> Answer:
        """
        Point d'entrée principal - trouve la meilleure réponse FAQ
        """
        try:
            if not question or not question.strip():
                return Answer(
                    status="no_match",
                    reason="Question vide"
                )
            
            # Récupérer toutes les FAQs actives
            faqs = self.get_active_faqs()
            if not faqs:
                return Answer(
                    status="no_match",
                    reason="Aucune FAQ disponible"
                )
            
            # Diviser en lots si nécessaire
            batches = self.create_batches(faqs)
            logger.info(f"Traitement de {len(faqs)} FAQs en {len(batches)} lots")
            
            # Traiter chaque lot
            batch_results = []
            for batch in batches:
                result = self.process_batch(batch, question)
                if result:
                    batch_results.append(result)
            
            # Trouver la meilleure correspondance
            best_match = self.find_best_across_batches(batch_results)
            
            if best_match:
                # Récupérer les détails complets de la FAQ
                faq_details = next(
                    (faq for faq in faqs if faq["id"] == best_match["faq_id"]), 
                    None
                )
                
                if faq_details:
                    return Answer(
                        faq_id=best_match["faq_id"],
                        answer=faq_details["answer"],
                        matched_question_index=best_match["matched_question_index"],
                        matched_question_text=best_match["matched_question_text"],
                        reason=best_match["reason"],
                        status="match"
                    )
            
            return Answer(
                status="no_match",
                reason="Aucune FAQ correspondante trouvée"
            )
            
        except Exception as e:
            logger.error(f"Erreur dans find_answers: {e}")
            return Answer(
                status="no_match",
                reason=f"Erreur technique: {str(e)}"
            )


def get_find_answers_service(user_id: str) -> FindAnswersService:
    """Factory pour créer le service find_answers"""
    return FindAnswersService(user_id)