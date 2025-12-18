"""Slack Bolt app configuration and async client management."""

import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async Slack app
bolt_app = AsyncApp(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret,
)

# Create handler for FastAPI integration
slack_request_handler = AsyncSlackRequestHandler(bolt_app)


def get_slack_client():
    """Get the Slack client from bolt app.

    Returns:
        Slack client
    """
    return bolt_app.client


def get_bolt_app():
    """Get the async Bolt app instance.

    Returns:
        AsyncApp instance
    """
    return bolt_app
