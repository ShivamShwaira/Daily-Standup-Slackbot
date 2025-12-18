"""User service: User management operations."""

import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repository import UserRepository, WorkspaceRepository
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


async def create_user(
    session: AsyncSession,
    workspace_id: int,
    user_create: UserCreate,
) -> dict:
    """Create a new user.

    Args:
        session: Async database session
        workspace_id: Workspace ID
        user_create: User creation schema

    Returns:
        Dict with user info
    """
    repo = UserRepository(session)

    # Check if user already exists in workspace
    existing = await repo.get_by_slack_id_and_workspace(
        user_create.slack_user_id, workspace_id
    )
    if existing:
        if not existing.active:
            logger.warning(
                f"User {user_create.slack_user_id} inactive in workspace {workspace_id}"
            )
            user = await repo.update(existing.id, active=True)
            await session.commit()
            return {
                "user_id": user.id,
                "slack_user_id": user.slack_user_id,
                "display_name": user.display_name,
            }
        else:
            logger.warning(
                f"User {user_create.slack_user_id} already exists in workspace {workspace_id}"
            )
            return {"error": "User already exists", "user_id": existing.id}

    user = await repo.create(
        workspace_id=workspace_id,
        slack_user_id=user_create.slack_user_id,
        display_name=user_create.display_name,
        email=user_create.email,
        timezone=user_create.timezone,
    )

    await session.commit()
    logger.info(f"Created user: {user_create.slack_user_id}")

    return {
        "user_id": user.id,
        "slack_user_id": user.slack_user_id,
        "display_name": user.display_name,
    }


async def get_user(
    session: AsyncSession,
    user_id: int,
) -> Optional[dict]:
    """Get user by ID.

    Args:
        session: Async database session
        user_id: User ID

    Returns:
        User dict or None
    """
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        return None

    return {
        "id": user.id,
        "slack_user_id": user.slack_user_id,
        "display_name": user.display_name,
        "email": user.email,
        "timezone": user.timezone,
        "active": user.active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


async def list_users(session: AsyncSession) -> List[dict]:
    """List all active users.

    Args:
        session: Async database session

    Returns:
        List of user dicts
    """
    repo = UserRepository(session)
    users = await repo.list_active()

    return [
        {
            "id": u.id,
            "slack_user_id": u.slack_user_id,
            "display_name": u.display_name,
            "email": u.email,
            "timezone": u.timezone,
            "active": u.active,
        }
        for u in users
    ]


async def list_users_by_workspace(
    session: AsyncSession, workspace_id: int
) -> List[dict]:
    """List all active users in a workspace.

    Args:
        session: Async database session
        workspace_id: Workspace ID

    Returns:
        List of user dicts
    """
    repo = UserRepository(session)
    users = await repo.list_active_by_workspace(workspace_id)

    return [
        {
            "id": u.id,
            "slack_user_id": u.slack_user_id,
            "display_name": u.display_name,
            "email": u.email,
            "timezone": u.timezone,
            "active": u.active,
        }
        for u in users
    ]


async def update_user(
    session: AsyncSession,
    user_id: int,
    user_update: UserUpdate,
) -> Optional[dict]:
    """Update user.

    Args:
        session: Async database session
        user_id: User ID
        user_update: Update schema

    Returns:
        Updated user dict or None
    """
    repo = UserRepository(session)

    # Build update dict
    update_data = {}
    if user_update.display_name:
        update_data["display_name"] = user_update.display_name
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.timezone is not None:
        update_data["timezone"] = user_update.timezone
    if user_update.active is not None:
        update_data["active"] = user_update.active

    user = await repo.update(user_id, **update_data)

    if not user:
        return None

    await session.commit()
    logger.info(f"Updated user: {user_id}")

    return {
        "id": user.id,
        "slack_user_id": user.slack_user_id,
        "display_name": user.display_name,
        "email": user.email,
        "timezone": user.timezone,
        "active": user.active,
    }


async def delete_user(
    session: AsyncSession,
    user_id: int,
) -> bool:
    """Delete user.

    Args:
        session: Async database session
        user_id: User ID

    Returns:
        True if deleted, False if not found
    """
    repo = UserRepository(session)
    success = await repo.delete(user_id)

    if success:
        await session.commit()
        logger.info(f"Deleted user: {user_id}")

    return success


async def deactivate_user(
    session: AsyncSession,
    user_id: int,
) -> Optional[dict]:
    """Deactivate user (pause standups).

    Args:
        session: Async database session
        user_id: User ID

    Returns:
        Updated user dict or None
    """
    return await update_user(
        session,
        user_id,
        UserUpdate(active=False),
    )
