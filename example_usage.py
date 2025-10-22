"""
Example usage of the Production RAG Framework.

This script demonstrates how to:
1. Index documents
2. Query the system
3. Use conversation history
4. Handle different query types
"""

import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def check_health():
    """Check if the API is healthy."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print("Health Check:", response.json())
        print()


async def index_sample_documents():
    """Index sample documents about AI and machine learning."""
    documents = [
        {
            "id": "ml-basics-1",
            "content": """
            Machine learning is a subset of artificial intelligence that enables systems to learn
            and improve from experience without being explicitly programmed. It focuses on developing
            computer programs that can access data and use it to learn for themselves.

            The process of learning begins with observations or data, such as examples, direct experience,
            or instruction, in order to look for patterns in data and make better decisions in the future
            based on the examples we provide.
            """,
            "metadata": {
                "title": "Introduction to Machine Learning",
                "author": "Dr. Sarah Johnson",
                "source": "AI Research Papers",
                "date": "2024-01-15"
            }
        },
        {
            "id": "deep-learning-1",
            "content": """
            Deep learning is a subset of machine learning that uses neural networks with multiple layers.
            These deep neural networks attempt to simulate the behavior of the human brain, allowing
            machines to cluster data and make predictions with incredible accuracy.

            Deep learning drives many artificial intelligence applications including computer vision,
            natural language processing, and autonomous vehicles. It has achieved remarkable results
            in image recognition, speech recognition, and language translation.
            """,
            "metadata": {
                "title": "Deep Learning Fundamentals",
                "author": "Prof. Michael Chen",
                "source": "AI Research Papers",
                "date": "2024-02-20"
            }
        },
        {
            "id": "nlp-overview-1",
            "content": """
            Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers
            understand, interpret and manipulate human language. NLP draws from many disciplines, including
            computer science and computational linguistics.

            Modern NLP techniques use machine learning to extract meaning from human languages. Applications
            include sentiment analysis, language translation, chatbots, and text summarization. Recent
            advances in transformer models have revolutionized the field.
            """,
            "metadata": {
                "title": "Natural Language Processing Overview",
                "author": "Dr. Emily Rodriguez",
                "source": "AI Research Papers",
                "date": "2024-03-10"
            }
        },
        {
            "id": "rag-systems-1",
            "content": """
            Retrieval-Augmented Generation (RAG) is an AI framework that combines information retrieval
            with text generation. RAG models retrieve relevant documents from a knowledge base and use
            them to generate more accurate and informative responses.

            The RAG approach has several advantages: it reduces hallucinations by grounding responses in
            actual documents, allows for easy knowledge updates without retraining, and provides source
            attribution for generated answers. Key components include document chunking, embedding models,
            vector databases, and reranking systems.
            """,
            "metadata": {
                "title": "Retrieval-Augmented Generation Systems",
                "author": "Dr. Alex Thompson",
                "source": "AI Research Papers",
                "date": "2024-04-05"
            }
        }
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/index",
            json={"documents": documents}
        )
        result = response.json()
        print("Indexing Result:")
        print(f"  Success: {result['success']}")
        print(f"  Documents processed: {result['documents_processed']}")
        print(f"  Chunks created: {result['chunks_created']}")
        print()


async def simple_query():
    """Perform a simple RAG query."""
    query = "What is machine learning and how does it work?"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={"query": query}
        )
        result = response.json()

        print(f"Query: {query}")
        print(f"\nAnswer: {result['answer']}")
        print(f"\nQuery Type: {result['query_type']}")
        print(f"Generated Queries: {len(result['generated_queries'])}")
        print(f"Retrieved Chunks: {len(result['chunks'])}")
        print()


async def query_with_history():
    """Perform a query with conversation history."""
    conversation_history = [
        {
            "role": "user",
            "content": "What is deep learning?"
        },
        {
            "role": "assistant",
            "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to simulate human brain behavior."
        }
    ]

    query = "How is it used in computer vision?"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={
                "query": query,
                "conversation_history": conversation_history
            }
        )
        result = response.json()

        print("Query with Conversation History:")
        print(f"Query: {query}")
        print(f"\nAnswer: {result['answer']}")
        print(f"\nGenerated Queries ({len(result['generated_queries'])}):")
        for gq in result['generated_queries']:
            print(f"  - [{gq['query_type']}] {gq['query']}")
        print()


async def summarization_query():
    """Test query routing with a summarization request."""
    query = "Summarize the main concepts in AI and machine learning"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={"query": query}
        )
        result = response.json()

        print(f"Summarization Query: {query}")
        print(f"\nQuery Type: {result['query_type']}")
        print(f"\nAnswer: {result['answer']}")
        print()


async def metadata_query():
    """Test query routing with a metadata question."""
    query = "Who are the authors that wrote about NLP?"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={"query": query}
        )
        result = response.json()

        print(f"Metadata Query: {query}")
        print(f"\nQuery Type: {result['query_type']}")
        print(f"\nAnswer: {result['answer']}")
        print()


async def query_with_filters():
    """Query with metadata filters."""
    query = "What did Dr. Sarah Johnson write about?"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/query",
            json={
                "query": query,
                "metadata_filter": {
                    "author": "Dr. Sarah Johnson"
                }
            }
        )
        result = response.json()

        print(f"Filtered Query: {query}")
        print(f"\nAnswer: {result['answer']}")
        print(f"Chunks used: {len(result['chunks'])}")
        print()


async def get_stats():
    """Get vector database statistics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/stats")
        stats = response.json()

        print("Vector Database Stats:")
        print(f"  Total vectors: {stats.get('total_vectors', 'N/A')}")
        print(f"  Dimension: {stats.get('dimension', 'N/A')}")
        print()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Production RAG Framework - Example Usage")
    print("=" * 60)
    print()

    try:
        # 1. Check health
        print("1. Checking API health...")
        await check_health()

        # 2. Index sample documents
        print("2. Indexing sample documents...")
        await index_sample_documents()

        # Wait a bit for indexing to complete
        print("Waiting for indexing to complete...")
        await asyncio.sleep(2)

        # 3. Simple query
        print("3. Simple RAG query...")
        await simple_query()

        # 4. Query with conversation history
        print("4. Query with conversation history...")
        await query_with_history()

        # 5. Summarization query
        print("5. Summarization query (query routing)...")
        await summarization_query()

        # 6. Metadata query
        print("6. Metadata query (query routing)...")
        await metadata_query()

        # 7. Query with filters
        print("7. Query with metadata filters...")
        await query_with_filters()

        # 8. Get stats
        print("8. Getting database statistics...")
        await get_stats()

        print("=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)

    except httpx.ConnectError:
        print("\nError: Could not connect to the API.")
        print("Make sure the server is running:")
        print("  python main.py")
        print()
    except Exception as e:
        print(f"\nError: {e}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
