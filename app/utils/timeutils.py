"""Timezone and date utilities."""

import logging
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_user_date(user_timezone: str) -> date:
    """Get today's date in user's timezone.

    Args:
        user_timezone: User's timezone string (e.g., 'America/New_York')

    Returns:
        Today's date in user's timezone
    """
    try:
        tz = ZoneInfo(user_timezone)
    except Exception as e:
        logger.warning(f"Invalid timezone {user_timezone}, using default: {e}")
        tz = ZoneInfo(settings.scheduler_timezone)

    return datetime.now(tz).date()


def get_user_datetime_now(user_timezone: str) -> datetime:
    """Get current datetime in user's timezone.

    Args:
        user_timezone: User's timezone string

    Returns:
        Current datetime in user's timezone
    """
    try:
        tz = ZoneInfo(user_timezone)
    except Exception as e:
        logger.warning(f"Invalid timezone {user_timezone}, using default: {e}")
        tz = ZoneInfo(settings.scheduler_timezone)

    return datetime.now(tz)


def get_scheduler_date() -> date:
    """Get today's date in scheduler timezone."""
    return get_user_date(settings.scheduler_timezone)


def get_scheduler_datetime() -> datetime:
    """Get current datetime in scheduler timezone."""
    return get_user_datetime_now(settings.scheduler_timezone)


def parse_time_string(time_str: str) -> tuple:
    """Parse HH:MM format time string.

    Args:
        time_str: Time string in HH:MM format

    Returns:
        Tuple of (hour: int, minute: int)

    Raises:
        ValueError: If format is invalid
    """
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {time_str}")

        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError(f"Invalid time values: hour={hour}, minute={minute}")

        return hour, minute
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse time string '{time_str}': {e}")
        raise ValueError(f"Invalid time format: {time_str}") from e


def is_workday(dt: datetime) -> bool:
    """Check if date is a workday (Monday-Friday).

    Args:
        dt: Datetime to check

    Returns:
        True if Monday-Friday, False if weekend
    """
    return dt.weekday() < 5


def get_days_since(earlier_date: date) -> int:
    """Get number of days between earlier_date and today.

    Args:
        earlier_date: The earlier date

    Returns:
        Number of days
    """
    return (get_scheduler_date() - earlier_date).days


def format_date_for_display(dt: date) -> str:
    """Format date for user display.

    Args:
        dt: Date to format

    Returns:
        Formatted date string (e.g., "Monday, Jan 15")
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = days[dt.weekday()]
    return dt.strftime(f"{day_name}, %b %d")
