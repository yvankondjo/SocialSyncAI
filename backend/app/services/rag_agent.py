import logging
import operator
import json
import os
from typing import List, Dict, Any, Optional, Literal, Annotated

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    AnyMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import RemoveMessage, REMOVE_ALL_MESSAGES, add_messages
from pydantic import BaseModel, Field
from psycopg import connect
from psycopg.rows import dict_row

from app.deps.runtime_prod import CHECKPOINTER_POSTGRES
from app.deps.runtime_test import CHECKPOINTER_REDIS
from app.services.escalation import Escalation
from app.services.find_answers import FindAnswers
from app.services.retriever import Retriever

load_dotenv()

logger = logging.getLogger(__name__)


class QueryItem(BaseModel):
    query: str = Field(..., description="The query to search for")
    lang: Literal["french", "english", "spanish"] = Field(
        default="french", description="The language to search for"
    )


def create_find_answers_tool(user_id: str):
    """Factory function to create find_answers tool with user_id"""
    find_answers_service = FindAnswers(user_id)

    @tool
    def find_answers(question: str) -> dict:
        """
        Find the answers to the given user question
        Args:
            question: str the question to find the answers to
        Returns:
            dict: The answer to the question as a dictionary
        """
        answer = find_answers_service.find_answers(question)
        return answer.model_dump()

    return find_answers


def create_search_files_tool(user_id: str):
    """Factory function to create search_files tool with user_id"""
    retriever = Retriever(user_id)

    @tool
    def search_files(queries: List[QueryItem]) -> List[str]:
        """
        Search the documents for the given query

        Args:
            queries: List of query items to search for

        Returns:
            List of search results
        """
        all_results = []
        queries_list = queries if isinstance(queries, list) else [queries]

        for q in queries_list:
            try:
                query_item = q if isinstance(q, QueryItem) else QueryItem(**q)
            except Exception as e:
                print(f"Error creating QueryItem from {q}: {e}")
                continue

            results = retriever.retrieve_from_knowledge_chunks(
                query_item.query, k=10, type="hybrid", query_lang=query_item.lang
            )
            for r in results:
                all_results.append(r.get("content"))
        return all_results

    return search_files


def create_unified_search_tool(user_id: str, model_name: str = "x-ai/grok-4-fast"):
    """
    Factory function to create unified_search tool with user_id.

    This tool replaces the separate find_answers and search_files tools,
    executing both searches in parallel for optimal performance.
    """
    from app.services.unified_search import (
        UnifiedSearchService,
        QueryItem as UnifiedQueryItem,
    )

    service = UnifiedSearchService(user_id, model_name)

    @tool
    def unified_search(question: str, queries: List[dict]) -> dict:
        """
        Unified search across FAQ and knowledge documents.

        This tool automatically searches both FAQ database and document chunks in parallel
        for optimal performance. It intelligently merges results based on FAQ answer quality.

        The LLM should generate search queries in the appropriate languages based on the
        doc_lang configuration provided in the system prompt.

        Args:
            question: The user's original question (exactly as written)
            queries: List of search queries with languages, e.g.:
                [
                    {"query": "billing information", "lang": "english"},
                    {"query": "plan pricing details", "lang": "english"}
                ]

        Returns:
            dict with:
            - answer_content: The synthesized answer (or None if no answer found)
            - answer_grade: "full" (complete answer), "partial" (incomplete), or "no-answer"
            - faq_references: List of FAQ entries that were referenced
            - doc_chunks: List of relevant document chunks
            - metadata: Performance metrics (latencies, strategy used, etc.)
        """
        try:
            # Convert dicts to QueryItem objects
            query_items = [UnifiedQueryItem(**q) for q in queries]

            # Execute parallel search
            result = service.search(question, query_items)

            return result.model_dump()

        except Exception as e:
            logger.error(f"❌ Unified search failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return {
                "answer_content": None,
                "answer_grade": "no-answer",
                "faq_references": [],
                "doc_chunks": [],
                "metadata": {
                    "faq_latency": 0,
                    "docs_latency": 0,
                    "total_latency": 0,
                    "strategy_used": "error",
                    "faq_count": 0,
                    "docs_count": 0,
                },
            }

    return unified_search


def create_escalation_tool(user_id: str, conversation_id: str):
    """Factory function to create escalation tool with user_id"""
    escalation_service = Escalation(user_id, conversation_id)

    @tool
    def escalation(message: str, confidence: float, reason: str) -> EscalationResult:
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
            # Run async method in sync context
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            escalation_id = loop.run_until_complete(
                escalation_service.create_escalation(message, confidence, reason)
            )

            if escalation_id:
                return EscalationResult(
                    escalated=True,
                    escalation_id=escalation_id,
                    reason=f"Escalation créée avec succès. Email envoyé à l'équipe support.",
                )
            else:
                return EscalationResult(
                    escalated=False,
                    escalation_id=None,
                    reason="Échec de création de l'escalation",
                )

        except Exception as e:
            logger.error(f"Erreur lors de l'escalation: {e}")
            import traceback

            traceback.print_exc()
            return EscalationResult(
                escalated=False,
                escalation_id=None,
                reason=f"Erreur technique: {str(e)}",
            )

    return escalation


# NOTE: RAGAgentResponse is no longer used because we switched to llm_with_tools
# which allows tool calling (escalation, search, etc.) but returns plain text instead of JSON.
# We now handle confidence with a default value (0.85) in the calling code.
#
# class RAGAgentResponse(BaseModel):
#     """Response of the RAG Agent"""
#     response: str = Field(..., description="The response to the question")
#     confidence: float = Field(..., description="The confidence score of the response")


class EscalationResult(BaseModel):
    """Result of an escalation"""

    escalated: bool
    escalation_id: Optional[str] = None
    reason: str


class RAGAgentState(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages]
    search_results: List[str] = []
    n_search: int = 0
    find_answers_results: List[dict] = []
    n_find_answers: int = 0
    max_searches: int = 5
    max_find_answers: int = 5
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
        conversation_id: str,
        model_name: str = "gpt-4o-mini",
        summarization_model_name: str = "gpt-4o-mini",
        summarization_max_tokens: int = 300,
        system_prompt: str = "",
        max_searches: int = 3,
        trim_strategy: Literal["none", "hard", "summary"] = "summary",
        max_tokens: int = 8000,
        max_find_answers: int = 5,
        test_mode: bool = False,
        checkpointer=None,
    ):

        self.user_id = user_id
        self.model_name = model_name
        self.max_searches = max_searches
        self.trim_strategy = trim_strategy
        self.max_tokens = max_tokens
        self.max_find_answers = max_find_answers
        self.max_tokens_before_summary = int(max_tokens * 0.8)
        self.summarization_model_name = summarization_model_name
        self.summarization_max_tokens = summarization_max_tokens

        self.init_system_prompt = False
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
            model=model_name,
        )

        self.sum_llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
            model=summarization_model_name,
        )

        self.unified_search_tool = create_unified_search_tool(user_id, model_name)
        self.tools = [self.unified_search_tool]

        if not test_mode:
            self.escalation_tool = create_escalation_tool(user_id, conversation_id)
            self.tools.append(self.escalation_tool)

        self.llm_with_tools = self.llm.bind_tools(self.tools)
        if not system_prompt or system_prompt.strip() == "":
            from app.deps.system_prompt import SYSTEM_PROMPT

            system_prompt = SYSTEM_PROMPT
            logger.warning(
                f"[RAGAgent] No system_prompt provided for user {user_id}, using default SYSTEM_PROMPT"
            )

        self.system_prompt = [SystemMessage(content=system_prompt)]

        if test_mode:
            self.checkpointer = CHECKPOINTER_REDIS
        else:
            self.checkpointer = CHECKPOINTER_POSTGRES

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
            return graph.compile(checkpointer=self.checkpointer)
        else:
            return graph.compile()

    def _guardrails_pre_check(self, state: RAGAgentState) -> Dict[str, Any]:
        """Pre-validation: Check incoming message with OpenAI Moderation + custom guardrails
        If flagged → Block response (silent, no AI message generated)
        """
        try:
            from app.services.ai_decision_service import AIDecisionService

            last_user_message = (
                state.messages[-1].content
                if isinstance(state.messages[-1], HumanMessage)
                else None
            )

            if not last_user_message:
                return {}

            if isinstance(last_user_message, list):

                text_parts = [
                    part.get("text", "")
                    for part in last_user_message
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                message_text = " ".join(text_parts).strip()
                message_content = last_user_message
            else:

                message_text = str(last_user_message)
                message_content = None

            if not message_text:
                return {}

            decision_service = AIDecisionService(self.user_id)
            decision, confidence, reason, matched_rule = decision_service.check_message(
                message_text, context_type="chat", message_content=message_content
            )

            decision_log = decision_service.log_decision(
                message_id=None,
                message_text=message_text,
                decision=decision,
                confidence=confidence,
                reason=reason,
                matched_rule=matched_rule,
            )
            logger.debug(
                f"[GUARDRAILS PRE] Decision logged: {decision_log.get('id') if decision_log else 'failed'}"
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

    def _guardrails_post_check(self, state: RAGAgentState) -> Dict[str, Any]:
        """Post-validation: Check generated response safety
        If unsafe → Remove AI response + triggering user message from context (silent blocking)
        """
        try:
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

                if not last_ai_msg_obj.id:
                    logger.error(
                        f"[GUARDRAILS POST] AI message has no ID, cannot remove from context"
                    )
                    return {
                        "should_respond": False,
                        "error_message": f"GUARDRAIL_POST_BLOCKED: {moderation_result.get('reason')}",
                    }

                messages_to_remove = [RemoveMessage(id=last_ai_msg_obj.id)]

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

            return {}

        except Exception as e:
            logger.error(f"Error in guardrails_post_check: {e}")
            return {}

    def _error_handler(self, state: RAGAgentState) -> Dict[str, Any]:
        """Handle errors and guardrail blocks silently
        Logs the issue but does not generate any user-facing message
        """
        error_msg = state.error_message or "Unknown error"

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

        return {}

    def _manage_history(
        self,
        messages: List[AnyMessage],
        trim_strategy: Literal["none", "hard", "summary"],
        max_tokens: int,
    ) -> List[AnyMessage]:
        """Manage the history according to the configured strategy"""
        try:
            system_messages = [m for m in messages if isinstance(m, SystemMessage)]
            messages = [m for m in messages if not isinstance(m, SystemMessage)]

            if trim_strategy == "none":
                return []

            elif (
                trim_strategy == "hard"
                and count_tokens_approximately(messages) > max_tokens
            ):
                trimmed = trim_messages(
                    messages,
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=max_tokens,
                    start_on="human",
                    end_on=("human", "tool"),
                    include_system=False,
                )
                new_messages = system_messages + trimmed
                return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages

            elif (
                trim_strategy == "summary"
                and count_tokens_approximately(messages)
                > self.max_tokens_before_summary
            ):
                TAIL_LENGTH = 1
                TAIL_MESSAGES = messages[-TAIL_LENGTH:]
                messages_to_summarize = trim_messages(
                    messages,
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=self.max_tokens_before_summary,
                    start_on="human",
                    end_on=("human", "tool"),
                    include_system=False,
                )

                summary_prompt = (
                    "Summarize this conversation in the language of the conversation, "
                    "concisely but without losing key facts, decisions, TODOs.\n\n"
                    + "\n".join(
                        f"{m.__class__.__name__}: {getattr(m, 'content', '')}"
                        for m in messages_to_summarize[0:-TAIL_LENGTH]
                    )
                )

                summary_response = self.sum_llm.invoke(
                    [HumanMessage(content=summary_prompt)],
                    max_tokens=self.summarization_max_tokens,
                )

                summary_system = SystemMessage(
                    content=f"[PREVIOUS CONVERSATION SUMMARY]\n{summary_response.content}\n[END SUMMARY]"
                )

                new_messages = system_messages + [summary_system] + TAIL_MESSAGES

                return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages

        except Exception as e:
            return [AIMessage(content=f"Error in history management: {str(e)}")]

    def _call_llm(self, state: RAGAgentState) -> Dict[str, Any]:
        """Call the LLM with trimming soft and silent retry on errors"""
        MAX_RETRIES = 3
        RETRY_DELAY = 2  # seconds

        try:
            messages = state.messages.copy()
            if self.system_prompt and not self.init_system_prompt:
                self.init_system_prompt = True
                messages = self.system_prompt + messages

            trimmed_messages = self._manage_history(
                messages, self.trim_strategy, self.max_tokens
            )
            llm_input = trimmed_messages if trimmed_messages else messages

            # Retry logic with exponential backoff
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    # CRITICAL FIX: Use llm_with_tools to allow tool calls
                    # Only use structured_llm for final response (when no tools needed)
                    response = self.llm_with_tools.invoke(llm_input)

                    # Success - reset retry count if needed
                    if attempt > 0:
                        logger.info(
                            f"[LLM RETRY] Success on attempt {attempt + 1}/{MAX_RETRIES}"
                        )

                    # Return the raw AI message (might contain tool_calls)
                    return {"messages": [response], "retry_count": 0}

                except Exception as retry_error:
                    last_error = retry_error
                    logger.warning(
                        f"[LLM RETRY] Attempt {attempt + 1}/{MAX_RETRIES} failed: {str(retry_error)}"
                    )

                    if attempt < MAX_RETRIES - 1:
                        # Wait before retrying (exponential backoff)
                        import time

                        time.sleep(RETRY_DELAY * (2**attempt))
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

    def _handle_tool_call(self, state: RAGAgentState) -> Dict[str, Any]:
        """Handle the tool call"""
        try:
            last_message = state.messages[-1] if state.messages else None
            tool_calls = getattr(last_message, "tool_calls", [])
            tool_call = tool_calls[0]
            tool_name = tool_call.get("name")

            if tool_name == "unified_search":
                return self._unified_search(state)
            elif tool_name == "search_files":
                # Legacy support (will be removed after migration)
                return self._search_files(state)
            elif tool_name == "find_answers":
                # Legacy support (will be removed after migration)
                return self._find_answers(state)
            elif tool_name == "escalation":
                return self._escalation(state)
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
            return {
                "messages": [AIMessage(content="Error processing tool")],
                "error_message": str(e),
            }

    def _unified_search(self, state: RAGAgentState) -> Dict[str, Any]:
        """
        Execute unified search (parallel FAQ + documents search).
        This is an async tool, so we need to run it in an event loop.
        """
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
            }

        tool_call = tool_calls[0]
        try:
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            tool_args = tool_call.get("args", {})

            logger.info(f"🔍 Executing unified_search with args: {tool_args}")

            results = self.unified_search_tool.invoke(tool_args)

            logger.info(
                f"✅ Unified search completed: grade={results.get('answer_grade')}, "
                f"strategy={results.get('metadata', {}).get('strategy_used')}"
            )

            content = json.dumps(results, ensure_ascii=False)

            tool_message = ToolMessage(
                content=content, tool_call_id=tool_call_id, name=tool_name
            )

            return {
                "messages": [tool_message],
                "n_search": state.n_search + 1,
                "search_results": results.get("doc_chunks", []),
                "find_answers_results": (
                    [results] if results.get("faq_references") else []
                ),
            }

        except Exception as e:
            logger.error(f"❌ Error in _unified_search: {str(e)}")
            import traceback

            traceback.print_exc()

            error_content = json.dumps({"error": str(e)})
            tool_message = ToolMessage(
                content=error_content, tool_call_id=tool_call_id, name=tool_name
            )
            return {
                "messages": [tool_message],
                "error_message": str(e),
            }

    # def _find_answers(self, state: RAGAgentState) -> Dict[str, Any]:
    #     """Execute the find answers (LEGACY - use unified_search instead)"""

    #     last_message = state.messages[-1]
    #     tool_calls = getattr(last_message, "tool_calls", [])

    #     if not tool_calls:
    #         return {
    #             "messages": [
    #                 ToolMessage(
    #                     content=json.dumps({"error": "No tool calls found"}),
    #                     tool_call_id=None,
    #                     name=None,
    #                 )
    #             ],
    #             "n_find_answers": state.n_find_answers,
    #         }

    #     tool_messages = []
    #     find_answers_results: List[dict] = []

    #     tool_call = tool_calls[0]
    #     try:
    #         tool_name = tool_call.get("name")
    #         tool_call_id = tool_call.get("id")
    #         tool_args = tool_call.get("args", {})

    #         if state.n_find_answers >= state.max_find_answers:
    #             return {
    #                 "messages": [
    #                     ToolMessage(
    #                         content=json.dumps({"error": "Max find answers reached"}),
    #                         tool_call_id=tool_call_id,
    #                         name=tool_name,
    #                     )
    #                 ],
    #                 "n_find_answers": state.n_find_answers,
    #             }
    #         question = tool_args.get("question", "")
    #         results = self.find_answers_tool.invoke({"question": question})

    #         content = json.dumps(
    #             {"results": results, "question": question}, ensure_ascii=False
    #         )
    #         find_answers_results.append(results)

    #         tool_message = ToolMessage(
    #             content=content, tool_call_id=tool_call_id, name=tool_name
    #         )
    #         tool_messages.append(tool_message)

    #     except Exception as e:
    #         error_content = json.dumps({"error": str(e)})
    #         tool_message = ToolMessage(
    #             content=error_content, tool_call_id=tool_call_id, name=tool_name
    #         )
    #         tool_messages.append(tool_message)

    #     return {
    #         "messages": tool_messages,
    #         "n_find_answers": state.n_find_answers + 1,
    #         "find_answers_results": find_answers_results,
    #     }

    # def _search_files(self, state: RAGAgentState) -> Dict[str, Any]:
    #     """Execute the search"""

    #     last_message = state.messages[-1]
    #     tool_calls = getattr(last_message, "tool_calls", [])

    #     if not tool_calls:
    #         return {
    #             "messages": [
    #                 ToolMessage(
    #                     content=json.dumps({"error": "No tool calls found"}),
    #                     tool_call_id=None,
    #                     name=None,
    #                 )
    #             ],
    #             "n_search": state.n_search,
    #         }

    #     tool_messages = []
    #     search_results: List[str] = []

    #     tool_call = tool_calls[0]
    #     try:
    #         tool_name = tool_call.get("name")
    #         tool_args = tool_call.get("args", {})

    #         if tool_name == "search_files":
    #             if state.n_search >= state.max_searches:
    #                 return {
    #                     "messages": [
    #                         ToolMessage(
    #                             content=json.dumps({"error": "Max searches reached"}),
    #                             tool_call_id=tool_call.get("id"),
    #                             name=tool_call.get("name"),
    #                         )
    #                     ],
    #                     "n_search": state.n_search,
    #                 }
    #             queries = tool_args.get("queries", [])
    #             results = self.search_files_tool.invoke({"queries": queries})

    #             content = json.dumps(
    #                 {"results": results, "query_count": len(queries)},
    #                 ensure_ascii=False,
    #             )
    #             search_results.extend(results)
    #         else:
    #             content = json.dumps({"error": f"Unknown tool: {tool_name}"})

    #         tool_message = ToolMessage(
    #             content=content,
    #             tool_call_id=tool_call.get("id"),
    #             name=tool_call.get("name"),
    #         )
    #         tool_messages.append(tool_message)

    #     except Exception as e:
    #         error_content = json.dumps({"error": str(e)})
    #         tool_message = ToolMessage(
    #             content=error_content,
    #             tool_call_id=tool_call.get("id"),
    #             name=tool_call.get("name"),
    #         )
    #         tool_messages.append(tool_message)

    #     return {
    #         "messages": tool_messages,
    #         "n_search": state.n_search + 1,
    #         "search_results": search_results,
    #     }

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

            logger.info(f"[ESCALATION] Tool called successfully: {escalation_result}")

            escalation_dict = {
                "escalated": escalation_result.escalated,
                "escalation_id": escalation_result.escalation_id,
                "reason": escalation_result.reason,
            }

            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps({"escalation_result": escalation_dict}),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                    )
                ],
                "escalation_result": escalation_result,
            }

        except Exception as e:
            logger.error(f"[ESCALATION ERROR] {str(e)}")
            import traceback

            traceback.print_exc()
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
    model_name: str = "gpt-4o-mini",
    max_searches: int = 3,
    system_prompt: str = "",
    trim_strategy: Literal["none", "hard", "summary"] = "summary",
    max_tokens: int = 8000,
    max_find_answers: int = 5,
    test_mode: bool = False,
    checkpointer=None,
) -> RAGAgent:
    """Factory function to create a RAG Agent"""
    return RAGAgent(
        user_id=user_id,
        conversation_id=conversation_id,
        model_name=model_name,
        max_searches=max_searches,
        max_find_answers=max_find_answers,
        trim_strategy=trim_strategy,
        summarization_model_name=summarization_model_name,
        summarization_max_tokens=summarization_max_tokens,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        test_mode=test_mode,
    )


if __name__ == "__main__":
    # Import uniquement pour les tests (évite de bloquer le démarrage du backend)
    from app.deps.runtime_prod import CHECKPOINTER_POSTGRES

    agent = create_rag_agent(
        user_id="example_user_id",
        conversation_id="example_conversation_id",
        system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
        trim_strategy="summary",
        max_tokens=6000,
        max_find_answers=5,
        checkpointer=CHECKPOINTER_POSTGRES,
        test_mode=True,
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
