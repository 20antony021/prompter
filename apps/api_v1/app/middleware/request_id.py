"""Request ID propagation middleware."""
import logging
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and propagate request IDs.
    
    - Accepts X-Request-ID header or generates a new UUID
    - Adds request ID to all responses
    - Adds request ID to log context
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add request ID."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Add to request state for downstream access
        request.state.request_id = request_id

        # Add to logging context
        # Note: This requires structlog or similar for proper context propagation
        logger_extra = {"request_id": request_id}

        try:
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response

        except Exception as e:
            # Log error with request ID
            logger.error(f"Request failed: {e}", extra=logger_extra)
            raise

