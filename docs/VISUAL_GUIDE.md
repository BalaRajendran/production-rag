# Visual Guide to Production RAG Framework

Quick visual reference for understanding the system.

---

## 📁 Project Structure (Visual)

```
production-rag/
│
├── 🚀 GETTING STARTED
│   ├── QUICKSTART.md          ← Start here (5 min)
│   ├── SUMMARY.md             ← What is this?
│   └── example_usage.py       ← Working examples
│
├── 📚 CORE DOCS
│   ├── README.md              ← Complete guide
│   ├── API_DOCUMENTATION.md   ← API reference
│   ├── ARCHITECTURE.md        ← System design
│   ├── DEPLOYMENT.md          ← Deploy guide
│   └── TROUBLESHOOTING.md     ← Fix issues
│
├── 🧠 CLAUDE INTEGRATION
│   └── .claude/
│       ├── memory.md          ← Project context
│       └── skills/
│           └── rag-framework.md ← Dev skills
│
├── ⚙️ CONFIGURATION
│   ├── .env.example           ← API keys template
│   ├── config.py              ← Settings
│   ├── pyproject.toml         ← Dependencies
│   ├── docker-compose.yml     ← Docker setup
│   └── Dockerfile             ← Container image
│
├── 🎯 APPLICATION
│   ├── main.py                ← FastAPI app
│   └── models.py              ← Data models
│
└── 🔧 SERVICES (Business Logic)
    └── services/
        ├── rag_service.py          ← 🎼 Orchestrator
        ├── query_generation.py     ← 🔍 Multi-query (Learning #1)
        ├── vector_store.py         ← 💾 Pinecone
        ├── reranker.py             ← 🏆 Cohere (Learning #2)
        ├── chunking.py             ← ✂️ Smart chunking (Learning #3)
        ├── llm_service.py          ← 🤖 OpenAI GPT-4
        └── query_router.py         ← 🔀 Routing (Learning #5)
```

---

## 🔄 Data Flow (Visual)

### Query Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
│                    "What is machine learning?"                  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: QUERY ROUTING                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pattern Match: "what is" → RAG query                    │  │
│  │  or LLM Classification if ambiguous                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 2: QUERY GENERATION (Learning #1)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Input: "What is machine learning?"                      │  │
│  │  Output:                                                  │  │
│  │    1. "What is machine learning?" (semantic)            │  │
│  │    2. "machine learning definition" (keyword)           │  │
│  │    3. "explain machine learning concepts" (variant)     │  │
│  │    4. "ML fundamentals and principles" (variant)        │  │
│  │    5. "artificial intelligence subset learning" (variant)│  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 3: PARALLEL VECTOR SEARCH                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Search Pinecone with all 5 queries simultaneously       │  │
│  │                                                           │  │
│  │  Query 1 ─┐                                              │  │
│  │  Query 2 ─┤                                              │  │
│  │  Query 3 ─┼──→ Pinecone ──→ 50 chunks (combined)       │  │
│  │  Query 4 ─┤                                              │  │
│  │  Query 5 ─┘                                              │  │
│  │                                                           │  │
│  │  Deduplicate by chunk ID                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 4: RERANKING (Learning #2) ⭐ HIGHEST ROI               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Input: 50 chunks with initial scores                    │  │
│  │                                                           │  │
│  │  Cohere Rerank API:                                      │  │
│  │    - Cross-encoder model                                 │  │
│  │    - Much more accurate than embeddings                  │  │
│  │    - Includes metadata in ranking                        │  │
│  │                                                           │  │
│  │  Output: Top 15 chunks (optimal!)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 5: ANSWER GENERATION (Learning #4)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Build Context from 15 chunks:                           │  │
│  │                                                           │  │
│  │  [Context 1]                                             │  │
│  │  Title: ML Guide | Author: Dr. Smith                     │  │
│  │  Machine learning is a subset of AI...                   │  │
│  │                                                           │  │
│  │  [Context 2]                                             │  │
│  │  Title: AI Basics | Author: Prof. Chen                   │  │
│  │  ML enables computers to learn...                        │  │
│  │                                                           │  │
│  │  ...15 contexts total...                                 │  │
│  │                                                           │  │
│  │  GPT-4 generates comprehensive answer                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                         RESPONSE                                │
│  {                                                              │
│    "answer": "Machine learning is a subset of artificial...",  │
│    "chunks": [15 source chunks with metadata],                 │
│    "generated_queries": [5 query variants],                    │
│    "query_type": "rag",                                        │
│    "metadata": {"chunks_before_rerank": 50, ...}              │
│  }                                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Timing Breakdown (Visual)

```
Total Query Time: ~3-5 seconds
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Query Routing
├─────────────┤  ~100ms (fast pattern match)


Step 2: Query Generation
├──────────────────────────────┤  500-800ms (LLM call)


Step 3: Vector Search (Parallel)
├────────────────┤  200-400ms (Pinecone API)


Step 4: Reranking  ⚠️ LARGEST COMPONENT
├─────────────────────────────────────────┤  800-1200ms (Cohere API)


Step 5: Answer Generation  ⚠️ LARGEST COMPONENT
├────────────────────────────────────────────────────────────┤  1500-2500ms (GPT-4)
```

---

## 🎯 The 5 Blog Learnings (Visual Map)

```
Blog Post: "Production RAG: what I learned from processing 5M+ documents"
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Learning #1  │   │ Learning #2  │   │ Learning #3  │
│    QUERY     │   │  RERANKING   │   │   CHUNKING   │
│ GENERATION   │   │              │   │   STRATEGY   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
  Multi-query          50→15 chunks       Sentence-aware
  semantic +           Highest ROI!       No mid-cuts
  keyword              Cohere v3.0        Logical units

        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐
│ Learning #4  │   │ Learning #5  │
│  METADATA    │   │    QUERY     │
│  TO LLM      │   │   ROUTING    │
└──────┬───────┘   └──────┬───────┘
       │                   │
       ▼                   ▼
  Title, author,      RAG vs Summary
  source in chunks    vs Metadata
  Better context!     Efficiency!
```

---

## 🏗️ Architecture Layers (Visual)

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│  Web App  │  Mobile App  │  CLI  │  Other Services    │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    API LAYER                            │
│              FastAPI (main.py)                          │
│  POST /query  │  POST /index  │  GET /health  │  ...   │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│               ORCHESTRATION LAYER                       │
│            RAGService (rag_service.py)                  │
│  Coordinates all services and pipeline flow             │
└─────┬──────────┬──────────┬──────────┬─────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Query   │ │ Vector  │ │ Rerank  │ │   LLM   │
│ Router  │ │  Store  │ │ Service │ │ Service │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────┐
│                EXTERNAL SERVICES                        │
│  OpenAI API  │  Pinecone  │  Cohere API                │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 Scaling Pattern (Visual)

```
                     Load Balancer
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    API Server 1      API Server 2      API Server N
    (stateless)       (stateless)       (stateless)
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    Pinecone          OpenAI            Cohere
    (managed)         (managed)         (managed)
    Auto-scales       Rate-limited      Rate-limited
```

---

## 🔍 Query Types Decision Tree (Visual)

```
                    User Query
                        │
                        ▼
             ┌──────────────────┐
             │  Pattern Match?  │
             └────┬─────────┬───┘
                  │         │
        Yes ◄─────┘         └─────► No
         │                          │
         ▼                          ▼
    ┌─────────┐             ┌────────────┐
    │ Pattern │             │ LLM Classify│
    │  Found  │             └──────┬──────┘
    └────┬────┘                    │
         │                          │
         └──────────┬───────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
  ┌─────────┐ ┌─────────┐ ┌─────────┐
  │   RAG   │ │ Summary │ │Metadata │
  │  Full   │ │ Direct  │ │ Query   │
  │Pipeline │ │   LLM   │ │ Simple  │
  └─────────┘ └─────────┘ └─────────┘
```

---

## 💾 Storage Pattern (Visual)

```
Document Indexing:

Document (full text)
       │
       ▼
┌──────────────┐
│   Chunking   │  512 tokens each, 50 overlap
└──────┬───────┘
       │
       ├──► Chunk 1 ──► Embedding ──┐
       ├──► Chunk 2 ──► Embedding ──┤
       ├──► Chunk 3 ──► Embedding ──┼──► Pinecone Index
       ├──► Chunk 4 ──► Embedding ──┤    (3072 dimensions)
       └──► Chunk N ──► Embedding ──┘

Each vector includes:
- Embedding (3072 floats)
- Text content
- Metadata (title, author, etc.)
- Document ID
- Chunk index
```

---

## 🎨 API Endpoint Map (Visual)

```
http://localhost:8000
       │
       ├──► GET  /              → API info
       │
       ├──► GET  /health        → Health check
       │                          ✓ Pinecone connected?
       │                          ✓ OpenAI configured?
       │                          ✓ Cohere configured?
       │
       ├──► POST /query         → RAG query (main)
       │         Input: {query, conversation_history?, top_k?, filters?}
       │         Output: {answer, chunks, generated_queries, ...}
       │
       ├──► POST /index         → Index documents
       │         Input: {documents: [{id, content, metadata}]}
       │         Output: {success, documents_processed, chunks_created}
       │
       ├──► DELETE /documents/{id} → Delete document
       │         Output: {success, message}
       │
       ├──► GET  /stats         → Database stats
       │         Output: {total_vectors, dimension, ...}
       │
       ├──► GET  /docs          → Interactive API docs (Swagger)
       │
       └──► GET  /redoc         → Alternative docs (ReDoc)
```

---

## 🛠️ Development Workflow (Visual)

```
┌──────────────────────────────────────────────────────┐
│  1. SETUP                                            │
│     uv pip install -e .                              │
│     cp .env.example .env                             │
│     (edit .env with API keys)                        │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  2. DEVELOP                                          │
│     • Modify services/                               │
│     • Update models.py if needed                     │
│     • Check .claude/skills/ for patterns             │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  3. TEST                                             │
│     python main.py                                   │
│     python example_usage.py                          │
│     curl http://localhost:8000/health                │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  4. DEBUG (if needed)                                │
│     • Check TROUBLESHOOTING.md                       │
│     • Enable debug logging                           │
│     • Test components individually                   │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  5. DEPLOY                                           │
│     See DEPLOYMENT.md                                │
│     • Docker / Kubernetes / Cloud                    │
└──────────────────────────────────────────────────────┘
```

---

## 📊 Quality Metrics Dashboard (Visual)

```
┌─────────────────────────────────────────────────────┐
│  QUERY QUALITY INDICATORS                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Generated Queries: [■■■■■] 5/5  ✓ Good            │
│  Chunks Retrieved: [■■■■■■■■■■] 50  ✓ Good         │
│  Reranking Scores: [■■■■■■■■□□] 0.75-0.95  ✓ Good  │
│  Response Time: [■■■■■□□□□□] 3.2s  ✓ Acceptable    │
│                                                     │
│  ⚠️  If reranking scores < 0.5: Poor retrieval      │
│  ⚠️  If response time > 10s: Check bottlenecks      │
│  ⚠️  If chunks < 10: Insufficient content           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Configuration Impact (Visual)

```
CHUNK_SIZE: 512 tokens (default)
    ↓ Lower (256)        ↑ Higher (1024)
    More precise         More context
    More chunks          Fewer chunks
    Slower indexing      Faster indexing

TOP_K_RETRIEVAL: 50 (default)
    ↓ Lower (30)         ↑ Higher (100)
    Faster reranking     Better coverage
    Less comprehensive   Higher cost

TOP_K_RERANK: 15 (default) ⭐ OPTIMAL
    ↓ Lower (10)         ↑ Higher (20)
    Less context         More context
    Faster              Slower, expensive
```

---

## 🚀 Performance Optimization Checklist (Visual)

```
┌─────────────────────────────────────────┐
│  OPTIMIZATION PRIORITIES                │
├─────────────────────────────────────────┤
│                                         │
│  🔥🔥🔥 HIGHEST IMPACT                  │
│  ├─ Cache reranking results            │
│  ├─ Cache embeddings                   │
│  └─ Reduce query variants (5→3)        │
│                                         │
│  🔥🔥 HIGH IMPACT                       │
│  ├─ Use faster model for simple queries│
│  ├─ Implement connection pooling       │
│  └─ Reduce reranking input (50→30)     │
│                                         │
│  🔥 MEDIUM IMPACT                       │
│  ├─ Batch document indexing            │
│  ├─ Enable streaming responses         │
│  └─ Optimize chunk size                │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🎓 Learning Path (Visual)

```
Beginner Path:
SUMMARY.md → QUICKSTART.md → example_usage.py → README.md
    ↓
Intermediate Path:
API_DOCUMENTATION.md → ARCHITECTURE.md → services/ code
    ↓
Advanced Path:
.claude/memory.md → .claude/skills/ → Custom implementations
    ↓
Production Path:
DEPLOYMENT.md → Monitoring → Scaling → Optimization
```

---

## 📋 Quick Command Reference (Visual)

```
┌────────────────────────────────────────────────────┐
│  COMMAND                 │  PURPOSE                │
├────────────────────────────────────────────────────┤
│  uv pip install -e .     │  Install dependencies   │
│  python main.py          │  Start server           │
│  curl .../health         │  Check health           │
│  python example_usage.py │  Run examples           │
│  docker-compose up       │  Run in Docker          │
│  kubectl apply -f ...    │  Deploy to K8s          │
└────────────────────────────────────────────────────┘
```

---

*This visual guide complements the detailed documentation*
*For full details, see the respective documentation files*
