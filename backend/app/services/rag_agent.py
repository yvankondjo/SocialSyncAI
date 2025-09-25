from langchain_core.tools import tool
from typing import List, Dict, Any, Optional, Literal
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))
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
from app.services.find_answers import Answer
# from langmem.short_term import SummarizationNode
load_dotenv()

class QueryItem(BaseModel):
    query: str = Field(..., description="The query to search for")
    lang: Literal["french", "english", "spanish"] = Field(default="french", description="The language to search for")




def create_find_answers_tool(user_id: str):
    """Factory function to create find_answers tool with user_id"""
    retriever = Retriever(user_id)
    
    @tool
    def find_answers(question: str) -> List[str]:
        """
        Find the answers to the given user question
        """
        return retriever.find_answers(question)
    
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
            query_item = q if isinstance(q, QueryItem) else QueryItem(**q)

            results = retriever.retrieve_from_knowledge_chunks(
                query_item.query, query_item.lang, type='hybrid'
            )
            for r in results:
                all_results.append(r.get('content'))
        return all_results
    
    return search_files

class RAGAgentState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add]
    search_results: List[str] = []
    n_search: int = 0
    find_answers_results: List[Answer] = []
    n_find_answers: int = 0
    max_searches: int = 3
    max_find_answers: int = 1
    last_error: Optional[str] = None
    trim_strategy: Literal["none", "soft", "hard", "summary"] = "soft"
    max_tokens: int = 8000
    summary_enabled: bool = False

class RAGAgent:
    """RAG Agent with LangGraph, PostgresSaver and advanced history management"""

    def __init__(self,
                 user_id: str,
                 model_name: str = "gpt-4o-mini", 
                 summarization_model_name: str = "gpt-4o-mini",
                 summarization_max_tokens: int = 300,
                 system_prompt: str = None,
                 max_searches: int = 3,
                 trim_strategy: Literal["none", "soft", "hard", "summary"] = "soft",
                 max_tokens: int = 8000,
                 max_find_answers: int = 1):
        
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
        self.search_files_tool = create_search_files_tool(user_id)
        self.find_answers_tool = create_find_answers_tool(user_id)
        self.tools = [self.search_files_tool, self.find_answers_tool]
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
      
        graph.add_node("history_manager", self._manage_history)
        graph.add_node("llm", self._call_llm)
        graph.add_node("search_files", self._search_files)
        graph.add_node("find_answers", self._find_answers)
        graph.add_node("summary_node", self._summarize_history)
        graph.add_node("error_handler", self._handle_error)

        graph.set_entry_point("history_manager")

        
        graph.add_conditional_edges(
            "history_manager",
            self._route_after_history_management,
            {
                "summary": "summary_node",
                "llm": "llm",
                "error": "error_handler"
            }
        )

    
        graph.add_edge("summary_node", "llm")

    
        graph.add_conditional_edges(
            "llm",
            self._should_search,
            {
                "search_files": "search_files",
                "find_answers": "find_answers",
                "error": "error_handler",
                "end": END
            }
        )
        
       
        graph.add_edge(
            "search_files",
            "llm"
        )
        
        graph.add_edge(
            "find_answers",
            "llm"
        )
        
        graph.add_edge("error_handler", END)
        
        return graph.compile(checkpointer=self.checkpointer)

    def _manage_history(self, state: RAGAgentState) -> Dict[str, Any]:
        """Manage the history according to the configured strategy"""
        try:
            if state.trim_strategy == "none" or len(state.messages) <= 5:
                return {"messages": []} 

            elif state.trim_strategy == "soft":
                return {"messages": []} 

            elif state.trim_strategy == "hard":
                trimmed = trim_messages(
                    state.messages,
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=state.max_tokens,
                    start_on="human",
                    end_on=("human", "tool"),
                    include_system=True
                )
                
                return {
                    "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + trimmed
                }

            elif state.trim_strategy == "summary":
                return {"summary_enabled": True, "messages": []}

        except Exception as e:
            return {"last_error": f"Error in history management: {str(e)}"}

    def _route_after_history_management(self, state: RAGAgentState) -> str:
        """Route after history management"""
        if state.last_error:
            return "error"
        if state.summary_enabled and count_tokens_approximately(state.messages) > self.max_tokens_before_summary:
            return "summary"
        return "llm"

    def _call_llm(self, state: RAGAgentState) -> Dict[str, Any]:
        """Call the LLM with trimming soft"""
        try:
            messages = state.messages.copy()
            if self.system_prompt and not self.init_system_prompt:
                self.init_system_prompt = True
                messages.insert(0, self.system_prompt)

            if state.trim_strategy == "soft":
                llm_input = trim_messages(
                    messages,
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=state.max_tokens,
                    start_on="human",
                    end_on=("human", "tool"),
                    include_system=True
                )
            else:
                llm_input = messages

           
            response = self.llm_with_tools.invoke(llm_input)

            return {
                "messages": [response]
            }
            
        except Exception as e:
            return {
                "messages": [],
                "last_error": f"Erreur LLM: {str(e)}"
            }

    def _should_search(self, state: RAGAgentState) -> str:
        """Determine whether we should perform a search"""
        if state.last_error:
            return "error"

        last_message = state.messages[-1] if state.messages else None

        if not last_message or not hasattr(last_message, 'tool_calls'):
            return "end"

        tool_calls = getattr(last_message, 'tool_calls', [])

        if not tool_calls:
            return "end"

        tool = tool_calls[0].get("name")
        if tool == "search_files":
            return "search_files"

        elif tool == "find_answers":    
            return "find_answers"
        else:
            return "end"


    def _find_answers(self, state: RAGAgentState) -> Dict[str, Any]:
        """Execute the find answers"""
        if state.n_find_answers >= state.max_find_answers:
            return {
                "messages": [f"Max find answers reached"],
                "n_find_answers": state.n_find_answers
            }
            
        try:
            last_message = state.messages[-1]
            tool_calls = getattr(last_message, 'tool_calls', [])

            if not tool_calls:
                return {
                    "messages": [f"No tool calls found"],
                    "n_find_answers": state.n_find_answers
                }

            tool_messages = []
            find_answers_results: List[Answer] = []

            tool_call = tool_calls[0]
            try:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})


                if tool_name == "find_answers":
                    question = tool_args.get("question", "")
                    results = self.find_answers_tool.invoke({"question": question})
                    
                    content = json.dumps({
                        "results": results,
                        "question": question
                    }, ensure_ascii=False)
                    find_answers_results.append(results)
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
                "n_find_answers": state.n_find_answers + 1,
                "find_answers_results": find_answers_results
            }

        except Exception as e:
            return {
                "messages": [f"Find answers error: {str(e)}"],
                "n_find_answers": state.n_find_answers + 1
            }


    def _search_files(self, state: RAGAgentState) -> Dict[str, Any]:
        """Execute the search"""
        if state.n_search >= state.max_searches:
            return {
                "messages": [f"Max searches reached"],
                "n_search": state.n_search
            }

        try:
            last_message = state.messages[-1]
            tool_calls = getattr(last_message, 'tool_calls', [])

            if not tool_calls:
                return {
                    "messages": [f"No tool calls found"],
                    "n_search": state.n_search
                }

            tool_messages = []
            search_results: List[str] = []

            tool_call = tool_calls[0]
            try:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

                if tool_name == "search_files":
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

        except Exception as e:
            return {
                "messages": [f"Search error: {str(e)}"],
                "n_search": state.n_search + 1
            }



    def _handle_error(self, state: RAGAgentState) -> Dict[str, Any]:
        """Handle errors"""
        error_message = AIMessage(
            content=f"I'm sorry, I encountered an error: {state.last_error}"
        )
        return {
            "messages": [error_message],
            "last_error": None
        }

    def _summarize_history(self, state: RAGAgentState) -> Dict[str, Any]:
        """Summarize the history"""
        try:
            TAIL_K = 8

            messages_to_summarize = trim_messages(
                state.messages,
                strategy="last",
                token_counter=count_tokens_approximately,
                max_tokens=self.max_tokens,
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

            system_messages = [m for m in state.messages if isinstance(m, SystemMessage)]
            non_system = [m for m in state.messages if not isinstance(m, SystemMessage)]
            tail = non_system[-TAIL_K:] if len(non_system) > TAIL_K else non_system

            new_messages = system_messages + [summary_system] + tail

            return {
                "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + new_messages,
                "summary_enabled": False
            }
            
        except Exception as e:
            return {
                "last_error": f"Summarization error: {str(e)}",
                "summary_enabled": False
            }

    def invoke(self, 
               message: HumanMessage, 
               conversation_id: str) -> Dict[str, Any]:
        """Invoke the agent with persistence"""
        
        config = {
            "configurable": {
                "thread_id": f"{conversation_id}"
            }
        }
        
        # Just add the new message, LangGraph handles the rest


        try:
            result = self.graph.invoke({"messages": [message]}, config=config)
            return result["messages"][-1].content
        except Exception as e:
            return {
                "messages": [
                    message,
                    AIMessage(content=f"Error: {str(e)}")
                ],
                "search_results": [],
                "n_search": 0,
                "last_error": str(e)
            }

    def get_conversation_history(self, conversation_id: str, limit: int = 10):
        """Retrieve the conversation history"""
        config = {
            "configurable": {
                "thread_id": f"{conversation_id}",
            }
        }
        
        try:
            
            current_state = self.graph.get_state(config)
            if current_state and current_state.values:
                return current_state.values.get("messages", [])
            
            
            history = list(self.graph.get_state_history(config, limit=limit))
            all_messages = []
            
            for checkpoint in reversed(history):
                if checkpoint.values and "messages" in checkpoint.values:
                    messages = checkpoint.values["messages"]
                    if isinstance(messages, list):
                        all_messages.extend(messages)
            
            return all_messages
            
        except Exception as e:
            print(f"Error when retrieving the history: {e}")
            return []

    def __del__(self):
        """Clean up the PostgreSQL connection"""
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except:
                pass

def create_rag_agent(user_id: str,
                     summarization_model_name: str = "gpt-4o-mini",
                     summarization_max_tokens: int = 350,
                     model_name: str = "gpt-4o-mini", 
                     max_searches: int = 3,
                     system_prompt: str = "",
                     trim_strategy: Literal["none", "soft", "hard", "summary"] = "hard",
                     max_tokens: int = 8000,
                     max_find_answers: int = 1) -> RAGAgent:
    """Factory function to create a RAG Agent"""
    return RAGAgent(
        user_id=user_id,
        model_name=model_name,
        max_searches=max_searches,
        max_find_answers=max_find_answers,
        trim_strategy=trim_strategy,
        summarization_model_name=summarization_model_name,
        summarization_max_tokens=summarization_max_tokens,
        max_tokens=max_tokens,
        system_prompt=system_prompt
    )

# Exemple d'utilisation
if __name__ == "__main__":
    
    agent = create_rag_agent(
        user_id="example_user_id",
        system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
        trim_strategy="hard", 
        max_tokens=6000,
        max_find_answers=1
    )
    


    # Accéder au graphique
    print('Accès au graphique...')
    graph = agent.graph.get_graph()

    # Obtenir le code Mermaid
    print('Génération du code Mermaid...')
    try:
        mermaid_code = graph.draw_mermaid()
        print('Code Mermaid généré avec succès!')
        print('Longueur du code:', len(mermaid_code), 'caractères')
        
        # Sauvegarder le code Mermaid dans un fichier
        with open('/workspace/rag_agent_graph.mmd', 'w', encoding='utf-8') as f:
            f.write(mermaid_code)
        print('Code Mermaid sauvegardé dans /workspace/rag_agent_graph.mmd')
        
        # Afficher les premières lignes du code
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