from langchain_core.tools import tool
from typing import List, Dict, Any, Optional, Literal
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
# import sys
# from pathlib import Path
# backend_path = Path(__file__).parent.parent.parent
# sys.path.insert(0, str(backend_path))
load_dotenv()
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import RemoveMessage, REMOVE_ALL_MESSAGES
from pydantic import BaseModel, Field
from typing import Annotated
import operator
import json
from psycopg import connect
from psycopg.rows import dict_row
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from app.services.retriever import Retriever
from app.services.find_answers import Answer, FindAnswers
from app.services.escalation import Escalation
# from langmem.short_term import SummarizationNode
load_dotenv()

class QueryItem(BaseModel):
    query: str = Field(..., description="The query to search for")
    lang: Literal["french", "english", "spanish"] = Field(default="french", description="The language to search for")




def create_find_answers_tool(user_id: str):
    """Factory function to create find_answers tool with user_id"""
    find_answers_service = FindAnswers(user_id)
    
    @tool
    def find_answers(question: str) -> Answer:
        """
        Find the answers to the given user question
        Args:
            question: str the question to find the answers to
        Returns:
            Answer: The answer to the question
        """
        return find_answers_service.find_answers(question)
    
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
                query_item.query, k=10, type='hybrid', query_lang=query_item.lang
            )
            for r in results:
                all_results.append(r.get('content'))
        return all_results
    
    return search_files
def create_escalation_tool(user_id: str, conversation_id: str):
    """Factory function to create escalation tool with user_id"""
    escalation_service = Escalation(user_id, conversation_id)
    
    @tool
    def escalation(message: str, confidence: float, reason: str) -> EscalationResult:
        """Escalate the conversation
        Args:
            message: str the message that triggered the escalation
            confidence: float the confidence score of the escalation
            reason: str the reason for the escalation
        Returns:
            EscalationResult: The escalation result
        """
        return escalation_service.create_escalation(message, confidence, reason)
    
    return escalation

class AIResponse(BaseModel):
    """Json format for the response"""
    response: str
    confidence: float

class EscalationResult(BaseModel):
    """Result of an escalation"""
    escalated: bool
    escalation_id: Optional[str] = None
    reason: str

class RAGAgentState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add]
    search_results: List[str] = []
    n_search: int = 0
    find_answers_results: List[Answer] = []
    n_find_answers: int = 0
    max_searches: int = 5
    max_find_answers: int = 5
    error_message: Optional[str] = None
    trim_strategy: Literal["none", "hard", "summary"] = "summary"
    max_tokens: int = 8000
    escalation_result: EscalationResult = EscalationResult(escalated=False, escalation_id=None, reason="")


class RAGAgent:
    """RAG Agent with LangGraph, PostgresSaver and advanced history management"""

    def __init__(self,
                 user_id: str,
                 conversation_id: str,
                 model_name: str = "gpt-4o-mini", 
                 summarization_model_name: str = "gpt-4o-mini",
                 summarization_max_tokens: int = 300,
                 system_prompt: str = None,
                 max_searches: int = 3,
                 trim_strategy: Literal["none", "hard", "summary"] = "summary",
                 max_tokens: int = 8000,
                 max_find_answers: int = 5):
        
        self.user_id = user_id
        self.model_name = model_name
        self.max_searches = max_searches
        self.trim_strategy = trim_strategy
        self.max_tokens = max_tokens
        self.max_find_answers = max_find_answers
        self.max_tokens_before_summary = int(max_tokens * 0.8)
        self.summarization_model_name = summarization_model_name
        self.summarization_max_tokens = summarization_max_tokens
        self.system_prompt = SystemMessage(content=system_prompt) if system_prompt else None
        self.init_system_prompt = False
        self.llm = ChatOpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL') or "https://openrouter.ai/api/v1",
            model=model_name
        )
        
        self.sum_llm = ChatOpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL') or "https://openrouter.ai/api/v1",
            model=summarization_model_name
        )
        self.escalation_tool = create_escalation_tool(user_id, conversation_id)
        self.search_files_tool = create_search_files_tool(user_id)
        self.find_answers_tool = create_find_answers_tool(user_id)
        self.tools = [self.search_files_tool, self.find_answers_tool, self.escalation_tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)


        host = os.getenv("SUPABASE_DB_HOST")
        port = os.getenv("SUPABASE_DB_PORT")
        dbname = os.getenv("SUPABASE_DB_NAME")
        user = os.getenv("SUPABASE_DB_USER")
        password = os.getenv("SUPABASE_DB_PASSWORD")
        self.conn = connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",
            connect_timeout=60,
            row_factory=dict_row
        )
        self.conn.autocommit = True
        

        self.checkpointer = PostgresSaver(self.conn)
        self.checkpointer.setup()

        
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with history management"""
        graph = StateGraph(RAGAgentState)
        graph.add_node("llm", self._call_llm)
        graph.add_node("handle_tool_call", self._handle_tool_call)
        graph.set_entry_point("llm")

    
        graph.add_conditional_edges(
            "llm",
            self._next_action,
            {
                "handle_tool_call": "handle_tool_call",
                "end": END
            }
        )
        
       
        graph.add_edge(
            "handle_tool_call",
            "llm"
        )
        


        
        return graph.compile(checkpointer=self.checkpointer)

    def _manage_history(self, messages: List[AnyMessage], trim_strategy: Literal["none", "hard", "summary"], max_tokens: int) -> List[AnyMessage]:
        """Manage the history according to the configured strategy"""
        try:
            if trim_strategy == "none":
                return [] 


            elif trim_strategy == "hard" and count_tokens_approximately(messages) > max_tokens:
                trimmed = trim_messages(
                    messages,
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=max_tokens,
                    start_on="human",
                    end_on=("human", "tool"),
                    include_system=True
                )
                
                return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + trimmed
                

            elif trim_strategy == "summary" and count_tokens_approximately(messages) > self.max_tokens_before_summary:

                messages_to_summarize = trim_messages(
                    messages,
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=self.max_tokens_before_summary,
                    start_on="human",
                    end_on=("human", "tool"),
                    include_system=True
                )

                summary_prompt = (
                    "Summarize this conversation in the language of the conversation, "
                    "concisely but without losing key facts, decisions, TODOs.\n\n"
                    + "\n".join(f"{m.__class__.__name__}: {getattr(m, 'content', '')}"
                                for m in messages_to_summarize)
                )

                summary_response = self.sum_llm.invoke(
                    [HumanMessage(content=summary_prompt)],
                    max_tokens=self.summarization_max_tokens
                )

                summary_system = SystemMessage(
                    content=f"[PREVIOUS CONVERSATION SUMMARY]\n{summary_response.content}\n[END SUMMARY]"
                )

                system_messages = [m for m in messages if isinstance(m, SystemMessage)]
                

                new_messages = system_messages + [summary_system]

                return [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages
            
        except Exception as e:
            return [AIMessage(content=f"Error in history management: {str(e)}")]


    def _call_llm(self, state: RAGAgentState) -> Dict[str, Any]:
        """Call the LLM with trimming soft"""
        try:
            messages = state.messages.copy()
            if self.system_prompt and not self.init_system_prompt:
                self.init_system_prompt = True
                messages.insert(0, self.system_prompt)

            llm_input = self._manage_history(messages, self.trim_strategy, self.max_tokens)

            response = self.llm_with_tools.invoke(llm_input)

            return {
                "messages": [response]
            }
            
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Sorry, I encountered an error")],
                "error_message": f"Sorry, I encountered an error: {str(e)}"
            }

    def _next_action(self, state: RAGAgentState) -> str:
        """Determine whether we should perform a tool call"""

        last_message = state.messages[-1] if state.messages else None
        if hasattr(last_message, 'tool_calls'):
            return "handle_tool_call"
        else:
            return "end"




    def _handle_tool_call(self, state: RAGAgentState) -> Dict[str, Any]:
        """Handle the tool call"""
        last_message = state.messages[-1] if state.messages else None
        tool_calls = getattr(last_message, 'tool_calls', [])
        tool_call = tool_calls[0]
        tool_name = tool_call.get("name")

        if tool_name == "search_files":
            return self._search_files(state)
        elif tool_name == "find_answers":
            return self._find_answers(state)
        elif tool_name == "escalation":
            return self._escalation(state)
        else:
            return {
                "messages": [ToolMessage(
                    content=json.dumps({"error": "Unknown tool"}),
                    tool_call_id=tool_call.get("id"),
                    name=tool_call.get("name")
                )],
            }



    def _find_answers(self, state: RAGAgentState) -> Dict[str, Any]:
        """Execute the find answers"""
            
    
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])

        if not tool_calls:
            return {
                "messages": [ToolMessage(
                    content=json.dumps({"error": "No tool calls found"}),
                    tool_call_id=None,
                    name=None
                )],
                "n_find_answers": state.n_find_answers
            }

        tool_messages = []
        find_answers_results: List[Answer] = []

        tool_call = tool_calls[0]
        try:
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            tool_args = tool_call.get("args", {})

            if state.n_find_answers >= state.max_find_answers:
                return {
                    "messages": [ToolMessage(
                   content=json.dumps({"error": "Max find answers reached"}),
                   tool_call_id=tool_call_id,
                   name=tool_name
                )],
                "n_find_answers": state.n_find_answers
                    }
            question = tool_args.get("question", "")
            results = self.find_answers_tool.invoke({"question": question})
            
            content = json.dumps({
                "results": results,
                "question": question
            }, ensure_ascii=False)
            find_answers_results.append(results)
    

            tool_message = ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=tool_name
            )
            tool_messages.append(tool_message)

        except Exception as e:
            error_content = json.dumps({"error": str(e)})
            tool_message = ToolMessage(
                content=error_content,
                tool_call_id=tool_call_id,
                name=tool_name
            )
            tool_messages.append(tool_message)

        return {
            "messages": tool_messages,
            "n_find_answers": state.n_find_answers + 1,
            "find_answers_results": find_answers_results
        }




    def _search_files(self, state: RAGAgentState) -> Dict[str, Any]:
        """Execute the search"""
    
    
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])

        if not tool_calls:
            return {
                "messages": [ToolMessage(
                    content=json.dumps({"error": "No tool calls found"}),
                    tool_call_id=None,
                    name=None
                )],
                "n_search": state.n_search
            }
        
        tool_messages = []
        search_results: List[str] = []

        tool_call = tool_calls[0]
        try:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            if tool_name == "search_files":
                if state.n_search >= state.max_searches:
                    return {
            "messages": [ToolMessage(
                content=json.dumps({"error": "Max searches reached"}),
                tool_call_id=tool_call.get("id"),
                name=tool_call.get("name")
            )],
            "n_search": state.n_search
            }
                queries = tool_args.get("queries", [])
                results = self.search_files_tool.invoke({"queries": queries})
                
                content = json.dumps({
                    "results": results,
                    "query_count": len(queries)
                }, ensure_ascii=False)
                search_results.extend(results)
            else:
                content = json.dumps({"error": f"Unknown tool: {tool_name}"})

            tool_message = ToolMessage(
                content=content,
                tool_call_id=tool_call.get("id"),
                name=tool_call.get("name")
            )
            tool_messages.append(tool_message)

        except Exception as e:
            error_content = json.dumps({"error": str(e)})
            tool_message = ToolMessage(
                content=error_content,
                tool_call_id=tool_call.get("id"),
                name=tool_call.get("name")
            )
            tool_messages.append(tool_message)

        return {
            "messages": tool_messages,
            "n_search": state.n_search + 1,
            "search_results": search_results
        }

        


    def _escalation(self, state: RAGAgentState) -> Dict[str, Any]:
        """Execute the escalation"""
        
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])

        if not tool_calls:
            return {
                "messages": [ToolMessage(
                    content=json.dumps({"error": "No tool calls found"}),
                    tool_call_id=None,
                    name=None
                )],
                "escalation_result": state.escalation_result
            }
        try:
            tool_call = tool_calls[0]
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            tool_args = tool_call.get("args", {})
            
            message = tool_args.get("message", "")
            confidence = tool_args.get("confidence", 0)
            reason = tool_args.get("reason", "")
            escalation_result = self.escalation_tool.invoke({"message": message, "confidence": confidence, "reason": reason})
            return {
                "messages": [ToolMessage(
                    content=json.dumps({"escalation_result": escalation_result}),
                    tool_call_id=tool_call_id,
                    name=tool_name
                )],
                "escalation_result": escalation_result
            }
            
        except Exception as e:
            return {
            "messages": [ToolMessage(
                content=json.dumps({"error": str(e)}),
                tool_call_id=tool_call_id,
                name=tool_name
            )],
            "escalation_result": state.escalation_result
            }
      




def create_rag_agent(user_id: str,
                    conversation_id: str,                        
                     summarization_model_name: str = "gpt-4o-mini",
                     summarization_max_tokens: int = 350,
                     model_name: str = "gpt-4o-mini", 
                     max_searches: int = 3,
                     system_prompt: str = "",
                     trim_strategy: Literal["none", "hard", "summary"] = "summary",
                     max_tokens: int = 8000,
                     max_find_answers: int = 5) -> RAGAgent:
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
        system_prompt=system_prompt
    )


if __name__ == "__main__":
    
    agent = create_rag_agent(
        user_id="example_user_id",
        conversation_id="example_conversation_id",
        system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
        trim_strategy="summary", 
        max_tokens=6000,
        max_find_answers=5
    )
    


    print('Accès au graphique...')
    graph = agent.graph.get_graph()

    print('Génération du code Mermaid...')
    try:
        mermaid_code = graph.draw_mermaid()
        print('Code Mermaid généré avec succès!')
        print('Longueur du code:', len(mermaid_code), 'caractères')
   
        with open('/workspace/rag_agent_graph.mmd', 'w', encoding='utf-8') as f:
            f.write(mermaid_code)
        print('Code Mermaid sauvegardé dans /workspace/rag_agent_graph.mmd')
    
        print('\nPremières lignes du code Mermaid:')
        print('=' * 50)
        lines = mermaid_code.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f'{i+1:2d}: {line}')
        if len(lines) > 20:
            print(f'... et {len(lines) - 20} lignes supplémentaires')
        
    except Exception as e:
        print(f'Erreur lors de la génération du code Mermaid: {e}')
        import traceback
        traceback.print_exc()