"""OpenAI Agent initialization and conversation management."""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models import ConversationHistory
try:
    from app.mcp.server import get_tool_definitions, execute_tool
except ImportError:
    # MCP module not available, define fallback functions
    def get_tool_definitions():
        """Fallback when MCP is not available."""
        return []

    async def execute_tool(tool_name: str, session, user_id: int, **kwargs):
        """Fallback when MCP is not available."""
        return {"success": False, "error": "MCP tools not available"}
from app.ai.prompts import SYSTEM_PROMPT


class TodoAgent:
    """AI agent for managing todo tasks via natural language."""

    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.tools = get_tool_definitions()

        # If no tools are available, set tools to None to avoid passing empty list to OpenAI
        if not self.tools:
            self.tools = None

    async def get_conversation_context(
        self,
        session: Session,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for context.

        Args:
            session: Database session
            user_id: User ID
            limit: Maximum number of messages to retrieve

        Returns:
            list: Recent conversation messages in OpenAI format
        """
        statement = (
            select(ConversationHistory)
            .where(ConversationHistory.user_id == user_id)
            .order_by(ConversationHistory.created_at.desc())
            .limit(limit)
        )

        history = session.exec(statement).all()

        # Reverse to get chronological order
        messages = []
        for msg in reversed(history):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    async def save_message(
        self,
        session: Session,
        user_id: int,
        role: str,
        content: str
    ) -> None:
        """Save a conversation message to history.

        Args:
            session: Database session
            user_id: User ID
            role: Message role ("user" or "assistant")
            content: Message content
        """
        message = ConversationHistory(
            user_id=user_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        session.add(message)
        session.commit()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def process_message(
        self,
        session: Session,
        user_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """Process a user message and generate a response.

        Args:
            session: Database session
            user_id: User ID
            user_message: User's natural language message

        Returns:
            dict: Response with message and optional metadata
        """
        # Save user message to history
        await self.save_message(session, user_id, "user", user_message)

        # Get conversation context
        history = await self.get_conversation_context(session, user_id)

        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + history

        metadata = None
        assistant_message = None

        # Multi-step tool calling loop: allow the model to (1) list_tasks, (2) pick an ID,
        # (3) update/delete/toggle, before producing the final user-facing response.
        max_tool_rounds = 5

        # Only use tools if they are available
        if self.tools is None or len(self.tools) == 0:
            # If no tools available, send request without tools
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            message = response.choices[0].message
            assistant_message = message.content
        else:
            # Tool-enabled processing
            metadata = None
            assistant_message = None

            for _ in range(max_tool_rounds):
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

                message = response.choices[0].message

                if not message.tool_calls:
                    assistant_message = message.content
                    break

                # Execute ALL tool calls returned in this round.
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    tool_result = await execute_tool(
                        tool_name=tool_name,
                        session=session,
                        user_id=user_id,
                        **tool_args
                    )

                    # Keep the latest successful metadata (final action usually matters most).
                    tool_metadata = self._generate_metadata(tool_name, tool_result)
                    if tool_metadata is not None:
                        metadata = tool_metadata

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })

            if assistant_message is None:
                assistant_message = "I ran into an issue while processing your request. Please try again."

        # Reset metadata to None if tools are not available
        if self.tools is None or len(self.tools) == 0:
            metadata = None

        # Save assistant response to history
        await self.save_message(session, user_id, "assistant", assistant_message)

        return {
            "message": assistant_message,
            "metadata": metadata
        }

    def _generate_metadata(
        self,
        tool_name: str,
        tool_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate metadata based on tool execution.

        Args:
            tool_name: Name of the executed tool
            tool_result: Result from tool execution

        Returns:
            dict: Metadata for the response
        """
        if not tool_result.get("success"):
            return None

        # Map tool names to action types
        action_map = {
            "create_task": "task_created",
            "update_task": "task_updated",
            "delete_task": "task_deleted",
            "toggle_task_completion": "task_completed",  # or task_uncompleted
            "list_tasks": "tasks_listed",
            "get_task": "no_action"
        }

        action = action_map.get(tool_name, "no_action")

        # Build metadata
        metadata = {"action": action}

        # Add task_id if available
        if "task" in tool_result and "id" in tool_result["task"]:
            metadata["task_id"] = tool_result["task"]["id"]

        # Add count for list operations
        if "count" in tool_result:
            metadata["count"] = tool_result["count"]

        # Handle toggle completion - determine if completed or uncompleted
        if tool_name == "toggle_task_completion" and "task" in tool_result:
            is_complete = tool_result["task"].get("is_complete")
            metadata["action"] = "task_completed" if is_complete else "task_uncompleted"

        return metadata
