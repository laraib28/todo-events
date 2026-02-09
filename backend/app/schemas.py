"""Pydantic schemas for request/response validation.

Task: T-522 - Reminder Scheduling Logic (Backend)
Added reminder_time and reminder_config fields to task schemas.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, Literal, Dict, Any


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (no password)."""

    id: int
    email: str
    created_at: datetime


class TaskCreate(BaseModel):
    """Schema for task creation.

    T-522: Added reminder_time and reminder_config for reminder scheduling.
    """

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    reminder_time: Optional[datetime] = Field(default=None, description="When to send reminder")
    reminder_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Reminder configuration (e.g., {'channels': ['email', 'push']})"
    )


class TaskUpdate(BaseModel):
    """Schema for task update.

    T-522: Added reminder_time and reminder_config for reminder scheduling.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    reminder_time: Optional[datetime] = Field(None, description="When to send reminder")
    reminder_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Reminder configuration (e.g., {'channels': ['email', 'push']})"
    )


class TaskResponse(BaseModel):
    """Schema for task response.

    T-522: Added reminder_time and reminder_config fields.
    """

    id: int
    user_id: int
    title: str
    description: str
    priority: str
    is_complete: bool
    created_at: datetime
    updated_at: datetime
    reminder_time: Optional[datetime] = None
    reminder_config: Optional[Dict[str, Any]] = None


# Phase III: Chat Schemas

class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language message from the user"
    )

    @validator('message')
    def message_not_empty(cls, v):
        """Validate that message is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Create a task to buy groceries tomorrow"
            }
        }


class ChatMetadata(BaseModel):
    """Metadata about the action performed."""

    action: Literal[
        "task_created",
        "task_updated",
        "task_deleted",
        "task_completed",
        "task_uncompleted",
        "tasks_listed",
        "no_action"
    ] = Field(description="Action type performed")
    task_id: Optional[int] = Field(default=None, description="ID of the task operated on")
    count: Optional[int] = Field(default=None, description="Number of tasks returned")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "task_created",
                "task_id": 42
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    message: str = Field(description="AI-generated response to the user")
    metadata: Optional[ChatMetadata] = Field(default=None, description="Optional action metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I've created a new task: 'Buy groceries' with medium priority.",
                "metadata": {
                    "action": "task_created",
                    "task_id": 42
                }
            }
        }
