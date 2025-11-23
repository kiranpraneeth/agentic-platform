"""Rate limiting for API endpoints."""

import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.cache import get_redis
from src.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
    ) -> tuple[bool, dict[str, int]]:
        """Check if request is within rate limits.

        Args:
            identifier: Unique identifier (tenant_id, user_id, IP)
            endpoint: Optional endpoint for per-endpoint limits

        Returns:
            (allowed, info) where info contains remaining requests and reset time
        """
        redis_client = await get_redis()
        now = int(time.time())

        # Keys for minute and hour windows
        minute_key = f"rate_limit:minute:{identifier}"
        hour_key = f"rate_limit:hour:{identifier}"

        if endpoint:
            minute_key += f":{endpoint}"
            hour_key += f":{endpoint}"

        # Check minute limit
        minute_count = await redis_client.get(minute_key)
        if minute_count and int(minute_count) >= self.requests_per_minute:
            ttl = await redis_client.ttl(minute_key)
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                window="minute",
                count=minute_count,
                limit=self.requests_per_minute,
            )
            return False, {
                "limit": self.requests_per_minute,
                "remaining": 0,
                "reset": now + ttl,
            }

        # Check hour limit
        hour_count = await redis_client.get(hour_key)
        if hour_count and int(hour_count) >= self.requests_per_hour:
            ttl = await redis_client.ttl(hour_key)
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                window="hour",
                count=hour_count,
                limit=self.requests_per_hour,
            )
            return False, {
                "limit": self.requests_per_hour,
                "remaining": 0,
                "reset": now + ttl,
            }

        # Increment counters
        pipe = redis_client.pipeline()

        # Minute counter
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)

        # Hour counter
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)

        await pipe.execute()

        # Calculate remaining requests
        minute_remaining = self.requests_per_minute - int(minute_count or 0) - 1
        hour_remaining = self.requests_per_hour - int(hour_count or 0) - 1

        return True, {
            "limit": self.requests_per_minute,
            "remaining": min(minute_remaining, hour_remaining),
            "reset": now + 60,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        enabled: bool = True,
    ):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI app
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, requests_per_hour)
        self.enabled = enabled

    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting.

        Priority:
        1. Tenant ID (from authenticated user)
        2. User ID (from authenticated user)
        3. Client IP address

        Args:
            request: HTTP request

        Returns:
            Unique identifier
        """
        # Check if user is authenticated
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "tenant_id"):
                return f"tenant:{user.tenant_id}"
            if hasattr(user, "id"):
                return f"user:{user.id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting.

        Args:
            path: Request path

        Returns:
            True if exempt
        """
        exempt_paths = [
            "/health",
            "/health/ready",
            "/health/live",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        return any(path.startswith(exempt) for exempt in exempt_paths)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            HTTP response

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip if disabled or exempt
        if not self.enabled or self._is_exempt(request.url.path):
            return await call_next(request)

        # Get identifier
        identifier = self._get_identifier(request)

        # Check rate limit
        allowed, info = await self.limiter.check_rate_limit(
            identifier,
            endpoint=request.url.path,
        )

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
        }

        if not allowed:
            # Rate limit exceeded
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "limit": info["limit"],
                    "reset": info["reset"],
                },
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


# Per-endpoint rate limiters
class EndpointRateLimiter:
    """Rate limiter for specific endpoints with custom limits."""

    def __init__(self, requests: int, window: int = 60):
        """Initialize endpoint rate limiter.

        Args:
            requests: Number of requests allowed
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request) -> None:
        """Check rate limit for endpoint.

        Args:
            request: HTTP request

        Raises:
            HTTPException: If rate limit exceeded
        """
        redis_client = await get_redis()

        # Get identifier
        if hasattr(request.state, "user"):
            identifier = f"user:{request.state.user.id}"
        else:
            identifier = f"ip:{request.client.host if request.client else 'unknown'}"

        # Create key
        key = f"endpoint_limit:{request.url.path}:{identifier}"

        # Check and increment
        count = await redis_client.get(key)

        if count and int(count) >= self.requests:
            ttl = await redis_client.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "endpoint_rate_limit_exceeded",
                    "message": f"Too many requests to {request.url.path}",
                    "limit": self.requests,
                    "window": self.window,
                    "reset": int(time.time()) + ttl,
                },
            )

        # Increment counter
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        await pipe.execute()


# Predefined rate limiters for expensive endpoints
expensive_endpoint_limiter = EndpointRateLimiter(requests=10, window=60)  # 10/min
workflow_execution_limiter = EndpointRateLimiter(requests=20, window=60)  # 20/min
embedding_generation_limiter = EndpointRateLimiter(requests=30, window=60)  # 30/min
