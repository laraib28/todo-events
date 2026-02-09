"""Reminders router for Phase V.

Task: T-576 to T-580 - Create Reminders CRUD endpoints
Phase: Phase V - Event-Driven Architecture

This router provides operations for task reminders:
- GET /reminders - List user's reminders
- GET /reminders/{id} - Get a specific reminder
- POST /reminders/{id}/snooze - Snooze a reminder
- DELETE /reminders/{id} - Cancel a reminder
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, List, Literal
import logging

from app.database import get_session
from app.models import Reminder, User
from app.dependencies import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/reminders", tags=["reminders"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ReminderResponse(BaseModel):
    """Response schema for reminders."""
    id: UUID
    task_id: UUID
    user_id: UUID
    scheduled_time: datetime
    status: str
    notification_channels: dict
    created_at: datetime
    fired_at: Optional[datetime]

    class Config:
        from_attributes = True


class SnoozeRequest(BaseModel):
    """Request schema for snoozing a reminder."""
    duration_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,  # Max 24 hours
        description="Minutes to snooze the reminder"
    )


class SnoozeResponse(BaseModel):
    """Response schema for snooze operation."""
    id: UUID
    new_scheduled_time: datetime
    snoozed_by_minutes: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=List[ReminderResponse])
async def list_reminders(
    status_filter: Optional[Literal["pending", "fired", "cancelled"]] = Query(
        None,
        alias="status",
        description="Filter by reminder status"
    ),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all reminders for the current user.

    Task: T-576 - GET /reminders endpoint
    """
    # Build query with user isolation
    statement = (
        select(Reminder)
        .where(Reminder.user_id == UUID(str(current_user.id)))
    )

    # Apply status filter if provided
    if status_filter:
        statement = statement.where(Reminder.status == status_filter)

    # Apply task filter if provided
    if task_id:
        statement = statement.where(Reminder.task_id == task_id)

    # Apply pagination and ordering
    statement = (
        statement
        .order_by(Reminder.scheduled_time.asc())
        .offset(offset)
        .limit(limit)
    )

    reminders = session.exec(statement).all()
    return reminders


@router.get("/upcoming", response_model=List[ReminderResponse])
async def list_upcoming_reminders(
    hours: int = Query(24, ge=1, le=168, description="Hours ahead to look"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List upcoming reminders within the specified time window.

    Task: T-577 - GET /reminders/upcoming endpoint
    """
    now = datetime.utcnow()
    window_end = now + timedelta(hours=hours)

    statement = (
        select(Reminder)
        .where(Reminder.user_id == UUID(str(current_user.id)))
        .where(Reminder.status == "pending")
        .where(Reminder.scheduled_time >= now)
        .where(Reminder.scheduled_time <= window_end)
        .order_by(Reminder.scheduled_time.asc())
        .limit(limit)
    )

    reminders = session.exec(statement).all()
    return reminders


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific reminder.

    Task: T-578 - GET /reminders/{id} endpoint
    """
    reminder = session.get(Reminder, reminder_id)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Verify ownership
    if reminder.user_id != UUID(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this reminder"
        )

    return reminder


@router.post("/{reminder_id}/snooze", response_model=SnoozeResponse)
async def snooze_reminder(
    reminder_id: UUID,
    snooze_data: SnoozeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Snooze a reminder by the specified duration.

    Task: T-579 - POST /reminders/{id}/snooze endpoint
    """
    reminder = session.get(Reminder, reminder_id)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Verify ownership
    if reminder.user_id != UUID(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to snooze this reminder"
        )

    # Only pending reminders can be snoozed
    if reminder.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot snooze a {reminder.status} reminder"
        )

    # Calculate new scheduled time
    new_time = datetime.utcnow() + timedelta(minutes=snooze_data.duration_minutes)
    reminder.scheduled_time = new_time

    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    logger.info(
        f"Snoozed reminder {reminder_id} by {snooze_data.duration_minutes} minutes "
        f"(new time: {new_time})"
    )

    return SnoozeResponse(
        id=reminder.id,
        new_scheduled_time=new_time,
        snoozed_by_minutes=snooze_data.duration_minutes
    )


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cancel (delete) a reminder.

    Task: T-580 - DELETE /reminders/{id} endpoint
    """
    reminder = session.get(Reminder, reminder_id)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Verify ownership
    if reminder.user_id != UUID(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this reminder"
        )

    # Mark as cancelled instead of deleting (for audit trail)
    if reminder.status == "pending":
        reminder.status = "cancelled"
        session.add(reminder)
        session.commit()
        logger.info(f"Cancelled reminder {reminder_id}")
    else:
        logger.info(
            f"Reminder {reminder_id} already in status '{reminder.status}', "
            f"no action taken"
        )

    return None
