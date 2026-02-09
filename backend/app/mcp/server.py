"""MCP server setup using Official MCP SDK."""

import json
from app.database import get_session
from app.mcp.tools import (
    create_task,
    list_tasks,
    update_task,
    toggle_task_completion,
    delete_task,
    get_task
)

# Check if mcp module is available
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent

    # Create MCP server instance
    server = Server("todo-mcp-server")
    MCP_AVAILABLE = True
except ImportError:
    # MCP module not available, create stub implementations
    class StubServer:
        def __init__(self, name):
            self.name = name

        def list_tools(self):
            def decorator(func):
                return func
            return decorator

        def call_tool(self):
            def decorator(func):
                return func
            return decorator

    class StubTool:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class StubTextContent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    server = StubServer("todo-mcp-server")
    Tool = StubTool
    TextContent = StubTextContent
    MCP_AVAILABLE = False

# Store user context (set by FastAPI on each request)
# Maps request_id -> user_id
_user_context: dict[str, int] = {}


def set_user_context(request_id: str, user_id: int):
    """Set user context for the current request.

    Args:
        request_id: Unique identifier for this request
        user_id: Authenticated user's ID from JWT
    """
    _user_context[request_id] = user_id


def get_user_context(request_id: str) -> int | None:
    """Get user context for the current request.

    Args:
        request_id: Unique identifier for this request

    Returns:
        User ID if found, None otherwise
    """
    return _user_context.get(request_id)


def clear_user_context(request_id: str):
    """Clear user context after request completes.

    Args:
        request_id: Unique identifier for this request
    """
    _user_context.pop(request_id, None)


# List available tools
if MCP_AVAILABLE:
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available MCP tools.

        Returns:
            List of Tool objects with schemas for OpenAI function calling
        """
        return [
            Tool(
                name="create_task",
                description="Create a new todo task with title, optional description, and priority",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title (1-200 characters)",
                            "minLength": 1,
                            "maxLength": 200
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description (optional, max 2000 characters)",
                            "maxLength": 2000,
                            "default": ""
                        },
                        "priority": {
                            "type": "string",
                            "description": "Task priority level",
                            "enum": ["low", "medium", "high"],
                            "default": "medium"
                        }
                    }
                }
            ),
            Tool(
                name="list_tasks",
                description="List tasks with optional filters for completion status, priority, and title search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "is_complete": {
                            "type": ["boolean", "null"],
                            "description": "Filter by completion status (true=completed, false=incomplete, null=all)",
                            "default": None
                        },
                        "priority": {
                            "type": ["string", "null"],
                            "description": "Filter by priority level",
                            "enum": ["low", "medium", "high", None],
                            "default": None
                        },
                        "title_query": {
                            "type": ["string", "null"],
                            "description": "Case-insensitive substring search for task titles (supports simple close matches like grocery/groceries)",
                            "default": None
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50
                        }
                    }
                }
            ),
            Tool(
                name="update_task",
                description="Update an existing task's title, description, or priority",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to update"
                        },
                        "title": {
                            "type": ["string", "null"],
                            "description": "New task title (1-200 characters)",
                            "minLength": 1,
                            "maxLength": 200
                        },
                        "description": {
                            "type": ["string", "null"],
                            "description": "New task description (max 2000 characters)",
                            "maxLength": 2000
                        },
                        "priority": {
                            "type": ["string", "null"],
                            "description": "New task priority level",
                            "enum": ["low", "medium", "high", None]
                        }
                    }
                }
            ),
            Tool(
                name="toggle_task_completion",
                description="Mark a task as complete or incomplete",
                inputSchema={
                    "type": "object",
                    "required": ["task_id", "is_complete"],
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to toggle"
                        },
                        "is_complete": {
                            "type": "boolean",
                            "description": "New completion status (true=completed, false=incomplete)"
                        }
                    }
                }
            ),
            Tool(
                name="delete_task",
                description="Permanently delete a task",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to retrieve"
                        }
                    }
                }
            ),
            Tool(
                name="get_task",
                description="Get a single task by ID",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "ID of the task to retrieve"
                        }
                    }
                }
            )
        ]
else:
    async def list_tools() -> list:
        """Stub function when MCP is not available."""
        return []


# Handle tool calls
if MCP_AVAILABLE:
    @server.call_tool()
    async def call_tool(name: str, arguments: dict, request_id: str = None) -> list[TextContent]:
        """Execute MCP tool calls.

        Args:
            name: Name of the tool to execute
            arguments: Tool arguments from OpenAI function call
            request_id: Request identifier for user context lookup

        Returns:
            List of TextContent with JSON-encoded results
        """
        # Get user context
        user_id = get_user_context(request_id) if request_id else None

        if not user_id:
            return [TextContent(
                type="text",
                text=json.dumps({"success": False, "error": "Unauthorized"})
            )]

        # Get database session
        session = next(get_session())

        # Route to appropriate tool
        try:
            if name == "create_task":
                result = await create_task(session=session, user_id=user_id, **arguments)
            elif name == "list_tasks":
                result = await list_tasks(session=session, user_id=user_id, **arguments)
            elif name == "update_task":
                result = await update_task(session=session, user_id=user_id, **arguments)
            elif name == "toggle_task_completion":
                result = await toggle_task_completion(session=session, user_id=user_id, **arguments)
            elif name == "delete_task":
                result = await delete_task(session=session, user_id=user_id, **arguments)
            elif name == "get_task":
                result = await get_task(session=session, user_id=user_id, **arguments)
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}
        except Exception as e:
            result = {"success": False, "error": f"Tool execution failed: {str(e)}"}
        finally:
            # Close session
            session.close()

        return [TextContent(type="text", text=json.dumps(result))]
else:
    async def call_tool(name: str, arguments: dict, request_id: str = None) -> list:
        """Stub function when MCP is not available."""
        return []


if MCP_AVAILABLE:
    def mcp_to_openai_tools(mcp_tools: list[Tool]) -> list[dict]:
        """Convert MCP tool schemas to OpenAI function calling format.

        This allows OpenAI Agents SDK to understand MCP tools.

        Args:
            mcp_tools: List of MCP Tool objects

        Returns:
            List of OpenAI function call schemas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in mcp_tools
        ]
else:
    def mcp_to_openai_tools(mcp_tools: list) -> list[dict]:
        """Stub function when MCP is not available."""
        return []


# Cache tool definitions at module level to avoid asyncio.run() in running event loop
_cached_tools: list[dict] | None = None


async def get_openai_tools() -> list[dict]:
    """Get tools in OpenAI function calling format.

    Returns:
        List of tool definitions for OpenAI API
    """
    mcp_tools = await list_tools()
    return mcp_to_openai_tools(mcp_tools)


async def initialize_tools() -> list[dict]:
    """Initialize and cache tool definitions.

    This should be called once at server startup to populate the cache.

    Returns:
        List of tool definitions for OpenAI API
    """
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = await get_openai_tools()
    return _cached_tools


def get_tool_definitions() -> list[dict]:
    """Get cached tool definitions for agent initialization.

    This returns pre-cached tools to avoid asyncio.run() in running event loop.
    Tools must be initialized via initialize_tools() at server startup.

    Returns:
        List of tool definitions for OpenAI API

    Raises:
        RuntimeError: If tools haven't been initialized yet
    """
    if not MCP_AVAILABLE:
        # Return empty list if MCP is not available
        return []

    if _cached_tools is None:
        raise RuntimeError(
            "Tools not initialized. Call initialize_tools() at server startup."
        )
    return _cached_tools


async def execute_tool(tool_name: str, session, user_id: int, **kwargs) -> dict:
    """Execute a tool by name (wrapper for agent compatibility).

    This wraps the MCP call_tool interface for easier use from the agent.

    Args:
        tool_name: Name of the tool to execute
        session: Database session
        user_id: User ID for authorization
        **kwargs: Tool-specific arguments

    Returns:
        dict: Tool execution result
    """
    if not MCP_AVAILABLE:
        return {"success": False, "error": "MCP tools not available"}

    import json
    from app.mcp.tools import (
        create_task,
        list_tasks,
        update_task,
        toggle_task_completion,
        delete_task,
        get_task
    )

    # Route to appropriate tool function
    if tool_name == "create_task":
        return await create_task(session=session, user_id=user_id, **kwargs)
    elif tool_name == "list_tasks":
        return await list_tasks(session=session, user_id=user_id, **kwargs)
    elif tool_name == "update_task":
        return await update_task(session=session, user_id=user_id, **kwargs)
    elif tool_name == "toggle_task_completion":
        return await toggle_task_completion(session=session, user_id=user_id, **kwargs)
    elif tool_name == "delete_task":
        return await delete_task(session=session, user_id=user_id, **kwargs)
    elif tool_name == "get_task":
        return await get_task(session=session, user_id=user_id, **kwargs)
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
