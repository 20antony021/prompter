"""Rate limiting middleware."""
import logging
import time
from typing import Callable, Optional

import redis
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis.
    
    Implements token bucket algorithm with per-org and per-user limits.
    """

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        if redis_client is None and settings.RATE_LIMIT_ENABLED:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=1,
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Rate limiting disabled - Redis unavailable: {e}")
                self.redis_client = None
        else:
            self.redis_client = redis_client

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        # Skip rate limiting if disabled or Redis unavailable
        if not settings.RATE_LIMIT_ENABLED or self.redis_client is None:
            return await call_next(request)

        # Skip rate limiting for health check endpoints
        if request.url.path in ["/healthz", "/readyz", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Extract user/org identifier from request
        # Priority: org_id (from auth) > user_id > IP address
        rate_limit_key = self._get_rate_limit_key(request)

        if not rate_limit_key:
            # No identifier found, fall back to IP-based limiting
            rate_limit_key = f"ratelimit:ip:{request.client.host if request.client else 'unknown'}"

        # Check rate limit
        try:
            allowed, remaining, reset_time = self._check_rate_limit(rate_limit_key)

            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Rate limit exceeded. Please try again later.",
                            "details": {
                                "limit": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                                "reset_at": reset_time,
                            },
                        }
                    },
                )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow request through (fail open)
            return await call_next(request)

    def _get_rate_limit_key(self, request: Request) -> Optional[str]:
        """
        Extract rate limit key from request.
        
        Priority:
        1. org_id from authenticated user
        2. user_id from authenticated user
        3. API key
        4. IP address
        """
        # Check if user is authenticated (set by auth middleware)
        if hasattr(request.state, "user"):
            user = request.state.user
            # If user has an org context, use org-level rate limiting
            if hasattr(request.state, "org_id"):
                return f"ratelimit:org:{request.state.org_id}"
            return f"ratelimit:user:{user.id}"

        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"ratelimit:apikey:{api_key[:16]}"  # Use prefix to avoid long keys

        return None

    def _check_rate_limit(self, key: str) -> tuple[bool, int, int]:
        """
        Check rate limit using token bucket algorithm.
        
        Returns:
            (allowed, remaining_tokens, reset_timestamp)
        """
        if self.redis_client is None:
            return True, settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 0

        now = int(time.time())
        window = 60  # 1 minute window

        # Use sliding window counter
        window_key = f"{key}:{now // window}"
        
        try:
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, window * 2)  # Keep for 2 windows
            results = pipe.execute()
            
            current_count = results[0]
            
            # Calculate remaining
            remaining = max(0, settings.RATE_LIMIT_BURST - current_count)
            reset_time = ((now // window) + 1) * window

            # Check against burst limit
            allowed = current_count <= settings.RATE_LIMIT_BURST

            return allowed, remaining, reset_time

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open on errors
            return True, settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 0


def get_rate_limiter(redis_client: Optional[redis.Redis] = None):
    """Factory function to create rate limiter."""
    return RateLimitMiddleware(None, redis_client=redis_client)

