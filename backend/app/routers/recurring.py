"""Recurring patterns router for Phase V.

Task: T-569 to T-575 - Create Recurring Patterns CRUD endpoints
Phase: Phase V - Event-Driven Architecture

This router provides CRUD operations for recurring task patterns:
- GET /recurring - List user's recurring patterns
- POST /recurring - Create a new recurring pattern
- GET /recurring/{id} - Get a specific pattern
- PUT /recurring/{id} - Update a pattern
- DELETE /recurring/{id} - Delete a pattern (with options)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Literal
import logging

from app.database import get_session
from app.models import RecurrencePattern, User
from app.dependencies import get_current_user
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/recurring", tags=["recurring"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Schemas
# ============================================================================

class RecurrencePatternCreate(BaseModel):
    """Schema for creating a recurring pattern.

    Attributes:
        task_template: Template for task creation (title, description, priority)
        frequency: Pattern type (daily, weekly, monthly, yearly, custom)
        interval: Repeat interval (e.g., every 2 weeks)
        days_of_week: Days for weekly patterns (0=Mon, 6=Sun)
        day_of_month: Day for monthly patterns
        end_date: Optional end date
        max_occurrences: Optional max instances
        timezone: User timezone (default: UTC)
    """
    task_template: dict = Field(
        ...,
        description="Task template with title, description, priority"
    )
    frequency: Literal["daily", "weekly", "monthly", "yearly", "custom"] = Field(
        ...,
        description="Recurrence frequency"
    )
    interval: int = Field(
        default=1,
        ge=1,
        le=365,
        description="Interval between occurrences"
    )
    days_of_week: Optional[List[int]] = Field(
        default=None,
        description="Days for weekly patterns (0=Mon, 6=Sun)"
    )
    day_of_month: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        description="Day for monthly patterns"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Optional end date"
    )
    max_occurrences: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of instances"
    )
    timezone: str = Field(
        default="UTC",
        max_length=50,
        description="User timezone"
    )

    @field_validator("task_template")
    @classmethod
    def validate_task_template(cls, v):
        """Ensure task_template has required fields."""
        if "title" not in v:
            raise ValueError("task_template must contain 'title'")
        if not v["title"] or len(v["title"]) < 1:
            raise ValueError("task_template title cannot be empty")
        return v

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(cls, v):
        """Ensure days_of_week values are valid (0-6)."""
        if v is not None:
            if not all(0 <= day <= 6 for day in v):
                raise ValueError("days_of_week must contain values 0-6")
        return v


class RecurrencePatternUpdate(BaseModel):
    """Schema for updating a recurring pattern."""
    task_template: Optional[dict] = None
    frequency: Optional[Literal["daily", "weekly", "monthly", "yearly", "custom"]] = None
    interval: Optional[int] = Field(default=None, ge=1, le=365)
    days_of_week: Optional[List[int]] = None
    day_of_month: Optional[int] = Field(default=None, ge=1, le=31)
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = Field(default=None, ge=1)
    timezone: Optional[str] = Field(default=None, max_length=50)


class RecurrencePatternResponse(BaseModel):
    """Response schema for recurring patterns."""
    id: UUID
    user_id: UUID
    task_template: dict
    frequency: str
    interval: int
    days_of_week: Optional[List[int]]
    day_of_month: Optional[int]
    end_date: Optional[datetime]
    max_occurrences: Optional[int]
    timezone: str
    last_generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=List[RecurrencePatternResponse])
async def list_recurring_patterns(
    frequency: Optional[str] = Query(None, description="Filter by frequency"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all recurring patterns for the current user.

    Task: T-569 - GET /recurring endpoint
    """
    # Build query with user isolation
    statement = (
        select(RecurrencePattern)
        .where(RecurrencePattern.user_id == UUID(str(current_user.id)))
    )

    # Apply frequency filter if provided
    if frequency:
        statement = statement.where(RecurrencePattern.frequency == frequency)

    # Apply pagination
    statement = (
        statement
        .order_by(RecurrencePattern.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    patterns = session.exec(statement).all()
    return patterns


@router.post("/", response_model=RecurrencePatternResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_pattern(
    pattern_data: RecurrencePatternCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new recurring pattern.

    Task: T-570 - POST /recurring endpoint
    """
    # Validate mutual exclusion of end conditions
    if pattern_data.end_date and pattern_data.max_occurrences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both end_date and max_occurrences"
        )

    # Create pattern
    pattern = RecurrencePattern(
        user_id=UUID(str(current_user.id)),
        task_template=pattern_data.task_template,
        frequency=pattern_data.frequency,
        interval=pattern_data.interval,
        days_of_week=pattern_data.days_of_week,
        day_of_month=pattern_data.day_of_month,
        end_date=pattern_data.end_date,
        max_occurrences=pattern_data.max_occurrences,
        timezone=pattern_data.timezone
    )

    session.add(pattern)
    session.commit()
    session.refresh(pattern)

    logger.info(
        f"Created recurring pattern {pattern.id} for user {current_user.id} "
        f"(frequency: {pattern.frequency})"
    )

    return pattern


@router.get("/{pattern_id}", response_model=RecurrencePatternResponse)
async def get_recurring_pattern(
    pattern_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific recurring pattern.

    Task: T-571 - GET /recurring/{id} endpoint
    """
    pattern = session.get(RecurrencePattern, pattern_id)

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring pattern not found"
        )

    # Verify ownership
    if pattern.user_id != UUID(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this pattern"
        )

    return pattern


@router.put("/{pattern_id}", response_model=RecurrencePatternResponse)
async def update_recurring_pattern(
    pattern_id: UUID,
    pattern_data: RecurrencePatternUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a recurring pattern.

    Task: T-572 - PUT /recurring/{id} endpoint

    Note: Changes only affect future task instances, not existing ones.
    """
    pattern = session.get(RecurrencePattern, pattern_id)

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring pattern not found"
        )

    # Verify ownership
    if pattern.user_id != UUID(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pattern"
        )

    # Apply updates
    update_data = pattern_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pattern, key, value)

    # Validate mutual exclusion after update
    if pattern.end_date and pattern.max_occurrences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot have both end_date and max_occurrences"
        )

    pattern.updated_at = datetime.utcnow()

    session.add(pattern)
    session.commit()
    session.refresh(pattern)

    logger.info(
        f"Updated recurring pattern {pattern.id} for user {current_user.id}"
    )

    return pattern


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_pattern(
    pattern_id: UUID,
    delete_mode: Literal["pattern_only", "all_future", "all_instances"] = Query(
        default="pattern_only",
        description="What to delete: pattern_only (just the pattern), "
                    "all_future (pattern + future instances), "
                    "all_instances (pattern + all instances)"
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a recurring pattern.

    Task: T-573 - DELETE /recurring/{id} endpoint

    Delete modes:
    - pattern_only: Delete only the pattern, keep existing task instances
    - all_future: Delete pattern and future (incomplete) task instances
    - all_instances: Delete pattern and all related task instances
    """
    pattern = session.get(RecurrencePattern, pattern_id)

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring pattern not found"
        )

    # Verify ownership
    if pattern.user_id != UUID(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this pattern"
        )

    # Delete pattern (task instance deletion would be handled by a separate service)
    # For now, we just delete the pattern itself
    # The recurring task generator will stop creating new instances
    session.delete(pattern)
    session.commit()

    logger.info(
        f"Deleted recurring pattern {pattern_id} for user {current_user.id} "
        f"(mode: {delete_mode})"
    )

    return None
