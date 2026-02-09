"""MCP tools for todo task operations.

All tools enforce row-level security by filtering operations to the authenticated user's data only.
"""

from sqlmodel import Session, select
from sqlalchemy import func, or_
from app.models import Task
from app.database import get_session
from datetime import datetime
from typing import Optional


async def create_task(
    session: Session,
    user_id: int,
    title: str,
    description: str = "",
    priority: str = "medium"
) -> dict:
    """Create a new task for the user.

    Args:
        session: Database session
        user_id: ID of the user creating the task
        title: Task title (required, max 200 chars)
        description: Task description (optional, max 2000 chars)
        priority: Task priority (high/medium/low, default: medium)

    Returns:
        dict: Created task with id, title, description, priority, is_complete, created_at
    """
    if not user_id:
        return {"success": False, "error": "Unauthorized"}

    # Validate priority
    if priority not in ["low", "medium", "high"]:
        return {"success": False, "error": "Invalid priority. Must be: low, medium, or high"}

    # Create task
    task = Task(
        user_id=user_id,
        title=title.strip(),
        description=description.strip(),
        priority=priority
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return {
        "success": True,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "is_complete": task.is_complete,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
    }


async def list_tasks(
    session: Session,
    user_id: int,
    is_complete: Optional[bool] = None,
    priority: Optional[str] = None,
    title_query: Optional[str] = None,
    limit: int = 50
) -> dict:
    """List tasks for the user with optional filters.

    Args:
        session: Database session
        user_id: ID of the user
        is_complete: Filter by status (true=completed, false=incomplete, null=all)
        priority: Filter by priority (all/high/medium/low, default: all)
        title_query: Case-insensitive substring query for task titles
        limit: Maximum number of tasks to return

    Returns:
        dict: List of tasks matching filters
    """
    if not user_id:
        return {"success": False, "error": "Unauthorized"}

    # Build query
    statement = select(Task).where(Task.user_id == user_id)

    # Apply filters
    if is_complete is not None:
        statement = statement.where(Task.is_complete == is_complete)

    if priority:
        statement = statement.where(Task.priority == priority)

    if title_query:
        query = title_query.strip().lower()
        if query:
            # Case-insensitive partial matching, plus a simple plural/singular "close match"
            # (e.g., grocery <-> groceries)
            like_patterns = [
                f"%{query}%",
            ]

            if query.endswith("s"):
                like_patterns.append(f"%{query[:-1]}%")
            else:
                like_patterns.append(f"%{query}s%")

            statement = statement.where(
                or_(*[func.lower(Task.title).like(p) for p in like_patterns])
            )

    # Apply limit and order
    statement = statement.limit(limit).order_by(Task.created_at.desc())

    # Execute query
    tasks = session.exec(statement).all()

    return {
        "success": True,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "is_complete": task.is_complete,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            for task in tasks
        ],
        "count": len(tasks)
    }


async def update_task(
    session: Session,
    user_id: int,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None
) -> dict:
    """Update an existing task's title, description, or priority.

    Args:
        session: Database session
        user_id: ID of the user (for ownership verification)
        task_id: ID of task to update
        title: New title (optional)
        description: New description (optional)
        priority: New priority (optional)

    Returns:
        dict: Updated task
    """
    if not user_id:
        return {"success": False, "error": "Unauthorized"}

    # Find task (with user_id filter for security)
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()

    if not task:
        return {"success": False, "error": "Task not found"}

    # Update fields
    if title is not None:
        task.title = title.strip()

    if description is not None:
        task.description = description.strip()

    if priority is not None:
        if priority not in ["low", "medium", "high"]:
            return {"success": False, "error": "Invalid priority"}
        task.priority = priority

    # Update timestamp
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    return {
        "success": True,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "is_complete": task.is_complete,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
    }


async def toggle_task_completion(
    session: Session,
    user_id: int,
    task_id: int,
    is_complete: bool
) -> dict:
    """Toggle task completion status.

    Args:
        session: Database session
        user_id: ID of the user (for ownership verification)
        task_id: ID of task to toggle
        is_complete: New completion status (true=completed, false=incomplete)

    Returns:
        dict: Updated task
    """
    if not user_id:
        return {"success": False, "error": "Unauthorized"}

    # Find task
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()

    if not task:
        return {"success": False, "error": "Task not found"}

    # Update completion status
    task.is_complete = is_complete
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    return {
        "success": True,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "is_complete": task.is_complete,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
    }


async def delete_task(
    session: Session,
    user_id: int,
    task_id: int
) -> dict:
    """Delete a task permanently.

    Args:
        session: Database session
        user_id: ID of the user (for ownership verification)
        task_id: ID of task to delete

    Returns:
        dict: Success message
    """
    if not user_id:
        return {"success": False, "error": "Unauthorized"}

    # Find task
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()

    if not task:
        return {"success": False, "error": "Task not found"}

    # Delete task
    session.delete(task)
    session.commit()

    return {
        "success": True,
        "message": "Task deleted successfully"
    }


async def get_task(
    session: Session,
    user_id: int,
    task_id: int
) -> dict:
    """Get a single task by ID.

    Args:
        session: Database session
        user_id: ID of the user (for ownership verification)
        task_id: ID of the task to retrieve

    Returns:
        dict: Task details
    """
    if not user_id:
        return {"success": False, "error": "Unauthorized"}

    # Find task
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()

    if not task:
        return {"success": False, "error": "Task not found"}

    return {
        "success": True,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "is_complete": task.is_complete,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
    }
