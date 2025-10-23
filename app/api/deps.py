"""
Shared dependencies for API endpoints.

Provides reusable dependencies for:
- Settings access
- Rate limiter access
- Observability manager access
- RAG service access
"""

from app.core.config import Settings, get_settings
from app.core.observability import ObservabilityManager, get_observability_manager
from app.core.rate_limiter import RateLimiter, get_rate_limiter
from app.services.rag_service import RAGService

# Singleton RAG service instance
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """
    Dependency to get RAG service instance.

    Returns:
        Singleton RAG service
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


# Convenience exports for common dependencies
def get_settings_dep() -> Settings:
    """Get settings dependency."""
    return get_settings()


def get_rate_limiter_dep() -> RateLimiter:
    """Get rate limiter dependency."""
    return get_rate_limiter()


def get_observability_dep() -> ObservabilityManager:
    """Get observability manager dependency."""
    return get_observability_manager()
