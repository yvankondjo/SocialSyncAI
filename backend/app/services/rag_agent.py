import logging
import operator
import json
import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Literal, Annotated, Tuple

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    AnyMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.utils import trim_messages
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import RemoveMessage, REMOVE_ALL_MESSAGES, add_messages
from pydantic import BaseModel, Field
from psycopg import connect
from psycopg.rows import dict_row

from app.deps.system_prompt import SYSTEM_PROMPT
from app.services.escalation import Escalation
from app.services.retriever import Retriever
from app.services.token_utils import (
    count_tokens,
    count_messages_tokens,
    get_model_context_window,
    get_max_input_tokens,
)
from app.db.session import get_db
from httpx import HTTPError

load_dotenv()

logger = logging.getLogger(__name__)

_AGENT_CACHE: Dict[str, Tuple["RAGAgent", float]] = {}
_AGENT_CACHE_TTL_SECONDS = int(os.getenv("RAG_AGENT_CACHE_TTL_SECONDS", "900"))


def _first_non_empty(*values: Optional[str], default: str) -> str:
    """Return the first non-empty/non-whitespace string, else default."""
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return default


def _parse_timeout(value: Optional[str], default: Optional[float]) -> Optional[float]:
    if value is None or value == "":
        return default
    lowered = value.lower()
    if lowered in {"none", "null", "off"}:
        return None
    try:
        return float(value)
    except ValueError:
        return default


def _setup_langsmith():
    """
    Configure LangSmith tracing according to official documentation:
    https://docs.langchain.com/langsmith/observability-llm-tutorial
    
    LangSmith tracing is automatically enabled when these environment variables are set:
    - LANGCHAIN_TRACING_V2=true (or LANGSMITH_TRACING_V2)
    - LANGCHAIN_API_KEY (or LANGSMITH_API_KEY)
    - LANGCHAIN_PROJECT (or LANGSMITH_PROJECT)
    - LANGCHAIN_ENDPOINT (or LANGSMITH_ENDPOINT, optional)
    """
    default_endpoint = "https://api.smith.langchain.com"

    langsmith_api_key = _first_non_empty(
        os.getenv("LANGSMITH_API_KEY"), os.getenv("LANGCHAIN_API_KEY"), default=""
    )
    langsmith_project = _first_non_empty(
        os.getenv("LANGSMITH_PROJECT"), os.getenv("LANGCHAIN_PROJECT"), default="pr-indelible-snail-69"
    )

    raw_endpoint = _first_non_empty(
        os.getenv("LANGSMITH_ENDPOINT"), os.getenv("LANGCHAIN_ENDPOINT"), default=""
    )
    langsmith_endpoint = raw_endpoint.strip() if raw_endpoint else ""

    if not langsmith_endpoint:
        langsmith_endpoint = default_endpoint
    
    tracing_v2 = os.getenv("LANGSMITH_TRACING_V2") or os.getenv("LANGCHAIN_TRACING_V2", "true")
    langsmith_tracing = tracing_v2.lower() == "true"
    
    if langsmith_api_key and langsmith_tracing:
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint
        os.environ["LANGSMITH_ENDPOINT"] = langsmith_endpoint
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        logger.info(
            f"LangSmith tracing enabled. Project: {langsmith_project}, Endpoint: {langsmith_endpoint}, "
            f"API Key: {langsmith_api_key[:10]}...{langsmith_api_key[-4:] if len(langsmith_api_key) > 14 else '***'}"
        )
        return True
    else:
        if not langsmith_api_key:
            logger.warning("LangSmith API key not found (LANGSMITH_API_KEY or LANGCHAIN_API_KEY), tracing disabled")
        else:
            logger.warning("LangSmith tracing disabled via LANGSMITH_TRACING_V2/LANGCHAIN_TRACING_V2")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

_setup_langsmith()


def load_user_faq(user_id: str) -> str:
    """
    Charge la FAQ de l'utilisateur depuis la base de données
    et la formate pour être incluse dans le system prompt.
    
    Returns:
        str: FAQ formatée pour le prompt, ou chaîne vide si aucune FAQ
    """
    try:
        db = get_db()
        question_answers = (
            db.table("faq_qa")
            .select("id, questions, answer")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        
        if not question_answers.data:
            logger.info(f"No FAQ found for user {user_id}")
            return ""
        
        faq_sections = []
        for item in question_answers.data:
            questions = item.get("questions", [])
            if isinstance(questions, str):
                questions = [questions]
            
            answer = item.get("answer", "")
            if questions and answer:
                questions_str = "\n".join(f"  - {q}" for q in questions)
                faq_sections.append(
                    f"**Questions:**\n{questions_str}\n**Réponse:**\n{answer}\n"
                )
        
        if faq_sections:
            formatted_faq = "\n---\n\n".join(faq_sections)
            logger.info(f"Loaded {len(faq_sections)} FAQ entries for user {user_id}")
            return formatted_faq
        
        return ""
        
    except HTTPError as e:
        logger.error(f"Database API error while loading FAQ: {str(e)}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error while loading FAQ: {str(e)}")
        return ""


def create_search_tool(user_id: str):
    """
    Factory function to create search tool for knowledge documents only.
    FAQ is now in the system prompt, so we only search documents when FAQ is insufficient.
    """
    retriever: Optional[Retriever] = None

    @tool
    def search(queries: List[dict]) -> dict:
        """
        Search knowledge documents when FAQ in system prompt is insufficient.

        Use this tool ONLY when:
        - The FAQ in your system prompt doesn't fully answer the question
        - You need additional information from knowledge documents
        - The question is complex and requires document context

        Args:
            queries: List of query dicts with 'query' and 'lang' keys
                - query: Search term (in the document language)
                - lang: One of "english", "french", or "spanish"

        Returns:
            dict with keys:
                - doc_chunks: List[str] - Retrieved document chunks
                - count: int - Number of chunks found
        """
        try:
            nonlocal retriever
            if retriever is None:
                init_start = time.perf_counter()
                retriever = Retriever(user_id)
                logger.info(f"🔎 Retriever init took {time.perf_counter() - init_start:.2f}s")

            all_chunks = []
            
            for query_dict in queries:
                query_text = query_dict.get("query", "")
                query_lang = query_dict.get("lang", "french")
                
                if not query_text:
                    continue
                
                results = retriever.retrieve_from_knowledge_chunks(
                    query=query_text,
                    k=10,
                    type="hybrid",
                    query_lang=query_lang
                )
                all_chunks.extend([r.get("content", "") for r in results if r.get("content")])
            
            return {
                "doc_chunks": all_chunks,
                "count": len(all_chunks)
            }
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "doc_chunks": [],
                "count": 0
            }

    return search


def create_escalation_tool(user_id: str, conversation_id: str):
    """Factory function to create escalation tool with user_id"""
    escalation_service = Escalation(user_id, conversation_id)

    @tool
    async def escalation(
        message: str, confidence: float, reason: str
    ) -> EscalationResult:
        """Escalate the conversation to human support

        This tool creates an escalation record, disables AI mode for the conversation,
        and sends an email notification to the support team with a secure link to
        access the conversation.

        Args:
            message: str the message that triggered the escalation
            confidence: float the confidence score of the escalation (0-100)
            reason: str the reason for the escalation

        Returns:
            EscalationResult: The escalation result with success status and details
        """
        try:

            escalation_id = await escalation_service.create_escalation(
                message, confidence, reason
            )

            if escalation_id:
                return EscalationResult(
                    escalated=True,
                    escalation_id=escalation_id,
                    reason=f"Escalation created successfully. Email sent to the support team.",
                )
            else:
                return EscalationResult(
                    escalated=False,
                    escalation_id=None,
                    reason="Escalation creation failed",
                )

        except Exception as e:
            logger.error(f"Error during escalation: {e}")
            return EscalationResult(
                escalated=False,
                escalation_id=None,
                reason=f"Technical error: {str(e)}",
            )

    return escalation


class RAGAgentResponse(BaseModel):
    """Response of the RAG Agent"""

    response: str = Field(..., description="The response to the question")
    confidence: float = Field(..., description="The confidence score of the response")


class EscalationResult(BaseModel):
    """Result of an escalation"""

    escalated: bool
    escalation_id: Optional[str] = None
    reason: str


class RAGAgentState(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages]
    search_results: List[str] = []
    n_search: int = 0
    max_searches: int = 5
    error_message: Optional[str] = None
    trim_strategy: Literal["none", "hard", "summary"] = "summary"
    max_tokens: int = 8000
    escalation_result: EscalationResult = EscalationResult(
        escalated=False, escalation_id=None, reason=""
    )
    guardrail_pre_result: Optional[dict] = None
    should_respond: bool = True
    retry_count: int = 0


class RAGAgent:
    """RAG Agent with LangGraph, PostgresSaver and advanced history management"""

    def __init__(
        self,
        user_id: str,
        summarization_model_name: str = "gpt-4o-mini",
        summarization_max_tokens: int = 300,
        max_searches: int = 3,
        trim_strategy: Literal["none", "hard", "summary"] = "summary",
        max_tokens: int = 8000,
        test_mode: bool = False,
        checkpointer=None,
        conversation_id: Optional[str] = None,
        credit_tracker=None,
        ai_settings: Dict[str, Any] = None,
    ):

        self.user_id = user_id

        # Ensure ai_settings is not None
        if ai_settings is None:
            ai_settings = {
                "ai_model": "gpt-4o-mini",
                "system_prompt": "",
                "doc_lang": ["french"]
            }

        self.model_name = ai_settings.get('ai_model', 'x-ai/grok-4-fast:free')
        
        # Store user's custom system prompt separately (will be added as 2nd SystemMessage)
        self.custom_user_prompt = ai_settings.get('system_prompt', '')
        
        # Get doc_lang for search tool instructions  
        self.doc_lang = ai_settings.get('doc_lang', ["french"])
        if isinstance(self.doc_lang, list):
            self.doc_lang = ", ".join(self.doc_lang)
        
        self.max_searches = max_searches
        self.trim_strategy = trim_strategy
        self.max_tokens = max_tokens
        
        # Stratégie OpenAI : utiliser 90% du context window du modèle (via token_utils)
        self.max_tokens_before_summary = get_max_input_tokens(self.model_name)
        model_context = get_model_context_window(self.model_name)
        logger.info(f"📊 [RAG_AGENT] Model: {self.model_name} | Context: {model_context:,} | Threshold (90%): {self.max_tokens_before_summary:,}")
        
        self.summarization_model_name = summarization_model_name
        self.summarization_max_tokens = summarization_max_tokens
        self.conversation_id = conversation_id

        self.credit_tracker = credit_tracker
        
        langsmith_enabled = _setup_langsmith()
        langsmith_config = {}
        if langsmith_enabled:
            logger.info("✅ LangSmith tracing enabled - LangChain will use env vars automatically")

        llm_timeout = _parse_timeout(os.getenv("RAG_LLM_TIMEOUT"), None)
        sum_timeout = _parse_timeout(os.getenv("RAG_SUM_TIMEOUT"), None)
        logger.info(f"⏱️ LLM timeout={llm_timeout}s, sum timeout={sum_timeout}s")

        llm_start = time.perf_counter()
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
            model=self.model_name,
            timeout=llm_timeout,
            max_retries=2,
            streaming=False,  # Disable streaming to speed up init
            model_kwargs={"parallel_tool_calls": False},
            **langsmith_config
        )
        logger.info(f"⏱️ LLM client init took {time.perf_counter() - llm_start:.2f}s")

        sum_start = time.perf_counter()
        self.sum_llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
            model=summarization_model_name,
            timeout=sum_timeout,
            max_retries=2,
            **langsmith_config
        )
        logger.info(f"⏱️ Summarization client init took {time.perf_counter() - sum_start:.2f}s")

        faq_start = time.time()
        faq_content = load_user_faq(user_id)
        logger.info(f"📚 [RAG_AGENT] FAQ loaded in {time.time() - faq_start:.2f}s (length: {len(faq_content)} chars)")
        self.faq_content = faq_content
        
        self.search_tool = create_search_tool(user_id)
        self.tools = [self.search_tool]

        if not test_mode:
            self.escalation_tool = create_escalation_tool(user_id, conversation_id)
            self.tools.append(self.escalation_tool)
        self.llm_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=False)
        
        # ===== BUILD SYSTEM PROMPTS =====
        # 1. Base system prompt with doc_lang
        base_system_prompt = SYSTEM_PROMPT.replace("{doc_lang}", self.doc_lang)
        
        # 2. Add FAQ section
        if faq_content:
            faq_section = f"\n\n## 📚 FAQ OF THE USER (USE THIS IN PRIORITY)\n\nYou have the following FAQ for this user. **YOU MUST USE THIS FAQ IN PRIORITY** to answer questions. Do not search in documents if the FAQ is sufficient.\n\n{faq_content}\n\n---\n\n**IMPORTANT RULE:**\n- If the FAQ contains a complete answer → Use it directly, NO NEED to call `search`\n- If the FAQ contains a partial answer → Use it and complete with `search` if necessary\n- If the FAQ does not contain an answer → Use `search` to search in documents\n- If even after `search` you don't find → Use `escalation`\n"
            base_system_prompt = base_system_prompt + faq_section
            logger.info(f"✅ [RAG_AGENT] FAQ section added to system prompt")
        else:
            faq_section = "\n\n## ⚠️ NO FAQ AVAILABLE\n\nNo FAQ is available for this user. You must use the `search` tool for all questions.\n"
            base_system_prompt = base_system_prompt + faq_section
            logger.info(f"⚠️ [RAG_AGENT] No FAQ found, using search-only mode")
        
        # 3. Create list of SystemMessages
        self.system_prompt = [SystemMessage(content=base_system_prompt)]
        
        # 4. Add user's custom system prompt as second SystemMessage (if provided)
        if self.custom_user_prompt:
            self.system_prompt.append(SystemMessage(content=f"## 🎯 CUSTOM INSTRUCTIONS FROM USER:\n\n{self.custom_user_prompt}"))
            logger.info(f"✅ [RAG_AGENT] Custom user prompt added ({len(self.custom_user_prompt)} chars)")
        
        logger.info(f"📋 [RAG_AGENT] System prompts built: {len(self.system_prompt)} message(s), total chars: {sum(len(m.content) for m in self.system_prompt)}")
        
        self.checkpointer = checkpointer

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with history management and guardrails"""
        graph = StateGraph(RAGAgentState)

        # Add nodes
        graph.add_node("guardrails_pre_check", self._guardrails_pre_check)
        graph.add_node("llm", self._call_llm)
        graph.add_node("handle_tool_call", self._handle_tool_call)
        graph.add_node("guardrails_post_check", self._guardrails_post_check)
        graph.add_node("error_handler", self._error_handler)

        # Entry point: pre-validation
        graph.set_entry_point("guardrails_pre_check")

        # Pre-check → llm (if safe) or error_handler (if flagged)
        graph.add_conditional_edges(
            "guardrails_pre_check",
            self._guardrails_pre_decision,
            {"proceed": "llm", "block": "error_handler"},
        )

        # LLM → Check for errors first, then tool_call or post_check
        graph.add_conditional_edges(
            "llm",
            self._check_llm_result,
            {
                "error": "error_handler",
                "tool_call": "handle_tool_call",
                "end": "guardrails_post_check",
            },
        )

        # Tool calls loop back to llm
        graph.add_edge("handle_tool_call", "llm")

        # Post-check → Check if response should be sent or blocked
        graph.add_conditional_edges(
            "guardrails_post_check",
            self._check_should_respond,
            {"blocked": "error_handler", "ok": END},
        )

        # Error handler → END (silent failure)
        graph.add_edge("error_handler", END)

        if self.checkpointer:
            logger.info(f"✅ [RAG_AGENT] Graph compiled with checkpointer for conversation {self.conversation_id}")
            return graph.compile(checkpointer=self.checkpointer)
        else:
            logger.warning(f"⚠️ [RAG_AGENT] Graph compiled WITHOUT checkpointer - memory will not persist!")
            return graph.compile()

    async def _guardrails_pre_check(self, state: RAGAgentState) -> Dict[str, Any]:
        """Pre-validation: Check incoming message with OpenAI Moderation + custom guardrails
        If flagged → Block response (silent, no AI message generated)
        """
        import time
        start_time = time.time()
        try:
            from app.services.ai_decision_service import AIDecisionService

            last_user_message = (
                state.messages[-1].content
                if isinstance(state.messages[-1], HumanMessage)
                else None
            )

            if not last_user_message:
                logger.info(f"⏱️ [GUARDRAILS_PRE] Completed in {time.time() - start_time:.2f}s (no message)")
                return {}

            # Handle messages with images/attachments
            if isinstance(last_user_message, list):
                # Extract text parts from message content (skip image parts)
                text_parts = [
                    part.get("text", "")
                    for part in last_user_message
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                message_text = " ".join(text_parts).strip()
                message_content = last_user_message
            else:
                # Simple text message
                message_text = str(last_user_message)
                message_content = None

            if not message_text:
                logger.info(f"⏱️ [GUARDRAILS_PRE] Completed in {time.time() - start_time:.2f}s (empty text)")
                return {}

            decision_start = time.time()
            decision_service = AIDecisionService(self.user_id)
            decision, confidence, reason, matched_rule = decision_service.check_message(
                message_text, context_type="chat", message_content=message_content
            )
            logger.info(f"⏱️ [GUARDRAILS_PRE] Decision check took {time.time() - decision_start:.2f}s")

            decision_log = decision_service.log_decision(
                message_id=None,
                message_text=message_text,
                decision=decision,
                confidence=confidence,
                reason=reason,
                matched_rule=matched_rule,
            )

            if decision.value == "ignore":
                logger.warning(
                    f"[GUARDRAILS PRE] Message flagged and blocked: {reason}"
                )

                return {
                    "guardrail_pre_result": {
                        "decision": "block",
                        "reason": reason,
                        "confidence": confidence,
                        "escalated": True,
                    },
                    "should_respond": False,
                    "error_message": f"GUARDRAIL_PRE_BLOCKED: {reason}",
                }

            return {
                "guardrail_pre_result": {
                    "decision": "proceed",
                    "reason": "Message passed guardrails",
                    "confidence": confidence,
                }
            }

        except Exception as e:
            logger.error(f"Error in guardrails_pre_check: {e}")
            return {}

    def _guardrails_pre_decision(self, state: RAGAgentState) -> str:
        """Decision point: proceed or block based on pre-check"""
        result = getattr(state, "guardrail_pre_result", None)

        if result and result.get("decision") == "block":
            logger.info(f"[GUARDRAILS] Blocking message: {result.get('reason')}")
            return "block"

        return "proceed"

    def _check_llm_result(self, state: RAGAgentState) -> str:
        """Check if LLM call resulted in error or should continue normally"""
        # Check for LLM errors
        if not state.should_respond:
            if state.error_message and "LLM_ERROR" in state.error_message:
                return "error"

        # Check for tool calls
        last_message = state.messages[-1] if state.messages else None
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.debug(
                f"[LLM RESULT] Found {len(last_message.tool_calls)} tool calls"
            )
            return "tool_call"

        # Normal end - proceed to post-check
        return "end"

    def _check_should_respond(self, state: RAGAgentState) -> str:
        """Check if post-guardrail blocked the response"""
        if not state.should_respond:
            if state.error_message and "GUARDRAIL_POST_BLOCKED" in state.error_message:
                logger.info(
                    f"[GUARDRAILS POST] Response blocked, routing to error handler"
                )
                return "blocked"

        return "ok"

    async def _guardrails_post_check(self, state: RAGAgentState) -> Dict[str, Any]:
        """Post-validation: Check generated response safety
        If unsafe → Remove AI response + triggering user message from context (silent blocking)
        """
        import time
        start_time = time.time()
        try:
            logger.info(f"🔍 [GUARDRAILS_POST] Starting post-check")
            from app.services.ai_decision_service import AIDecisionService

            # Find last AI message and its index
            last_ai_message = None
            last_ai_msg_obj = None
            last_ai_index = None

            for i in range(len(state.messages) - 1, -1, -1):
                msg = state.messages[i]
                if isinstance(msg, AIMessage):
                    if hasattr(msg, "content") and isinstance(msg.content, str):
                        last_ai_message = msg.content
                        last_ai_msg_obj = msg
                        last_ai_index = i
                        break

            if not last_ai_message or last_ai_msg_obj is None:
                return {}

            decision_service = AIDecisionService(self.user_id)
            moderation_result = decision_service._check_openai_moderation(
                last_ai_message
            )

            if moderation_result.get("flagged"):
                logger.warning(
                    f"[GUARDRAILS POST] Generated response flagged: {moderation_result.get('reason')}"
                )

                # Verify message has an ID before attempting removal
                if not last_ai_msg_obj.id:
                    logger.error(
                        f"[GUARDRAILS POST] AI message has no ID, cannot remove from context"
                    )
                    return {
                        "should_respond": False,
                        "error_message": f"GUARDRAIL_POST_BLOCKED: {moderation_result.get('reason')}",
                    }

                # Find the user message that triggered this AI response
                messages_to_remove = [RemoveMessage(id=last_ai_msg_obj.id)]

                # Look for the last HumanMessage before this AI response
                for i in range(last_ai_index - 1, -1, -1):
                    if isinstance(state.messages[i], HumanMessage):
                        if state.messages[i].id:
                            messages_to_remove.append(
                                RemoveMessage(id=state.messages[i].id)
                            )
                            logger.info(
                                f"[GUARDRAILS POST] Removing triggering user message from context"
                            )
                        else:
                            logger.warning(
                                f"[GUARDRAILS POST] User message has no ID, cannot remove from context"
                            )
                        break

                return {
                    "messages": messages_to_remove,
                    "should_respond": False,
                    "error_message": f"GUARDRAIL_POST_BLOCKED: {moderation_result.get('reason')}",
                }

            logger.info(f"⏱️ [GUARDRAILS_POST] Total time: {time.time() - start_time:.2f}s")
            return {}

        except Exception as e:
            logger.error(f"Error in guardrails_post_check: {e}")
            logger.info(f"⏱️ [GUARDRAILS_POST] Total time (error): {time.time() - start_time:.2f}s")
            return {}

    async def _error_handler(self, state: RAGAgentState) -> Dict[str, Any]:
        """Handle errors and guardrail blocks silently
        Logs the issue but does not generate any user-facing message
        """
        error_msg = state.error_message or "Unknown error"

        # Categorize the error type
        if "GUARDRAIL_PRE_BLOCKED" in error_msg:
            logger.info(
                f"[SILENT FAILURE] Pre-guardrail blocked message for user {self.user_id}"
            )
        elif "GUARDRAIL_POST_BLOCKED" in error_msg:
            logger.info(
                f"[SILENT FAILURE] Post-guardrail blocked response for user {self.user_id}"
            )
        elif "LLM_ERROR" in error_msg:
            logger.error(
                f"[SILENT FAILURE] LLM error for user {self.user_id}: {error_msg}"
            )
        else:
            logger.warning(
                f"[SILENT FAILURE] Unknown error type for user {self.user_id}: {error_msg}"
            )

        # Return empty dict - no messages generated (silent failure)
        return {}

    async def _manage_history(
        self,
        messages: List[AnyMessage],
        trim_strategy: Literal["none", "hard", "summary"],
        max_tokens: int,
    ) -> List[AnyMessage]:
        """
        Gestion avancée de l'historique - Stratégie digne des ingénieurs d'OpenAI :
        
        1. Utilise tiktoken pour un comptage précis des tokens
        2. Seuil élevé de 100K tokens avant intervention
        3. Stratégie de sliding window + summary progressif :
           - Conserve les N derniers messages (fenêtre récente)
           - Résume les messages plus anciens de manière progressive
           - Préserve la structure conversationnelle (human/ai pairs)
        4. Async natif pour éviter les problèmes d'event loop
        """
        history_start = time.time()
        try:
            # Séparer les messages système des autres
            system_messages = [m for m in messages if isinstance(m, SystemMessage)]
            conversation_messages = [m for m in messages if not isinstance(m, SystemMessage)]
            
            # Compter les tokens avec tiktoken (précis) via token_utils
            current_tokens = count_messages_tokens(conversation_messages)
            
            if trim_strategy == "none":
                logger.info(f"⏱️ [MANAGE_HISTORY] Strategy: none | Tokens: {current_tokens:,} | Time: {time.time() - history_start:.2f}s")
                return []
            
            # Stratégie HARD : trim simple pour respecter max_tokens immédiat
            elif trim_strategy == "hard" and current_tokens > max_tokens:
                logger.info(f"📉 [MANAGE_HISTORY] Hard trim activated | Current: {current_tokens:,} > Max: {max_tokens:,}")
                
                # Garder les derniers messages jusqu'à max_tokens
                trimmed = []
                tokens_count = 0
                
                # Partir de la fin et remonter
                for msg in reversed(conversation_messages):
                    msg_tokens = count_messages_tokens([msg])
                    if tokens_count + msg_tokens <= max_tokens:
                        trimmed.insert(0, msg)
                        tokens_count += msg_tokens
                    else:
                        break
                
                new_messages = system_messages + trimmed
                logger.info(f"✂️ [MANAGE_HISTORY] Hard trim done | Kept: {len(trimmed)}/{len(conversation_messages)} messages | Tokens: {tokens_count:,} | Time: {time.time() - history_start:.2f}s")
                return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages
            
            # Stratégie SUMMARY : résumé progressif avec sliding window (100K tokens seuil)
            elif trim_strategy == "summary" and current_tokens > self.max_tokens_before_summary:
                logger.info(f"📝 [MANAGE_HISTORY] Summary strategy activated | Current: {current_tokens:,} > Threshold: {self.max_tokens_before_summary:,}")
                
                # Configuration de la fenêtre glissante
                # Conserver les 20 derniers messages (≈ 10 échanges) pour le contexte immédiat
                SLIDING_WINDOW_SIZE = 20
                
                # Messages récents à conserver (fenêtre glissante)
                recent_messages = conversation_messages[-SLIDING_WINDOW_SIZE:] if len(conversation_messages) > SLIDING_WINDOW_SIZE else conversation_messages
                
                # Messages plus anciens à résumer
                old_messages = conversation_messages[:-SLIDING_WINDOW_SIZE] if len(conversation_messages) > SLIDING_WINDOW_SIZE else []
                
                if not old_messages:
                    # Pas assez de messages pour résumer
                    logger.info(f"⚠️ [MANAGE_HISTORY] Not enough messages to summarize, keeping all")
                    return []
                
                # Préparer le prompt de résumé optimisé
                summary_prompt = (
                    "Tu es un expert en résumé de conversations. "
                    "Résume cette conversation de manière concise mais complète :\n\n"
                    "INSTRUCTIONS :\n"
                    "- Conserve TOUS les faits importants, décisions, TODOs, et informations clés\n"
                    "- Utilise la même langue que la conversation\n"
                    "- Structure le résumé par thèmes ou chronologiquement\n"
                    "- Sois concis mais ne perds AUCUNE information importante\n\n"
                    "CONVERSATION À RÉSUMER :\n\n"
                )
                
                # Formater les messages à résumer
                for msg in old_messages:
                    role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                    content = getattr(msg, 'content', '')
                    if isinstance(content, str):
                        summary_prompt += f"{role}: {content}\n\n"
                
                summary_start = time.time()
                logger.info(f"🤖 [MANAGE_HISTORY] Generating summary | Messages to summarize: {len(old_messages)} | Prompt length: {len(summary_prompt):,} chars")
                
                # ⚠️ IMPORTANT: Track credit cost for summarization LLM call
                if self.credit_tracker:
                    from app.deps.credit_tracker import get_model_credit_cost
                    summary_credit_cost = await get_model_credit_cost(self.summarization_model_name)
                    can_summarize = await self.credit_tracker.track_ai_call(
                        model_name=self.summarization_model_name,
                        credit_cost=summary_credit_cost,
                        has_tool_calls=False,
                        conversation_id=self.conversation_id,
                        metadata={"type": "history_summarization", "messages_count": len(old_messages)}
                    )
                    if not can_summarize:
                        logger.warning(f"⚠️ [MANAGE_HISTORY] Cannot summarize - credit limit reached, keeping recent messages only")
                        # Fallback: just keep recent messages without summary
                        return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + system_messages + recent_messages
                
                # Appel ASYNC natif (pas asyncio.run qui cause l'erreur)
                summary_response = await asyncio.to_thread(
                    self.sum_llm.invoke,
                    [HumanMessage(content=summary_prompt)],
                    {"max_tokens": self.summarization_max_tokens}
                )
                
                summary_time = time.time() - summary_start
                summary_content = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)
                logger.info(f"✅ [MANAGE_HISTORY] Summary generated | Length: {len(summary_content):,} chars | Time: {summary_time:.2f}s")
                
                # Créer un message système avec le résumé
                summary_system = SystemMessage(
                    content=(
                        f"═══════════════════════════════════════════════════════════\n"
                        f"📚 RÉSUMÉ DE LA CONVERSATION PRÉCÉDENTE\n"
                        f"═══════════════════════════════════════════════════════════\n\n"
                        f"{summary_content}\n\n"
                        f"═══════════════════════════════════════════════════════════\n"
                        f"La conversation récente continue ci-dessous...\n"
                        f"═══════════════════════════════════════════════════════════\n"
                    )
                )
                
                # Nouvelle structure : système + résumé + messages récents
                new_messages = system_messages + [summary_system] + recent_messages
                new_tokens = count_messages_tokens(new_messages)
                
                reduction_percent = ((current_tokens - new_tokens) / current_tokens * 100) if current_tokens > 0 else 0
                
                logger.info(
                    f"🎯 [MANAGE_HISTORY] Summary strategy completed | "
                    f"Old messages: {len(old_messages)} → Summary | "
                    f"Recent messages kept: {len(recent_messages)} | "
                    f"Tokens: {current_tokens:,} → {new_tokens:,} ({reduction_percent:.1f}% reduction) | "
                    f"Total time: {time.time() - history_start:.2f}s"
                )
                
                return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages
            
            else:
                # Pas de gestion nécessaire
                logger.info(f"✅ [MANAGE_HISTORY] No action needed | Tokens: {current_tokens:,}/{self.max_tokens_before_summary:,} | Time: {time.time() - history_start:.2f}s")
                return []
        
        except Exception as e:
            logger.error(f"❌ [MANAGE_HISTORY] Error: {e}", exc_info=True)
            logger.info(f"⏱️ [MANAGE_HISTORY] Total time (error): {time.time() - history_start:.2f}s")
            # En cas d'erreur, ne pas bloquer - retourner vide
            return []

    async def _call_llm(self, state: RAGAgentState) -> Dict[str, Any]:
        """Call the LLM with trimming soft, credit tracking, and silent retry on errors"""
        import time
        start_time = time.time()
        MAX_RETRIES = 3
        RETRY_DELAY = 2  # seconds

        try:
            logger.info(f"🤖 [CALL_LLM] Starting LLM call for user {self.user_id}")
            if self.credit_tracker:
                from app.deps.credit_tracker import get_model_credit_cost

                credit_cost = await get_model_credit_cost(self.model_name)

                can_proceed = await self.credit_tracker.track_ai_call(
                    model_name=self.model_name,
                    credit_cost=credit_cost,
                    has_tool_calls=False,
                    conversation_id=getattr(state, "conversation_id", None),
                )
                if not can_proceed:
                    logger.error(
                        f"[LLM ERROR] Credit limit exceeded for user {self.user_id}"
                    )
                    return {
                        "should_respond": False,
                        "error_message": "LLM_ERROR: Credit limit exceeded",
                    }

            messages = state.messages.copy()
            
            # ALWAYS prepend system prompt - it contains FAQ and instructions
            # The checkpointer stores conversation state separately, so we need
            # to inject the system prompt on every LLM call
            if self.system_prompt:
                # Check if first message is already a SystemMessage (avoid duplicates within same invoke)
                has_system_msg = messages and isinstance(messages[0], SystemMessage)
                if not has_system_msg:
                    messages = self.system_prompt + messages
                    logger.info(f"📋 [CALL_LLM] Injected system prompt with FAQ ({len(self.faq_content)} chars)")

            trimmed_messages = await self._manage_history(
                messages, self.trim_strategy, self.max_tokens
            )
            llm_input = trimmed_messages if trimmed_messages else messages

            # Retry logic with exponential backoff
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    # CRITICAL FIX: Use llm_with_tools to allow tool calls
                    # The graph will automatically detect tool_calls via _check_llm_result
                    # Use asyncio.to_thread to avoid blocking the event loop
                    import asyncio
                    llm_call_start = time.time()
                    logger.info(f"🤖 [CALL_LLM] Starting LLM invoke (attempt {attempt + 1}/{MAX_RETRIES})")
                    response = await asyncio.to_thread(self.llm_with_tools.invoke, llm_input)
                    logger.info(f"⏱️ [CALL_LLM] LLM invoke completed in {time.time() - llm_call_start:.2f}s (attempt {attempt + 1})")

                    # Success - reset retry count if needed
                    if attempt > 0:
                        logger.info(
                            f"[LLM RETRY] Success on attempt {attempt + 1}/{MAX_RETRIES}"
                        )

                    # Return the raw AI message (might contain tool_calls or final response)
                    logger.info(f"⏱️ [CALL_LLM] Total time: {time.time() - start_time:.2f}s")
                    return {"messages": [response], "retry_count": 0}

                except Exception as retry_error:
                    last_error = retry_error
                    logger.warning(
                        f"[LLM RETRY] Attempt {attempt + 1}/{MAX_RETRIES} failed: {str(retry_error)}"
                    )

                    if attempt < MAX_RETRIES - 1:
                        # Wait before retrying (exponential backoff)
                        import asyncio

                        await asyncio.sleep(RETRY_DELAY * (2**attempt))
                    else:
                        # Max retries reached
                        logger.error(
                            f"[LLM ERROR] Max retries ({MAX_RETRIES}) reached for user {self.user_id}: {str(last_error)}"
                        )

            # All retries failed - return silent failure
            return {
                "should_respond": False,
                "error_message": f"LLM_ERROR: {str(last_error)}",
                "retry_count": MAX_RETRIES,
            }

        except Exception as e:
            logger.error(
                f"[LLM ERROR] Critical error in _call_llm for {self.user_id}: {e}"
            )
            return {"should_respond": False, "error_message": f"LLM_ERROR: {str(e)}"}

    async def _handle_tool_call(self, state: RAGAgentState) -> Dict[str, Any]:
        """Handle the tool call with credit tracking"""
        import time
        start_time = time.time()
        try:
            logger.info(f"🔧 [HANDLE_TOOL] Starting tool call handling")
            if self.credit_tracker:
                from app.deps.credit_tracker import get_model_credit_cost

                credit_cost = await get_model_credit_cost(self.model_name)

                can_proceed = await self.credit_tracker.track_ai_call(
                    model_name=self.model_name,
                    credit_cost=credit_cost,
                    has_tool_calls=True,
                    conversation_id=getattr(state, "conversation_id", None),
                    metadata={"tool_call": True},
                )
                if not can_proceed:
                    return {
                        "messages": [
                            AIMessage(
                                content="Error credit limit exceeded for tool call"
                            )
                        ],
                        "error_message": "Credit limit exceeded for tool call",
                    }

            last_message = state.messages[-1] if state.messages else None
            tool_calls = getattr(last_message, "tool_calls", [])
            tool_call = tool_calls[0]
            tool_name = tool_call.get("name")

            tool_start = time.time()
            if tool_name == "search":
                logger.info(f"🔍 [HANDLE_TOOL] Calling search tool")
                result = self._search(state)
                logger.info(f"⏱️ [HANDLE_TOOL] Search tool completed in {time.time() - tool_start:.2f}s")
                logger.info(f"⏱️ [HANDLE_TOOL] Total time: {time.time() - start_time:.2f}s")
                return result
            elif tool_name == "escalation":
                logger.info(f"🚨 [HANDLE_TOOL] Calling escalation tool")
                result = self._escalation(state)
                logger.info(f"⏱️ [HANDLE_TOOL] Escalation tool completed in {time.time() - tool_start:.2f}s")
                logger.info(f"⏱️ [HANDLE_TOOL] Total time: {time.time() - start_time:.2f}s")
                return result
            else:
                return {
                    "messages": [
                        ToolMessage(
                            content=json.dumps({"error": "Unknown tool"}),
                            tool_call_id=tool_call.get("id"),
                            name=tool_call.get("name"),
                        )
                    ],
                }
        except Exception as e:
            logger.error(f"Error in _handle_tool_call: {e}")
            logger.info(f"⏱️ [HANDLE_TOOL] Total time (error): {time.time() - start_time:.2f}s")
            return {
                "messages": [AIMessage(content="Error processing tool")],
                "error_message": str(e),
            }

    def _search(self, state: RAGAgentState) -> Dict[str, Any]:
        """
        Execute search in knowledge documents only.
        FAQ is now in system prompt, so this is only for document search.
        """
        import time
        search_start = time.time()
        logger.info(f"🔍 [SEARCH] Starting document search")
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        if not tool_calls:
            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps({"error": "No tool calls found"}),
                        tool_call_id=None,
                        name=None,
                    )
                ],
                "n_search": state.n_search,
            }

        tool_call = tool_calls[0]
        try:
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            tool_args = tool_call.get("args", {})

            if state.n_search >= state.max_searches:
                return {
                    "messages": [
                        ToolMessage(
                            content=json.dumps({"error": "Max searches reached"}),
                            tool_call_id=tool_call_id,
                            name=tool_name,
                        )
                    ],
                    "n_search": state.n_search,
                }

            logger.info(f"🔍 [SEARCH] Executing search with args: {tool_args}")
            search_invoke_start = time.time()
            
            results = self.search_tool.invoke(tool_args)
            
            logger.info(
                f"✅ [SEARCH] Search completed in {time.time() - search_invoke_start:.2f}s: {results.get('count', 0)} document chunks found"
            )
            logger.info(f"⏱️ [SEARCH] Total time: {time.time() - search_start:.2f}s")

            doc_chunks = results.get("doc_chunks", [])

            content = json.dumps(results, ensure_ascii=False)
            tool_message = ToolMessage(
                content=content, tool_call_id=tool_call_id, name=tool_name
            )

            return {
                "messages": [tool_message],
                "n_search": state.n_search + 1,
                "search_results": doc_chunks,
            }

        except Exception as e:
            logger.error(f"❌ Error in _search: {str(e)}")
            import traceback

            traceback.print_exc()

            error_content = json.dumps({"error": str(e)})
            tool_message = ToolMessage(
                content=error_content,
                tool_call_id=tool_call.get("id"),
                name=tool_call.get("name"),
            )

            return {
                "messages": [tool_message],
                "n_search": state.n_search,
                "error_message": str(e),
            }

    def _escalation(self, state: RAGAgentState) -> Dict[str, Any]:
        """Execute the escalation"""

        last_message = state.messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        if not tool_calls:
            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps({"error": "No tool calls found"}),
                        tool_call_id=None,
                        name=None,
                    )
                ],
                "escalation_result": state.escalation_result,
            }
        try:
            tool_call = tool_calls[0]
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            tool_args = tool_call.get("args", {})

            message = tool_args.get("message", "")
            confidence = tool_args.get("confidence", 0)
            reason = tool_args.get("reason", "")
            escalation_result = self.escalation_tool.invoke(
                {"message": message, "confidence": confidence, "reason": reason}
            )
            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps({"escalation_result": escalation_result}),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                    )
                ],
                "escalation_result": escalation_result,
            }

        except Exception as e:
            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps({"error": str(e)}),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                    )
                ],
                "escalation_result": state.escalation_result,
            }


def create_rag_agent(
    user_id: str,
    conversation_id: str,
    summarization_model_name: str = "gpt-4o-mini",
    summarization_max_tokens: int = 350,
    max_searches: int = 3,
    trim_strategy: Literal["none", "hard", "summary"] = "summary",
    max_tokens: int = 8000,
    test_mode: bool = False,
    checkpointer=None,
    credit_tracker=None,
    ai_settings: Optional[Dict[str, Any]] = None,
) -> RAGAgent:
    """Factory function to create a RAG Agent with caching."""
    # Use ai_settings if provided, otherwise create default
    if ai_settings is None:
        ai_settings = {
            "ai_model": "gpt-4o-mini",
            "system_prompt": "",
            "doc_lang": ["french"]
        }

    # Create cache key based on ai_settings
    cache_key = ":".join(
        [
            user_id,
            conversation_id,
            ai_settings.get('ai_model', 'gpt-4o-mini'),
            str(hash(ai_settings.get('system_prompt', ''))),
            str(hash(str(ai_settings.get('doc_lang', ['french'])))),
            summarization_model_name,
            str(max_searches),
            trim_strategy,
            str(max_tokens),
            str(test_mode),
        ]
    )

    now = time.time()
    cached = _AGENT_CACHE.get(cache_key)
    if cached:
        agent, ts = cached
        if now - ts < _AGENT_CACHE_TTL_SECONDS:
            agent.credit_tracker = credit_tracker
            logger.info(
                "♻️ [RAG_AGENT_CACHE] Reusing cached agent for user=%s conversation=%s",
                user_id,
                conversation_id,
            )
            return agent

    expired_keys = [k for k, (_, ts) in _AGENT_CACHE.items() if now - ts >= _AGENT_CACHE_TTL_SECONDS]
    for key in expired_keys:
        _AGENT_CACHE.pop(key, None)

    agent = RAGAgent(
        user_id=user_id,
        conversation_id=conversation_id,
        max_searches=max_searches,
        trim_strategy=trim_strategy,
        summarization_model_name=summarization_model_name,
        summarization_max_tokens=summarization_max_tokens,
        max_tokens=max_tokens,
        checkpointer=checkpointer,
        test_mode=test_mode,
        credit_tracker=credit_tracker,
        ai_settings=ai_settings,
    )
    _AGENT_CACHE[cache_key] = (agent, now)
    logger.info(
        "✅ [RAG_AGENT_CACHE] Agent cached for user=%s conversation=%s (ttl=%ss)",
        user_id,
        conversation_id,
        _AGENT_CACHE_TTL_SECONDS,
    )
    return agent


async def main():
    # Import uniquement pour les tests (évite de bloquer le démarrage du backend)
    from app.deps.runtime_prod import get_checkpointer

    checkpointer = await get_checkpointer()
    agent = create_rag_agent(
        user_id="example_user_id",
        conversation_id="example_conversation_id",
        trim_strategy="summary",
        max_tokens=6000,
        checkpointer=checkpointer,
        test_mode=True,
        ai_settings={
            "ai_model": "gpt-4o-mini",
            "system_prompt": "You are a helpful assistant that can answer questions and help with tasks.",
            "doc_lang": ["french"]
        }
    )

    print("Accès au graphique...")
    graph = agent.graph.get_graph()

    print("Génération du code Mermaid...")
    try:
        mermaid_code = graph.draw_mermaid()
        print("Code Mermaid généré avec succès!")
        print("Longueur du code:", len(mermaid_code), "caractères")

        with open("/workspace/rag_agent_graph.mmd", "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        print("Code Mermaid sauvegardé dans /workspace/rag_agent_graph.mmd")

        print("\nPremières lignes du code Mermaid:")
        print("=" * 50)
        lines = mermaid_code.split("\n")
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {line}")
        if len(lines) > 20:
            print(f"... et {len(lines) - 20} lignes supplémentaires")

    except Exception as e:
        print(f"Erreur lors de la génération du code Mermaid: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
