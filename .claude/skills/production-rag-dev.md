# Production RAG - Development Skills

## Overview
Skills for developing, debugging, and extending the Production RAG Framework with enterprise-grade v2.0.0 architecture.

**Version:** 2.0.0
**Features:** API versioning, rate limiting, observability, structured logging, comprehensive testing
**Test Coverage:** 75-80% with 180+ tests

---

## Quick Reference

### v2.0.0 Quick Start

```bash
# Development workflow (NEW v2.0)
make install-dev      # Install all dependencies + dev tools
make format           # Format code with Black + isort
make lint             # Run all linters (Ruff, mypy, Bandit)
make test             # Run complete test suite
make test-cov         # Run tests with coverage report
make docker-up        # Start all services
make docker-logs      # View logs
make quick-start      # Complete setup and run

# Testing (NEW v2.0)
pytest -m unit           # Run unit tests only
pytest -m integration    # Run integration tests only
pytest -m "not slow"     # Skip slow tests
open htmlcov/index.html  # View coverage report

# Pre-commit hooks (NEW v2.0)
pre-commit install       # Install hooks
pre-commit run --all-files  # Run all hooks manually
```

### New API Endpoints (v2.0)

All endpoints now under `/api/v1/` with response headers:
- `X-Correlation-ID` - Request tracking
- `X-Process-Time` - Request duration
- `X-RateLimit-Limit` - Rate limit max
- `X-RateLimit-Remaining` - Requests remaining

```bash
# Health checks
curl http://localhost:8000/api/v1/health  # Full health check
curl http://localhost:8000/api/v1/ready   # Readiness check
curl http://localhost:8000/api/v1/live    # Liveness check

# RAG operations
curl -X POST http://localhost:8000/api/v1/query -d '{...}'
curl -X POST http://localhost:8000/api/v1/index -d '{...}'
curl -X DELETE http://localhost:8000/api/v1/documents/{id}

# Monitoring
curl http://localhost:8000/api/v1/stats
```

### Project Structure (v2.0.0)
```
app/
├── api/                    # Future: Organized API routes
├── core/
│   └── config.py          # Settings and environment
├── models/
│   └── models.py          # Pydantic schemas
├── services/              # Business logic
│   ├── rag_service.py    # Main orchestrator
│   ├── vector_store.py   # Qdrant operations
│   ├── query_generation.py
│   ├── reranker.py
│   ├── query_router.py
│   ├── llm_service.py
│   └── chunking.py
└── main.py                # FastAPI app
```

### Import Pattern
All imports use relative paths:
```python
# From app/main.py
from .core.config import settings
from .models.models import QueryRequest
from .services.rag_service import RAGService

# From app/services/rag_service.py
from ..models.models import QueryRequest
from ..core.config import settings
from .vector_store import VectorStoreService
```

### Docker Commands
```bash
# Start services (no rebuild needed for code changes)
docker compose up -d

# View logs
docker logs production-rag-rag-api-1 --tail 50 -f
docker logs production-rag-qdrant-1 --tail 50 -f

# Check status
docker compose ps

# Restart single service
docker compose restart rag-api

# Rebuild (only needed for dependency changes)
docker compose up -d --build
```

---

## Skill: Fix Import Errors After Restructuring

**When to use:** Getting ModuleNotFoundError after v1.1.0 update

**Common Issues:**
1. Absolute imports instead of relative
2. Missing `__init__.py` files
3. Incorrect relative path depth

**Solution:**
```python
# ❌ OLD (absolute imports)
from config import settings
from models import QueryRequest
from services.rag_service import RAGService

# ✅ NEW (relative imports)
# From app/main.py
from .core.config import settings
from .models.models import QueryRequest
from .services.rag_service import RAGService

# From app/services/rag_service.py
from ..models.models import QueryRequest  # Go up one level
from ..core.config import settings
from .vector_store import VectorStoreService  # Same level
```

**Verification:**
```bash
# Test imports work
docker compose up -d
docker logs production-rag-rag-api-1 --tail 20
# Should see "Application startup complete" without import errors
```

---

## Skill: Add New Service

**When to use:** Creating new business logic component

**Steps:**

1. **Create service file** in `app/services/`:
```python
# app/services/new_service.py
from typing import List
from ..core.config import settings
from ..models.models import SomeModel

class NewService:
    """
    Description of what this service does.
    """

    def __init__(self):
        self.config = settings

    async def do_something(self, input: str) -> str:
        """Method description."""
        # Implementation
        return result
```

2. **Export from `__init__.py`**:
```python
# app/services/__init__.py
from .new_service import NewService

__all__ = [
    # ... existing exports
    "NewService",
]
```

3. **Use in other services**:
```python
# app/services/rag_service.py
from .new_service import NewService

class RAGService:
    def __init__(self):
        self.new_service = NewService()
```

4. **Test with hot reload** (no rebuild needed):
```bash
# Save files and check logs
docker logs production-rag-rag-api-1 --tail 10
# Should see "Reloading..." message
```

---

## Skill: Add New API Endpoint

**When to use:** Exposing new functionality via REST API

**Steps:**

1. **Define request/response models**:
```python
# app/models/models.py
class NewFeatureRequest(BaseModel):
    input: str
    options: Optional[Dict[str, Any]] = None

class NewFeatureResponse(BaseModel):
    result: str
    metadata: Dict[str, Any]
```

2. **Add endpoint in main.py**:
```python
# app/main.py
@app.post("/new-feature", response_model=NewFeatureResponse, tags=["Features"])
async def new_feature(request: NewFeatureRequest):
    """
    Description of what this endpoint does.

    ## Example Request
    ```json
    {
        "input": "test",
        "options": {"key": "value"}
    }
    ```
    """
    try:
        result = await rag_service.some_method(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Operation failed: {str(e)}"
        )
```

3. **Test immediately** (hot reload active):
```bash
# Check endpoint in docs
open http://localhost:8000/docs

# Or test with curl
curl -X POST http://localhost:8000/new-feature \
  -H "Content-Type: application/json" \
  -d '{"input": "test"}'
```

---

## Skill: Debug Qdrant Connection Issues

**When to use:** Qdrant connection failures or errors

**Common Issues & Solutions:**

### Issue 1: Connection Refused
```python
# Error: Connection refused to localhost:6333
# Problem: Using localhost instead of Docker service name
```
**Solution:**
```python
# app/core/config.py
qdrant_host: str = "qdrant"  # ✅ Docker service name
# NOT: "localhost" or "127.0.0.1"
```

### Issue 2: Collection Not Found
```bash
# Check if collection exists
docker exec -it production-rag-qdrant-1 sh
# Or use Qdrant dashboard
open http://localhost:6333/dashboard
```
**Solution:**
```python
# Collection is auto-created on first index operation
# POST /index with documents will create collection
```

### Issue 3: Pydantic Validation Errors
```
# Error: 3 validation errors for ParsingModel[InlineResponse2005]
```
**Solution:** Already fixed in v1.1.0
```python
# app/services/vector_store.py uses raw HTTP requests
# No client SDK validation issues
```

### Issue 4: Check Qdrant Logs
```bash
docker logs production-rag-qdrant-1 --tail 100
# Look for startup messages and errors
```

---

## Skill: Update Dependencies

**When to use:** Adding/updating Python packages

**Important:** Versions must be in `requirements.txt` (single source of truth)

**Steps:**

1. **Update requirements.txt**:
```txt
# requirements.txt
fastapi==0.115.0
new-package==1.2.3  # Add new dependency
```

2. **Rebuild Docker image** (required for dependency changes):
```bash
docker compose up -d --build
```

3. **Verify installation**:
```bash
docker exec production-rag-rag-api-1 pip list | grep new-package
```

4. **Update pyproject.toml** (optional, for local dev):
```toml
[project]
dependencies = [
    "fastapi",
    "new-package",  # Without version
]
```

---

## Skill: Configure Environment Variables

**When to use:** Adding new configuration options

**Steps:**

1. **Add to `.env.example`**:
```env
# .env.example
NEW_FEATURE_ENABLED=true
NEW_API_KEY=your-api-key-here
```

2. **Add to config.py**:
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...

    new_feature_enabled: bool = False
    new_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
```

3. **Add to docker-compose.yml**:
```yaml
# docker-compose.yml
services:
  rag-api:
    environment:
      - NEW_FEATURE_ENABLED=${NEW_FEATURE_ENABLED:-false}
      - NEW_API_KEY=${NEW_API_KEY}
```

4. **Use in code**:
```python
# app/services/new_service.py
from ..core.config import settings

if settings.new_feature_enabled:
    # Feature logic
    pass
```

---

## Skill: Debug Hot Reload Issues

**When to use:** Code changes not being picked up

**Checklist:**

1. **Verify volume mounts** in docker-compose.yml:
```yaml
volumes:
  - ./app:/app/app:ro  # ✅ Read-only mount
```

2. **Check uvicorn is running with --reload**:
```bash
docker exec production-rag-rag-api-1 ps aux | grep uvicorn
# Should see: uvicorn app.main:app --reload
```

3. **Check watchfiles is detecting changes**:
```bash
docker logs production-rag-rag-api-1 -f
# Edit a file in app/
# Should see: "WatchFiles detected changes in 'app/...'. Reloading..."
```

4. **Restart if stuck**:
```bash
docker compose restart rag-api
```

---

## Skill: Add Custom Chunking Strategy

**When to use:** Domain-specific document chunking needed

**Steps:**

1. **Create custom chunker**:
```python
# app/services/chunking.py

class ChunkingService:
    async def chunk_by_custom_logic(
        self,
        text: str,
        chunk_size: int = 512
    ) -> List[Dict[str, Any]]:
        """
        Custom chunking strategy for specific domain.

        Example: Legal documents by section
        """
        sections = self._split_by_section_markers(text)
        chunks = []

        for section in sections:
            # Custom logic here
            chunks.append({
                "text": section,
                "metadata": {"type": "section"}
            })

        return chunks
```

2. **Use in RAG service**:
```python
# app/services/rag_service.py
async def index(self, request: IndexRequest):
    # Use custom chunker
    chunks = await self.chunking.chunk_by_custom_logic(
        document.content
    )
```

---

## Skill: Monitor Performance

**When to use:** Analyzing query latency and bottlenecks

**Tools:**

### 1. FastAPI Logs
```bash
docker logs production-rag-rag-api-1 -f | grep "INFO:"
# Shows all HTTP requests with response times
```

### 2. Add Timing Decorators
```python
# app/services/utils.py (create if needed)
import time
from functools import wraps

def timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

# Use in services
@timed
async def rerank_chunks(self, ...):
    # Method will log its duration
    pass
```

### 3. Qdrant Dashboard
```bash
open http://localhost:6333/dashboard
# View collection stats, search performance
```

### 4. Health Check Stats
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
```

---

## Skill: Test RAG Pipeline End-to-End

**When to use:** Verifying complete system functionality

**Steps:**

1. **Index test documents**:
```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "test-1",
        "content": "Machine learning is a subset of AI...",
        "metadata": {
          "title": "ML Guide",
          "author": "Test Author"
        }
      }
    ]
  }'
```

2. **Query system**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "conversation_history": []
  }'
```

3. **Check response**:
```json
{
  "answer": "Machine learning is...",
  "sources": [...],
  "query_type": "rag",
  "queries_generated": [...],
  "chunks_retrieved": 50,
  "chunks_reranked": 15
}
```

4. **Verify in Qdrant**:
```bash
open http://localhost:6333/dashboard
# Check collection has indexed documents
```

---

## Skill: Troubleshoot Common Errors

### Error: "ModuleNotFoundError: No module named 'app'"
**Cause:** Running Python outside Docker or incorrect PYTHONPATH
**Solution:** Always use Docker Compose, or set PYTHONPATH locally
```bash
export PYTHONPATH=/path/to/production-rag:$PYTHONPATH
```

### Error: "ImportError: attempted relative import with no known parent package"
**Cause:** Trying to run files directly
**Solution:** Use uvicorn with module path
```bash
# ✅ Correct
uvicorn app.main:app

# ❌ Wrong
python app/main.py
```

### Error: Service shows "(unhealthy)"
**Cause:** Health check failing
**Solution:** Check logs and verify services
```bash
docker logs production-rag-rag-api-1 --tail 50
curl http://localhost:8000/health
```

### Error: "Qdrant validation errors"
**Cause:** Fixed in v1.1.0, but if recurring:
**Solution:** Verify qdrant-client version
```bash
docker exec production-rag-rag-api-1 pip show qdrant-client
# Should be 1.12.1 or higher
```

---

## Skill: Organize API Routes (Future)

**When to use:** As project grows, organize endpoints

**Planned Structure:**
```
app/api/
├── __init__.py
├── v1/
│   ├── __init__.py
│   ├── documents.py      # /api/v1/documents/*
│   ├── query.py          # /api/v1/query/*
│   └── admin.py          # /api/v1/admin/*
└── dependencies.py       # Shared dependencies
```

**Example:**
```python
# app/api/v1/query.py
from fastapi import APIRouter
from ...models.models import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/v1/query", tags=["Query"])

@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest):
    # Implementation
    pass

# app/main.py
from .api.v1 import query

app.include_router(query.router)
```

---

## Best Practices

### 1. Always Use Relative Imports
```python
# ✅ Good
from ..models.models import QueryRequest
from .vector_store import VectorStoreService

# ❌ Bad
from app.models.models import QueryRequest
from services.vector_store import VectorStoreService
```

### 2. Leverage Hot Reload
- Edit files in `app/`
- Save and check logs
- No rebuild needed
- Faster iteration

### 3. Use Type Hints
```python
async def process_query(self, query: str) -> QueryResponse:
    # Type hints enable better IDE support and validation
    pass
```

### 4. Document API Endpoints
```python
@app.post("/endpoint", response_model=Response)
async def endpoint(request: Request):
    """
    Clear description.

    ## Example
    ```json
    {"key": "value"}
    ```

    ## Returns
    Description of return value
    """
```

### 5. Handle Errors Gracefully
```python
try:
    result = await service.method()
    return result
except SpecificError as e:
    raise HTTPException(
        status_code=400,
        detail=f"Specific error: {str(e)}"
    )
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Internal error: {str(e)}"
    )
```

---

## Quick Commands Reference

### Development
```bash
# Start services
docker compose up -d

# Watch logs
docker compose logs -f rag-api

# Restart after env changes
docker compose restart rag-api

# Rebuild after dependency changes
docker compose up -d --build

# Stop all
docker compose down
```

### Testing
```bash
# API documentation
open http://localhost:8000/docs

# Health check
curl http://localhost:8000/health

# Qdrant UI
open http://localhost:6333/dashboard
```

### Debugging
```bash
# Shell into container
docker exec -it production-rag-rag-api-1 bash

# Check Python packages
docker exec production-rag-rag-api-1 pip list

# View environment
docker exec production-rag-rag-api-1 env | grep -i api
```

---

## Resources

- **Project Structure**: [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md)
- **Memory File**: [.claude/memory.md](../memory.md)
- **API Docs**: [API_DOCUMENTATION.md](../../API_DOCUMENTATION.md)
- **Architecture**: [ARCHITECTURE.md](../../ARCHITECTURE.md)
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Qdrant Docs**: https://qdrant.tech/documentation
