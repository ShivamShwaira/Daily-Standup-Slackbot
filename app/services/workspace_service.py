"""Workspace service: Workspace management operations."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repository import WorkspaceRepository

logger = logging.getLogger(__name__)


async def get_or_create_workspace(
    session: AsyncSession,
    slack_team_id: str,
    report_channel_id: str,
) -> dict:
    """Get or create workspace during bot installation.

    Args:
        session: Async database session
        slack_team_id: Slack team ID
        report_channel_id: Slack channel ID for reports

    Returns:
        Dict with workspace info
    """
    repo = WorkspaceRepository(session)
    workspace = await repo.get_or_create_default(slack_team_id, report_channel_id)

    await session.commit()
    logger.info(f"Workspace initialized: {slack_team_id}")

    return {
        "workspace_id": workspace.id,
        "slack_team_id": workspace.slack_team_id,
        "report_channel_id": workspace.report_channel_id,
        "default_time": workspace.default_time,
        "timezone": workspace.timezone,
    }


async def get_workspace(
    session: AsyncSession,
    slack_team_id: str,
) -> Optional[dict]:
    """Get workspace by Slack team ID.

    Args:
        session: Async database session
        slack_team_id: Slack team ID

    Returns:
        Workspace dict or None
    """
    repo = WorkspaceRepository(session)
    workspace = await repo.get_by_team_id(slack_team_id)

    if not workspace:
        return None

    return {
        "workspace_id": workspace.id,
        "slack_team_id": workspace.slack_team_id,
        "report_channel_id": workspace.report_channel_id,
        "default_time": workspace.default_time,
        "timezone": workspace.timezone,
    }


async def update_workspace(
    session: AsyncSession,
    workspace_id: int,
    default_time: Optional[str] = None,
    timezone: Optional[str] = None,
    report_channel_id: Optional[str] = None,
) -> Optional[dict]:
    """Update workspace settings.

    Args:
        session: Async database session
        workspace_id: Workspace ID
        default_time: New default time (HH:MM format)
        timezone: New timezone
        report_channel_id: New report channel ID

    Returns:
        Updated workspace dict or None
    """
    repo = WorkspaceRepository(session)

    update_data = {}
    if default_time:
        update_data["default_time"] = default_time
    if timezone:
        update_data["timezone"] = timezone
    if report_channel_id:
        update_data["report_channel_id"] = report_channel_id

    workspace = await repo.update(workspace_id, **update_data)

    if not workspace:
        return None

    await session.commit()
    logger.info(f"Updated workspace: {workspace_id}")

    return {
        "workspace_id": workspace.id,
        "slack_team_id": workspace.slack_team_id,
        "report_channel_id": workspace.report_channel_id,
        "default_time": workspace.default_time,
        "timezone": workspace.timezone,
    }
