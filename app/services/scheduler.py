"""APScheduler configuration and job management."""

import logging
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings

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


async def start_scheduler() -> None:
    """Start the scheduler.

    This should be called on FastAPI startup.
    """
    global scheduler
    scheduler = get_scheduler()

    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    scheduler.start()
    logger.info("APScheduler started")

    # Schedule the daily standup dispatch
    try:
        # Parse default time (HH:MM format)
        parts = settings.default_standup_time.split(":")
        hour, minute = int(parts[0]), int(parts[1])

        # Create cron trigger for weekdays at specified time
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week="mon-fri",
            timezone=settings.scheduler_timezone,
        )

        scheduler.add_job(
            dispatch_pending_standups,
            trigger=trigger,
            id="daily_standup_dispatch",
            name="Daily Standup Dispatch",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled daily standup dispatch at {settings.default_standup_time} "
            f"({settings.scheduler_timezone}) on weekdays"
        )
    except Exception as e:
        logger.error(f"Failed to schedule standup job: {e}")
        raise


async def stop_scheduler() -> None:
    """Stop the scheduler.

    This should be called on FastAPI shutdown.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped")


async def dispatch_pending_standups() -> None:
    """Main job: Check for users without reports and send DMs.

    This is the core standup dispatch logic that runs on schedule.
    """
    from app.db.base import async_session
    from app.services.standup_service import send_pending_standups

    logger.info("Running standup dispatch job")

    try:
        async with async_session() as session:
            await send_pending_standups(session)
        logger.info("Standup dispatch completed")
    except Exception as e:
        logger.error(f"Error during standup dispatch: {e}", exc_info=True)

    # TODO: For production with multiple instances:
    # - Use Celery + Redis for distributed job queuing
    # - Add job locks to prevent duplicate execution
    # - Monitor job execution via a metrics store
