"""
Global error handler middleware.

Catches all exceptions and converts them to proper HTTP responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger, get_correlation_id
from app.core.exceptions import RAGException, rag_exception_to_http_exception

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle all exceptions and convert to HTTP responses.

    Catches:
    - RAGException (custom exceptions)
    - HTTPException (FastAPI exceptions)
    - General exceptions (unexpected errors)

    Returns consistent JSON error responses with correlation IDs.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle any exceptions.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response

        except RAGException as exc:
            # Handle custom RAG exceptions
            correlation_id = get_correlation_id()

            logger.error(
                "RAG exception occurred",
                exception_type=type(exc).__name__,
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details
            )

            error_response = {
                "error": {
                    "type": type(exc).__name__,
                    "message": exc.message,
                    "details": exc.details,
                    "correlation_id": correlation_id
                }
            }

            return JSONResponse(
                status_code=exc.status_code,
                content=error_response
            )

        except Exception as exc:
            # Handle unexpected exceptions
            correlation_id = get_correlation_id()

            logger.exception(
                "Unexpected exception occurred",
                exception_type=type(exc).__name__,
                path=request.url.path,
                method=request.method
            )

            # Don't expose internal error details in production
            error_response = {
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred. Please try again later.",
                    "correlation_id": correlation_id
                }
            }

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response
            )
