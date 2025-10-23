"""
Monitoring and statistics endpoints.

Provides system metrics and database statistics.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_rag_service
from app.core.logging import get_logger
from app.services.rag_service import RAGService

logger = get_logger(__name__)

router = APIRouter(tags=["Monitoring"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get vector database statistics",
    description="Retrieve statistics about the vector database",
)
async def get_stats(rag_service: RAGService = Depends(get_rag_service)) -> dict[str, Any]:
    """
    Get vector database statistics.

    Returns:
        Database statistics including vector count and dimensions

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        stats = await rag_service.get_stats()

        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to retrieve statistics",
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get stats: {e!s}"
        ) from e
