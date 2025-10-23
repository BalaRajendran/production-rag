"""
Request timing middleware.

Measures request processing time and adds timing headers to responses.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to measure and log request processing time.

    Adds X-Process-Time header to all responses with duration in seconds.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and measure time.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response with timing header
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        process_time = time.time() - start_time

        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Log slow requests (> 1 second)
        if process_time > 1.0:
            logger.warning(
                "Slow request detected",
                path=request.url.path,
                method=request.method,
                duration_seconds=process_time
            )

        return response
