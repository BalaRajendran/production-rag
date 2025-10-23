# Troubleshooting Guide

Common issues and solutions for the Production RAG Framework.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [API Connection Issues](#api-connection-issues)
4. [Query Quality Issues](#query-quality-issues)
5. [Performance Issues](#performance-issues)
6. [Deployment Issues](#deployment-issues)
7. [Error Messages](#error-messages)
8. [Debugging Techniques](#debugging-techniques)

---

## Installation Issues

### Import Errors / Module Not Found

**Problem:**
```python
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Install dependencies with uv
uv pip install -e .

# Or reinstall
uv pip install --force-reinstall -e .

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

### IDE Shows Import Warnings

**Problem:** IDE shows red underlines on imports

**Solution:**
1. Dependencies not installed yet (normal before first install)
2. IDE needs to be restarted after installation
3. Check IDE is using correct Python interpreter

```bash
# Verify interpreter
which python
python --version

# Restart IDE language server
# VSCode: Cmd+Shift+P -> "Python: Restart Language Server"
```

### uv Not Found

**Problem:**
```bash
bash: uv: command not found
```

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if needed)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify
uv --version
```

---

## Configuration Issues

### Missing .env File

**Problem:**
```
pydantic_core._pydantic_core.ValidationError: Field required
```

**Solution:**
```bash
# Create .env from template
cp .env.example .env

# Edit with your API keys
nano .env  # or your preferred editor
```

### Invalid API Keys

**Problem:**
```
Error: Invalid API key
```

**Solution:**
1. **OpenAI:** Verify at https://platform.openai.com/api-keys
2. **Pinecone:** Check at https://app.pinecone.io
3. **Cohere:** Verify at https://dashboard.cohere.com

```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Pinecone key
curl -H "Api-Key: $PINECONE_API_KEY" \
  https://api.pinecone.io/indexes

# Test Cohere key
curl -X POST https://api.cohere.ai/v1/rerank \
  -H "Authorization: Bearer $COHERE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"rerank-english-v3.0","query":"test","documents":["test"]}'
```

### Port Already in Use

**Problem:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

---

## API Connection Issues

### Cannot Connect to Pinecone

**Problem:**
```
Error initializing Pinecone: API key or environment invalid
```

**Solutions:**

1. **Check API Key:**
```bash
# Verify key in .env
cat .env | grep PINECONE_API_KEY
```

2. **Check Environment:**
```bash
# List available environments in Pinecone console
# Ensure PINECONE_ENVIRONMENT matches your region
# Common: us-east-1, us-west-2, eu-west-1
```

3. **Network Issues:**
```bash
# Test connectivity
curl https://api.pinecone.io/indexes \
  -H "Api-Key: $PINECONE_API_KEY"

# Check firewall/proxy settings
```

4. **Index Not Found:**
```python
# The system auto-creates indexes
# If this fails, create manually in Pinecone console
# Name: Must match PINECONE_INDEX_NAME in .env
# Dimensions: 3072 (for text-embedding-3-large)
# Metric: cosine
```

### OpenAI Rate Limits

**Problem:**
```
openai.RateLimitError: Rate limit exceeded
```

**Solutions:**

1. **Check Tier:**
```bash
# Free tier: 3 RPM, 40K TPM
# Tier 1: 500 RPM, 10M TPM
# Upgrade at: https://platform.openai.com/account/limits
```

2. **Implement Backoff:**
```python
# Add exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def embed_texts(self, texts):
    return await self.openai_client.embeddings.create(...)
```

3. **Reduce Concurrent Requests:**
```python
# Limit concurrent queries
import asyncio

semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def rate_limited_query(query):
    async with semaphore:
        return await rag_service.query(query)
```

### Cohere Rate Limits

**Problem:**
```
cohere.error.CohereAPIError: too many requests
```

**Solutions:**

1. **Free Tier Limits:** 100 requests/min
2. **Upgrade:** https://dashboard.cohere.com/billing
3. **Cache Reranking:**
```python
# Cache reranking results
from functools import lru_cache

@lru_cache(maxsize=1000)
def rerank_cached(query_hash, chunks_hash):
    return self.rerank(query, chunks)
```

---

## Query Quality Issues

### No Results Returned

**Problem:** Query returns empty chunks

**Debug Steps:**

1. **Check if documents are indexed:**
```bash
curl http://localhost:8000/stats
# Should show total_vectors > 0
```

2. **Index test documents:**
```python
import httpx

response = httpx.post("http://localhost:8000/index", json={
    "documents": [{
        "id": "test-1",
        "content": "Machine learning is a subset of AI...",
        "metadata": {"title": "ML Test"}
    }]
})
print(response.json())
```

3. **Test with simple query:**
```python
response = httpx.post("http://localhost:8000/query", json={
    "query": "machine learning"
})
print(response.json())
```

4. **Check Pinecone directly:**
```python
from pinecone import Pinecone
pc = Pinecone(api_key="...")
index = pc.Index("rag-index")
stats = index.describe_index_stats()
print(stats)  # Should show vectors
```

### Poor Answer Quality

**Problem:** Answers are irrelevant or incorrect

**Debug Steps:**

1. **Check Generated Queries:**
```python
response = httpx.post("http://localhost:8000/query", json={
    "query": "What is deep learning?"
})
print("Generated queries:", response.json()["generated_queries"])
# Should show multiple semantic + keyword variants
```

2. **Inspect Retrieved Chunks:**
```python
result = response.json()
for i, chunk in enumerate(result["chunks"]):
    print(f"\n[Chunk {i+1}] Score: {chunk['score']:.3f}")
    print(f"Text: {chunk['text'][:200]}...")
    print(f"Metadata: {chunk['metadata']}")
# Verify chunks are relevant
```

3. **Check Reranking Scores:**
```python
# Add logging to services/reranker.py
print("Before rerank:", [c.score for c in chunks[:5]])
print("After rerank:", [r.rerank_score for r in reranked[:5]])
# Scores should change significantly
```

4. **Verify Chunk Quality:**
```python
# Check chunk content during indexing
# In services/chunking.py
for chunk in chunks:
    print(f"Chunk length: {chunk['token_count']} tokens")
    print(f"Text: {chunk['text'][:100]}...")
    print(f"Complete sentence: {chunk['text'].endswith(('.', '!', '?'))}")
```

**Common Fixes:**

1. **Adjust Chunk Size:**
```env
# In .env
CHUNK_SIZE=256  # Try smaller for more precise
CHUNK_SIZE=1024 # Try larger for more context
```

2. **Increase Retrieval:**
```env
TOP_K_RETRIEVAL=100  # Get more chunks before reranking
TOP_K_RERANK=20      # Keep more after reranking
```

3. **Improve Metadata:**
```python
# Always include rich metadata
document = {
    "id": "doc-1",
    "content": "...",
    "metadata": {
        "title": "Specific Title",  # Important!
        "author": "Author Name",     # Important!
        "source": "source.com",      # Important!
        "date": "2024-01-15"
    }
}
```

4. **Custom Chunking:**
```python
# For domain-specific content, customize chunking
# See .claude/skills/rag-framework.md
```

### Wrong Query Routing

**Problem:** Query routed incorrectly (e.g., RAG query routed to summarization)

**Debug:**
```python
# Add logging to services/query_router.py
print(f"Query: {query}")
print(f"Routed to: {query_type}")
print(f"Reason: {explanation}")
```

**Fix:**
```python
# In services/query_router.py
# Add more patterns or adjust LLM prompt

# For summarization false positives:
if "specific" in query.lower() or "what" in query.lower():
    # Bias toward RAG for specific questions
    return QueryType.RAG, "Specific question"
```

---

## Performance Issues

### Slow Query Response

**Problem:** Queries take >10 seconds

**Debug:**

1. **Profile Components:**
```python
import time

# In services/rag_service.py
async def query(self, request):
    t0 = time.time()

    # Routing
    query_type, _ = await self.query_router.route_query(request.query)
    print(f"Routing: {time.time() - t0:.2f}s")

    # Query generation
    t1 = time.time()
    queries = await self.query_generator.generate_queries(...)
    print(f"Query gen: {time.time() - t1:.2f}s")

    # Search
    t2 = time.time()
    chunks = await self.vector_store.search_multiple_queries(...)
    print(f"Search: {time.time() - t2:.2f}s")

    # Reranking
    t3 = time.time()
    reranked = await self.reranker.rerank(...)
    print(f"Rerank: {time.time() - t3:.2f}s")

    # Answer gen
    t4 = time.time()
    answer = await self.llm.generate_answer(...)
    print(f"Answer: {time.time() - t4:.2f}s")

    print(f"Total: {time.time() - t0:.2f}s")
```

**Common Bottlenecks:**

1. **Reranking (800-1200ms):**
```python
# Reduce input chunks
TOP_K_RETRIEVAL=30  # Instead of 50

# Cache results
from functools import lru_cache
import hashlib

def cache_key(query, chunks):
    return hashlib.md5(f"{query}{len(chunks)}".encode()).hexdigest()
```

2. **LLM Generation (1500-2500ms):**
```python
# Use faster model for simple queries
if query_type == QueryType.GENERAL:
    self.model = "gpt-3.5-turbo"  # Faster
else:
    self.model = "gpt-4-turbo-preview"  # Better quality
```

3. **Query Generation (500-800ms):**
```python
# Skip for simple queries
if not conversation_history or len(request.query.split()) < 5:
    # Use only original query
    queries = [GeneratedQuery(query=request.query, type="semantic")]
```

### High Memory Usage

**Problem:** Server uses too much memory

**Solutions:**

1. **Reduce Batch Size:**
```python
# In services/vector_store.py
batch_size = 50  # Reduce from 100
```

2. **Clear Caches:**
```python
# If using caching
cache.clear()  # Periodically clear
```

3. **Limit Workers:**
```bash
# Reduce uvicorn workers
uvicorn main:app --workers 2  # Instead of 4
```

### High API Costs

**Problem:** Unexpected API bills

**Debug:**

1. **Track Usage:**
```python
# Add counters
embedding_calls = 0
llm_calls = 0
rerank_calls = 0

# Log costs
print(f"Embeddings: {embedding_calls} calls × $0.0001")
print(f"LLM: {llm_calls} calls × $0.01")
print(f"Reranking: {rerank_calls} calls × $0.002")
```

2. **Optimize:**
```python
# Cache embeddings
# Reduce query variants (5 → 3)
# Use cheaper models for simple queries
# Implement request quotas
```

---

## Deployment Issues

### Docker Build Fails

**Problem:**
```
ERROR: failed to solve: process "/bin/sh -c uv pip install --system -e ."
```

**Solutions:**

1. **Check Dockerfile syntax**
2. **Ensure pyproject.toml is valid**
3. **Try building without cache:**
```bash
docker build --no-cache -t production-rag .
```

### Container Exits Immediately

**Problem:** Container starts then stops

**Debug:**
```bash
# Check logs
docker logs rag-api

# Run interactively
docker run -it --entrypoint /bin/bash production-rag

# Check environment
docker run production-rag env
```

### Health Check Fails

**Problem:** Health check returns 503

**Debug:**
```bash
# Check directly
curl http://localhost:8000/health

# Check Pinecone connection
# Check API keys loaded
# Check logs for errors
```

### Kubernetes Pods Crashing

**Problem:** Pods in CrashLoopBackOff

**Debug:**
```bash
# Check pod logs
kubectl logs -f <pod-name>

# Describe pod
kubectl describe pod <pod-name>

# Check secrets
kubectl get secret rag-secrets -o yaml

# Check resource limits
kubectl top pod <pod-name>
```

---

## Error Messages

### "Field required" Validation Error

**Full Error:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "query"],
      "msg": "Field required"
    }
  ]
}
```

**Cause:** Missing required field in request

**Fix:**
```python
# Ensure required fields are present
{
  "query": "Your question here"  # Required!
}
```

### "Connection refused" Error

**Cause:** Server not running or wrong port

**Fix:**
```bash
# Check if server is running
curl http://localhost:8000/health

# Start server if not running
python main.py

# Check port
# Default is 8000, ensure consistent
```

### "Too many requests" Error

**Cause:** Rate limit exceeded

**Fix:**
1. Wait and retry
2. Upgrade API tier
3. Implement request queuing
4. Add caching

### "Vector dimension mismatch" Error

**Cause:** Pinecone index has wrong dimensions

**Fix:**
```python
# Recreate Pinecone index with correct dimensions
# text-embedding-3-large = 3072 dimensions
# Delete old index and restart app (auto-creates)
```

---

## Debugging Techniques

### Enable Debug Logging

```python
# In main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Test Components Individually

```python
# Test chunking
from services.chunking import ChunkingService
chunker = ChunkingService()
chunks = chunker.chunk_text("Your text here...")
print(f"Created {len(chunks)} chunks")

# Test embeddings
from services.vector_store import VectorStoreService
vs = VectorStoreService()
await vs.initialize()
embeddings = await vs.embed_texts(["test query"])
print(f"Embedding dimension: {len(embeddings[0])}")

# Test reranking
from services.reranker import RerankingService
reranker = RerankingService()
reranked = await reranker.rerank("query", chunks)
print(f"Reranked to {len(reranked)} chunks")
```

### Use Interactive API Docs

1. Go to http://localhost:8000/docs
2. Try each endpoint interactively
3. See request/response examples
4. Debug validation errors

### Check System Resources

```bash
# CPU and memory
top

# Disk space
df -h

# Network connections
netstat -an | grep 8000

# Docker resources
docker stats rag-api
```

### Enable Request Logging

```python
# In main.py
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"{request.method} {request.url}")
    print(f"Headers: {request.headers}")
    response = await call_next(request)
    print(f"Status: {response.status_code}")
    return response
```

---

## Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Review error messages carefully
3. ✅ Check API keys and configuration
4. ✅ Test with minimal example
5. ✅ Check logs for details

### Information to Provide

When asking for help, include:

1. **Error message** (complete stacktrace)
2. **Environment** (OS, Python version, Docker version)
3. **Configuration** (sanitized .env)
4. **Steps to reproduce**
5. **Expected vs actual behavior**
6. **Logs** (with DEBUG level enabled)

### Resources

- **Documentation:** [README.md](README.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Skills:** [.claude/skills/rag-framework.md](.claude/skills/rag-framework.md)

### External Resources

- FastAPI: https://fastapi.tiangolo.com
- Pinecone: https://docs.pinecone.io
- OpenAI: https://platform.openai.com/docs
- Cohere: https://docs.cohere.com

---

## Quick Fixes

### Reset Everything

```bash
# Stop all containers
docker-compose down

# Remove .env and recreate
rm .env
cp .env.example .env
# Edit with your keys

# Reinstall dependencies
uv pip install --force-reinstall -e .

# Restart
python main.py
```

### Test Basic Functionality

```bash
# Test server
curl http://localhost:8000/

# Test health
curl http://localhost:8000/health

# Test query (requires indexed docs)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Verify All Services

```python
# test_services.py
import asyncio
from config import settings

async def test_all():
    # Test OpenAI
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    models = await client.models.list()
    print("✓ OpenAI connected")

    # Test Pinecone
    from pinecone import Pinecone
    pc = Pinecone(api_key=settings.pinecone_api_key)
    indexes = pc.list_indexes()
    print("✓ Pinecone connected")

    # Test Cohere
    import cohere
    co = cohere.Client(settings.cohere_api_key)
    print("✓ Cohere connected")

asyncio.run(test_all())
```

---

*For additional help, consult the documentation files or create an issue.*
