"""APScheduler configuration and job management."""

import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.repository import WorkspaceRepository
from app.services.standup_service import send_pending_standups_for_workspace

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance.

    Returns:
        AsyncIOScheduler instance
    """
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def start_scheduler(session: AsyncSession) -> None:
    """Start the scheduler.

    This should be called on FastAPI startup.
    """
    global scheduler
    scheduler = get_scheduler()
    workspace_repo = WorkspaceRepository(session)
    workspaces = await workspace_repo.list_all_active()

    for workspace in workspaces:
        hour, minute = map(int, workspace.default_time.split(":"))

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=ZoneInfo(workspace.timezone),
        )

        scheduler.add_job(
            send_pending_standups_for_workspace,
            trigger=trigger,
            args=[workspace.id],
            id=f"standup-{workspace.id}",
            replace_existing=True,
        )

    scheduler.start()


async def stop_scheduler() -> None:
    """Stop the scheduler.

    This should be called on FastAPI shutdown.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped")


async def dispatch_pending_standups(workspace_id: str) -> None:
    """Main job: Check for users without reports and send DMs.

    This is the core standup dispatch logic that runs on schedule.
    """
    from app.db.base import async_session
    from app.services.standup_service import send_pending_standups_for_workspace

    logger.info("Running standup dispatch job")

    try:
        async with async_session() as session:
            await send_pending_standups_for_workspace(workspace_id=workspace_id)
        logger.info("Standup dispatch completed")
    except Exception as e:
        logger.error(f"Error during standup dispatch: {e}", exc_info=True)

    # TODO: For production with multiple instances:
    # - Use Celery + Redis for distributed job queuing
    # - Add job locks to prevent duplicate execution
    # - Monitor job execution via a metrics store
