"""Admin routes for user and workspace management."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_session
from app.core.config import settings
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.standup import SettingsUpdate
from app.services.user_service import (
    create_user,
    get_user,
    list_users,
    update_user,
    delete_user,
)
from app.db.repository import WorkspaceRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")


def verify_admin_token(x_admin_token: Optional[str] = Header(None)) -> None:
    """Verify admin token from header.

    Args:
        x_admin_token: Admin token from X-Admin-Token header

    Raises:
        HTTPException: If token is invalid
    """
    if not settings.admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )


@router.post("/users", response_model=dict, dependencies=[Depends(verify_admin_token)])
async def create_new_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new user.

    Args:
        user_data: User creation data
        session: Database session

    Returns:
        Created user info
    """
    logger.info(f"Admin: Creating user {user_data.slack_user_id}")
    result = await create_user(session, user_data)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result["error"],
        )

    return result


@router.get("/users", response_model=List[dict], dependencies=[Depends(verify_admin_token)])
async def list_all_users(session: AsyncSession = Depends(get_session)):
    """List all active users.

    Args:
        session: Database session

    Returns:
        List of users
    """
    logger.info("Admin: Listing users")
    return await list_users(session)


@router.get("/users/{user_id}", response_model=dict, dependencies=[Depends(verify_admin_token)])
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get user by ID.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        User info
    """
    user = await get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch("/users/{user_id}", response_model=dict, dependencies=[Depends(verify_admin_token)])
async def update_user_info(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update user information.

    Args:
        user_id: User ID
        user_data: Update data
        session: Database session

    Returns:
        Updated user info
    """
    logger.info(f"Admin: Updating user {user_id}")
    user = await update_user(session, user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.delete("/users/{user_id}", dependencies=[Depends(verify_admin_token)])
async def remove_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a user.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        Deletion status
    """
    logger.info(f"Admin: Deleting user {user_id}")
    success = await delete_user(session, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"deleted": True, "user_id": user_id}


@router.get("/metrics", dependencies=[Depends(verify_admin_token)])
async def get_metrics(session: AsyncSession = Depends(get_session)):
    """Get standup metrics.

    Args:
        session: Database session

    Returns:
        Metrics dict
    """
    from app.db.repository import UserRepository

    user_repo = UserRepository(session)
    total_active = await user_repo.count_active()

    return {
        "total_active_users": total_active,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@router.patch("/settings", dependencies=[Depends(verify_admin_token)])
async def update_settings(
    settings_data: SettingsUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update workspace settings.

    Args:
        settings_data: Settings to update
        session: Database session

    Returns:
        Updated settings
    """
    logger.info("Admin: Updating workspace settings")

    # TODO: Implement workspace settings update
    # For now, this is a placeholder
    # In production, you'd update the Workspace table

    return {
        "message": "Settings update not yet implemented",
        "data": settings_data,
    }
