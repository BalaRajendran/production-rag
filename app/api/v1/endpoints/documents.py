"""
Document management endpoints.

Provides CRUD operations for documents in the RAG system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.core.logging import get_logger
from app.models.models import IndexRequest, IndexResponse
from app.api.deps import get_rag_service
from app.services.rag_service import RAGService

logger = get_logger(__name__)

router = APIRouter(tags=["Document Management"])


@router.post(
    "/index",
    response_model=IndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Index documents",
    description="Add documents to the RAG system with chunking and embedding"
)
async def index_documents(
    request: IndexRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> IndexResponse:
    """
    Index documents into the RAG system.

    This endpoint:
    1. **Chunks documents** using smart chunking strategy
    2. **Injects metadata** into chunks for better context
    3. **Generates embeddings** using text-embedding-3-large
    4. **Stores in Qdrant** for fast retrieval

    Args:
        request: Index request with documents to add
        rag_service: RAG service instance (injected)

    Returns:
        IndexResponse with indexing status

    Raises:
        HTTPException: If indexing fails

    Example Request:
        ```json
        {
            "documents": [
                {
                    "id": "doc-1",
                    "content": "Document content here...",
                    "metadata": {
                        "title": "My Document",
                        "author": "John Doe",
                        "source": "example.com"
                    }
                }
            ]
        }
        ```
    """
    try:
        logger.info("Indexing documents", num_documents=len(request.documents))

        response = await rag_service.index_documents(request)

        logger.info(
            "Documents indexed successfully",
            num_documents=len(request.documents)
        )

        return response

    except Exception as e:
        logger.error("Document indexing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete document",
    description="Delete a document and all its chunks from the system"
)
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Delete a document and all its chunks.

    Args:
        document_id: Unique document identifier
        rag_service: RAG service instance (injected)

    Returns:
        Deletion status

    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        logger.info("Deleting document", document_id=document_id)

        success = await rag_service.delete_document(document_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        logger.info("Document deleted successfully", document_id=document_id)

        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document deletion failed", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )
