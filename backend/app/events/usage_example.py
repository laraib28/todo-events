"""Example usage of EventPublisher in FastAPI endpoints.

Task: T-520 - Backend Event Publisher Utility
Phase: Phase V - Event-Driven Architecture

This file demonstrates how to integrate the EventPublisher into FastAPI
endpoints to publish CloudEvents when domain events occur.

IMPORTANT: This is an example file for documentation purposes.
DO NOT import this in production code.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import datetime

from app.database import get_session
from app.dependencies import get_current_user
from app.models import User, Task
from app.schemas import TaskCreate, TaskResponse
from app.events.publisher import get_event_publisher, EventPublisher
from app.events.schemas import TaskCreatedEvent, TaskCreatedData, TaskUpdatedEvent, TaskUpdatedData

# Example router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ============================================================================
# Example 1: Publish task.created event after creating a task
# ============================================================================

@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task_with_event(
    task_data: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    publisher: EventPublisher = Depends(get_event_publisher)
):
    """Create a new task and publish task.created event.

    This endpoint demonstrates:
    1. Creating a task in the database
    2. Creating a CloudEvent with task data
    3. Publishing the event asynchronously
    4. Handling publish failures gracefully (logging but not failing the request)
    """
    # Create task in database
    task = Task(
        user_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.created event
    try:
        event = TaskCreatedEvent(
            source="/api/tasks",
            subject=f"task/{task.id}",
            data=TaskCreatedData(
                task_id=task.id,
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                priority=task.priority
            )
        )
        await publisher.publish_task_event(event)
    except Exception as e:
        # Log error but don't fail the request
        # The task was successfully created, event publishing is best-effort
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to publish task.created event for task {task.id}: {e}")

    return task


# ============================================================================
# Example 2: Publish task.updated event with change tracking
# ============================================================================

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_with_event(
    task_id: int,
    task_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    publisher: EventPublisher = Depends(get_event_publisher)
):
    """Update a task and publish task.updated event with change tracking.

    This endpoint demonstrates:
    1. Capturing previous values before update
    2. Updating the task
    3. Publishing event with both old and new values
    """
    # Fetch task
    task = session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    # Capture previous values
    changes = {}
    previous_values = {}

    for field, new_value in task_data.items():
        old_value = getattr(task, field, None)
        if old_value != new_value:
            changes[field] = new_value
            previous_values[field] = old_value
            setattr(task, field, new_value)

    # Update timestamp
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.updated event if there were changes
    if changes:
        try:
            event = TaskUpdatedEvent(
                source="/api/tasks",
                subject=f"task/{task.id}",
                data=TaskUpdatedData(
                    task_id=task.id,
                    user_id=task.user_id,
                    changes=changes,
                    previous_values=previous_values
                )
            )
            await publisher.publish_task_event(event)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to publish task.updated event for task {task.id}: {e}")

    return task


# ============================================================================
# Example 3: Using EventPublisher in background tasks
# ============================================================================

from fastapi import BackgroundTasks

@router.post("/bulk-create")
async def bulk_create_tasks(
    tasks_data: list[TaskCreate],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    publisher: EventPublisher = Depends(get_event_publisher)
):
    """Create multiple tasks and publish events in background.

    This endpoint demonstrates:
    1. Creating multiple tasks
    2. Publishing events in background to avoid blocking the response
    """
    created_tasks = []

    for task_data in tasks_data:
        task = Task(
            user_id=current_user.id,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority
        )
        session.add(task)
        created_tasks.append(task)

    session.commit()

    # Publish events in background
    for task in created_tasks:
        background_tasks.add_task(
            publish_task_created_event,
            publisher,
            task
        )

    return {"created": len(created_tasks), "tasks": created_tasks}


async def publish_task_created_event(publisher: EventPublisher, task: Task):
    """Background task helper to publish task.created event."""
    try:
        event = TaskCreatedEvent(
            source="/api/tasks",
            subject=f"task/{task.id}",
            data=TaskCreatedData(
                task_id=task.id,
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                priority=task.priority
            )
        )
        await publisher.publish_task_event(event)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Background task failed to publish event for task {task.id}: {e}")


# ============================================================================
# Example 4: Application lifecycle - startup and shutdown
# ============================================================================

"""
Add this to your main.py to ensure proper cleanup:

```python
from app.events.publisher import close_event_publisher

@app.on_event("shutdown")
async def shutdown_event():
    '''Cleanup EventPublisher resources on shutdown.'''
    await close_event_publisher()
```
"""


# ============================================================================
# Example 5: Testing with EventPublisher disabled
# ============================================================================

"""
For local development and testing, disable event publishing in .env:

```
EVENT_PUBLISHING_ENABLED=false
```

The publisher will operate in no-op mode, logging what would be published
without making actual HTTP requests. This allows you to:
- Develop locally without running Dapr
- Run unit tests without event infrastructure
- Verify event creation logic without side effects
"""
