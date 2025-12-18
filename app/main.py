"""FastAPI main application with Slack Bolt integration."""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.core.logging_config import configure_logging
from app.core.config import settings
from app.db.base import init_db, close_db
from app.slack.bolt_app import slack_request_handler, get_bolt_app
from app.slack.handlers import register_handlers
from app.slack.onboarding_handlers import (
    register_onboarding_handlers,
    register_installation_handler,
)
from app.services.scheduler import start_scheduler, stop_scheduler
from app.api.health import router as health_router
from app.api.admin_routes import router as admin_router

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup/shutdown.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("=== Application Startup ===")
    try:
        await init_db()
        logger.info("Database initialized")

        # Register Slack handlers
        await register_handlers(get_bolt_app())
        await register_onboarding_handlers(get_bolt_app())
        await register_installation_handler(get_bolt_app())
        logger.info("Slack handlers registered")

        # Start scheduler
        await start_scheduler()
        logger.info("Scheduler started")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        sys.exit(1)

    yield

    # Shutdown
    logger.info("=== Application Shutdown ===")
    try:
        await stop_scheduler()
        logger.info("Scheduler stopped")

        await close_db()
        logger.info("Database closed")

    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="Daily Standup Bot",
    description="Enterprise Slack Standup Bot",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount routers
app.include_router(health_router)
app.include_router(admin_router)


# Mount Slack Bolt adapter
@app.post("/slack/events")
async def slack_events(request: Request):
    """Slack events endpoint for Bolt app.

    Args:
        request: FastAPI request

    Returns:
        Response from Slack handler
    """
    logger.debug("Received Slack event")
    return await slack_request_handler.handle(request)


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "name": "Daily Standup Bot",
        "version": "0.1.0",
        "status": "running",
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions.

    Args:
        request: Request
        exc: Exception

    Returns:
        Plain text response
    """
    logger.error(f"ValueError: {exc}")
    return PlainTextResponse(str(exc), status_code=400)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions.

    Args:
        request: Request
        exc: Exception

    Returns:
        Plain text response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return PlainTextResponse("Internal server error", status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "dev",
    )
