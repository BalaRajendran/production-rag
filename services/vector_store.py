from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from openai import AsyncOpenAI
import hashlib
from config import settings
from models import Chunk
import asyncio


class VectorStoreService:
    """
    Handles vector database operations with Qdrant.

    Features:
    - Document embedding and indexing
    - Hybrid search (semantic + keyword)
    - Metadata filtering
    - Batch processing
    """

    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.collection_name = settings.qdrant_collection_name
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model

    async def initialize(self):
        """Initialize Qdrant collection."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]

            if self.collection_name not in collection_names:
                # Create collection if it doesn't exist
                # text-embedding-3-large has 3072 dimensions
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=3072,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: {self.collection_name}")
            else:
                print(f"Connected to Qdrant collection: {self.collection_name}")

        except Exception as e:
            print(f"Error initializing Qdrant: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using OpenAI.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise

    async def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_id: str,
        namespace: str = ""
    ) -> int:
        """
        Index document chunks into Qdrant.

        Args:
            chunks: List of chunks with text and metadata
            document_id: Unique document identifier
            namespace: Optional namespace for isolation (stored as metadata)

        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0

        # Ensure collection exists
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            await self.initialize()

        # Prepare chunks for indexing
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embed_texts(texts)

        # Create points with metadata
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = self._generate_chunk_id(document_id, i)

            metadata = chunk.get("metadata", {}).copy()
            metadata.update({
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk["text"],  # Store text in metadata for retrieval
                "token_count": chunk.get("token_count", 0)
            })

            # Add namespace to metadata if provided
            if namespace:
                metadata["namespace"] = namespace

            points.append(
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload=metadata
                )
            )

        # Batch upsert to Qdrant
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )

        return len(points)

    async def search(
        self,
        query: str,
        top_k: int = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        namespace: str = ""
    ) -> List[Chunk]:
        """
        Search for similar chunks using semantic search.

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Optional metadata filters
            namespace: Optional namespace for isolation

        Returns:
            List of matching chunks
        """
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            await self.initialize()

        top_k = top_k or settings.top_k_retrieval

        # Generate query embedding
        query_embeddings = await self.embed_texts([query])
        query_embedding = query_embeddings[0]

        # Build filter
        query_filter = None
        if metadata_filter or namespace:
            conditions = []

            # Add namespace filter if provided
            if namespace:
                conditions.append(
                    FieldCondition(
                        key="namespace",
                        match=MatchValue(value=namespace)
                    )
                )

            # Add custom metadata filters
            if metadata_filter:
                for key, value in metadata_filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )

            if conditions:
                query_filter = Filter(must=conditions)

        # Search Qdrant
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter
            )

            # Convert to Chunk objects
            chunks = []
            for result in results:
                payload = result.payload.copy()
                text = payload.pop("text", "")

                chunk = Chunk(
                    id=str(result.id),
                    text=text,
                    score=result.score,
                    metadata=payload
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            return []

    async def search_multiple_queries(
        self,
        queries: List[str],
        top_k: int = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        namespace: str = ""
    ) -> List[Chunk]:
        """
        Search with multiple queries in parallel and combine results.

        Based on blog learning #1: Query Generation
        - Process all queries in parallel
        - Combine and deduplicate results
        """
        if not queries:
            return []

        # Search all queries in parallel
        search_tasks = [
            self.search(query, top_k, metadata_filter, namespace)
            for query in queries
        ]

        results = await asyncio.gather(*search_tasks)

        # Combine and deduplicate results
        seen_ids = set()
        combined_chunks = []

        for chunk_list in results:
            for chunk in chunk_list:
                if chunk.id not in seen_ids:
                    seen_ids.add(chunk.id)
                    combined_chunks.append(chunk)

        # Sort by score
        combined_chunks.sort(key=lambda x: x.score, reverse=True)

        # Return top_k after deduplication
        top_k = top_k or settings.top_k_retrieval
        return combined_chunks[:top_k]

    async def delete_document(
        self,
        document_id: str,
        namespace: str = ""
    ) -> bool:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document identifier
            namespace: Optional namespace

        Returns:
            True if successful
        """
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            await self.initialize()

        try:
            # Build filter for deletion
            conditions = [
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]

            if namespace:
                conditions.append(
                    FieldCondition(
                        key="namespace",
                        match=MatchValue(value=namespace)
                    )
                )

            delete_filter = Filter(must=conditions)

            # Delete by filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=delete_filter
            )
            return True

        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """Generate unique chunk ID."""
        content = f"{document_id}_{chunk_index}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            await self.initialize()

        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "total_vectors": collection_info.points_count,
                "dimension": collection_info.config.params.vectors.size,
                "status": collection_info.status
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
