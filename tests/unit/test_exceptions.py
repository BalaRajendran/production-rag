"""
Unit tests for custom exceptions module.

Tests custom exception classes, HTTP status codes, and error responses.
"""

import pytest
from fastapi import HTTPException, status

from app.core.exceptions import (
    RAGException,
    ConfigurationError,
    VectorStoreError,
    EmbeddingError,
    LLMError,
    RerankError,
    DocumentProcessingError,
    DocumentNotFoundError,
    RateLimitError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    rag_exception_to_http_exception,
)


class TestRAGException:
    """Tests for base RAGException class."""

    def test_default_initialization(self):
        """Test default exception initialization."""
        exc = RAGException("Test error")
        assert exc.message == "Test error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {}

    def test_with_status_code(self):
        """Test exception with custom status code."""
        exc = RAGException("Test error", status_code=status.HTTP_400_BAD_REQUEST)
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_with_details(self):
        """Test exception with details."""
        details = {"field": "value", "count": 42}
        exc = RAGException("Test error", details=details)
        assert exc.details == details

    def test_string_representation(self):
        """Test string representation of exception."""
        exc = RAGException("Test error")
        assert str(exc) == "Test error"


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_default_status_code(self):
        """Test that configuration errors use 500 status code."""
        exc = ConfigurationError("Invalid configuration")
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_with_details(self):
        """Test configuration error with details."""
        details = {"missing_key": "API_KEY"}
        exc = ConfigurationError("Missing required configuration", details=details)
        assert exc.details == details


class TestVectorStoreError:
    """Tests for VectorStoreError."""

    def test_default_status_code(self):
        """Test that vector store errors use 503 status code."""
        exc = VectorStoreError("Connection failed")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_error_message(self):
        """Test error message."""
        exc = VectorStoreError("Qdrant connection timeout")
        assert "timeout" in exc.message.lower()


class TestEmbeddingError:
    """Tests for EmbeddingError."""

    def test_default_status_code(self):
        """Test that embedding errors use 503 status code."""
        exc = EmbeddingError("OpenAI API error")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestLLMError:
    """Tests for LLMError."""

    def test_default_status_code(self):
        """Test that LLM errors use 503 status code."""
        exc = LLMError("Rate limit exceeded")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_with_api_details(self):
        """Test LLM error with API response details."""
        details = {
            "api": "openai",
            "error_code": "rate_limit_exceeded",
            "retry_after": 60
        }
        exc = LLMError("OpenAI rate limit", details=details)
        assert exc.details["api"] == "openai"
        assert exc.details["retry_after"] == 60


class TestRerankError:
    """Tests for RerankError."""

    def test_default_status_code(self):
        """Test that rerank errors use 503 status code."""
        exc = RerankError("Cohere API unavailable")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestDocumentProcessingError:
    """Tests for DocumentProcessingError."""

    def test_default_status_code(self):
        """Test that document processing errors use 422 status code."""
        exc = DocumentProcessingError("Invalid document format")
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_with_document_id(self):
        """Test error with document ID in details."""
        details = {"document_id": "doc-123"}
        exc = DocumentProcessingError("Failed to process", details=details)
        assert exc.details["document_id"] == "doc-123"


class TestDocumentNotFoundError:
    """Tests for DocumentNotFoundError."""

    def test_default_status_code(self):
        """Test that not found errors use 404 status code."""
        exc = DocumentNotFoundError("doc-123")
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_error_message(self):
        """Test error message includes document ID."""
        exc = DocumentNotFoundError("doc-123")
        assert "doc-123" in exc.message

    def test_details_include_document_id(self):
        """Test that details include document ID."""
        exc = DocumentNotFoundError("doc-123")
        assert exc.details["document_id"] == "doc-123"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_status_code(self):
        """Test that rate limit errors use 429 status code."""
        exc = RateLimitError()
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_default_message(self):
        """Test default error message."""
        exc = RateLimitError()
        assert "rate limit" in exc.message.lower()

    def test_with_retry_after(self):
        """Test rate limit error with retry_after."""
        exc = RateLimitError(retry_after=60)
        assert exc.retry_after == 60
        assert exc.details["retry_after"] == 60

    def test_custom_message(self):
        """Test custom error message."""
        exc = RateLimitError(message="Too many requests from IP")
        assert exc.message == "Too many requests from IP"


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_status_code(self):
        """Test that validation errors use 422 status code."""
        exc = ValidationError("Invalid input")
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_with_field_details(self):
        """Test validation error with field details."""
        details = {
            "field": "email",
            "expected": "valid email format",
            "received": "invalid-email"
        }
        exc = ValidationError("Email validation failed", details=details)
        assert exc.details["field"] == "email"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_status_code(self):
        """Test that authentication errors use 401 status code."""
        exc = AuthenticationError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_default_message(self):
        """Test default error message."""
        exc = AuthenticationError()
        assert exc.message == "Authentication failed"

    def test_custom_message(self):
        """Test custom error message."""
        exc = AuthenticationError("Invalid API key")
        assert exc.message == "Invalid API key"


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_status_code(self):
        """Test that authorization errors use 403 status code."""
        exc = AuthorizationError()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_default_message(self):
        """Test default error message."""
        exc = AuthorizationError()
        assert exc.message == "Insufficient permissions"

    def test_custom_message(self):
        """Test custom error message."""
        exc = AuthorizationError("Access denied")
        assert exc.message == "Access denied"


class TestRagExceptionToHttpException:
    """Tests for rag_exception_to_http_exception converter."""

    def test_basic_conversion(self):
        """Test basic exception conversion."""
        rag_exc = RAGException("Test error")
        http_exc = rag_exception_to_http_exception(rag_exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in http_exc.detail
        assert http_exc.detail["error"] == "Test error"

    def test_conversion_with_details(self):
        """Test conversion with exception details."""
        details = {"field": "value", "count": 42}
        rag_exc = RAGException("Test error", details=details)
        http_exc = rag_exception_to_http_exception(rag_exc)

        assert http_exc.detail["field"] == "value"
        assert http_exc.detail["count"] == 42

    def test_rate_limit_conversion(self):
        """Test conversion of rate limit error with headers."""
        rag_exc = RateLimitError(retry_after=60)
        http_exc = rag_exception_to_http_exception(rag_exc)

        assert http_exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert http_exc.headers is not None
        assert http_exc.headers["Retry-After"] == "60"

    def test_document_not_found_conversion(self):
        """Test conversion of document not found error."""
        rag_exc = DocumentNotFoundError("doc-123")
        http_exc = rag_exception_to_http_exception(rag_exc)

        assert http_exc.status_code == status.HTTP_404_NOT_FOUND
        assert "doc-123" in http_exc.detail["error"]
        assert http_exc.detail["document_id"] == "doc-123"


@pytest.mark.parametrize(
    "exception_class,expected_status",
    [
        (ConfigurationError, status.HTTP_500_INTERNAL_SERVER_ERROR),
        (VectorStoreError, status.HTTP_503_SERVICE_UNAVAILABLE),
        (EmbeddingError, status.HTTP_503_SERVICE_UNAVAILABLE),
        (LLMError, status.HTTP_503_SERVICE_UNAVAILABLE),
        (RerankError, status.HTTP_503_SERVICE_UNAVAILABLE),
        (DocumentProcessingError, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (DocumentNotFoundError, status.HTTP_404_NOT_FOUND),
        (RateLimitError, status.HTTP_429_TOO_MANY_REQUESTS),
        (ValidationError, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (AuthenticationError, status.HTTP_401_UNAUTHORIZED),
        (AuthorizationError, status.HTTP_403_FORBIDDEN),
    ],
)
def test_exception_status_codes(exception_class, expected_status):
    """Test that all exception classes have correct status codes."""
    if exception_class == DocumentNotFoundError:
        exc = exception_class("doc-id")
    else:
        exc = exception_class("Test error")

    assert exc.status_code == expected_status
