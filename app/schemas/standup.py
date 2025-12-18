"""Pydantic schemas for Standup-related operations."""

from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class StandupReportCreate(BaseModel):
    """Schema for creating a standup report."""

    user_id: int
    report_date: date
    feeling: Optional[str] = None
    yesterday: Optional[str] = None
    today: Optional[str] = None
    blockers: Optional[str] = None
    skipped: bool = False


class StandupReportUpdate(BaseModel):
    """Schema for updating a standup report."""

    feeling: Optional[str] = None
    yesterday: Optional[str] = None
    today: Optional[str] = None
    blockers: Optional[str] = None
    skipped: Optional[bool] = None


class StandupReportRead(BaseModel):
    """Schema for reading a standup report."""

    id: int
    user_id: int
    report_date: date
    feeling: Optional[str] = None
    yesterday: Optional[str] = None
    today: Optional[str] = None
    blockers: Optional[str] = None
    skipped: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class StandupStateRead(BaseModel):
    """Schema for reading standup state."""

    id: int
    user_id: int
    pending_report_date: date
    current_question_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class StandupStateUpdate(BaseModel):
    """Schema for updating standup state."""

    current_question_index: Optional[int] = None
    pending_report_date: Optional[date] = None


class SettingsUpdate(BaseModel):
    """Schema for updating workspace settings."""

    default_time: Optional[str] = Field(None, description="HH:MM format")
    timezone: Optional[str] = None
    report_channel_id: Optional[str] = None
