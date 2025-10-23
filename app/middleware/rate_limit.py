"""
Rate limiting middleware.

Enforces rate limits on API requests using Redis-backed limiter.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitError
from app.core.logging import get_correlation_id, get_logger
from app.core.rate_limiter import get_rate_limiter

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on requests.

    Uses client IP address as identifier by default.
    Adds rate limit headers to all responses.
    """

    def get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.

        Args:
            request: Incoming request

        Returns:
            Unique identifier (IP address or API key)
        """
        # Try to get API key from headers first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        # Fallback identifier
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limits.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response with rate limit headers
        """
        rate_limiter = get_rate_limiter()

        # Get identifier for rate limiting
        identifier = self.get_identifier(request)

        try:
            # Check rate limit
            rate_limit_info = rate_limiter.check_rate_limit(identifier)

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])

            return response

        except RateLimitError as exc:
            # Rate limit exceeded
            correlation_id = get_correlation_id()

            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                path=request.url.path,
                retry_after=exc.retry_after,
            )

            error_response = {
                "error": {
                    "type": "RateLimitError",
                    "message": exc.message,
                    "retry_after": exc.retry_after,
                    "correlation_id": correlation_id,
                }
            }

            headers = {
                "X-RateLimit-Limit": str(exc.details.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
            }

            if exc.retry_after:
                headers["Retry-After"] = str(exc.retry_after)

            return JSONResponse(status_code=429, content=error_response, headers=headers)
