# Complete API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production, implement JWT/OAuth2.

---

## Endpoints

### 1. Root Endpoint

Get basic API information.

**Request:**
```http
GET /
```

**Response:**
```json
{
  "message": "Production RAG Framework",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

**Status Codes:**
- `200` - Success

---

### 2. Health Check

Check system health and service connectivity.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "pinecone_connected": true,
  "openai_configured": true,
  "cohere_configured": true
}
```

**Response Fields:**
- `status` (string): `"healthy"` or `"degraded"`
- `pinecone_connected` (boolean): Pinecone connection status
- `openai_configured` (boolean): OpenAI API key configured
- `cohere_configured` (boolean): Cohere API key configured

**Status Codes:**
- `200` - System healthy or degraded
- `503` - Service unavailable

**Example (cURL):**
```bash
curl http://localhost:8000/health
```

**Example (Python):**
```python
import httpx

response = httpx.get("http://localhost:8000/health")
print(response.json())
```

---

### 3. Query RAG System

Execute a RAG query with full pipeline processing.

**Request:**
```http
POST /query
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What are the benefits of exercise?",
  "conversation_history": [
    {
      "role": "user",
      "content": "Tell me about health"
    },
    {
      "role": "assistant",
      "content": "Health is important for wellbeing..."
    }
  ],
  "top_k": 15,
  "metadata_filter": {
    "author": "Dr. Smith",
    "source": "medical-journal"
  }
}
```

**Request Fields:**
- `query` (string, required): The user's question
- `conversation_history` (array, optional): Previous conversation messages
  - Each message has `role` (string) and `content` (string)
- `top_k` (integer, optional): Number of chunks to return (default: 15)
- `metadata_filter` (object, optional): Filter by document metadata

**Response:**
```json
{
  "answer": "Exercise provides numerous benefits including improved cardiovascular health...",
  "chunks": [
    {
      "id": "abc123",
      "text": "Regular exercise strengthens the heart...",
      "score": 0.95,
      "metadata": {
        "title": "Exercise Benefits",
        "author": "Dr. Smith",
        "source": "medical-journal",
        "document_id": "doc-1",
        "chunk_index": 0
      }
    }
  ],
  "generated_queries": [
    {
      "query": "What are the benefits of exercise?",
      "query_type": "semantic"
    },
    {
      "query": "exercise benefits health advantages",
      "query_type": "keyword"
    }
  ],
  "query_type": "rag",
  "metadata": {
    "chunks_before_rerank": 50,
    "chunks_after_rerank": 15
  }
}
```

**Response Fields:**
- `answer` (string): Generated answer
- `chunks` (array): Retrieved and reranked source chunks
  - `id` (string): Chunk identifier
  - `text` (string): Chunk content
  - `score` (float): Relevance score
  - `metadata` (object): Chunk metadata
- `generated_queries` (array): Query variants generated
  - `query` (string): Query text
  - `query_type` (string): "semantic" or "keyword"
- `query_type` (string): Type of query processed
  - `"rag"` - Standard RAG query
  - `"summarization"` - Summary request
  - `"metadata_query"` - Metadata question
  - `"general"` - General conversation
- `metadata` (object): Additional response metadata

**Status Codes:**
- `200` - Success
- `422` - Validation error
- `500` - Internal server error

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?"
  }'
```

**Example (Python):**
```python
import httpx

response = httpx.post(
    "http://localhost:8000/query",
    json={
        "query": "What is machine learning?",
        "conversation_history": [
            {"role": "user", "content": "Tell me about AI"},
            {"role": "assistant", "content": "AI is..."}
        ]
    }
)

result = response.json()
print(result["answer"])
print(f"Sources: {len(result['chunks'])} chunks")
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What is machine learning?'
  })
});

const result = await response.json();
console.log(result.answer);
```

---

### 4. Index Documents

Index new documents into the RAG system.

**Request:**
```http
POST /index
Content-Type: application/json
```

**Request Body:**
```json
{
  "documents": [
    {
      "id": "doc-1",
      "content": "Machine learning is a subset of artificial intelligence...",
      "metadata": {
        "title": "Introduction to ML",
        "author": "Dr. Sarah Johnson",
        "source": "ai-research.com",
        "date": "2024-01-15",
        "category": "education"
      }
    },
    {
      "id": "doc-2",
      "content": "Deep learning uses neural networks...",
      "metadata": {
        "title": "Deep Learning Basics",
        "author": "Prof. Michael Chen",
        "source": "ai-research.com",
        "date": "2024-02-20"
      }
    }
  ]
}
```

**Request Fields:**
- `documents` (array, required): List of documents to index
  - `id` (string, required): Unique document identifier
  - `content` (string, required): Document text content
  - `metadata` (object, optional): Document metadata
    - Common fields: `title`, `author`, `source`, `date`, `category`
    - Any custom fields are supported

**Response:**
```json
{
  "success": true,
  "documents_processed": 2,
  "chunks_created": 45,
  "message": "Successfully indexed 2 documents"
}
```

**Response Fields:**
- `success` (boolean): Whether indexing succeeded
- `documents_processed` (integer): Number of documents processed
- `chunks_created` (integer): Total chunks created and indexed
- `message` (string): Status message

**Status Codes:**
- `200` - Success
- `422` - Validation error
- `500` - Indexing failed

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "id": "doc-1",
      "content": "Document content here...",
      "metadata": {
        "title": "My Document",
        "author": "John Doe"
      }
    }]
  }'
```

**Example (Python):**
```python
import httpx

documents = [
    {
        "id": "ml-guide-1",
        "content": "Machine learning is...",
        "metadata": {
            "title": "ML Guide",
            "author": "Dr. Smith",
            "source": "example.com",
            "date": "2024-01-15"
        }
    }
]

response = httpx.post(
    "http://localhost:8000/index",
    json={"documents": documents},
    timeout=30.0
)

result = response.json()
print(f"Indexed: {result['documents_processed']} documents")
print(f"Created: {result['chunks_created']} chunks")
```

**Batch Indexing Best Practices:**
- Index 10-50 documents per request
- Use unique, descriptive document IDs
- Include rich metadata (title, author, source, date)
- Wait 1-2 seconds between batches for rate limits

---

### 5. Delete Document

Delete a document and all its chunks from the system.

**Request:**
```http
DELETE /documents/{document_id}
```

**Path Parameters:**
- `document_id` (string, required): Unique document identifier

**Response:**
```json
{
  "success": true,
  "message": "Document doc-1 deleted successfully"
}
```

**Response Fields:**
- `success` (boolean): Whether deletion succeeded
- `message` (string): Status message

**Status Codes:**
- `200` - Success
- `404` - Document not found
- `500` - Deletion failed

**Example (cURL):**
```bash
curl -X DELETE http://localhost:8000/documents/doc-1
```

**Example (Python):**
```python
import httpx

document_id = "doc-1"
response = httpx.delete(f"http://localhost:8000/documents/{document_id}")

if response.status_code == 200:
    print(f"Deleted: {document_id}")
else:
    print(f"Error: {response.json()}")
```

---

### 6. Get Statistics

Get vector database statistics and metrics.

**Request:**
```http
GET /stats
```

**Response:**
```json
{
  "total_vectors": 1523,
  "dimension": 3072,
  "namespaces": {
    "": {
      "vector_count": 1523
    }
  }
}
```

**Response Fields:**
- `total_vectors` (integer): Total number of vectors in database
- `dimension` (integer): Vector dimension (3072 for text-embedding-3-large)
- `namespaces` (object): Per-namespace statistics

**Status Codes:**
- `200` - Success
- `500` - Failed to get stats

**Example (cURL):**
```bash
curl http://localhost:8000/stats
```

**Example (Python):**
```python
import httpx

response = httpx.get("http://localhost:8000/stats")
stats = response.json()

print(f"Total vectors: {stats['total_vectors']}")
print(f"Dimension: {stats['dimension']}")
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Status Codes:**
- `400` - Bad Request (invalid input)
- `422` - Validation Error (Pydantic validation failed)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `503` - Service Unavailable

**Example Validation Error:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "query"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## Rate Limits

The system is limited by external API rate limits:

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| OpenAI | 3 RPM, 40K TPM | Varies by tier |
| Cohere | 100 requests/min | 10K requests/min |
| Pinecone | 100 requests/sec | Unlimited |

**Best Practices:**
- Implement exponential backoff for retries
- Cache frequent queries
- Batch document indexing
- Monitor quota usage

---

## Webhooks (Future)

Planned webhook support for async operations:

```json
{
  "webhook_url": "https://your-app.com/webhook",
  "events": ["indexing.complete", "indexing.failed"]
}
```

---

## Interactive Documentation

Access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide:
- Live API testing
- Request/response schemas
- Example payloads
- Authentication testing (when implemented)

---

## SDK Examples

### Python SDK Pattern

```python
class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def query(self, query: str, **kwargs):
        response = await self.client.post(
            f"{self.base_url}/query",
            json={"query": query, **kwargs}
        )
        return response.json()

    async def index(self, documents: list):
        response = await self.client.post(
            f"{self.base_url}/index",
            json={"documents": documents}
        )
        return response.json()

# Usage
client = RAGClient()
result = await client.query("What is machine learning?")
```

### JavaScript SDK Pattern

```javascript
class RAGClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async query(query, options = {}) {
    const response = await fetch(`${this.baseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, ...options })
    });
    return response.json();
  }

  async index(documents) {
    const response = await fetch(`${this.baseUrl}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documents })
    });
    return response.json();
  }
}

// Usage
const client = new RAGClient();
const result = await client.query('What is machine learning?');
```

---

## Performance Tips

1. **Caching**: Cache frequent queries and reranking results
2. **Batching**: Index documents in batches of 10-50
3. **Parallel Requests**: Make independent requests in parallel
4. **Streaming**: Implement SSE for streaming LLM responses
5. **Connection Pooling**: Reuse HTTP connections

---

## Monitoring

**Key Metrics to Track:**

```python
# Query latency
query_duration_seconds{endpoint="query", status="200"}

# Chunks retrieved
chunks_retrieved_total{query_type="rag"}

# Reranking score distribution
reranking_score_bucket{le="0.8"}

# API errors
api_errors_total{endpoint="query", error_type="timeout"}
```

---

## Version History

### v1.0.0 (Current)
- Initial release
- Full RAG pipeline
- Query routing
- Multi-query generation
- Reranking support
- Document management

### Planned Features
- Authentication (JWT/OAuth2)
- Streaming responses
- Webhook support
- Query analytics
- A/B testing framework
- Custom rerankers
