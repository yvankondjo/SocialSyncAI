"""
Content Creation Agent for AI Studio
Specialized agent for social media content creation with AI assistance
"""
import logging
import operator
import os
from typing import List, Annotated, Optional, Literal
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.session import get_db
from app.services.content_creation_tools import (
    create_schedule_post_tool,
    SchedulePostResult
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
    max_iterations: int = 10
    iteration_count: int = 0




CONTENT_CREATION_SYSTEM_PROMPT = """You are an expert social media content creator and strategist. You help users create engaging, high-quality content for their social media platforms (Instagram, WhatsApp, Facebook, Twitter).
**CURRENT DATE AND TIME:**
Today's date: {current_date_str}
Current time: {current_time_str}

**IMPORTANT:** When the user says "tomorrow", "next week", etc., calculate the date based on TODAY ({current_date_str}).
For example:
- Tomorrow = {tomorrow_str}
- In 2 days = {in_two_days_str}
- Next Monday = (calculate from {current_date_str})

Always use dates in the FUTURE (after {current_date_str}). Never use dates from 2023 or earlier.

---
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
4. Use the schedule_post tool when the user is ready to schedule
5. Provide actionable suggestions for improvement

**IMPORTANT - Tool Usage Guidelines:**

When using the `schedule_post` tool:
- Platform names must be LOWERCASE: "instagram", "whatsapp", "facebook", or "twitter" (never "Instagram" or "Twitter")
- Date format must be ISO 8601: "YYYY-MM-DDTHH:MM:SS" (e.g., "2025-10-26T14:30:00")
- Always schedule for FUTURE dates only (at least 5 minutes from now)
- CRITICAL: Use the current date/time provided above to calculate future dates
- Example: If today is 2025-10-25, use "2025-10-26T15:00:00" for tomorrow at 3pm
- Example tool call: schedule_post(platform="instagram", content_text="Great post!", publish_at="2025-10-26T15:00:00")

Platforms you support:
- **instagram**: Focus on visual storytelling, use hashtags, first 125 chars matter (2,200 char limit)
- **twitter**: Concise, punchy, use threads for longer content (280 char limit)
- **whatsapp**: Direct and personal, great for community engagement (65k char limit)
- **facebook**: Mix of personal and promotional, questions drive engagement (63k char limit)

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

        self.tools = [self.schedule_post_tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        current_datetime = datetime.now()
        current_date_str = current_datetime.strftime("%Y-%m-%d")
        current_time_str = current_datetime.strftime("%H:%M:%S")
        tomorrow_str = (current_datetime + timedelta(days=1)).strftime("%Y-%m-%d")
        in_two_days_str = (current_datetime + timedelta(days=2)).strftime("%Y-%m-%d")
        self.system_prompt = [SystemMessage(content=CONTENT_CREATION_SYSTEM_PROMPT.format(
            current_date_str=current_date_str,
            current_time_str=current_time_str,
            tomorrow_str=tomorrow_str,
            in_two_days_str=in_two_days_str
        ))]
        if system_prompt:
            self.system_prompt.append(SystemMessage(content=system_prompt))

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
                    "max_iterations": self.max_iterations,
                    "iteration_count": 0
                },
                config=config
            )

            try:
                self._save_conversation_metadata(config, result)
            except Exception as metadata_error:
                logger.warning(f"Failed to save conversation metadata: {metadata_error}")

            return result

        except Exception as e:
            logger.error(f"Error invoking Content Creation Agent: {e}")
            raise

    def _save_conversation_metadata(self, config: dict, result: dict):
        """
        Save or update conversation metadata after each agent invocation
        """
        try:
            from app.db.session import get_db

            thread_id = config.get("configurable", {}).get("thread_id")
            user_id = config.get("configurable", {}).get("user_id")

            if not thread_id or not user_id:
                logger.warning("Missing thread_id or user_id in config, skipping metadata save")
                return

            messages = result.get("messages", [])
            if not messages:
                return

            title = self._generate_title(messages)
            message_count = len([m for m in messages if isinstance(m, (HumanMessage, AIMessage))])

            db = get_db()

            existing = db.table("ai_studio_conversation_metadata")\
                .select("*")\
                .eq("thread_id", thread_id)\
                .execute()

            if existing.data and len(existing.data) > 0:
                db.table("ai_studio_conversation_metadata")\
                    .update({
                        "message_count": message_count,
                        "updated_at": "NOW()"
                    })\
                    .eq("thread_id", thread_id)\
                    .execute()
            else:
                db.table("ai_studio_conversation_metadata")\
                    .insert({
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "title": title,
                        "model": self.model_name,
                        "message_count": message_count
                    })\
                    .execute()

            logger.info(f"Saved conversation metadata for thread {thread_id}")

        except Exception as e:
            logger.error(f"Error saving conversation metadata: {e}")
            raise

    def _generate_title(self, messages: list) -> str:
        """
        Generate conversation title from first user message
        """
        for msg in messages:
            if isinstance(msg, HumanMessage):
                content = msg.content
                title = content.split('\n')[0][:50]
                return title if len(title) < len(content) else title + "..."

        return "New Conversation"
