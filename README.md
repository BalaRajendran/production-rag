# Production RAG Framework

A production-grade RAG (Retrieval-Augmented Generation) framework built with FastAPI and Qdrant, implementing best practices from processing 5M+ documents.

> **🎉 Version 1.1.0** - Updated with restructured codebase, hot reload support, and Qdrant vector database!

## Features

This framework implements all key learnings from production RAG systems:

### 1. **Query Generation** 🎯
- Generates multiple semantic + keyword query variants from conversation context
- Processes queries in parallel for better coverage
- Not dependent on single hybrid search score

### 2. **Reranking** 🏆
- Uses Cohere rerank-english-v3.0
- Optimal setup: 50 chunks input → 15 chunks output
- Significantly improves ranking accuracy

### 3. **Smart Chunking Strategy** 📄
- No mid-word/sentence cuts
- Each chunk is a logical unit
- Captures information standalone
- Configurable chunk size and overlap

### 4. **Metadata Injection** 📝
- Includes title, author, source in chunks
- Improves context and answer quality
- Metadata passed to both reranker and LLM

### 5. **Query Routing** 🔀
- Routes queries to appropriate handlers
- Supports: RAG, Summarization, Metadata queries, General conversation
- Avoids unnecessary RAG pipeline for simple queries

## Architecture

```
┌─────────────┐
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Query Router   │  → Determines handling strategy
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Query Generator │  → Generates multiple query variants
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Vector Search   │  → Parallel search with all queries
│   (Qdrant)      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Reranker      │  → 50 → 15 chunks (Cohere)
│   (Cohere)      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  LLM Generator  │  → Generate final answer
│   (OpenAI)      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│    Answer       │
└─────────────────┘
```

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Vector DB**: Qdrant 1.15.5 (self-hosted)
- **Embeddings**: OpenAI text-embedding-3-large
- **Reranker**: Cohere rerank-english-v3.0
- **LLM**: GPT-4 Turbo
- **Chunking**: Custom implementation with tiktoken

## Project Structure (v1.1.0)

```
production-rag/
├── app/                        # Main application package
│   ├── api/                   # API routes (ready for expansion)
│   ├── core/                  # Configuration
│   │   └── config.py         # Settings from environment
│   ├── models/                # Pydantic models
│   │   └── models.py         # Request/Response schemas
│   ├── services/              # Business logic
│   │   ├── rag_service.py    # Main RAG orchestrator
│   │   ├── vector_store.py   # Qdrant operations
│   │   ├── query_generation.py
│   │   ├── reranker.py
│   │   ├── query_router.py
│   │   ├── llm_service.py
│   │   └── chunking.py
│   └── main.py               # FastAPI application
├── frontend/                  # Frontend (optional)
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker Compose config
├── Dockerfile                 # Docker build config
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed documentation.

## Quick Start (Docker - Recommended)

### 1. Configure environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required environment variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Configuration (auto-configured for Docker)
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=rag_collection

# Cohere Configuration (for reranking)
COHERE_API_KEY=your_cohere_api_key_here
```

### 2. Start services with Docker Compose

```bash
# Start all services (Qdrant + RAG API)
docker compose up -d

# View logs
docker compose logs -f rag-api

# Check status
docker compose ps
```

The API will be available at:
- **API**: `http://localhost:8000`
- **Interactive docs**: `http://localhost:8000/docs`
- **Qdrant UI**: `http://localhost:6333/dashboard`

### 3. Hot Reload Development

Thanks to volume mounts, you can edit code in the `app/` directory and changes will automatically reload without rebuilding:

```bash
# Edit any file in app/
vim app/services/rag_service.py

# Changes automatically reload in container
# No docker compose up --build needed!
```

## Local Development (Without Docker)

### 1. Install dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Qdrant locally

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant:latest

# Or download from https://qdrant.tech/
```

### 3. Run the server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

### Index Documents

```python
import httpx

# Index documents
response = httpx.post("http://localhost:8000/index", json={
    "documents": [
        {
            "id": "doc-1",
            "content": "Your document content here...",
            "metadata": {
                "title": "Document Title",
                "author": "Author Name",
                "source": "source.com",
                "date": "2024-01-01"
            }
        }
    ]
})

print(response.json())
```

### Query the System

```python
# Simple query
response = httpx.post("http://localhost:8000/query", json={
    "query": "What are the main benefits of exercise?"
})

print(response.json()["answer"])

# Query with conversation history
response = httpx.post("http://localhost:8000/query", json={
    "query": "Tell me more about the cardiovascular benefits",
    "conversation_history": [
        {"role": "user", "content": "What are the main benefits of exercise?"},
        {"role": "assistant", "content": "Exercise has many benefits including..."}
    ]
})

print(response.json())
```

### Query with Filters

```python
# Filter by metadata
response = httpx.post("http://localhost:8000/query", json={
    "query": "What does the research say?",
    "metadata_filter": {
        "author": "Dr. Smith"
    },
    "top_k": 20
})
```

## API Endpoints

### `POST /query`
Query the RAG system with full pipeline.

**Request:**
```json
{
  "query": "Your question here",
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ],
  "top_k": 15,
  "metadata_filter": {"author": "John Doe"}
}
```

**Response:**
```json
{
  "answer": "Generated answer here...",
  "chunks": [...],
  "generated_queries": [...],
  "query_type": "rag",
  "metadata": {}
}
```

### `POST /index`
Index new documents.

**Request:**
```json
{
  "documents": [
    {
      "id": "unique-doc-id",
      "content": "Document content...",
      "metadata": {
        "title": "Title",
        "author": "Author"
      }
    }
  ]
}
```

### `DELETE /documents/{document_id}`
Delete a document and all its chunks.

### `GET /stats`
Get vector database statistics.

### `GET /health`
Health check endpoint.

## Configuration

Key configuration options in `.env`:

```env
# Chunking
CHUNK_SIZE=512                # Tokens per chunk
CHUNK_OVERLAP=50             # Overlap between chunks

# Retrieval
TOP_K_RETRIEVAL=50           # Chunks to retrieve before reranking
TOP_K_RERANK=15              # Chunks after reranking

# Query Generation
MAX_QUERIES_GENERATED=5      # Max query variants to generate

# Models
EMBEDDING_MODEL=text-embedding-3-large
LLM_MODEL=gpt-4-turbo-preview
```

## Performance Tips

1. **Optimal Reranking**: Keep 50 → 15 ratio for best results
2. **Chunk Size**: 512 tokens works well for most cases
3. **Query Generation**: 3-5 variants provide good coverage
4. **Metadata**: Always include title, author, source when available
5. **Conversation History**: Include last 5 messages for context

## Query Routing Examples

The system automatically routes queries:

- **RAG Query**: "What are the benefits of regular exercise?"
  - Uses full RAG pipeline

- **Summarization**: "Summarize the main findings"
  - Retrieves content and generates summary

- **Metadata Query**: "Who wrote this document?"
  - Queries metadata directly

- **General**: "Hello, how are you?"
  - Direct LLM response without retrieval

## Development

### Project Structure

```
production-rag/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── models.py              # Pydantic models
├── services/
│   ├── rag_service.py     # Main RAG orchestration
│   ├── vector_store.py    # Pinecone integration
│   ├── query_generation.py # Query variant generation
│   ├── reranker.py        # Cohere reranking
│   ├── query_router.py    # Query routing logic
│   ├── llm_service.py     # LLM interactions
│   └── chunking.py        # Document chunking
├── pyproject.toml         # Dependencies (uv)
├── .env.example           # Environment template
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
uv pip install pytest httpx pytest-asyncio

# Run tests (coming soon)
pytest
```

## Troubleshooting

### Import errors
The import warnings in the IDE are normal before installing dependencies. Run:
```bash
uv pip install -e .
```

### Pinecone connection issues
- Verify your API key and environment
- Check that your index exists or will be auto-created
- Ensure you're using serverless Pinecone

### Cohere rate limits
- Free tier has rate limits
- Consider caching reranking results
- Upgrade to paid tier for production

### OpenAI rate limits
- Use batch processing for indexing
- Implement exponential backoff
- Monitor token usage

## License

MIT

## Credits

Based on learnings from processing 5M+ documents. Inspired by the blog post "Production RAG: what I learned from processing 5M+ documents".
