"""Observability middleware for request tracking and logging."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger, set_correlation_id
from src.core.metrics import (
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
)

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and add correlation ID."""
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)

        # Add to request state for access in endpoints
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Log request and response details."""
        start_time = time.time()
        method = request.method
        path = request.url.path

        # Extract request info
        request_info = {
            "method": method,
            "path": path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()

        # Log request
        logger.info(
            "request_started",
            **request_info,
        )

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=path).dec()

            # Log exception
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_seconds=duration,
                **request_info,
            )

            # Record metrics
            http_requests_total.labels(
                method=method, endpoint=path, status_code="500"
            ).inc()
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(
                duration
            )

            raise

        # Decrement in-progress counter
        http_requests_in_progress.labels(method=method, endpoint=path).dec()

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=method, endpoint=path, status_code=str(status_code)
        ).inc()
        http_request_duration_seconds.labels(method=method, endpoint=path).observe(
            duration
        )

        # Log response
        logger.info(
            "request_completed",
            status_code=status_code,
            duration_seconds=duration,
            **request_info,
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        return response
