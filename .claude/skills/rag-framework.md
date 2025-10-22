# RAG Framework Development Skills

## Overview
Skills for developing, debugging, and extending the Production RAG Framework.

---

## Skill: Add New Document Source

**When to use:** Adding support for new document types or sources

**Steps:**

1. Identify document type (PDF, CSV, API, etc.)
2. Create extraction logic in `services/chunking.py` or new file
3. Add document parsing to handle new format
4. Update `models.py` if new metadata fields needed
5. Test with sample documents

**Example:**
```python
# In services/document_extractors.py
class PDFExtractor:
    def extract(self, file_path: str) -> Dict[str, Any]:
        # Extract text and metadata from PDF
        return {
            "content": extracted_text,
            "metadata": {
                "title": pdf_title,
                "author": pdf_author,
                "pages": page_count
            }
        }
```

---

## Skill: Customize Chunking Strategy

**When to use:** Adjusting chunking for domain-specific content

**Steps:**

1. Open `services/chunking.py`
2. Identify customization point:
   - Sentence splitting logic
   - Chunk size calculation
   - Overlap strategy
   - Metadata injection
3. Create custom method or modify existing
4. Test with representative documents
5. Monitor chunk quality in queries

**Example:**
```python
# Custom chunking for code documentation
def chunk_code_docs(self, text: str, metadata: dict) -> List[Dict]:
    # Split by code blocks and text sections
    sections = self._split_code_and_text(text)
    chunks = []
    for section in sections:
        if section["type"] == "code":
            # Don't split code blocks
            chunks.append(self._create_chunk([section["content"]], metadata))
        else:
            # Use normal chunking for text
            chunks.extend(self.chunk_text(section["content"], metadata))
    return chunks
```

---

## Skill: Add Custom Query Router

**When to use:** Need to route queries to new handler types

**Steps:**

1. Open `services/query_router.py`
2. Add new `QueryType` to `models.py`
3. Add pattern or LLM prompt to detect new type
4. Implement handler in `services/rag_service.py`
5. Test with various query examples

**Example:**
```python
# In models.py
class QueryType(str, Enum):
    RAG = "rag"
    SUMMARIZATION = "summarization"
    METADATA_QUERY = "metadata_query"
    COMPARISON = "comparison"  # NEW
    GENERAL = "general"

# In query_router.py
def _pattern_based_routing(self, query: str):
    # Add comparison detection
    comparison_patterns = [
        r'\bcompare\b',
        r'\bdifference between\b',
        r'\bversus\b', r'\bvs\.?\b'
    ]
    for pattern in comparison_patterns:
        if re.search(pattern, query_lower):
            return QueryType.COMPARISON, "Comparison query"

# In rag_service.py
async def _handle_comparison(self, request: QueryRequest):
    # Implement comparison logic
    pass
```

---

## Skill: Integrate Custom Reranker

**When to use:** Want to use different reranking model or logic

**Steps:**

1. Open `services/reranker.py`
2. Add new reranker class or method
3. Update configuration in `config.py` if needed
4. Implement reranking logic
5. Update `rag_service.py` to use new reranker
6. Compare results with baseline

**Example:**
```python
# Custom reranker with business rules
class CustomReranker(RerankingService):
    async def rerank_with_rules(
        self,
        query: str,
        chunks: List[Chunk],
        boost_recent: bool = True
    ):
        # Standard reranking
        reranked = await self.rerank(query, chunks)

        # Apply business rules
        if boost_recent:
            for item in reranked:
                date = item.chunk.metadata.get("date")
                if date and self._is_recent(date):
                    item.rerank_score *= 1.2  # Boost recent docs

        # Re-sort and return
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)
        return reranked
```

---

## Skill: Add Streaming Response

**When to use:** Want to stream LLM responses for better UX

**Steps:**

1. Update `services/llm_service.py` to support streaming
2. Modify FastAPI endpoint to use `StreamingResponse`
3. Update client code to handle SSE
4. Test with various query types

**Example:**
```python
# In llm_service.py
async def generate_answer_stream(self, query: str, chunks: List[Chunk]):
    context = self._build_context(chunks)
    messages = self._build_messages(query, context)

    stream = await self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# In main.py
from fastapi.responses import StreamingResponse

@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    async def event_generator():
        async for chunk in rag_service.query_stream(request):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

## Skill: Add Caching Layer

**When to use:** Improve performance for repeated queries

**Steps:**

1. Choose cache backend (Redis, in-memory)
2. Identify what to cache:
   - Query embeddings
   - Reranking results
   - Full responses
3. Implement cache wrapper
4. Add cache invalidation logic
5. Monitor cache hit rates

**Example:**
```python
# Simple in-memory cache
from functools import lru_cache
import hashlib

class CachedVectorStore(VectorStoreService):
    def __init__(self):
        super().__init__()
        self._embedding_cache = {}

    async def embed_texts(self, texts: List[str]):
        # Check cache
        cache_keys = [hashlib.md5(t.encode()).hexdigest() for t in texts]
        cached = [self._embedding_cache.get(k) for k in cache_keys]

        if all(cached):
            return cached

        # Generate missing
        embeddings = await super().embed_texts(texts)

        # Update cache
        for key, emb in zip(cache_keys, embeddings):
            self._embedding_cache[key] = emb

        return embeddings
```

---

## Skill: Add Authentication

**When to use:** Securing the API for production

**Steps:**

1. Choose auth method (JWT, API Key, OAuth2)
2. Add auth dependencies to FastAPI
3. Create user/key management
4. Update endpoints with auth decorators
5. Add rate limiting per user

**Example:**
```python
# JWT authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Protect endpoints
@app.post("/query")
async def query(
    request: QueryRequest,
    user: dict = Depends(verify_token)
):
    # user is authenticated
    response = await rag_service.query(request)
    return response
```

---

## Skill: Debug Query Quality

**When to use:** Queries returning poor results

**Debugging Checklist:**

1. **Check Query Generation:**
   ```python
   # Log generated queries
   print("Generated queries:", [q.query for q in generated_queries])
   ```

2. **Check Retrieved Chunks:**
   ```python
   # Log retrieval scores
   for chunk in chunks:
       print(f"Score: {chunk.score:.3f} - {chunk.text[:100]}")
   ```

3. **Check Reranking:**
   ```python
   # Compare before/after reranking
   print("Before rerank:", [c.score for c in chunks[:5]])
   print("After rerank:", [r.rerank_score for r in reranked[:5]])
   ```

4. **Check Context:**
   ```python
   # Inspect what's sent to LLM
   context = self._build_context(chunks)
   print("Context length:", len(context))
   print("Context preview:", context[:500])
   ```

5. **Test Components Individually:**
   - Test embedding quality
   - Test chunking output
   - Test reranker separately
   - Test LLM with manual context

---

## Skill: Monitor Performance

**When to use:** Optimizing system performance

**Key Metrics:**

```python
import time
from functools import wraps

def monitor_latency(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__}: {duration:.2f}s")
        return result
    return wrapper

# Apply to critical methods
@monitor_latency
async def query(self, request: QueryRequest):
    # Track end-to-end latency
    pass
```

**Performance Bottlenecks:**
- Query generation: 500-800ms
- Vector search: 200-400ms
- Reranking: 800-1200ms (largest)
- LLM generation: 1500-2500ms (largest)

**Optimization Targets:**
1. Reduce reranking input (50→30 chunks)
2. Cache reranking results
3. Use faster LLM for simple queries
4. Parallel process where possible

---

## Skill: Add Custom Metadata

**When to use:** Need domain-specific metadata fields

**Steps:**

1. Define metadata schema in docs
2. Update indexing to capture new fields
3. Update chunking to include in context
4. Add metadata to reranking if relevant
5. Update query filters to support new fields

**Example:**
```python
# Domain-specific metadata
document = {
    "id": "legal-doc-1",
    "content": "...",
    "metadata": {
        # Standard
        "title": "Contract Agreement",
        "author": "Legal Team",
        "date": "2024-01-15",

        # Custom legal metadata
        "case_number": "2024-CV-1234",
        "jurisdiction": "California",
        "practice_area": "Contract Law",
        "confidentiality": "internal",
        "effective_date": "2024-02-01",
        "parties": ["Company A", "Company B"]
    }
}

# Query with custom filters
response = httpx.post("/query", json={
    "query": "What are the terms?",
    "metadata_filter": {
        "practice_area": "Contract Law",
        "jurisdiction": "California"
    }
})
```

---

## Skill: Batch Processing

**When to use:** Processing large document collections

**Example:**
```python
import asyncio
from pathlib import Path

async def batch_index_directory(directory: str, batch_size: int = 20):
    """Index all documents in a directory."""
    files = list(Path(directory).glob("*.txt"))

    for i in range(0, len(files), batch_size):
        batch_files = files[i:i + batch_size]
        documents = []

        for file in batch_files:
            content = file.read_text()
            documents.append({
                "id": file.stem,
                "content": content,
                "metadata": {
                    "title": file.stem,
                    "source": str(file),
                    "filename": file.name
                }
            })

        # Index batch
        response = await client.post("/index", json={
            "documents": documents
        })

        print(f"Batch {i//batch_size + 1}: {response.json()}")

        # Rate limiting
        await asyncio.sleep(1)

# Usage
await batch_index_directory("/path/to/docs", batch_size=20)
```

---

## Common Pitfalls

1. **Chunk Size Too Large/Small**
   - Too large: Loses precision
   - Too small: Loses context
   - Optimal: 512 tokens for most cases

2. **Missing Metadata**
   - Always include title, author, source
   - Metadata significantly improves quality

3. **Not Using Reranking**
   - Reranking is highest ROI improvement
   - Always rerank before sending to LLM

4. **Ignoring Query Routing**
   - Don't use RAG for all queries
   - Route simple queries appropriately

5. **Single Query Search**
   - Generate multiple query variants
   - Parallel search improves coverage

---

## Testing Patterns

```python
# Test chunking
def test_chunking():
    chunker = ChunkingService(chunk_size=100, chunk_overlap=20)
    text = "Long document text here..."
    chunks = chunker.chunk_text(text)

    # Validate
    assert len(chunks) > 0
    assert all(chunk["text"] for chunk in chunks)
    assert all(chunk["token_count"] <= 100 for chunk in chunks)

# Test query generation
async def test_query_generation():
    service = QueryGenerationService()
    queries = await service.generate_queries(
        "What is ML?",
        conversation_history=[]
    )

    assert len(queries) >= 2
    assert any(q.query_type == "semantic" for q in queries)
    assert any(q.query_type == "keyword" for q in queries)

# Test end-to-end
async def test_full_pipeline():
    # Index
    index_response = await client.post("/index", json={
        "documents": [test_document]
    })
    assert index_response.json()["success"]

    # Query
    query_response = await client.post("/query", json={
        "query": "test question"
    })
    result = query_response.json()

    assert result["answer"]
    assert len(result["chunks"]) > 0
```

---

## Resources

- FastAPI docs: https://fastapi.tiangolo.com
- Pinecone docs: https://docs.pinecone.io
- OpenAI docs: https://platform.openai.com/docs
- Cohere docs: https://docs.cohere.com

## See Also

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design
- [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - API reference
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Problem solving
