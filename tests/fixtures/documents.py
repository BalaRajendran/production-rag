"""
Sample documents and test data for testing.

Provides reusable test data for document indexing and retrieval tests.
"""

# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "id": "doc-python-1",
        "content": """
        Python is a high-level, interpreted programming language known for its simplicity and readability.
        It was created by Guido van Rossum and first released in 1991. Python supports multiple programming
        paradigms including procedural, object-oriented, and functional programming. It has a comprehensive
        standard library and a large ecosystem of third-party packages available through PyPI.
        """,
        "metadata": {
            "title": "Introduction to Python",
            "author": "Tech Writer",
            "category": "programming",
            "language": "python",
            "difficulty": "beginner",
        },
    },
    {
        "id": "doc-fastapi-1",
        "content": """
        FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard
        Python type hints. It's one of the fastest Python frameworks available, thanks to Starlette
        and Pydantic. FastAPI provides automatic interactive API documentation using Swagger UI and
        ReDoc. It includes built-in data validation, serialization, and async support out of the box.
        """,
        "metadata": {
            "title": "FastAPI Framework Overview",
            "author": "API Expert",
            "category": "web-development",
            "framework": "fastapi",
            "difficulty": "intermediate",
        },
    },
    {
        "id": "doc-redis-1",
        "content": """
        Redis is an open-source, in-memory data structure store used as a database, cache, and message
        broker. It supports various data structures such as strings, hashes, lists, sets, and sorted sets.
        Redis is known for its exceptional performance, handling millions of requests per second. It's
        commonly used for session management, real-time analytics, caching, and pub/sub messaging.
        """,
        "metadata": {
            "title": "Redis Data Store",
            "author": "Database Admin",
            "category": "database",
            "type": "nosql",
            "difficulty": "intermediate",
        },
    },
    {
        "id": "doc-rag-1",
        "content": """
        Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with
        large language models to generate more accurate and contextually relevant responses. RAG systems
        first retrieve relevant documents from a knowledge base using vector similarity search, then use
        those documents as context for generating responses. This approach reduces hallucinations and
        provides more factual, grounded answers compared to standalone language models.
        """,
        "metadata": {
            "title": "RAG Systems Explained",
            "author": "AI Researcher",
            "category": "artificial-intelligence",
            "topic": "rag",
            "difficulty": "advanced",
        },
    },
    {
        "id": "doc-vector-db-1",
        "content": """
        Vector databases are specialized databases designed to store and query high-dimensional vectors
        efficiently. They use techniques like approximate nearest neighbor (ANN) search algorithms to
        quickly find similar vectors. Popular vector databases include Pinecone, Qdrant, Weaviate, and
        Milvus. These databases are essential for applications like semantic search, recommendation
        systems, and RAG (Retrieval-Augmented Generation) pipelines.
        """,
        "metadata": {
            "title": "Vector Databases Introduction",
            "author": "Data Engineer",
            "category": "database",
            "type": "vector-db",
            "difficulty": "advanced",
        },
    },
]

# Minimal document for basic tests
MINIMAL_DOCUMENT = {
    "id": "minimal-1",
    "content": "This is a minimal test document.",
    "metadata": {"title": "Minimal Test"},
}

# Document with long content
LONG_DOCUMENT = {
    "id": "long-doc-1",
    "content": " ".join([f"This is sentence number {i}." for i in range(1, 501)]),
    "metadata": {"title": "Long Document", "length": "500_sentences"},
}

# Document with special characters
SPECIAL_CHARS_DOCUMENT = {
    "id": "special-1",
    "content": 'Document with special chars: @#$%^&*()_+-={}[]|\\:";<>?,./`~',
    "metadata": {"title": "Special Characters Test"},
}

# Document with multilingual content
MULTILINGUAL_DOCUMENT = {
    "id": "multilingual-1",
    "content": "Hello! Bonjour! Hola! Привет! 你好! こんにちは! مرحبا! नमस्ते!",
    "metadata": {"title": "Multilingual Greetings", "languages": "multiple"},
}

# Sample queries for testing
SAMPLE_QUERIES = [
    "What is Python programming?",
    "How does FastAPI work?",
    "Tell me about Redis",
    "Explain RAG systems",
    "What are vector databases?",
]

# Sample conversation history
SAMPLE_CONVERSATION = [
    {"role": "user", "content": "What programming languages should I learn?"},
    {
        "role": "assistant",
        "content": "Python is a great language to start with due to its simplicity.",
    },
    {"role": "user", "content": "Tell me more about Python"},
]

# Expected chunks (for chunking tests)
EXPECTED_CHUNKS_PYTHON = [
    "Python is a high-level, interpreted programming language known for its simplicity and readability.",
    "It was created by Guido van Rossum and first released in 1991.",
    # ... more chunks based on chunk_size
]

# Test data for error cases
INVALID_DOCUMENTS = [
    {"id": "invalid-1"},  # Missing content
    {"content": "No ID provided"},  # Missing ID
    {},  # Empty document
    {"id": "", "content": ""},  # Empty strings
]

# Mock API responses
MOCK_OPENAI_EMBEDDING = {
    "data": [{"embedding": [0.1] * 3072, "index": 0}],  # 3072-dimensional vector
    "usage": {"prompt_tokens": 10, "total_tokens": 10},
}

MOCK_OPENAI_COMPLETION = {
    "choices": [
        {
            "message": {
                "content": "This is a test response from the language model.",
                "role": "assistant",
            },
            "finish_reason": "stop",
            "index": 0,
        }
    ],
    "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
}

MOCK_COHERE_RERANK = {
    "results": [
        {"index": 0, "relevance_score": 0.95},
        {"index": 2, "relevance_score": 0.85},
        {"index": 1, "relevance_score": 0.75},
    ]
}

# Mock Qdrant responses
MOCK_QDRANT_SEARCH_RESULTS = [
    {
        "id": "chunk-1",
        "score": 0.95,
        "payload": {
            "text": "Python is a high-level programming language.",
            "document_id": "doc-python-1",
            "metadata": {"title": "Introduction to Python"},
        },
    },
    {
        "id": "chunk-2",
        "score": 0.85,
        "payload": {
            "text": "FastAPI is a modern web framework.",
            "document_id": "doc-fastapi-1",
            "metadata": {"title": "FastAPI Framework"},
        },
    },
]

# Expected API responses
EXPECTED_QUERY_RESPONSE = {
    "answer": "Based on the retrieved documents, Python is a high-level programming language...",
    "sources": [
        {
            "document_id": "doc-python-1",
            "chunk_id": "chunk-1",
            "text": "Python is a high-level programming language.",
            "score": 0.95,
            "metadata": {"title": "Introduction to Python"},
        }
    ],
    "metadata": {
        "num_sources": 1,
        "retrieval_time": 0.05,
        "generation_time": 0.15,
        "total_time": 0.20,
    },
}

EXPECTED_INDEX_RESPONSE = {
    "success": True,
    "documents_indexed": 5,
    "chunks_created": 15,
    "message": "Successfully indexed 5 documents",
}

# Rate limiting test data
RATE_LIMIT_TEST_CASES = [
    {"identifier": "user-1", "requests": 10, "should_pass": True},
    {"identifier": "user-2", "requests": 100, "should_pass": False},  # Exceeds limit
    {"identifier": "ip:192.168.1.1", "requests": 50, "should_pass": True},
]
