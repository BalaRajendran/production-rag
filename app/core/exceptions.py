"""
Custom exceptions for the Production RAG Framework.

Provides structured error handling with proper HTTP status codes and error messages.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class RAGException(Exception):
    """Base exception for RAG-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(RAGException):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class VectorStoreError(RAGException):
    """Raised when vector store operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class EmbeddingError(RAGException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class LLMError(RAGException):
    """Raised when LLM operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class RerankError(RAGException):
    """Raised when reranking operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class DocumentProcessingError(RAGException):
    """Raised when document processing fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class DocumentNotFoundError(RAGException):
    """Raised when a document is not found."""

    def __init__(self, document_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Document '{document_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"document_id": document_id}
        )


class RateLimitError(RAGException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=error_details
        )
        self.retry_after = retry_after


class ValidationError(RAGException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationError(RAGException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(RAGException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


def rag_exception_to_http_exception(exc: RAGException) -> HTTPException:
    """
    Convert a RAG exception to FastAPI HTTPException.

    Args:
        exc: The RAG exception to convert

    Returns:
        HTTPException with appropriate status code and details
    """
    detail = {
        "error": exc.message,
        **exc.details
    }

    # Add retry-after header for rate limit errors
    headers = {}
    if isinstance(exc, RateLimitError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    return HTTPException(
        status_code=exc.status_code,
        detail=detail,
        headers=headers if headers else None
    )
