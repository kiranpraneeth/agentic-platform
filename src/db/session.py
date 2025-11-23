"""Database session configuration."""

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

from src.core.config import settings

# Create async engine with optimized pool settings
engine = create_async_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,
    poolclass=QueuePool,  # Use queue-based pooling
    connect_args={
        "server_settings": {
            "application_name": "agentic-platform",
            "jit": "off",  # Disable JIT for faster queries
        },
        "command_timeout": 60,  # 60 second query timeout
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_pool_status() -> dict[str, int]:
    """Get current database connection pool status.

    Returns:
        Dictionary with pool metrics
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow(),
    }


async def update_pool_metrics() -> None:
    """Update Prometheus metrics for connection pool."""
    try:
        from src.core.metrics import db_connection_pool_overflow, db_connection_pool_size

        status = get_pool_status()
        db_connection_pool_size.set(status["checked_out"])
        db_connection_pool_overflow.set(status["overflow"])
    except ImportError:
        pass  # Metrics not available
