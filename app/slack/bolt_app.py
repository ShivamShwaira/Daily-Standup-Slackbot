"""Slack Bolt app configuration and async client management."""

import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient
from app.core.config import settings
from app.db.repository import WorkspaceRepository
from slack_bolt.authorization.async_authorize import AuthorizeResult
from app.db.base import async_session

logger = logging.getLogger(__name__)

async def authorize(enterprise_id, team_id, user_id, **kwargs):
    async with async_session() as session:
        repo = WorkspaceRepository(session)
        workspace = await repo.get_by_team_id(team_id)

        if not workspace or not workspace.bot_token:
            raise Exception(f"No bot token found for team_id={team_id}")

        return AuthorizeResult(
            enterprise_id=enterprise_id,
            user_id=user_id,
            team_id=team_id,
            bot_token=workspace.bot_token,
            bot_user_id=workspace.bot_user_id,
        )
    
# Create async Slack app
bolt_app = AsyncApp(
    signing_secret=settings.slack_signing_secret,
    authorize=authorize,
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

def get_slack_client_for_workspace(bot_token: str) -> AsyncWebClient:
    return AsyncWebClient(token=bot_token)