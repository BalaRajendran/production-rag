from typing import List, Dict, Any
from ..models.models import (
    QueryRequest, QueryResponse, Chunk, QueryType,
    GeneratedQuery, IndexRequest, IndexResponse, Document
)
from .vector_store import VectorStoreService
from .query_generation import QueryGenerationService
from .reranker import RerankingService
from .query_router import QueryRouter
from .llm_service import LLMService
from .chunking import ChunkingService


class RAGService:
    """
    Main RAG orchestration service.

    Implements production RAG pipeline based on blog learnings:
    1. Query Generation - Generate multiple query variants
    2. Reranking - Rerank retrieved chunks
    3. Chunking Strategy - Smart document chunking
    4. Metadata to LLM - Include metadata for better context
    5. Query routing - Route queries to appropriate handlers
    """

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.query_generator = QueryGenerationService()
        self.reranker = RerankingService()
        self.query_router = QueryRouter()
        self.llm = LLMService()
        self.chunker = ChunkingService()

    async def initialize(self):
        """Initialize all services."""
        await self.vector_store.initialize()

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Execute RAG query pipeline.

        Pipeline:
        1. Route query to determine handling strategy
        2. Generate multiple query variants (if RAG)
        3. Search vector database with all queries in parallel
        4. Rerank results
        5. Generate answer using LLM

        Args:
            request: Query request with query and optional history

        Returns:
            Query response with answer and sources
        """
        # Step 1: Route query
        query_type, routing_explanation = await self.query_router.route_query(
            request.query
        )

        print(f"Query routed to: {query_type} - {routing_explanation}")

        # Handle non-RAG queries
        if query_type == QueryType.SUMMARIZATION:
            return await self._handle_summarization(request)

        elif query_type == QueryType.METADATA_QUERY:
            return await self._handle_metadata_query(request)

        elif query_type == QueryType.GENERAL:
            return await self._handle_general_query(request)

        # Handle RAG query
        return await self._handle_rag_query(request)

    async def _handle_rag_query(self, request: QueryRequest) -> QueryResponse:
        """
        Handle standard RAG query with full pipeline.
        """
        # Step 2: Generate multiple query variants
        generated_queries = await self.query_generator.generate_queries(
            request.query,
            request.conversation_history
        )

        print(f"Generated {len(generated_queries)} query variants")

        # Step 3: Search with all queries in parallel
        query_strings = [gq.query for gq in generated_queries]

        chunks = await self.vector_store.search_multiple_queries(
            queries=query_strings,
            top_k=request.top_k,
            metadata_filter=request.metadata_filter
        )

        print(f"Retrieved {len(chunks)} chunks before reranking")

        if not chunks:
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question.",
                chunks=[],
                generated_queries=generated_queries,
                query_type=QueryType.RAG,
                metadata={"message": "No chunks found"}
            )

        # Step 4: Rerank chunks
        reranked = await self.reranker.rerank_with_metadata(
            query=request.query,
            chunks=chunks,
            top_k=request.top_k
        )

        print(f"Reranked to {len(reranked)} chunks")

        # Extract chunks from reranked results
        final_chunks = [r.chunk for r in reranked]

        # Step 5: Generate answer
        answer = await self.llm.generate_answer(
            query=request.query,
            chunks=final_chunks,
            conversation_history=request.conversation_history
        )

        return QueryResponse(
            answer=answer,
            chunks=final_chunks,
            generated_queries=generated_queries,
            query_type=QueryType.RAG,
            metadata={
                "chunks_before_rerank": len(chunks),
                "chunks_after_rerank": len(final_chunks)
            }
        )

    async def _handle_summarization(
        self,
        request: QueryRequest
    ) -> QueryResponse:
        """
        Handle summarization queries.

        Based on blog learning #5: Query routing
        """
        # Search for relevant content
        chunks = await self.vector_store.search(
            query=request.query,
            top_k=10  # Get more chunks for summarization
        )

        if not chunks:
            return QueryResponse(
                answer="I couldn't find any content to summarize.",
                chunks=[],
                generated_queries=[],
                query_type=QueryType.SUMMARIZATION,
                metadata={"message": "No content found"}
            )

        # Combine chunk text
        content = "\n\n".join([chunk.text for chunk in chunks])

        # Generate summary
        answer = await self.llm.generate_summarization(
            content=content,
            instruction=request.query
        )

        return QueryResponse(
            answer=answer,
            chunks=chunks,
            generated_queries=[],
            query_type=QueryType.SUMMARIZATION,
            metadata={"chunks_used": len(chunks)}
        )

    async def _handle_metadata_query(
        self,
        request: QueryRequest
    ) -> QueryResponse:
        """
        Handle metadata queries (author, date, etc.).

        Based on blog learning #5: Query routing
        """
        # Search for relevant documents
        chunks = await self.vector_store.search(
            query=request.query,
            top_k=20  # Get more for metadata queries
        )

        if not chunks:
            return QueryResponse(
                answer="I couldn't find any relevant documents.",
                chunks=[],
                generated_queries=[],
                query_type=QueryType.METADATA_QUERY,
                metadata={"message": "No documents found"}
            )

        # Generate answer based on metadata
        answer = await self.llm.answer_metadata_query(
            query=request.query,
            chunks=chunks
        )

        return QueryResponse(
            answer=answer,
            chunks=chunks[:5],  # Return fewer chunks
            generated_queries=[],
            query_type=QueryType.METADATA_QUERY,
            metadata={"documents_analyzed": len(chunks)}
        )

    async def _handle_general_query(
        self,
        request: QueryRequest
    ) -> QueryResponse:
        """
        Handle general conversational queries.
        """
        # For general queries, use LLM without RAG
        messages = []
        if request.conversation_history:
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        messages.append({"role": "user", "content": request.query})

        answer = await self.llm.generate_answer(
            query=request.query,
            chunks=[],
            conversation_history=request.conversation_history
        )

        return QueryResponse(
            answer=answer,
            chunks=[],
            generated_queries=[],
            query_type=QueryType.GENERAL,
            metadata={"message": "General conversation"}
        )

    async def index_documents(
        self,
        request: IndexRequest,
        namespace: str = ""
    ) -> IndexResponse:
        """
        Index documents into vector database.

        Pipeline:
        1. Chunk documents with metadata injection
        2. Generate embeddings
        3. Store in Pinecone

        Args:
            request: Index request with documents
            namespace: Optional namespace for isolation

        Returns:
            Index response with status
        """
        total_chunks = 0

        try:
            for document in request.documents:
                # Chunk document with metadata injection
                chunks = self.chunker.chunk_with_metadata_injection(
                    text=document.content,
                    metadata=document.metadata
                )

                if not chunks:
                    continue

                # Index chunks
                chunks_indexed = await self.vector_store.index_chunks(
                    chunks=chunks,
                    document_id=document.id,
                    namespace=namespace
                )

                total_chunks += chunks_indexed

                print(f"Indexed {chunks_indexed} chunks for document {document.id}")

            return IndexResponse(
                success=True,
                documents_processed=len(request.documents),
                chunks_created=total_chunks,
                message=f"Successfully indexed {len(request.documents)} documents"
            )

        except Exception as e:
            print(f"Error indexing documents: {e}")
            return IndexResponse(
                success=False,
                documents_processed=0,
                chunks_created=0,
                message=f"Error indexing documents: {str(e)}"
            )

    async def delete_document(
        self,
        document_id: str,
        namespace: str = ""
    ) -> bool:
        """Delete document and all its chunks."""
        return await self.vector_store.delete_document(document_id, namespace)

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return await self.vector_store.get_stats()
