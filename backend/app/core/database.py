"""
Database configuration and session management for NexusAI.
Handles async PostgreSQL connections with SQLAlchemy 2.0.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database URL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/nexusai"
)

# Create async engine
engine_kwargs = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
    "future": True,
    "pool_pre_ping": "sqlite" not in DATABASE_URL,
}

# Only add pool settings for PostgreSQL, not SQLite
if "sqlite" not in DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
    })
else:
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session in FastAPI routes.

    Usage in routes:
        @app.get("/items/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            items = result.scalars().all()
            return items
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        if "already exists" in str(e) or "UNIQUE constraint failed" in str(e):
            # Index or table already exists - safe to ignore
            pass
        else:
            raise


async def close_db():
    """Close database connection."""
    await engine.dispose()
