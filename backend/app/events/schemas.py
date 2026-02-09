"""CloudEvents-compatible event schemas for Phase V event-driven architecture.

Task: T-519 - Define CloudEvents-compatible event schemas and backend models
Phase: Phase V - Event-Driven Architecture

This module defines event schemas following the CloudEvents specification v1.0:
https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md

Events are used for:
- Event sourcing and audit logging
- Asynchronous task processing
- Notification delivery tracking
- Inter-service communication
"""

from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from typing import Optional, Any, Dict, Literal
from uuid import uuid4


# ============================================================================
# CloudEvents Base Schema
# ============================================================================

class CloudEvent(BaseModel):
    """Base CloudEvent schema following CloudEvents v1.0 specification.

    This schema defines the standard attributes required by CloudEvents.
    All event types inherit from this base schema.

    Attributes:
        id: Unique event identifier (UUID)
        source: URI identifying the event source (e.g., "/api/tasks")
        specversion: CloudEvents spec version (always "1.0")
        type: Event type identifier (e.g., "task.created")
        datacontenttype: Content type of data payload (default: "application/json")
        dataschema: Optional URI of the schema for the data
        subject: Optional subject of the event (e.g., "task/123")
        time: Timestamp when event occurred (ISO 8601)
        data: Event-specific payload
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this event"
    )
    source: str = Field(
        ...,
        description="URI identifying the context in which the event happened"
    )
    specversion: str = Field(
        default="1.0",
        description="CloudEvents specification version"
    )
    type: str = Field(
        ...,
        description="Event type identifier (e.g., 'task.created')"
    )
    datacontenttype: str = Field(
        default="application/json",
        description="Content type of the data payload"
    )
    dataschema: Optional[str] = Field(
        default=None,
        description="URI of the schema that data adheres to"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject of the event in the context of the source"
    )
    time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the event occurred"
    )
    data: Any = Field(
        ...,
        description="Event-specific data payload"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "source": "/api/tasks",
                "specversion": "1.0",
                "type": "task.created",
                "datacontenttype": "application/json",
                "subject": "task/123",
                "time": "2026-01-09T12:00:00Z",
                "data": {"task_id": 123, "title": "Buy groceries"}
            }
        }


# ============================================================================
# Task Event Data Schemas
# ============================================================================

class TaskCreatedData(BaseModel):
    """Event data for task.created event.

    Emitted when a new task is created by a user.

    Attributes:
        task_id: ID of the newly created task
        user_id: ID of the user who created the task
        title: Task title
        description: Task description
        priority: Task priority (high, medium, low)
    """

    task_id: int = Field(description="ID of the created task")
    user_id: int = Field(description="ID of the user who created the task")
    title: str = Field(description="Task title")
    description: str = Field(default="", description="Task description")
    priority: Literal["high", "medium", "low"] = Field(description="Task priority")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 123,
                "user_id": 1,
                "title": "Buy groceries",
                "description": "Get milk, eggs, and bread",
                "priority": "medium"
            }
        }


class TaskUpdatedData(BaseModel):
    """Event data for task.updated event.

    Emitted when a task is updated (title, description, priority, or completion status).

    Attributes:
        task_id: ID of the updated task
        user_id: ID of the user who owns the task
        changes: Dictionary of changed fields and their new values
        previous_values: Dictionary of previous values before update
    """

    task_id: int = Field(description="ID of the updated task")
    user_id: int = Field(description="ID of the user who owns the task")
    changes: Dict[str, Any] = Field(
        description="Fields that were changed and their new values"
    )
    previous_values: Dict[str, Any] = Field(
        description="Previous values of changed fields"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 123,
                "user_id": 1,
                "changes": {
                    "title": "Buy groceries and cook dinner",
                    "priority": "high"
                },
                "previous_values": {
                    "title": "Buy groceries",
                    "priority": "medium"
                }
            }
        }


class TaskDeletedData(BaseModel):
    """Event data for task.deleted event.

    Emitted when a task is permanently deleted by a user.

    Attributes:
        task_id: ID of the deleted task
        user_id: ID of the user who owned the task
        title: Title of the deleted task (for audit purposes)
        was_complete: Whether the task was completed at deletion time
    """

    task_id: int = Field(description="ID of the deleted task")
    user_id: int = Field(description="ID of the user who owned the task")
    title: str = Field(description="Title of the deleted task")
    was_complete: bool = Field(description="Whether task was complete when deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 123,
                "user_id": 1,
                "title": "Buy groceries",
                "was_complete": False
            }
        }


# ============================================================================
# Reminder Event Data Schemas
# ============================================================================

class ReminderScheduledData(BaseModel):
    """Event data for reminder.scheduled event.

    Emitted when a reminder is scheduled for a task.

    Attributes:
        reminder_id: UUID of the scheduled reminder
        task_id: UUID of the task this reminder is for
        user_id: UUID of the user who owns the task
        scheduled_time: When the reminder should fire
        notification_channels: List of channels to send notifications (email, push, sms)
    """

    reminder_id: UUID4 = Field(description="UUID of the scheduled reminder")
    task_id: UUID4 = Field(description="UUID of the task")
    user_id: UUID4 = Field(description="UUID of the user")
    scheduled_time: datetime = Field(description="When the reminder should fire")
    notification_channels: list[str] = Field(
        description="Notification channels (e.g., ['email', 'push'])"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "user_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "scheduled_time": "2026-01-10T09:00:00Z",
                "notification_channels": ["email", "push"]
            }
        }


class ReminderFiredData(BaseModel):
    """Event data for reminder.fired event.

    Emitted when a scheduled reminder fires and notifications are dispatched.

    Attributes:
        reminder_id: UUID of the fired reminder
        task_id: UUID of the task this reminder is for
        user_id: UUID of the user who owns the task
        fired_at: Actual timestamp when the reminder fired
        scheduled_time: Original scheduled time
        notification_channels: Channels that notifications were sent to
    """

    reminder_id: UUID4 = Field(description="UUID of the fired reminder")
    task_id: UUID4 = Field(description="UUID of the task")
    user_id: UUID4 = Field(description="UUID of the user")
    fired_at: datetime = Field(description="When the reminder actually fired")
    scheduled_time: datetime = Field(description="Original scheduled time")
    notification_channels: list[str] = Field(
        description="Channels that notifications were sent to"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "user_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "fired_at": "2026-01-10T09:00:15Z",
                "scheduled_time": "2026-01-10T09:00:00Z",
                "notification_channels": ["email", "push"]
            }
        }


class TaskReminderScheduledData(BaseModel):
    """Event data for reminder.scheduled event from task operations.

    Emitted when a task is created/updated with a reminder_time.
    Uses integer IDs to match the task model.

    Task: T-522 - Reminder Scheduling Logic (Backend)

    Attributes:
        task_id: ID of the task (int)
        user_id: ID of the user (int)
        scheduled_time: When the reminder should fire
        notification_channels: List of channels (parsed from reminder_config)
    """

    task_id: int = Field(description="ID of the task")
    user_id: int = Field(description="ID of the user")
    scheduled_time: datetime = Field(description="When the reminder should fire")
    notification_channels: list[str] = Field(
        default=["email"],
        description="Notification channels (e.g., ['email', 'push'])"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 123,
                "user_id": 1,
                "scheduled_time": "2026-01-10T09:00:00Z",
                "notification_channels": ["email"]
            }
        }


class ReminderCancelledData(BaseModel):
    """Event data for reminder.cancelled event.

    Emitted when a reminder is cancelled (task updated to remove reminder or task deleted).

    Task: T-522 - Reminder Scheduling Logic (Backend)

    Attributes:
        task_id: ID of the task (int for existing tasks)
        user_id: ID of the user (int for existing users)
        reason: Reason for cancellation (task_deleted, reminder_removed)
        cancelled_at: When the reminder was cancelled
    """

    task_id: int = Field(description="ID of the task")
    user_id: int = Field(description="ID of the user")
    reason: Literal["task_deleted", "reminder_removed"] = Field(
        description="Reason for cancellation"
    )
    cancelled_at: datetime = Field(description="When the reminder was cancelled")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 123,
                "user_id": 1,
                "reason": "task_deleted",
                "cancelled_at": "2026-01-09T14:00:00Z"
            }
        }


class TaskReminderFiredData(BaseModel):
    """Event data for reminder.fired event from reminder worker.

    Emitted when a scheduled reminder fires and is processed by the worker.
    Uses integer IDs to match the current task model.

    Task: T-523 - Reminder Service (Worker)

    Attributes:
        reminder_id: UUID of the fired reminder
        task_id: ID of the task (int)
        user_id: ID of the user (int)
        fired_at: Actual timestamp when the reminder fired
        scheduled_time: Original scheduled time
        notification_channels: Channels for notifications
    """

    reminder_id: UUID4 = Field(description="UUID of the fired reminder")
    task_id: int = Field(description="ID of the task")
    user_id: int = Field(description="ID of the user")
    fired_at: datetime = Field(description="When the reminder actually fired")
    scheduled_time: datetime = Field(description="Original scheduled time")
    notification_channels: list[str] = Field(
        default=["email"],
        description="Notification channels (e.g., ['email', 'push'])"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "task_id": 123,
                "user_id": 1,
                "fired_at": "2026-01-10T09:00:15Z",
                "scheduled_time": "2026-01-10T09:00:00Z",
                "notification_channels": ["email"]
            }
        }


# ============================================================================
# Notification Event Data Schemas
# ============================================================================

class NotificationSentData(BaseModel):
    """Event data for notification.sent event.

    Emitted when a notification is successfully sent through a channel.

    Attributes:
        notification_id: UUID of the notification
        reminder_id: UUID of the reminder that triggered this notification
        user_id: UUID of the user receiving the notification
        channel: Delivery channel (email, push, sms)
        status: Delivery status (sent, failed)
        sent_at: When the notification was sent
        attempt: Delivery attempt number (for retries)
        error: Error message if delivery failed
    """

    notification_id: UUID4 = Field(description="UUID of the notification")
    reminder_id: UUID4 = Field(description="UUID of the reminder")
    user_id: UUID4 = Field(description="UUID of the user")
    channel: Literal["email", "push", "sms"] = Field(description="Delivery channel")
    status: Literal["sent", "failed"] = Field(description="Delivery status")
    sent_at: datetime = Field(description="When the notification was sent")
    attempt: int = Field(ge=1, description="Delivery attempt number")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "channel": "email",
                "status": "sent",
                "sent_at": "2026-01-10T09:00:30Z",
                "attempt": 1,
                "error": None
            }
        }


# ============================================================================
# Typed CloudEvent Schemas
# ============================================================================

class TaskCreatedEvent(CloudEvent):
    """CloudEvent for task.created event type.

    Emitted when a new task is created.
    """

    type: Literal["task.created"] = "task.created"
    data: TaskCreatedData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "source": "/api/tasks",
                "specversion": "1.0",
                "type": "task.created",
                "subject": "task/123",
                "time": "2026-01-09T12:00:00Z",
                "data": {
                    "task_id": 123,
                    "user_id": 1,
                    "title": "Buy groceries",
                    "description": "Get milk and eggs",
                    "priority": "medium"
                }
            }
        }


class TaskUpdatedEvent(CloudEvent):
    """CloudEvent for task.updated event type.

    Emitted when a task is updated.
    """

    type: Literal["task.updated"] = "task.updated"
    data: TaskUpdatedData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "source": "/api/tasks",
                "specversion": "1.0",
                "type": "task.updated",
                "subject": "task/123",
                "time": "2026-01-09T13:00:00Z",
                "data": {
                    "task_id": 123,
                    "user_id": 1,
                    "changes": {"priority": "high"},
                    "previous_values": {"priority": "medium"}
                }
            }
        }


class TaskDeletedEvent(CloudEvent):
    """CloudEvent for task.deleted event type.

    Emitted when a task is deleted.
    """

    type: Literal["task.deleted"] = "task.deleted"
    data: TaskDeletedData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "source": "/api/tasks",
                "specversion": "1.0",
                "type": "task.deleted",
                "subject": "task/123",
                "time": "2026-01-09T14:00:00Z",
                "data": {
                    "task_id": 123,
                    "user_id": 1,
                    "title": "Buy groceries",
                    "was_complete": False
                }
            }
        }


class ReminderScheduledEvent(CloudEvent):
    """CloudEvent for reminder.scheduled event type.

    Emitted when a reminder is scheduled.
    """

    type: Literal["reminder.scheduled"] = "reminder.scheduled"
    data: ReminderScheduledData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "source": "/api/reminders",
                "specversion": "1.0",
                "type": "reminder.scheduled",
                "subject": "reminder/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "time": "2026-01-09T15:00:00Z",
                "data": {
                    "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "user_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                    "scheduled_time": "2026-01-10T09:00:00Z",
                    "notification_channels": ["email", "push"]
                }
            }
        }


class ReminderFiredEvent(CloudEvent):
    """CloudEvent for reminder.fired event type.

    Emitted when a scheduled reminder fires.
    """

    type: Literal["reminder.fired"] = "reminder.fired"
    data: ReminderFiredData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "e5f6a7b8-c9d0-1234-ef56-789012345678",
                "source": "/api/reminders",
                "specversion": "1.0",
                "type": "reminder.fired",
                "subject": "reminder/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "time": "2026-01-10T09:00:15Z",
                "data": {
                    "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "user_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                    "fired_at": "2026-01-10T09:00:15Z",
                    "scheduled_time": "2026-01-10T09:00:00Z",
                    "notification_channels": ["email", "push"]
                }
            }
        }


class TaskReminderScheduledEvent(CloudEvent):
    """CloudEvent for reminder.scheduled event type from task operations.

    Emitted when a task is created/updated with a reminder_time.
    Task: T-522 - Reminder Scheduling Logic (Backend)
    """

    type: Literal["reminder.scheduled"] = "reminder.scheduled"
    data: TaskReminderScheduledData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f6a7b8c9-d0e1-2345-f678-901234567890",
                "source": "/api/tasks",
                "specversion": "1.0",
                "type": "reminder.scheduled",
                "subject": "task/123",
                "time": "2026-01-09T15:00:00Z",
                "data": {
                    "task_id": 123,
                    "user_id": 1,
                    "scheduled_time": "2026-01-10T09:00:00Z",
                    "notification_channels": ["email"]
                }
            }
        }


class ReminderCancelledEvent(CloudEvent):
    """CloudEvent for reminder.cancelled event type.

    Emitted when a reminder is cancelled.
    Task: T-522 - Reminder Scheduling Logic (Backend)
    """

    type: Literal["reminder.cancelled"] = "reminder.cancelled"
    data: ReminderCancelledData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a7b8c9d0-e1f2-3456-7890-123456789012",
                "source": "/api/tasks",
                "specversion": "1.0",
                "type": "reminder.cancelled",
                "subject": "task/123",
                "time": "2026-01-09T14:00:00Z",
                "data": {
                    "task_id": 123,
                    "user_id": 1,
                    "reason": "task_deleted",
                    "cancelled_at": "2026-01-09T14:00:00Z"
                }
            }
        }


class TaskReminderFiredEvent(CloudEvent):
    """CloudEvent for reminder.fired event type from reminder worker.

    Emitted when a scheduled reminder fires and is processed.
    Task: T-523 - Reminder Service (Worker)
    """

    type: Literal["reminder.fired"] = "reminder.fired"
    data: TaskReminderFiredData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b8c9d0e1-f2a3-4567-8901-234567890123",
                "source": "/workers/reminder-worker",
                "specversion": "1.0",
                "type": "reminder.fired",
                "subject": "reminder/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "time": "2026-01-10T09:00:15Z",
                "data": {
                    "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "task_id": 123,
                    "user_id": 1,
                    "fired_at": "2026-01-10T09:00:15Z",
                    "scheduled_time": "2026-01-10T09:00:00Z",
                    "notification_channels": ["email"]
                }
            }
        }


class NotificationSentEvent(CloudEvent):
    """CloudEvent for notification.sent event type.

    Emitted when a notification is sent through a delivery channel.
    """

    type: Literal["notification.sent"] = "notification.sent"
    data: NotificationSentData

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f6a7b8c9-d0e1-2345-f678-901234567890",
                "source": "/api/notifications",
                "specversion": "1.0",
                "type": "notification.sent",
                "subject": "notification/d4e5f6a7-b8c9-0123-def4-567890123456",
                "time": "2026-01-10T09:00:30Z",
                "data": {
                    "notification_id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                    "reminder_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "user_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                    "channel": "email",
                    "status": "sent",
                    "sent_at": "2026-01-10T09:00:30Z",
                    "attempt": 1,
                    "error": None
                }
            }
        }
