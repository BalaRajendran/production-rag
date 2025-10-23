"""
Request/response logging middleware.

Logs all incoming requests and outgoing responses for audit and debugging.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import log_api_request


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.

    Logs request details (method, path, headers) and response details (status, headers).
    Optionally logs request/response bodies based on configuration.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process and log request/response.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from downstream
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Build context for logging
        context = {}

        if request.client:
            context["client_host"] = request.client.host

        if request.query_params:
            context["query_params"] = dict(request.query_params)

        # Log using helper function
        log_api_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            **context
        )

        return response
