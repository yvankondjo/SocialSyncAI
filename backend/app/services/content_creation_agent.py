"""
Content Creation Agent for AI Studio
Specialized agent for social media content creation with AI assistance
"""
import logging
import operator
import os
from typing import List, Annotated, Optional, Literal

from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.session import get_db
from app.services.content_creation_tools import (
    create_schedule_post_tool,
    create_preview_post_tool,
    SchedulePostResult,
    PreviewPostResult
)

load_dotenv()

logger = logging.getLogger(__name__)


class ContentCreationAgentResponse(BaseModel):
    """Response from the Content Creation Agent"""
    response: str
    confidence: float = 0.9


class ContentCreationAgentState(BaseModel):
    """State for the Content Creation Agent"""
    messages: Annotated[List[AnyMessage], operator.add]
    scheduled_posts: List[SchedulePostResult] = []
    previews: List[PreviewPostResult] = []
    max_iterations: int = 10
    iteration_count: int = 0


# Default system prompt for content creation
CONTENT_CREATION_SYSTEM_PROMPT = """You are an expert social media content creator and strategist. You help users create engaging, high-quality content for their social media platforms (Instagram, WhatsApp, Facebook, Twitter).

Your capabilities:
- Generate creative and engaging post ideas
- Write compelling copy optimized for each platform
- Suggest optimal posting times
- Schedule posts for future publication
- Preview posts and provide feedback
- Optimize content for maximum engagement

When helping users create content:
1. Ask about their target audience and goals if not specified
2. Suggest platform-specific best practices
3. Use the preview_post tool to analyze content before scheduling
4. Use the schedule_post tool when the user is ready to schedule
5. Provide actionable suggestions for improvement

Platforms you support:
- **Instagram**: Focus on visual storytelling, use hashtags, first 125 chars matter
- **Twitter**: Concise, punchy, use threads for longer content
- **WhatsApp**: Direct and personal, great for community engagement
- **Facebook**: Mix of personal and promotional, questions drive engagement

Always respond in a helpful, creative, and professional manner. Format your responses clearly using markdown."""


class ContentCreationAgent:
    """Agent specialized for social media content creation with AI assistance"""

    def __init__(
        self,
        user_id: str,
        model_name: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None,
        checkpointer=None,
        max_iterations: int = 10
    ):
        self.user_id = user_id
        self.model_name = model_name
        self.max_iterations = max_iterations

        self.llm = ChatOpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL') or "https://openrouter.ai/api/v1",
            model=model_name,
            temperature=0.7
        )
        db = get_db()
        self.schedule_post_tool = create_schedule_post_tool(user_id, db)
        self.preview_post_tool = create_preview_post_tool(user_id)


        self.tools = [self.schedule_post_tool, self.preview_post_tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)


        self.system_prompt = system_prompt or CONTENT_CREATION_SYSTEM_PROMPT

        self.graph = self._build_graph(checkpointer)

    def _build_graph(self, checkpointer):
        """Build the LangGraph workflow"""
        workflow = StateGraph(ContentCreationAgentState)

        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", self._call_tools)


        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile(checkpointer=checkpointer)

    def _call_model(self, state: ContentCreationAgentState) -> dict:
        """Call the LLM with tools"""
        try:
            messages = state.messages

            if len(messages) == 1 and isinstance(messages[0], HumanMessage):
                messages = [SystemMessage(content=self.system_prompt)] + messages

            response = self.llm_with_tools.invoke(messages)

            return {
                "messages": [response],
                "iteration_count": state.iteration_count + 1
            }

        except Exception as e:
            logger.error(f"Error calling model: {e}")
            error_msg = AIMessage(
                content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
            )
            return {"messages": [error_msg]}

    def _call_tools(self, state: ContentCreationAgentState) -> dict:
        """Execute tool calls"""
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])

        if not tool_calls:
            return {"messages": []}

        from langchain_core.messages import ToolMessage

        tool_messages = []
        scheduled_posts = list(state.scheduled_posts)
        previews = list(state.previews)

        for tool_call in tool_calls:
            try:
                tool = next((t for t in self.tools if t.name == tool_call['name']), None)

                if tool:
                    if tool_call['name'] == 'schedule_post':
                        result = tool.invoke(tool_call['args'])
                        scheduled_posts.append(result)
                        tool_msg = ToolMessage(
                            content=result.model_dump_json(),
                            tool_call_id=tool_call['id']
                        )
                    elif tool_call['name'] == 'preview_post':
                        result = tool.invoke(tool_call['args'])
                        previews.append(result)
                        tool_msg = ToolMessage(
                            content=result.model_dump_json(),
                            tool_call_id=tool_call['id']
                        )
                    else:
                        tool_msg = ToolMessage(
                            content=f"Unknown tool: {tool_call['name']}",
                            tool_call_id=tool_call['id']
                        )

                    tool_messages.append(tool_msg)

            except Exception as e:
                logger.error(f"Error executing tool {tool_call.get('name')}: {e}")
                tool_msg = ToolMessage(
                    content=f"Error: {str(e)}",
                    tool_call_id=tool_call['id']
                )
                tool_messages.append(tool_msg)

        return {
            "messages": tool_messages,
            "scheduled_posts": scheduled_posts,
            "previews": previews
        }

    def _should_continue(self, state: ContentCreationAgentState) -> Literal["continue", "end"]:
        """Determine if we should continue or end"""
        last_message = state.messages[-1]

        if state.iteration_count >= state.max_iterations:
            return "end"

        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"

        return "end"

    def invoke(self, message: str, config: dict) -> dict:
        """Invoke the agent with a user message"""
        try:
            result = self.graph.invoke(
                {
                    "messages": [HumanMessage(content=message)],
                    "scheduled_posts": [],
                    "previews": [],
                    "max_iterations": self.max_iterations,
                    "iteration_count": 0
                },
                config=config
            )

            return result

        except Exception as e:
            logger.error(f"Error invoking Content Creation Agent: {e}")
            raise
