"""Slack API utility helpers."""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_user_info_text(user_name: str, email: Optional[str] = None) -> str:
    """Format user info for display.

    Args:
        user_name: User's display name
        email: User's email (optional)

    Returns:
        Formatted string for Slack
    """
    if email:
        return f"{user_name} ({email})"
    return user_name


def extract_user_id_from_mention(mention: str) -> Optional[str]:
    """Extract Slack user ID from mention format.

    Args:
        mention: String like '<@U123456>' or 'U123456'

    Returns:
        User ID or None if invalid
    """
    if mention.startswith("<@") and mention.endswith(">"):
        return mention[2:-1]
    if mention.startswith("U"):
        return mention
    return None


def escape_slack_text(text: str) -> str:
    """Escape special characters for Slack messages.

    Args:
        text: Raw text

    Returns:
        Escaped text safe for Slack
    """
    if not text:
        return ""

    # Slack uses standard HTML entities
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
    }

    result = text
    for char, escaped in replacements.items():
        result = result.replace(char, escaped)

    return result


def unescape_slack_text(text: str) -> str:
    """Unescape Slack entities.

    Args:
        text: Slack message text with entities

    Returns:
        Unescaped text
    """
    if not text:
        return ""

    replacements = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
    }

    result = text
    for escaped, char in replacements.items():
        result = result.replace(escaped, char)

    return result


def build_user_profile_link(slack_user_id: str) -> str:
    """Build a Slack user profile link.

    Args:
        slack_user_id: Slack user ID

    Returns:
        Slack user link in format <@USERID>
    """
    return f"<@{slack_user_id}>"


def is_bot_message(message: Dict[str, Any]) -> bool:
    """Check if a message was sent by a bot.

    Args:
        message: Slack message event dict

    Returns:
        True if message is from a bot
    """
    return message.get("bot_id") is not None or message.get("subtype") == "bot_message"
