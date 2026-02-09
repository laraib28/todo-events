"""SQLModel database models.

Task: T-522 - Reminder Scheduling Logic (Backend)
Added reminder_time and reminder_config fields to Task model.

Task: T-523 - Reminder Service (Worker)
Added Reminder model for reminders table.
"""

from enum import Enum as PyEnum
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Text, Column, text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQL_UUID, ARRAY
from sqlalchemy import Integer
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


# ============================================================================
# Enum Definitions
# ============================================================================

class PriorityEnum(str, PyEnum):
    """Task priority levels."""
    low = "low"
    medium = "medium"
    high = "high"


class FrequencyEnum(str, PyEnum):
    """Recurrence frequency types."""
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    custom = "custom"


class ReminderStatusEnum(str, PyEnum):
    """Reminder status values."""
    pending = "pending"
    fired = "fired"
    cancelled = "cancelled"


class NotificationChannelEnum(str, PyEnum):
    """Notification delivery channels."""
    email = "email"
    push = "push"
    sms = "sms"


class NotificationStatusEnum(str, PyEnum):
    """Notification delivery status."""
    pending = "pending"
    sent = "sent"
    failed = "failed"


class User(SQLModel, table=True):
    """User model for authentication."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tasks: list["Task"] = Relationship(back_populates="user")
    conversation_history: list["ConversationHistory"] = Relationship(back_populates="user")


class Task(SQLModel, table=True):
    """Task model for todo items.

    T-522: Added reminder_time and reminder_config fields.
    """

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: PriorityEnum = Field(
        default=PriorityEnum.medium,
        sa_column=Column(SAEnum(PriorityEnum, name="priority_enum", create_type=False), nullable=False)
    )
    is_complete: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # T-522: Phase V reminder fields (from migration 004)
    reminder_time: Optional[datetime] = Field(default=None)
    reminder_config: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )

    # Relationship
    user: Optional[User] = Relationship(back_populates="tasks")


class ConversationHistory(SQLModel, table=True):
    """Conversation history model for AI chat sessions."""

    __tablename__ = "conversation_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationship
    user: Optional[User] = Relationship(back_populates="conversation_history")


class RecurrencePattern(SQLModel, table=True):
    """Recurrence pattern model for recurring tasks.

    Task: T-530 - Create RecurrencePattern model
    Phase: Phase V - Event-Driven Architecture

    This model maps to the recurrence_patterns table created in migration 004 (T-504).
    Supports daily, weekly, monthly, yearly, and custom recurrence patterns.

    Attributes:
        id: UUID primary key
        user_id: UUID foreign key to users (CASCADE delete)
        task_template: JSONB template for task creation
        frequency: Pattern type (daily, weekly, monthly, yearly, custom)
        interval: Repeat interval (e.g., every 2 weeks)
        days_of_week: Array of weekdays for weekly patterns (0=Mon, 6=Sun)
        day_of_month: Day of month for monthly patterns
        end_date: Optional end date for the pattern
        max_occurrences: Optional max number of instances
        timezone: User timezone for scheduling
        last_generated_at: Last time instances were generated
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "recurrence_patterns"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    )
    user_id: UUID = Field(
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    )
    task_template: Dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False)
    )
    frequency: FrequencyEnum = Field(
        sa_column=Column(SAEnum(FrequencyEnum, name="frequency_enum", create_type=False), nullable=False)
    )
    interval: int = Field(default=1, nullable=False)
    days_of_week: Optional[List[int]] = Field(
        default=None,
        sa_column=Column(ARRAY(Integer), nullable=True)
    )  # 0=Mon, 6=Sun
    day_of_month: Optional[int] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    max_occurrences: Optional[int] = Field(default=None)
    timezone: str = Field(default="UTC", max_length=50, nullable=False)
    last_generated_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Reminder(SQLModel, table=True):
    """Reminder model for scheduled task reminders.

    Task: T-523 - Reminder Service (Worker)

    This model maps to the reminders table created in migration 004 (T-507).

    Note: Migration schema uses UUID types for id, task_id, and user_id.
    Current Task and User models use integer IDs. This mismatch will be
    resolved in a future Phase V migration that converts to UUIDs.

    For T-523, we use UUID types to match the migration schema.
    """

    __tablename__ = "reminders"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    )
    task_id: UUID = Field(
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    )
    user_id: UUID = Field(
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    )
    scheduled_time: datetime = Field(nullable=False)
    status: ReminderStatusEnum = Field(
        default=ReminderStatusEnum.pending,
        sa_column=Column(SAEnum(ReminderStatusEnum, name="reminder_status_enum", create_type=False), nullable=False)
    )
    notification_channels: Dict[str, Any] = Field(
        default_factory=lambda: {"channels": ["email"]},
        sa_column=Column(JSONB, nullable=False)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    fired_at: Optional[datetime] = Field(default=None, nullable=True)


class Event(SQLModel, table=True):
    """Event model for audit logging and event sourcing.

    Task: T-532 - Create Event model
    Phase: Phase V - Event-Driven Architecture

    This model maps to the events table created in migration 004 (T-510).
    Stores all system events for audit trail and event replay.

    Attributes:
        id: UUID primary key
        event_type: Event type identifier (e.g., task.created)
        aggregate_type: Type of entity (e.g., task, reminder)
        aggregate_id: UUID of the entity
        user_id: Optional UUID of the user who triggered the event
        payload: JSONB event data
        metadata: Optional JSONB metadata
        created_at: Event timestamp
    """

    __tablename__ = "events"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    )
    event_type: str = Field(max_length=50, nullable=False)
    aggregate_type: str = Field(max_length=50, nullable=False)
    aggregate_id: UUID = Field(
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    )
    user_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=True)
    )
    payload: Dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False)
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Notification(SQLModel, table=True):
    """Notification model for tracking sent notifications.

    Task: T-533 - Create Notification model
    Phase: Phase V - Event-Driven Architecture

    This model maps to the notifications table created in migration 004 (T-513).
    Tracks notification delivery status across channels (email, push, sms).

    Attributes:
        id: UUID primary key
        reminder_id: UUID foreign key to reminders
        user_id: UUID of the notification recipient
        channel: Delivery channel (email, push, sms)
        status: Delivery status (pending, sent, failed)
        attempt: Delivery attempt count
        last_error: Error message if delivery failed
        created_at: Creation timestamp
        sent_at: Delivery timestamp
    """

    __tablename__ = "notifications"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    )
    reminder_id: UUID = Field(
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    )
    user_id: UUID = Field(
        sa_column=Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    )
    channel: NotificationChannelEnum = Field(
        sa_column=Column(SAEnum(NotificationChannelEnum, name="notification_channel_enum", create_type=False), nullable=False)
    )
    status: NotificationStatusEnum = Field(
        default=NotificationStatusEnum.pending,
        sa_column=Column(SAEnum(NotificationStatusEnum, name="notification_status_enum", create_type=False), nullable=False)
    )
    attempt: int = Field(default=0, nullable=False)
    last_error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    sent_at: Optional[datetime] = Field(default=None, nullable=True)
