# Production RAG Backend Architecture

## Complete Folder Structure

```
production-rag/
├── app/
│   ├── __init__.py
│   ├── main.py                          # Application entry point with middleware stack
│   │
│   ├── api/                             # API layer (versioned)
│   │   ├── __init__.py
│   │   ├── deps.py                      # Shared dependencies (DB, settings, etc.)
│   │   │
│   │   └── v1/                          # Version 1 API
│   │       ├── __init__.py
│   │       ├── router.py                # V1 router aggregator
│   │       │
│   │       └── endpoints/               # Versioned endpoints
│   │           ├── __init__.py
│   │           ├── health.py            # Health check endpoints
│   │           ├── rag.py               # RAG query endpoints
│   │           ├── documents.py         # Document management
│   │           └── monitoring.py        # Stats and monitoring
│   │
│   ├── core/                            # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                    # Hierarchical configuration system
│   │   ├── logging.py                   # Structured logging with correlation IDs
│   │   ├── observability.py             # Langfuse integration
│   │   ├── rate_limiter.py              # Redis-backed rate limiting
│   │   ├── exceptions.py                # Custom exceptions
│   │   └── security.py                  # Security utilities (API keys, etc.)
│   │
│   ├── middleware/                      # Middleware components
│   │   ├── __init__.py
│   │   ├── timing.py                    # Request timing
│   │   ├── correlation.py               # Correlation ID injection
│   │   ├── logging.py                   # Request/response logging
│   │   ├── error_handler.py             # Global error handling
│   │   └── rate_limit.py                # Rate limiting middleware
│   │
│   ├── models/                          # Pydantic models
│   │   ├── __init__.py
│   │   ├── models.py                    # Request/response models
│   │   └── domain.py                    # Domain models
│   │
│   └── services/                        # Business logic (existing)
│       ├── __init__.py
│       ├── rag_service.py               # Main RAG orchestration
│       ├── llm_service.py               # LLM interactions
│       ├── vector_store.py              # Vector DB operations
│       ├── chunking.py                  # Document chunking
│       ├── query_generation.py          # Query generation
│       ├── query_router.py              # Query routing
│       └── reranker.py                  # Reranking service
│
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures and configuration
│   │
│   ├── unit/                            # Unit tests
│   │   ├── __init__.py
│   │   ├── test_config.py               # Configuration tests
│   │   ├── test_logging.py              # Logging tests
│   │   ├── test_rate_limiter.py         # Rate limiter tests
│   │   ├── test_observability.py        # Langfuse tests
│   │   ├── test_chunking.py             # Chunking tests
│   │   ├── test_query_generation.py     # Query generation tests
│   │   └── test_reranker.py             # Reranker tests
│   │
│   ├── integration/                     # Integration tests
│   │   ├── __init__.py
│   │   ├── test_api_v1.py               # V1 API endpoint tests
│   │   ├── test_rag_pipeline.py         # Full RAG pipeline tests
│   │   ├── test_middleware.py           # Middleware integration tests
│   │   └── test_vector_store.py         # Vector DB integration tests
│   │
│   ├── e2e/                             # End-to-end tests
│   │   ├── __init__.py
│   │   ├── test_complete_flow.py        # Complete user flows
│   │   └── test_rate_limiting.py        # Rate limiting E2E tests
│   │
│   └── fixtures/                        # Test data and fixtures
│       ├── __init__.py
│       ├── documents.py                 # Sample documents
│       └── responses.py                 # Sample API responses
│
├── docs/                                # Documentation
│   ├── BACKEND_ARCHITECTURE.md          # This file
│   ├── API_DOCUMENTATION.md             # API endpoints documentation
│   ├── CONFIGURATION.md                 # Configuration guide
│   ├── DEPLOYMENT.md                    # Deployment instructions
│   └── TESTING.md                       # Testing guide
│
├── scripts/                             # Utility scripts
│   ├── setup_db.py                      # Database initialization
│   ├── seed_data.py                     # Seed test data
│   └── benchmark.py                     # Performance benchmarking
│
├── .env.example                         # Environment variables template
├── .env.test                            # Test environment variables
├── docker-compose.yml                   # Local development stack
├── docker-compose.test.yml              # Test environment stack
├── pytest.ini                           # Pytest configuration
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Development dependencies
└── README.md                            # Main documentation
```

## Test Coverage Requirements

### 1. Unit Tests (70%+ coverage)
- **Core Module Tests**
  - Configuration validation and loading
  - Logging formatter and handlers
  - Rate limiter logic (fixed/sliding window)
  - Langfuse trace creation and management
  - Custom exceptions

- **Service Tests**
  - Chunking algorithms (different strategies)
  - Query generation (with mocked LLM)
  - Query routing logic
  - Reranker integration (mocked)
  - Vector store operations (mocked)

### 2. Integration Tests (90%+ coverage)
- **API Endpoint Tests**
  - `GET /api/v1/health` - Health check
  - `POST /api/v1/query` - RAG query with various inputs
  - `POST /api/v1/index` - Document indexing
  - `DELETE /api/v1/documents/{id}` - Document deletion
  - `GET /api/v1/stats` - Statistics retrieval

- **Middleware Tests**
  - Request timing middleware
  - Correlation ID injection and propagation
  - Request/response logging
  - Error handling for various error types
  - Rate limiting enforcement

- **Pipeline Tests**
  - Complete RAG pipeline (query → retrieval → rerank → generate)
  - Document ingestion pipeline
  - Error recovery and fallback behavior

### 3. End-to-End Tests
- Complete user workflows
- Rate limiting across multiple requests
- Concurrent request handling
- Langfuse trace verification
- Performance benchmarks

## Middleware Stack Order

```
Request Flow:
┌─────────────────────────────────────────┐
│ 1. Timing Middleware (start timer)     │
├─────────────────────────────────────────┤
│ 2. Correlation ID (inject/extract)     │
├─────────────────────────────────────────┤
│ 3. Request Logging (log incoming)      │
├─────────────────────────────────────────┤
│ 4. Error Handler (catch all errors)    │
├─────────────────────────────────────────┤
│ 5. Rate Limiter (check limits)         │
├─────────────────────────────────────────┤
│ 6. CORS (handle cross-origin)          │
├─────────────────────────────────────────┤
│ 7. Security Headers (add headers)      │
├─────────────────────────────────────────┤
│ 8. API Endpoints (business logic)      │
└─────────────────────────────────────────┘

Response Flow (reverse order):
┌─────────────────────────────────────────┐
│ 8. API Response                         │
├─────────────────────────────────────────┤
│ 7. Security Headers (already added)    │
├─────────────────────────────────────────┤
│ 6. CORS (already handled)              │
├─────────────────────────────────────────┤
│ 5. Rate Limit Headers (X-RateLimit-*)  │
├─────────────────────────────────────────┤
│ 4. Error Handler (format if error)     │
├─────────────────────────────────────────┤
│ 3. Response Logging (log outgoing)     │
├─────────────────────────────────────────┤
│ 2. Correlation ID (already in context)  │
├─────────────────────────────────────────┤
│ 1. Timing (log duration, add header)   │
└─────────────────────────────────────────┘
```

## Production Dependencies

### Core Framework
- `fastapi==0.115.0` - Web framework
- `uvicorn[standard]==0.32.0` - ASGI server
- `pydantic==2.9.2` - Data validation
- `pydantic-settings==2.6.0` - Settings management
- `python-dotenv==1.0.1` - Environment variables

### Rate Limiting
- `redis==5.0.1` - Redis client for distributed rate limiting
- `slowapi==0.1.9` - FastAPI rate limiting
- `limits==3.10.1` - Rate limiting utilities

### Observability
- `langfuse==2.50.0` - LLM observability and tracing
- `structlog==24.1.0` - Structured logging
- `python-json-logger==2.0.7` - JSON log formatting

### Monitoring
- `prometheus-client==0.19.0` - Metrics collection
- `prometheus-fastapi-instrumentator==7.0.0` - FastAPI metrics

### Existing (keep)
- `qdrant-client==1.12.1` - Vector DB
- `openai==1.54.0` - LLM and embeddings
- `cohere==5.11.0` - Reranking
- `unstructured==0.16.6` - Document processing
- `tiktoken==0.8.0` - Token counting
- `httpx==0.27.2` - HTTP client

## Development Dependencies

### Testing
- `pytest==8.0.0` - Test framework
- `pytest-asyncio==0.23.0` - Async test support
- `pytest-cov==4.1.0` - Coverage reporting
- `pytest-mock==3.12.0` - Mocking utilities
- `httpx==0.27.2` - Test client (already in prod)
- `faker==24.0.0` - Test data generation
- `pytest-env==1.1.3` - Environment variable testing

### Development Tools
- `black==24.1.0` - Code formatting
- `ruff==0.2.0` - Linting
- `mypy==1.8.0` - Type checking
- `pre-commit==3.6.0` - Git hooks

### Debugging
- `ipython==8.21.0` - Enhanced REPL
- `ipdb==0.13.13` - Debugger

## Configuration Strategy

### Environment-based Configuration
- `.env` - Local development (gitignored)
- `.env.example` - Template for all variables
- `.env.test` - Test environment (committed)
- `.env.production` - Production (secret management)

### Hierarchical Settings Groups
1. **AppSettings** - Application metadata, API config
2. **LLMSettings** - OpenAI, Cohere configuration
3. **VectorDBSettings** - Qdrant configuration
4. **RAGSettings** - RAG pipeline parameters
5. **RateLimitSettings** - Rate limiting and Redis
6. **ObservabilitySettings** - Langfuse, logging, metrics
7. **SecuritySettings** - API keys, request limits

## API Versioning Strategy

### Path-based Versioning
- `/api/v1/*` - Current stable API
- `/api/v2/*` - Future version (when needed)

### Version Migration
- V1 remains stable indefinitely
- V2 introduced only for breaking changes
- Clients specify version in URL path
- No version defaults to latest stable

### Endpoint Organization
- **Health**: `/api/v1/health` - System health
- **RAG**: `/api/v1/query` - RAG queries
- **Documents**: `/api/v1/documents/*` - CRUD operations
- **Monitoring**: `/api/v1/stats`, `/api/v1/metrics` - Observability

## Implementation Sequence

### Phase 1: Foundation (Priority 1)
1. Hierarchical configuration system
2. Structured logging setup
3. Error handling and custom exceptions

### Phase 2: Infrastructure (Priority 1)
4. Redis-backed rate limiter
5. Langfuse observability integration
6. Middleware stack creation

### Phase 3: API Structure (Priority 2)
7. API versioning (v1) structure
8. Migrate endpoints to versioned routes
9. Update main.py with new architecture

### Phase 4: Testing (Priority 1)
10. Unit tests for core modules
11. Integration tests for endpoints
12. Middleware tests
13. E2E tests for critical flows

### Phase 5: Observability (Priority 2)
14. Add Langfuse tracing to RAG service
15. Add request/response logging
16. Setup Prometheus metrics

### Phase 6: Infrastructure (Priority 3)
17. Docker Compose for local dev (Redis, Qdrant)
18. Test environment Docker Compose
19. CI/CD pipeline configuration

### Phase 7: Documentation (Priority 3)
20. API documentation (OpenAPI)
21. README updates
22. Deployment guide

## Success Criteria

- [ ] All unit tests passing (70%+ coverage)
- [ ] All integration tests passing (90%+ coverage)
- [ ] Rate limiting enforced on all endpoints
- [ ] Langfuse traces visible for all LLM calls
- [ ] Structured logs with correlation IDs
- [ ] API versioning working (v1)
- [ ] Health checks reporting accurately
- [ ] Redis connection pooling configured
- [ ] Error responses consistent and informative
- [ ] Performance benchmarks established
