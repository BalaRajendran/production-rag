"""
RAG query endpoints.

Provides the main RAG query interface with full pipeline support.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.core.observability import get_observability_manager, ObservabilityManager
from app.models.models import QueryRequest, QueryResponse
from app.api.deps import get_rag_service
from app.services.rag_service import RAGService

logger = get_logger(__name__)

router = APIRouter(tags=["RAG"])


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the RAG system",
    description="Execute a RAG query with the full production pipeline"
)
async def query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
    obs_manager: ObservabilityManager = Depends(get_observability_manager)
) -> QueryResponse:
    """
    Query the RAG system.

    This endpoint implements the full production RAG pipeline:

    1. **Query Routing** - Determines the best way to handle the query
    2. **Query Generation** - Creates multiple query variants for better coverage
    3. **Parallel Retrieval** - Searches with all queries simultaneously
    4. **Reranking** - Reranks results using Cohere (50 → 15 chunks)
    5. **Answer Generation** - Uses LLM to generate final answer with metadata

    Args:
        request: Query request with question and optional conversation history
        rag_service: RAG service instance (injected)
        obs_manager: Observability manager (injected)

    Returns:
        QueryResponse with answer, sources, and metadata

    Raises:
        HTTPException: If query processing fails

    Example Request:
        ```json
        {
            "query": "What are the benefits of exercise?",
            "conversation_history": [
                {"role": "user", "content": "Tell me about health"},
                {"role": "assistant", "content": "Health is important..."}
            ]
        }
        ```
    """
    try:
        logger.info("Processing RAG query", query=request.query[:100])

        # Create observability trace if enabled
        trace = None
        if obs_manager.is_enabled():
            trace = obs_manager.create_trace(
                name="RAG Query",
                metadata={"query": request.query[:100]}
            )

        # Execute query
        response = await rag_service.query(request)

        logger.info(
            "RAG query completed successfully",
            query=request.query[:100],
            num_sources=len(response.sources) if response.sources else 0
        )

        return response

    except Exception as e:
        logger.error("RAG query failed", query=request.query[:100], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )
