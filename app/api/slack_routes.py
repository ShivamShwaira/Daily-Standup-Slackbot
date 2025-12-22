import logging

from fastapi import APIRouter
from fastapi.params import Depends
import httpx
from app.core.config import settings
from app.db.base import get_session
from app.services.workspace_service import get_or_create_workspace
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/slack/oauth/callback")
async def slack_oauth_callback(code: str, session: AsyncSession = Depends(get_session)):
    response = httpx.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": settings.slack_client_id,
            "client_secret": settings.slack_client_secret,
            "code": code,
        },
    )

    data = response.json()
    if not data.get("ok"):
        logger.error(f"Slack OAuth failed: {data.get('error')}")
        return {"status": "error"}

    # store per workspace
    workspace = await get_or_create_workspace(
        slack_team_id=data["team"]["id"],
        bot_token=data["access_token"],
        bot_user_id=data["bot_user_id"],
        session=session,
        report_channel_id="",
    )

    if not workspace:
        logger.error("Failed to create workspace during OAuth")
        return {"status": "error"}

    return {"status": "installed"}
