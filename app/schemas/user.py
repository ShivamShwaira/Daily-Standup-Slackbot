"""Pydantic schemas for User-related operations."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    slack_user_id: str = Field(..., description="Slack user ID (e.g., U123456)")
    display_name: str = Field(..., description="User's display name")
    email: Optional[str] = Field(None, description="User's email address")
    timezone: Optional[str] = Field(None, description="User's timezone (e.g., America/New_York)")


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    display_name: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    active: Optional[bool] = None


class UserRead(BaseModel):
    """Schema for reading user information."""

    id: int
    slack_user_id: str
    display_name: str
    email: Optional[str] = None
    timezone: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
