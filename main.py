from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from models import (
    QueryRequest, QueryResponse,
    IndexRequest, IndexResponse,
    HealthResponse
)
from services.rag_service import RAGService


# Initialize RAG service
rag_service = RAGService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    print("Initializing Production RAG Framework...")
    await rag_service.initialize()
    print("RAG Framework ready!")
    yield
    print("Shutting down RAG Framework...")


# Create FastAPI app
app = FastAPI(
    title="Production RAG Framework",
    description="Production-grade RAG system with query generation, reranking, and smart routing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Production RAG Framework",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns system status and service connectivity.
    """
    try:
        # Check Pinecone connection
        pinecone_connected = False
        try:
            stats = await rag_service.get_stats()
            pinecone_connected = stats is not None
        except Exception:
            pass

        return HealthResponse(
            status="healthy" if pinecone_connected else "degraded",
            pinecone_connected=pinecone_connected,
            openai_configured=bool(settings.openai_api_key),
            cohere_configured=bool(settings.cohere_api_key)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Query the RAG system.

    This endpoint implements the full production RAG pipeline:

    1. **Query Routing** - Determines the best way to handle the query
    2. **Query Generation** - Creates multiple query variants for better coverage
    3. **Parallel Retrieval** - Searches with all queries simultaneously
    4. **Reranking** - Reranks results using Cohere (50 ’ 15 chunks)
    5. **Answer Generation** - Uses LLM to generate final answer with metadata

    Args:
        request: Query request with question and optional conversation history

    Returns:
        QueryResponse with answer, sources, and metadata

    Example:
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
        response = await rag_service.query(request)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@app.post("/index", response_model=IndexResponse, tags=["Document Management"])
async def index_documents(request: IndexRequest):
    """
    Index documents into the RAG system.

    This endpoint:
    1. **Chunks documents** using smart chunking strategy
    2. **Injects metadata** into chunks for better context
    3. **Generates embeddings** using text-embedding-3-large
    4. **Stores in Pinecone** for fast retrieval

    Args:
        request: Index request with documents to add

    Returns:
        IndexResponse with indexing status

    Example:
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
        response = await rag_service.index_documents(request)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@app.delete("/documents/{document_id}", tags=["Document Management"])
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks.

    Args:
        document_id: Unique document identifier

    Returns:
        Deletion status
    """
    try:
        success = await rag_service.delete_document(document_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@app.get("/stats", tags=["Monitoring"])
async def get_stats():
    """
    Get vector database statistics.

    Returns:
        Database statistics including vector count and dimensions
    """
    try:
        stats = await rag_service.get_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
