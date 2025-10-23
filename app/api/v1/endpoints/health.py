"""
Health check endpoints.

Provides health status and readiness checks for the application.
"""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.deps import get_rag_service
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.models import HealthResponse
from app.services.rag_service import RAGService

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the application and its dependencies",
)
async def health_check(
    settings: Settings = Depends(get_settings), rag_service: RAGService = Depends(get_rag_service)
) -> HealthResponse:
    """
    Health check endpoint.

    Returns system status and service connectivity.

    Returns:
        HealthResponse with status and service availability
    """
    # Check Qdrant connection
    qdrant_connected = False
    try:
        stats = await rag_service.get_stats()
        qdrant_connected = stats is not None
    except Exception as e:
        logger.warning("Qdrant health check failed", error=str(e))

    # Determine overall status
    is_healthy = qdrant_connected

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        pinecone_connected=qdrant_connected,  # Note: Using qdrant but keeping model field name for compatibility
        openai_configured=bool(settings.llm.openai_api_key),
        cohere_configured=bool(settings.llm.cohere_api_key),
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the application is ready to serve requests",
)
async def readiness_check(rag_service: RAGService = Depends(get_rag_service)) -> dict[str, Any]:
    """
    Readiness check endpoint.

    Returns whether the application is ready to handle requests.
    Used by Kubernetes/orchestration systems.

    Returns:
        Dict with ready status
    """
    try:
        # Check if vector DB is accessible
        stats = await rag_service.get_stats()
        ready = stats is not None

        return {
            "ready": ready,
            "message": "Application is ready" if ready else "Application is not ready",
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"ready": False, "message": f"Readiness check failed: {e!s}"}


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if the application is alive",
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness check endpoint.

    Simple check that the application is running.
    Used by Kubernetes/orchestration systems.

    Returns:
        Dict with alive status
    """
    return {"status": "alive"}
