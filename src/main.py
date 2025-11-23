"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1 import api_router
from src.core.cache import close_redis
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.core.metrics import get_metrics, get_metrics_content_type
from src.core.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware
from src.core.rate_limit import RateLimitMiddleware
from src.core.sentry_config import configure_sentry
from src.core.tracing import configure_tracing
from src.db.session import engine, get_db, update_pool_metrics

# Configure logging and error tracking on startup
configure_logging()
configure_sentry()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info(
        "application_startup",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Update pool metrics on startup
    await update_pool_metrics()

    yield

    # Shutdown
    logger.info("application_shutdown")

    # Close connections
    await close_redis()
    await engine.dispose()

    logger.info("application_shutdown_complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-tenant AI agentic platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure tracing
configure_tracing(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    enabled=True,
)

# Observability middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str | bool]:
    """Readiness probe - checks database connectivity."""
    checks = {"status": "ready", "database": False, "details": {}}

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
        checks["details"]["database"] = "connected"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["status"] = "not_ready"
        checks["details"]["database"] = f"error: {str(e)}"

    return checks


@app.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "alive"}


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type=get_metrics_content_type())
