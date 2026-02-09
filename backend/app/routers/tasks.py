"""Tasks router for CRUD operations.

Task: T-521 - Integrate Event Publisher into Task APIs
Phase: Phase V - Event-Driven Architecture

This router emits CloudEvents for all task domain events:
- task.created: When a new task is created
- task.updated: When a task is updated (fields or completion status)
- task.deleted: When a task is deleted
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
import logging

from app.database import get_session
from app.models import Task, User
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.dependencies import get_current_user

# T-521: Import event publishing components
from app.events.publisher import get_event_publisher, EventPublisher
from app.events.schemas import (
    TaskCreatedEvent,
    TaskCreatedData,
    TaskUpdatedEvent,
    TaskUpdatedData,
    TaskDeletedEvent,
    TaskDeletedData,
    # T-522: Reminder event schemas
    TaskReminderScheduledEvent,
    TaskReminderScheduledData,
    ReminderCancelledEvent,
    ReminderCancelledData
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


# T-522: Helper function to extract notification channels
def _get_notification_channels(reminder_config: dict | None) -> list[str]:
    """Extract notification channels from reminder_config.

    Args:
        reminder_config: JSONB reminder configuration

    Returns:
        List of notification channels (defaults to ['email'])
    """
    if not reminder_config:
        return ["email"]
    return reminder_config.get("channels", ["email"])


@router.get("/", response_model=list[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all tasks for the current user."""
    statement = (
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
    )
    tasks = session.exec(statement).all()
    return tasks


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    publisher: EventPublisher = Depends(get_event_publisher)  # T-521: Inject event publisher
):
    """Create a new task for the current user.

    T-521: Emits task.created event after successful task creation.
    T-522: Emits reminder.scheduled event if reminder_time is set.
    """
    task = Task(
        **task_data.model_dump(),
        user_id=current_user.id
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    # T-521: Publish task.created event
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
        logger.info(f"Published task.created event for task {task.id}")
    except Exception as e:
        # Log error but don't fail the request
        # Event publishing is best-effort; task was successfully created
        logger.error(
            f"Failed to publish task.created event for task {task.id}: {e}",
            exc_info=True
        )

    # T-522: Publish reminder.scheduled event if reminder_time is set
    if task.reminder_time:
        try:
            reminder_event = TaskReminderScheduledEvent(
                source="/api/tasks",
                subject=f"task/{task.id}",
                data=TaskReminderScheduledData(
                    task_id=task.id,
                    user_id=task.user_id,
                    scheduled_time=task.reminder_time,
                    notification_channels=_get_notification_channels(task.reminder_config)
                )
            )
            await publisher.publish_reminder_event(reminder_event)
            logger.info(
                f"Published reminder.scheduled event for task {task.id} "
                f"(scheduled_time: {task.reminder_time})"
            )
        except Exception as e:
            logger.error(
                f"Failed to publish reminder.scheduled event for task {task.id}: {e}",
                exc_info=True
            )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    publisher: EventPublisher = Depends(get_event_publisher)  # T-521: Inject event publisher
):
    """Update a task (with ownership check).

    T-521: Emits task.updated event with change tracking after successful update.
    T-522: Emits reminder.scheduled or reminder.cancelled based on reminder_time changes.
    """
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )

    # T-521: Capture previous values for change tracking
    # T-522: Specifically track reminder_time changes
    previous_reminder_time = task.reminder_time

    update_data = task_data.model_dump(exclude_unset=True)
    changes = {}
    previous_values = {}

    for key, value in update_data.items():
        old_value = getattr(task, key, None)
        if old_value != value:
            changes[key] = value
            previous_values[key] = old_value
            setattr(task, key, value)

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)

    # T-521: Publish task.updated event if there were changes
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
            logger.info(
                f"Published task.updated event for task {task.id} "
                f"(changed fields: {list(changes.keys())})"
            )
        except Exception as e:
            logger.error(
                f"Failed to publish task.updated event for task {task.id}: {e}",
                exc_info=True
            )

    # T-522: Handle reminder scheduling changes
    reminder_time_changed = "reminder_time" in changes

    if reminder_time_changed:
        # Reminder was removed (was set, now None)
        if previous_reminder_time and not task.reminder_time:
            try:
                cancel_event = ReminderCancelledEvent(
                    source="/api/tasks",
                    subject=f"task/{task.id}",
                    data=ReminderCancelledData(
                        task_id=task.id,
                        user_id=task.user_id,
                        reason="reminder_removed",
                        cancelled_at=datetime.utcnow()
                    )
                )
                await publisher.publish_reminder_event(cancel_event)
                logger.info(
                    f"Published reminder.cancelled event for task {task.id} "
                    f"(reason: reminder_removed)"
                )
            except Exception as e:
                logger.error(
                    f"Failed to publish reminder.cancelled event for task {task.id}: {e}",
                    exc_info=True
                )

        # Reminder was added or changed (new value is not None)
        elif task.reminder_time:
            try:
                schedule_event = TaskReminderScheduledEvent(
                    source="/api/tasks",
                    subject=f"task/{task.id}",
                    data=TaskReminderScheduledData(
                        task_id=task.id,
                        user_id=task.user_id,
                        scheduled_time=task.reminder_time,
                        notification_channels=_get_notification_channels(task.reminder_config)
                    )
                )
                await publisher.publish_reminder_event(schedule_event)
                action = "rescheduled" if previous_reminder_time else "scheduled"
                logger.info(
                    f"Published reminder.scheduled event for task {task.id} "
                    f"({action}, scheduled_time: {task.reminder_time})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to publish reminder.scheduled event for task {task.id}: {e}",
                    exc_info=True
                )

    return task


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    publisher: EventPublisher = Depends(get_event_publisher)  # T-521: Inject event publisher
):
    """Toggle task completion status.

    T-521: Emits task.updated event when completion status changes.
    """
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )

    # T-521: Capture previous completion status
    previous_is_complete = task.is_complete
    task.is_complete = not task.is_complete
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    # T-521: Publish task.updated event for completion status change
    try:
        event = TaskUpdatedEvent(
            source="/api/tasks",
            subject=f"task/{task.id}",
            data=TaskUpdatedData(
                task_id=task.id,
                user_id=task.user_id,
                changes={"is_complete": task.is_complete},
                previous_values={"is_complete": previous_is_complete}
            )
        )
        await publisher.publish_task_event(event)
        logger.info(
            f"Published task.updated event for task {task.id} "
            f"(completion: {previous_is_complete} -> {task.is_complete})"
        )
    except Exception as e:
        logger.error(
            f"Failed to publish task.updated event for task {task.id}: {e}",
            exc_info=True
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    publisher: EventPublisher = Depends(get_event_publisher)  # T-521: Inject event publisher
):
    """Delete a task.

    T-521: Emits task.deleted event after successful deletion.
    T-522: Emits reminder.cancelled if task had a reminder.
    """
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )

    # T-521: Capture task details before deletion for event payload
    # T-522: Also capture reminder_time for cancellation event
    task_id_for_event = task.id
    user_id_for_event = task.user_id
    title_for_event = task.title
    was_complete_for_event = task.is_complete
    had_reminder = task.reminder_time is not None

    session.delete(task)
    session.commit()

    # T-521: Publish task.deleted event
    try:
        event = TaskDeletedEvent(
            source="/api/tasks",
            subject=f"task/{task_id_for_event}",
            data=TaskDeletedData(
                task_id=task_id_for_event,
                user_id=user_id_for_event,
                title=title_for_event,
                was_complete=was_complete_for_event
            )
        )
        await publisher.publish_task_event(event)
        logger.info(
            f"Published task.deleted event for task {task_id_for_event} "
            f"(title: '{title_for_event}')"
        )
    except Exception as e:
        logger.error(
            f"Failed to publish task.deleted event for task {task_id_for_event}: {e}",
            exc_info=True
        )

    # T-522: Publish reminder.cancelled if task had a reminder
    if had_reminder:
        try:
            cancel_event = ReminderCancelledEvent(
                source="/api/tasks",
                subject=f"task/{task_id_for_event}",
                data=ReminderCancelledData(
                    task_id=task_id_for_event,
                    user_id=user_id_for_event,
                    reason="task_deleted",
                    cancelled_at=datetime.utcnow()
                )
            )
            await publisher.publish_reminder_event(cancel_event)
            logger.info(
                f"Published reminder.cancelled event for task {task_id_for_event} "
                f"(reason: task_deleted)"
            )
        except Exception as e:
            logger.error(
                f"Failed to publish reminder.cancelled event for task {task_id_for_event}: {e}",
                exc_info=True
            )

    return None
