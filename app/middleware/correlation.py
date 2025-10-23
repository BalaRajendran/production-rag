"""
Correlation ID middleware.

Extracts or generates correlation IDs for request tracking across services.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import set_correlation_id, get_logger

logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for distributed tracing.

    Extracts correlation ID from X-Correlation-ID header or generates a new one.
    Sets the ID in context for use in logging and adds it to response headers.
    """

    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and handle correlation ID.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get(self.HEADER_NAME)

        if not correlation_id:
            # Generate new UUID-based correlation ID
            correlation_id = str(uuid.uuid4())

        # Set in context for logging
        set_correlation_id(correlation_id)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[self.HEADER_NAME] = correlation_id

        return response
