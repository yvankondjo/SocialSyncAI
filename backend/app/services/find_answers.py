# import sys
# from pathlib import Path
# backend_path = Path(__file__).parent.parent.parent
# sys.path.insert(0, str(backend_path))

from pydantic import BaseModel, Field, ValidationError
from typing import Optional, TypeAlias, Literal, List
from datetime import datetime
from app.db.session import get_db
import logging
from langchain_openai import ChatOpenAI
import os
import json
from openai import OpenAIError
from supabase.lib.client_options import ClientOptions
from httpx import HTTPError
logger = logging.getLogger(__name__)
class QuestionAnswer(BaseModel):
    question_id: str
    questions: List[str]
    answer: str

class ReferencedAnswer(BaseModel):
    question_id: str
    quotes: list[str]



class _AnswerSchema(BaseModel):
    user_questions: list[str]
    relevant_question_variants: Optional[list[str]] = None
    full_answer_can_be_found_in_background_info: Optional[str] = None
    partial_answer_can_be_found_in_background_info: Optional[str] = None
    insights_on_what_could_be_a_legitimate_answer: Optional[str] = None
    collected_relevant_quotes_from_background_info: Optional[list[ReferencedAnswer]] = (
        None
    )
    concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__draft: Optional[
        str
    ] = None
    critique: Optional[str] = None
    brief_explanation_of_what_needs_to_change_in_order_to_stay_within_the_boundaries_of_collected_quotes: Optional[
        str
    ] = None
    could_use_better_markdown: Optional[bool] = None
    concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__revised: Optional[
        str
    ] = None
    extracted_entities_found_in_background_info_and_referred_to_by_answer: Optional[
        list[str]
    ] = None
    question_answered_in_full: bool
    question_answered_partially: bool
    question_not_answered_at_all: bool

AnswerGrade: TypeAlias = Literal["partial", "full", "no-answer"]
class Answer(BaseModel):
    content:Optional[str] = None
    grade: AnswerGrade
    generation_info: Optional[dict] = None
    evaluation: Optional[str] = None
    references: Optional[list[ReferencedAnswer]] = None
    extracted_entities: Optional[list[str]] = None
class FindAnswersError(Exception):
    """Exception personnalisée pour les erreurs de FindAnswers"""
    def __init__(self, message: str, error_type: str = "UNKNOWN", details: dict = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

class FindAnswers:
    def __init__(self, user_id: str, model_name: str = "x-ai/grok-4-fast:free"):
        if not user_id:
            raise FindAnswersError(
                "User ID is required and cannot be empty",
                error_type="INVALID_USER_ID",
                details={"user_id": user_id}
            )
        
        self.user_id = user_id
        self.model_name = model_name
        
        try:
            self.db = get_db()
        except Exception as e:
            raise FindAnswersError(
                f"Failed to initialize database connection: {str(e)}",
                error_type="DATABASE_CONNECTION_ERROR",
                details={"original_error": str(e)}
            )
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise FindAnswersError(
                "OPENROUTER_API_KEY environment variable is required but not set",
                error_type="MISSING_API_KEY",
                details={"env_var": "OPENROUTER_API_KEY"}
            )
        
        try:
            self.llm = ChatOpenAI(
                api_key=api_key,
                base_url=os.getenv('OPENROUTER_BASE_URL') or "https://openrouter.ai/api/v1",
                model=model_name
            )
        except Exception as e:
            raise FindAnswersError(
                f"Failed to initialize LLM client: {str(e)}",
                error_type="LLM_INITIALIZATION_ERROR",
                details={"model_name": model_name, "original_error": str(e)}
            )

    def get_question_answers(self) -> list[QuestionAnswer]:
        try:
            if not self.user_id:
                raise FindAnswersError(
                    "User ID is required for retrieving question answers",
                    error_type="INVALID_USER_ID",
                    details={"user_id": self.user_id}
                )
            
            question_answers = self.db.table("faq_qa").select("id, question, answer").eq("user_id", self.user_id).eq("is_active", True).execute()
            
            if not question_answers.data:
                logger.warning(f"No question answers found for user {self.user_id}")
                return []
            
            result = []
            for item in question_answers.data:
                try:
                    qa = QuestionAnswer(
                        question_id=item["id"], 
                        question=item["question"], 
                        answer=item["answer"]
                    )
                    result.append(qa)
                except ValidationError as e:
                    logger.error(f"Validation error for question answer {item.get('id', 'unknown')}: {str(e)}")
                    continue
                except KeyError as e:
                    logger.error(f"Missing required field in question answer: {str(e)}")
                    continue
            
            return result
            
        except HTTPError as e:
            raise FindAnswersError(
                f"Database API error while retrieving question answers: {str(e)}",
                error_type="DATABASE_API_ERROR",
                details={"user_id": self.user_id, "original_error": str(e)}
            )
        except Exception as e:
            raise FindAnswersError(
                f"Unexpected error while retrieving question answers: {str(e)}",
                error_type="UNEXPECTED_ERROR",
                details={"user_id": self.user_id, "original_error": str(e)}
            )
    

    def find_answers(self, question: str) -> Answer:
        try:
            if not question or not question.strip():
                raise FindAnswersError(
                    "Question cannot be empty or only whitespace",
                    error_type="INVALID_QUESTION",
                    details={"question": question}
                )
            
            logger.info(f"Looking for answers for '{question}' for user {self.user_id}")
            
            try:
                question_answers = self.get_question_answers()
            except FindAnswersError:
                raise
            except Exception as e:
                raise FindAnswersError(
                    f"Failed to retrieve question answers: {str(e)}",
                    error_type="QUESTION_RETRIEVAL_ERROR",
                    details={"question": question, "user_id": self.user_id, "original_error": str(e)}
                )
            
            logger.info(f"Found {len(question_answers)} question answers")
            
            if not question_answers:
                logger.warning(f"No question answers available for user {self.user_id}")
                return Answer(
                    content=None,
                    grade="no-answer",
                    generation_info=None,
                    evaluation="No question answers found in the knowledge base",
                    references=[],
                    extracted_entities=[]
                )
            
            #prompt taken from parlant.io : https://github.com/emcie-co/parlant-qna/blob/main/parlant_qna/app.py
            prompt = f"""\
You are a RAG agent who has exactly one job: to answer the user's question
based ONLY on the background information provided here in-context.

Note that there are cases when data is provided in the answer in a way that's
implied by the question for that answer. For example, if the question is
"What is Blabooshka" and the answer provided is "It's a banana", then
you can infer that "A Blabooshka is a banana".
In this way, the question variants themselves are directly connected to
their answers. Also, often, the answer is to be considered an explicit and
direct continuation of one of the question variants, as if continuing the idea or sentence.
This is only true within a particular question, its variants, and its answer.
It does not apply cross-questions (i.e. the answer to one question is never
a direct continuation of a different question).

IMPORTANT: Try your best to answer the question *fully*, based on the background information provided.

Always attempt to provide the answer in a clean Markdown format,
separating your answer into multiple lines where applicable, for readability,
using Markdown elements like bold text, lists, and tables where applicable.
However, avoid headings, to make your responses more conversational.

Finally, note that, for review and improvement purposes, it's important to capture the quotes
on which you base your answer, as well as any entity you've made reference to.
Examples of entities are (but not limited to): pronouns, products, companies, domain-specific concepts, etc.

You must produce the following report.
- What is the user asking? Is it one question? Is it different ones? Rephrase the user's input approrpiately to better articulate this.
- What question variants from the provided background information contain the answer to each of the user's queries?
- Determine if any or all of the user's queries can be answered (fully or at least partially) solely based on and using the background information provided here exclusively.
- Try to reason about what could be a satisfying answer to the user. Use your generated insight to seek out the most relevant quotes from the background information, making sure to stay exclusively within the bounds of the background information provided here.
- Draft an answer. Make sure it's nicely formatted with Markdown.
- Critique your initial answer to ensure it meets all of the required standards you are given here.
- Draft a final, satisfactory answer, that stays within the strict bounds and standards you are given here.

Produce a JSON object according to the following schema: ###
{{
    "user_questions": [ QUERY_1, ..., QUERY_N ],
    "relevant_question_variants": [ VARIANT_1, ..., VARIANT_N ],
    "full_answer_can_be_found_in_background_info": <"BRIEF EXPLANATION OF WHETHER AND WHY">,
    "partial_answer_can_be_found_in_background_info": <"BRIEF EXPLANATION OF WHETHER AND WHY">,
    "insights_on_what_could_be_a_legitimate_answer": <"YOUR BRIEF INSIGHTS AS TO WHAT COULD BE A LEGITIMATE ANSWER">,
    "collected_relevant_quotes_from_background_info": [
        {{
            "question_id": QUESTION_ID,
            "quotes": [ QUOTE_1, ..., QUOTE_N ]
        }},
        ...
    ],
    "concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__draft": <"PRODUCE AN ANSWER HERE EXCLUSIVELY AND ONLY BASED ON THE COLLECTED QUOTES, WITHOUT ADDING ANYTHING ELSE">
    "critique": <"EXPLAIN IF ANY PART OF THE DRAFT IS UNBASED/UNGROUNDED IN BACKGROUND INFO">,
    "brief_explanation_of_what_needs_to_change_in_order_to_stay_within_the_boundaries_of_collected_quotes": <"BRIEF EXPLANATION OF WHAT NEEDS TO CHANGE TO MITIGATE FACTUAL ISSUES">,
    "could_use_better_markdown": <BOOL>,
    "concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__revised": <"PRODUCE AN ANSWER HERE EXCLUSIVELY AND ONLY BASED ON THE COLLECTED QUOTES, WITHOUT ADDING ANYTHING ELSE">
    "extracted_entities_found_in_background_info_and_referred_to_by_answer": [ ENTITY_1, ..., ENTITY_N ],
    "question_answered_in_full": <BOOL>,
    "question_answered_partially": <BOOL>,
    "question_not_answered_at_all": <BOOL>
}}
###


Please note that in case you couldn't find any answer (neither full nor partial) within the background information provided here, meaning, you couldn't find specific quotes in the background info, then this is the format you should follow in such a case — note specifically how some of the fields in this case are left as null : ###
{{
    "user_questions": [ QUERY_1, ..., QUERY_N ],
    "relevant_question_variants": [],
    "full_answer_can_be_found_in_background_info": null,
    "partial_answer_can_be_found_in_background_info": null,
    "insights_on_what_could_be_a_legitimate_answer": <"YOUR BRIEF INSIGHTS AS TO WHAT COULD HAVE BEEN A LEGITIMATE ANSWER">,
    "collected_relevant_quotes_from_background_info": [],
    "concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__draft": null,
    "critique": null,
    "brief_explanation_of_what_needs_to_change_in_order_to_stay_within_the_boundaries_of_collected_quotes": "N/A",
    "could_use_better_markdown": null,
    "concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__revised": null,
    "extracted_entities_found_in_background_info_and_referred_to_by_answer": [ ENTITY_1, ..., ENTITY_N ],
    "question_answered_in_full": false,
    "question_answered_partially": false,
    "question_not_answered_at_all": true
}}
###

Background Information: ###
{question_answers}
###

User Question: ###
{question}
###
"""

            try:
                result = self.llm.with_structured_output(_AnswerSchema).invoke(prompt)
                logger.debug(result.model_dump_json(indent=2))
            except OpenAIError as e:
                raise FindAnswersError(
                    f"OpenAI API error during answer generation: {str(e)}",
                    error_type="OPENAI_API_ERROR",
                    details={"question": question, "model": self.model_name, "original_error": str(e)}
                )
            except ValidationError as e:
                raise FindAnswersError(
                    f"Validation error in LLM response: {str(e)}",
                    error_type="LLM_RESPONSE_VALIDATION_ERROR",
                    details={"question": question, "original_error": str(e)}
                )
            except Exception as e:
                raise FindAnswersError(
                    f"Unexpected error during LLM processing: {str(e)}",
                    error_type="LLM_PROCESSING_ERROR",
                    details={"question": question, "model": self.model_name, "original_error": str(e)}
                )

            if (
                (
                    not result.full_answer_can_be_found_in_background_info
                    and not result.partial_answer_can_be_found_in_background_info
                )
                or not (
                    result.question_answered_in_full
                    or result.question_answered_partially
                )
                or result.question_not_answered_at_all
                or not result.collected_relevant_quotes_from_background_info
            ):
                logger.info("No answer found in knowledge base")

                return Answer(
                    content=None,
                    evaluation=result.insights_on_what_could_be_a_legitimate_answer
                    or "No relevant information found in the knowledge base",
                    grade="no-answer",
                    generation_info=None,
                    references=[],
                    extracted_entities=[],
                )

            final_answer = None

            if result.concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__revised:
                final_answer = result.concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__revised
            elif not result.brief_explanation_of_what_needs_to_change_in_order_to_stay_within_the_boundaries_of_collected_quotes:
                final_answer = (
                    result.concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__draft
                    or None
                )
            elif (
                result.brief_explanation_of_what_needs_to_change_in_order_to_stay_within_the_boundaries_of_collected_quotes
                and result.concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__draft
            ):
                logger.warning(
                    "Underlying LLM failed to generate a revised answer; falling back to draft"
                )
                final_answer = result.concise_and_minimal_synthesized_answer_based_solely_on_relevant_quotes__draft

            try:
                # Process final answer for proper encoding
                processed_content = None
                if final_answer:
                    processed_content = final_answer.encode("utf8").decode("unicode-escape").encode("utf16", "surrogatepass").decode("utf16")
                
                answer = Answer(
                    content=processed_content,
                    evaluation=result.insights_on_what_could_be_a_legitimate_answer or "",
                    grade="full" if result.question_answered_in_full else "partial",
                    generation_info=None,
                    references=[
                        ReferencedAnswer(
                            question_id=q.question_id,
                            quotes=q.quotes,
                        )
                        for q in result.collected_relevant_quotes_from_background_info
                    ],
                    extracted_entities=result.extracted_entities_found_in_background_info_and_referred_to_by_answer or [],
                )

                logger.info(
                    f'Question: "{question}"; Answer ({answer.grade}): "{answer.content}"'
                )

                return answer
                
            except UnicodeError as e:
                raise FindAnswersError(
                    f"Unicode encoding error while processing answer: {str(e)}",
                    error_type="UNICODE_ENCODING_ERROR",
                    details={"question": question, "original_error": str(e)}
                )
            except Exception as e:
                raise FindAnswersError(
                    f"Error while processing final answer: {str(e)}",
                    error_type="ANSWER_PROCESSING_ERROR",
                    details={"question": question, "original_error": str(e)}
                )
                
        except FindAnswersError:
            raise
        except Exception as e:
            raise FindAnswersError(
                f"Unexpected error in find_answers: {str(e)}",
                error_type="UNEXPECTED_ERROR",
                details={"question": question, "user_id": self.user_id, "original_error": str(e)}
            )
        



if __name__ == "__main__":
    find_answers = FindAnswers(user_id="b46a7229-2c29-4a88-ada1-c21a59f4eda1")
    answer = find_answers.find_answers("qui est yvan kondjo?")
    print(answer)