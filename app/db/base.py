"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.env == "dev",
    future=True,
    pool_pre_ping=True,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Declarative base for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (dependency injection)."""
    async with async_session() as session:
        yield session


async def init_db() -> None:
    """Initialize database (create tables if needed)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database engine."""
    await engine.dispose()
