# Architecture Documentation

## System Overview

The Production RAG Framework is designed as a modular, scalable system that implements production best practices from processing 5M+ documents.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Application                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Server                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                          │   │
│  │  • POST /query      • POST /index                        │   │
│  │  • GET /health      • DELETE /documents/{id}             │   │
│  │  • GET /stats                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RAG Service                                │
│                    (Main Orchestrator)                           │
└─────────┬────────────┬────────────┬────────────┬────────────────┘
          │            │            │            │
          ▼            ▼            ▼            ▼
    ┌─────────┐  ┌──────────┐ ┌─────────┐ ┌────────────┐
    │  Query  │  │  Vector  │ │ Rerank  │ │    LLM     │
    │  Router │  │  Store   │ │ Service │ │  Service   │
    └─────────┘  └──────────┘ └─────────┘ └────────────┘
          │            │            │            │
          │            ▼            ▼            ▼
          │      ┌──────────┐ ┌─────────┐ ┌────────────┐
          │      │ Pinecone │ │ Cohere  │ │   OpenAI   │
          │      │  Vector  │ │ Rerank  │ │  GPT-4 +   │
          │      │    DB    │ │   API   │ │ Embeddings │
          │      └──────────┘ └─────────┘ └────────────┘
          │
          ▼
    ┌──────────────────────────────────────────┐
    │        Query Generation Service          │
    │  • Semantic queries                      │
    │  • Keyword queries                       │
    │  • Context-aware variants                │
    └──────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Application (`main.py`)

**Purpose**: HTTP API layer, request handling, response formatting

**Key Features**:
- RESTful endpoints
- Request validation with Pydantic
- CORS middleware
- Health checks
- Error handling

**Endpoints**:
- `POST /query` - Main RAG query endpoint
- `POST /index` - Document indexing
- `DELETE /documents/{id}` - Document deletion
- `GET /stats` - Vector DB statistics
- `GET /health` - Health check

### 2. RAG Service (`services/rag_service.py`)

**Purpose**: Main orchestration layer that coordinates all RAG operations

**Pipeline Flow**:
```
User Query → Route Query → Generate Variants → Parallel Search →
Rerank → Generate Answer → Return Response
```

**Key Methods**:
- `query()` - Main query handler
- `_handle_rag_query()` - Full RAG pipeline
- `_handle_summarization()` - Summarization queries
- `_handle_metadata_query()` - Metadata queries
- `index_documents()` - Document indexing

### 3. Query Router (`services/query_router.py`)

**Purpose**: Intelligently route queries to appropriate handlers

**Query Types**:
1. **RAG** - Semantic search + answer generation
2. **SUMMARIZATION** - Content summarization
3. **METADATA_QUERY** - Document metadata queries
4. **GENERAL** - Conversational queries

**Routing Methods**:
- Pattern-based (fast, regex matching)
- LLM-based (accurate, for ambiguous cases)

### 4. Query Generation Service (`services/query_generation.py`)

**Purpose**: Generate multiple query variants for comprehensive retrieval

**Implementation**:
```python
Input: "How does deep learning work?"
       + Conversation history

Output:
  - "How does deep learning work?" (semantic)
  - "deep learning working mechanism" (keyword)
  - "explain deep learning process" (variant)
  - "neural networks multiple layers training" (variant)
  - "backpropagation gradient descent learning" (variant)
```

**Benefits**:
- Covers more surface area
- Not dependent on single query interpretation
- Captures context from conversation history

### 5. Vector Store Service (`services/vector_store.py`)

**Purpose**: Pinecone vector database operations

**Key Features**:
- Document embedding (OpenAI text-embedding-3-large)
- Parallel multi-query search
- Metadata filtering
- Batch processing
- Automatic index creation

**Operations**:
- `embed_texts()` - Generate embeddings
- `index_chunks()` - Store chunks in Pinecone
- `search()` - Single query search
- `search_multiple_queries()` - Parallel search with deduplication
- `delete_document()` - Remove document

### 6. Reranking Service (`services/reranker.py`)

**Purpose**: Rerank retrieved chunks for better relevance

**Configuration**:
- Input: 50 chunks
- Output: 15 chunks
- Model: Cohere rerank-english-v3.0

**Why Reranking?**:
- Initial retrieval scores can be noisy
- Cross-encoder rerankers are more accurate than bi-encoders
- Can compensate for suboptimal retrieval
- Significantly improves final answer quality

### 7. LLM Service (`services/llm_service.py`)

**Purpose**: OpenAI GPT-4 integration for answer generation

**Key Methods**:
- `generate_answer()` - RAG answer generation
- `generate_summarization()` - Content summarization
- `answer_metadata_query()` - Metadata-based answers

**Context Building**:
```
[Context 1]
Title: Document Title | Author: John Doe
Chunk text here...

[Context 2]
Title: Another Document | Source: example.com
More chunk text...

Question: User's question
Answer: <LLM generates answer>
```

### 8. Chunking Service (`services/chunking.py`)

**Purpose**: Smart document chunking with metadata injection

**Features**:
- Sentence-aware splitting (no mid-sentence cuts)
- Token-based sizing
- Configurable overlap
- Metadata injection into chunk text
- Handles long sentences

**Chunking Strategy**:
```
Document → Sentences → Group by token count → Add overlap →
Inject metadata → Create chunks
```

## Data Flow

### Indexing Flow

```
1. Client sends documents
   └→ POST /index
       └→ RAGService.index_documents()
           └→ ChunkingService.chunk_with_metadata_injection()
               ├→ Split into logical chunks
               ├→ Inject metadata (title, author, etc.)
               └→ Return chunks
           └→ VectorStoreService.index_chunks()
               ├→ Generate embeddings (OpenAI)
               ├→ Create vectors with metadata
               └→ Batch upsert to Pinecone
```

### Query Flow

```
1. Client sends query
   └→ POST /query
       └→ RAGService.query()
           └→ QueryRouter.route_query()
               ├→ Pattern matching (fast)
               └→ LLM classification (if needed)

           If RAG query:
           └→ QueryGenerationService.generate_queries()
               ├→ Analyze conversation history
               ├→ Generate semantic variants
               └→ Generate keyword variants

           └→ VectorStoreService.search_multiple_queries()
               ├→ Embed all queries (parallel)
               ├→ Search Pinecone (parallel)
               ├→ Combine results
               └→ Deduplicate by chunk ID

           └→ RerankingService.rerank_with_metadata()
               ├→ Enhance chunks with metadata
               ├→ Call Cohere rerank API
               └→ Return top 15 chunks

           └→ LLMService.generate_answer()
               ├→ Build context from chunks
               ├→ Include metadata in context
               ├→ Add conversation history
               └→ Generate answer with GPT-4
```

## Configuration Management

### Environment Variables (`config.py`)

```python
Settings (from .env):
├── API Configuration
│   ├── OPENAI_API_KEY
│   ├── PINECONE_API_KEY
│   └── COHERE_API_KEY
├── RAG Parameters
│   ├── CHUNK_SIZE (512)
│   ├── CHUNK_OVERLAP (50)
│   ├── TOP_K_RETRIEVAL (50)
│   ├── TOP_K_RERANK (15)
│   └── MAX_QUERIES_GENERATED (5)
└── Model Selection
    ├── EMBEDDING_MODEL (text-embedding-3-large)
    └── LLM_MODEL (gpt-4-turbo-preview)
```

## Performance Characteristics

### Latency Breakdown (Typical)

```
Total Query Time: ~3-5 seconds

├── Query Generation: 500-800ms
│   └── LLM call for variants
├── Parallel Search: 200-400ms
│   └── Pinecone queries (parallel)
├── Reranking: 800-1200ms
│   └── Cohere rerank API
└── Answer Generation: 1500-2500ms
    └── GPT-4 generation
```

### Optimization Strategies

1. **Caching**:
   - Cache reranking results for repeated queries
   - Cache embeddings for common queries

2. **Batch Processing**:
   - Index documents in batches
   - Generate embeddings in batches

3. **Parallel Execution**:
   - Multi-query search runs in parallel
   - Can process multiple user requests concurrently

4. **Streaming**:
   - Can stream LLM responses for faster perceived latency

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
    │
    ├─── API Server 1
    ├─── API Server 2
    └─── API Server N
         │
         └─── Shared Services:
              ├── Pinecone (managed, auto-scales)
              ├── OpenAI API (rate-limited)
              └── Cohere API (rate-limited)
```

### Vertical Scaling

- Increase server resources for concurrent requests
- More workers for uvicorn
- Connection pooling for API clients

### Database Scaling

- Pinecone Serverless auto-scales
- Consider namespaces for multi-tenancy
- Pod-based Pinecone for extreme scale

## Security Considerations

1. **API Key Management**:
   - Store keys in environment variables
   - Use secrets manager in production
   - Rotate keys regularly

2. **Input Validation**:
   - Pydantic models validate all inputs
   - Sanitize user queries
   - Limit query length

3. **Rate Limiting**:
   - Implement per-user rate limits
   - Throttle based on API quotas
   - Queue requests during high load

4. **Authentication**:
   - Add JWT/OAuth2 for production
   - API key authentication
   - Role-based access control

## Monitoring & Observability

### Key Metrics to Track

1. **Performance**:
   - Query latency (p50, p95, p99)
   - Indexing throughput
   - API response times

2. **Quality**:
   - Reranking score distribution
   - Number of chunks retrieved
   - Query routing accuracy

3. **Resources**:
   - API quota usage (OpenAI, Cohere)
   - Vector DB operations
   - Memory usage

4. **Errors**:
   - Failed queries
   - Embedding errors
   - Reranking failures

### Logging Strategy

```python
# Structured logging
{
  "query": "user question",
  "query_type": "rag",
  "generated_queries": 5,
  "chunks_retrieved": 50,
  "chunks_reranked": 15,
  "latency_ms": 3200,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Deployment Architectures

### Development
```
Local Machine → FastAPI → External APIs (OpenAI, Pinecone, Cohere)
```

### Production (Cloud)
```
Users → CDN → Load Balancer → Container Service (ECS/GKE/AKS) →
    ├── API Servers (auto-scaling)
    ├── Monitoring (CloudWatch/Prometheus)
    └── Logging (ELK/DataDog)
```

### Production (Serverless)
```
Users → API Gateway → Lambda/Cloud Functions →
    External APIs (managed)
```

## Extension Points

### Custom Components

1. **Custom Chunking**:
   - Implement domain-specific chunking
   - Use ML-based sentence segmentation
   - Add table/image extraction

2. **Custom Reranker**:
   - Use different reranking models
   - Implement custom scoring logic
   - Add business rule filters

3. **Custom Embeddings**:
   - Use open-source models
   - Fine-tune embeddings for domain
   - Multi-modal embeddings

4. **Custom Routing**:
   - Add more query types
   - Implement intent classification
   - Add business logic routing

## Best Practices

1. **Always include metadata** - Title, author, source improve quality
2. **Monitor reranking scores** - Low scores indicate retrieval issues
3. **Tune chunk size** - Balance between context and precision
4. **Use conversation history** - Better query generation
5. **Cache aggressively** - Especially embeddings and reranking
6. **Log everything** - Essential for debugging and optimization
7. **Test with real data** - Synthetic data doesn't reveal issues
8. **Iterate on chunking** - Biggest impact on quality

## References

- Blog post: "Production RAG: what I learned from processing 5M+ documents"
- Pinecone documentation
- OpenAI API documentation
- Cohere Rerank documentation
