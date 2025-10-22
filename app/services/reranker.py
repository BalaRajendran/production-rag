from typing import List
import cohere
from ..core.config import settings
from ..models.models import Chunk, RerankedChunk


class RerankingService:
    """
    Reranks retrieved chunks for better relevance.

    Based on blog learning #2: Reranking
    - Highest value 5 lines of code
    - 50 chunk input -> 15 output (optimal setup)
    - Can compensate for bad setup if enough chunks provided
    """

    def __init__(self):
        self.client = cohere.Client(settings.cohere_api_key)
        self.model = "rerank-english-v3.0"  # Cohere's latest reranker

    async def rerank(
        self,
        query: str,
        chunks: List[Chunk],
        top_k: int = None
    ) -> List[RerankedChunk]:
        """
        Rerank chunks based on relevance to query.

        Args:
            query: The search query
            chunks: List of retrieved chunks
            top_k: Number of top chunks to return (default from settings)

        Returns:
            List of reranked chunks with scores
        """
        if not chunks:
            return []

        top_k = top_k or settings.top_k_rerank

        try:
            # Prepare documents for reranking
            documents = [chunk.text for chunk in chunks]

            # Call Cohere rerank API
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=top_k,
                return_documents=False  # We already have the documents
            )

            # Map reranked results back to chunks
            reranked = []
            for result in response.results:
                original_chunk = chunks[result.index]
                reranked.append(
                    RerankedChunk(
                        chunk=original_chunk,
                        rerank_score=result.relevance_score
                    )
                )

            return reranked

        except Exception as e:
            print(f"Error during reranking: {e}")
            # Fallback: return top chunks by original score
            sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
            return [
                RerankedChunk(chunk=chunk, rerank_score=chunk.score)
                for chunk in sorted_chunks[:top_k]
            ]

    async def rerank_with_metadata(
        self,
        query: str,
        chunks: List[Chunk],
        top_k: int = None
    ) -> List[RerankedChunk]:
        """
        Rerank chunks considering both text and metadata.

        Based on blog learning #4: Metadata to LLM
        """
        if not chunks:
            return []

        # For reranking, we combine chunk text with formatted metadata
        enhanced_chunks = []
        for chunk in chunks:
            text = chunk.text
            if chunk.metadata:
                metadata_str = self._format_metadata(chunk.metadata)
                if metadata_str:
                    text = f"{metadata_str}\n\n{text}"
            enhanced_chunks.append(text)

        top_k = top_k or settings.top_k_rerank

        try:
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=enhanced_chunks,
                top_n=top_k,
                return_documents=False
            )

            reranked = []
            for result in response.results:
                original_chunk = chunks[result.index]
                reranked.append(
                    RerankedChunk(
                        chunk=original_chunk,
                        rerank_score=result.relevance_score
                    )
                )

            return reranked

        except Exception as e:
            print(f"Error during reranking with metadata: {e}")
            sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
            return [
                RerankedChunk(chunk=chunk, rerank_score=chunk.score)
                for chunk in sorted_chunks[:top_k]
            ]

    def _format_metadata(self, metadata: dict) -> str:
        """Format metadata for inclusion in reranking."""
        parts = []
        if "title" in metadata:
            parts.append(f"Title: {metadata['title']}")
        if "author" in metadata:
            parts.append(f"Author: {metadata['author']}")
        if "source" in metadata:
            parts.append(f"Source: {metadata['source']}")

        return " | ".join(parts) if parts else ""
