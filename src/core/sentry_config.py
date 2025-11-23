"""Sentry error tracking and performance monitoring configuration."""

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def configure_sentry() -> None:
    """Configure Sentry for error tracking and performance monitoring.

    Only initializes in production/staging environments.
    Includes integrations for FastAPI, SQLAlchemy, Redis, HTTPX, and more.
    """
    if not settings.SENTRY_DSN:
        logger.info("sentry_disabled", reason="no_dsn_configured")
        return

    if settings.ENVIRONMENT not in ["production", "staging"]:
        logger.info("sentry_disabled", environment=settings.ENVIRONMENT)
        return

    # Determine sample rates based on environment
    traces_sample_rate = 0.1 if settings.ENVIRONMENT == "production" else 1.0
    profiles_sample_rate = 0.1 if settings.ENVIRONMENT == "production" else 1.0

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Environment and release tracking
        environment=settings.ENVIRONMENT,
        release=f"agentic-platform@{settings.VERSION}",
        # Performance monitoring
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[500, 501, 502, 503, 504, 505],
            ),
            SqlalchemyIntegration(),
            RedisIntegration(),
            HttpxIntegration(),
            AsyncioIntegration(),
            LoggingIntegration(
                level=None,  # Capture breadcrumbs for all log levels
                event_level=None,  # Don't send log records as events (we'll use capture_exception)
            ),
        ],
        # Error filtering
        ignore_errors=[
            KeyboardInterrupt,
            SystemExit,
            # HTTP client errors (4xx) - don't need to track these
            "httpx.HTTPStatusError",
        ],
        # Performance tuning
        max_breadcrumbs=50,
        attach_stacktrace=True,
        # Privacy
        send_default_pii=False,  # Don't send PII by default
        # Before send hook for additional filtering
        before_send=before_send_hook,
        # Before breadcrumb hook for filtering
        before_breadcrumb=before_breadcrumb_hook,
    )

    logger.info(
        "sentry_initialized",
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        traces_sample_rate=traces_sample_rate,
    )


def before_send_hook(event: dict, hint: dict) -> dict | None:
    """Filter and modify events before sending to Sentry.

    Args:
        event: The event data
        hint: Additional context about the event

    Returns:
        Modified event or None to drop the event
    """
    # Don't send health check errors
    if event.get("transaction", "").endswith("/health"):
        return None

    # Don't send 404 errors
    if event.get("request", {}).get("status_code") == 404:
        return None

    # Scrub sensitive data from request headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["Authorization", "Cookie", "X-API-Key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[Filtered]"

    # Scrub sensitive data from request body
    if "request" in event and "data" in event["request"]:
        data = event["request"]["data"]
        if isinstance(data, dict):
            sensitive_fields = ["password", "api_key", "secret", "token"]
            for field in sensitive_fields:
                if field in data:
                    data[field] = "[Filtered]"

    return event


def before_breadcrumb_hook(crumb: dict, hint: dict) -> dict | None:
    """Filter breadcrumbs before adding to event.

    Args:
        crumb: The breadcrumb data
        hint: Additional context

    Returns:
        Modified breadcrumb or None to drop it
    """
    # Don't track health check requests in breadcrumbs
    if crumb.get("category") == "httpx" and "/health" in crumb.get("data", {}).get("url", ""):
        return None

    # Limit query breadcrumbs to avoid noise
    if crumb.get("category") == "query":
        # Only keep queries that take > 100ms
        duration = crumb.get("data", {}).get("duration", 0)
        if duration < 0.1:
            return None

    return crumb


def capture_exception(error: Exception, **context) -> str | None:
    """Capture an exception and send to Sentry with context.

    Args:
        error: The exception to capture
        **context: Additional context to attach

    Returns:
        Event ID or None if not sent
    """
    if not settings.SENTRY_DSN or settings.ENVIRONMENT not in ["production", "staging"]:
        return None

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in context.items():
            scope.set_context(key, value)

        # Capture the exception
        event_id = sentry_sdk.capture_exception(error)

        logger.error(
            "exception_captured_by_sentry",
            error=str(error),
            event_id=event_id,
            **context,
        )

        return event_id


def capture_message(message: str, level: str = "info", **context) -> str | None:
    """Capture a message and send to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **context: Additional context

    Returns:
        Event ID or None if not sent
    """
    if not settings.SENTRY_DSN or settings.ENVIRONMENT not in ["production", "staging"]:
        return None

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in context.items():
            scope.set_context(key, value)

        # Capture the message
        event_id = sentry_sdk.capture_message(message, level=level)

        logger.info(
            "message_captured_by_sentry",
            message=message,
            level=level,
            event_id=event_id,
        )

        return event_id


def set_user_context(user_id: str, **user_data) -> None:
    """Set user context for Sentry events.

    Args:
        user_id: User identifier
        **user_data: Additional user data (email, username, etc.)
    """
    sentry_sdk.set_user({"id": user_id, **user_data})


def set_tag(key: str, value: str) -> None:
    """Set a tag for Sentry events.

    Args:
        key: Tag key
        value: Tag value
    """
    sentry_sdk.set_tag(key, value)


def set_context(name: str, context: dict) -> None:
    """Set additional context for Sentry events.

    Args:
        name: Context name
        context: Context data
    """
    sentry_sdk.set_context(name, context)


def start_transaction(name: str, op: str) -> sentry_sdk.tracing.Transaction:
    """Start a Sentry transaction for performance monitoring.

    Args:
        name: Transaction name
        op: Operation type (e.g., "http.server", "db.query")

    Returns:
        Transaction object
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def start_span(op: str, description: str | None = None) -> sentry_sdk.tracing.Span:
    """Start a Sentry span within a transaction.

    Args:
        op: Operation type
        description: Optional description

    Returns:
        Span object
    """
    return sentry_sdk.start_span(op=op, description=description)
