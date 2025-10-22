from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class QueryType(str, Enum):
    """Types of queries that can be routed."""
    RAG = "rag"
    SUMMARIZATION = "summarization"
    METADATA_QUERY = "metadata_query"
    GENERAL = "general"


class Message(BaseModel):
    """Chat message in a conversation thread."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    query: str = Field(..., description="The user's question")
    conversation_history: Optional[List[Message]] = Field(
        default=None,
        description="Previous conversation messages for context"
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Number of results to return (overrides default)"
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata filters for retrieval"
    )


class GeneratedQuery(BaseModel):
    """A generated query variant."""
    query: str = Field(..., description="The generated query text")
    query_type: str = Field(..., description="Type: semantic or keyword")


class Chunk(BaseModel):
    """Retrieved document chunk."""
    id: str = Field(..., description="Unique chunk identifier")
    text: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class RerankedChunk(BaseModel):
    """Chunk after reranking."""
    chunk: Chunk
    rerank_score: float = Field(..., description="Reranking score")


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str = Field(..., description="Generated answer")
    chunks: List[Chunk] = Field(..., description="Retrieved and reranked chunks used")
    generated_queries: List[GeneratedQuery] = Field(
        default_factory=list,
        description="Queries generated from conversation"
    )
    query_type: QueryType = Field(..., description="Type of query processed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata"
    )


class Document(BaseModel):
    """Document to be indexed."""
    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (title, author, etc.)"
    )


class IndexRequest(BaseModel):
    """Request model for indexing documents."""
    documents: List[Document] = Field(..., description="Documents to index")


class IndexResponse(BaseModel):
    """Response model for indexing operation."""
    success: bool = Field(..., description="Whether indexing succeeded")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    pinecone_connected: bool = Field(..., description="Pinecone connection status")
    openai_configured: bool = Field(..., description="OpenAI configuration status")
    cohere_configured: bool = Field(..., description="Cohere configuration status")
