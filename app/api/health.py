"""Health check endpoints."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_session
from app.services.scheduler import get_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Dict with health status
    """
    scheduler = get_scheduler()
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running if scheduler else False,
    }


@router.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """Readiness probe (checks database connectivity).

    Args:
        session: Async database session

    Returns:
        Dict with readiness status
    """
    try:
        # Simple query to check DB connectivity
        await session.execute("SELECT 1")
        return {
            "ready": True,
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "database": "disconnected",
            "error": str(e),
        }
