# Production RAG Framework - Documentation Index

Complete documentation map for the Production RAG Framework.

---

## 🚀 Getting Started

### New Users Start Here

1. **[SUMMARY.md](SUMMARY.md)** - 5-minute overview of what this project is
2. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
3. **[README.md](README.md)** - Complete guide and features
4. **[example_usage.py](example_usage.py)** - Working code examples

### Quick Links

- **Interactive API Docs:** http://localhost:8000/docs (after starting server)
- **Health Check:** http://localhost:8000/health
- **ReDoc:** http://localhost:8000/redoc

---

## 📚 Core Documentation

### Technical Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and data flow | Developers, Architects |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete API reference | API consumers |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deploy to production | DevOps, SRE |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Debug and fix issues | All users |

### User Guides

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Complete features and usage | All users |
| [QUICKSTART.md](QUICKSTART.md) | Fast setup guide | New users |
| [SUMMARY.md](SUMMARY.md) | High-level overview | Decision makers |
| [example_usage.py](example_usage.py) | Code examples | Developers |

---

## 🎯 By Use Case

### "I want to..."

#### Get Started
- **Install and run** → [QUICKSTART.md](QUICKSTART.md)
- **Understand what this is** → [SUMMARY.md](SUMMARY.md)
- **See it in action** → [example_usage.py](example_usage.py)

#### Develop
- **Understand architecture** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Use the API** → [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Learn skills** → [.claude/skills/rag-framework.md](.claude/skills/rag-framework.md)
- **Understand design** → [.claude/memory.md](.claude/memory.md)

#### Deploy
- **Deploy to cloud** → [DEPLOYMENT.md](DEPLOYMENT.md)
- **Use Docker** → [docker-compose.yml](docker-compose.yml)
- **Configure environment** → [.env.example](.env.example)

#### Troubleshoot
- **Fix issues** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Debug quality** → [TROUBLESHOOTING.md#query-quality-issues](TROUBLESHOOTING.md#query-quality-issues)
- **Debug performance** → [TROUBLESHOOTING.md#performance-issues](TROUBLESHOOTING.md#performance-issues)

#### Extend
- **Add features** → [.claude/skills/rag-framework.md](.claude/skills/rag-framework.md)
- **Customize chunking** → [services/chunking.py](services/chunking.py)
- **Custom routing** → [services/query_router.py](services/query_router.py)

---

## 📖 By Topic

### Configuration

- **Environment setup:** [.env.example](.env.example)
- **Configuration management:** [config.py](config.py)
- **Docker setup:** [docker-compose.yml](docker-compose.yml)

### API Reference

- **Endpoints:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Request models:** [models.py](models.py)
- **Interactive docs:** http://localhost:8000/docs

### Services

- **RAG orchestration:** [services/rag_service.py](services/rag_service.py)
- **Query generation:** [services/query_generation.py](services/query_generation.py)
- **Reranking:** [services/reranker.py](services/reranker.py)
- **Chunking:** [services/chunking.py](services/chunking.py)
- **Vector store:** [services/vector_store.py](services/vector_store.py)
- **LLM service:** [services/llm_service.py](services/llm_service.py)
- **Query routing:** [services/query_router.py](services/query_router.py)

### Architecture

- **System design:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Data flow:** [ARCHITECTURE.md#data-flow](ARCHITECTURE.md#data-flow)
- **Performance:** [ARCHITECTURE.md#performance-characteristics](ARCHITECTURE.md#performance-characteristics)
- **Scaling:** [ARCHITECTURE.md#scalability-considerations](ARCHITECTURE.md#scalability-considerations)

### Deployment

- **Local:** [DEPLOYMENT.md#local-development](DEPLOYMENT.md#local-development)
- **Docker:** [DEPLOYMENT.md#docker-deployment](DEPLOYMENT.md#docker-deployment)
- **AWS:** [DEPLOYMENT.md#aws-deployment](DEPLOYMENT.md#aws-deployment)
- **GCP:** [DEPLOYMENT.md#gcp-deployment](DEPLOYMENT.md#gcp-deployment)
- **Azure:** [DEPLOYMENT.md#azure-deployment](DEPLOYMENT.md#azure-deployment)
- **Kubernetes:** [DEPLOYMENT.md#kubernetes-deployment](DEPLOYMENT.md#kubernetes-deployment)

### Troubleshooting

- **Installation:** [TROUBLESHOOTING.md#installation-issues](TROUBLESHOOTING.md#installation-issues)
- **Configuration:** [TROUBLESHOOTING.md#configuration-issues](TROUBLESHOOTING.md#configuration-issues)
- **API issues:** [TROUBLESHOOTING.md#api-connection-issues](TROUBLESHOOTING.md#api-connection-issues)
- **Quality issues:** [TROUBLESHOOTING.md#query-quality-issues](TROUBLESHOOTING.md#query-quality-issues)
- **Performance:** [TROUBLESHOOTING.md#performance-issues](TROUBLESHOOTING.md#performance-issues)

---

## 🎓 By Skill Level

### Beginner

Start with these in order:

1. [SUMMARY.md](SUMMARY.md) - What is this?
2. [QUICKSTART.md](QUICKSTART.md) - Get it running
3. [README.md](README.md) - Learn the features
4. [example_usage.py](example_usage.py) - See code examples
5. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Learn the API

### Intermediate

You understand the basics, now go deeper:

1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. [services/](services/) - Read the code
3. [.claude/skills/rag-framework.md](.claude/skills/rag-framework.md) - Development patterns
4. [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy it
5. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Debug issues

### Advanced

You're ready to extend and optimize:

1. [.claude/memory.md](.claude/memory.md) - Project deep dive
2. [services/](services/) - Modify services
3. [.claude/skills/rag-framework.md](.claude/skills/rag-framework.md) - Extension patterns
4. [ARCHITECTURE.md#extension-points](ARCHITECTURE.md#extension-points) - Customization
5. Custom implementations

---

## 🔍 By Problem

### "My queries return poor results"

1. [TROUBLESHOOTING.md#query-quality-issues](TROUBLESHOOTING.md#query-quality-issues)
2. [.claude/skills/rag-framework.md#debug-query-quality](.claude/skills/rag-framework.md#debug-query-quality)
3. [services/chunking.py](services/chunking.py) - Adjust chunking
4. [config.py](config.py) - Tune parameters

### "It's too slow"

1. [TROUBLESHOOTING.md#performance-issues](TROUBLESHOOTING.md#performance-issues)
2. [ARCHITECTURE.md#performance-characteristics](ARCHITECTURE.md#performance-characteristics)
3. [.claude/skills/rag-framework.md#add-caching-layer](.claude/skills/rag-framework.md#add-caching-layer)
4. [ARCHITECTURE.md#optimization-strategies](ARCHITECTURE.md#optimization-strategies)

### "Installation fails"

1. [TROUBLESHOOTING.md#installation-issues](TROUBLESHOOTING.md#installation-issues)
2. [QUICKSTART.md#step-1-install-dependencies](QUICKSTART.md#step-1-install-dependencies)
3. [requirements.txt](requirements.txt) or [pyproject.toml](pyproject.toml)

### "Deployment failed"

1. [TROUBLESHOOTING.md#deployment-issues](TROUBLESHOOTING.md#deployment-issues)
2. [DEPLOYMENT.md](DEPLOYMENT.md) - Correct procedure
3. [docker-compose.yml](docker-compose.yml) - Docker config

### "I want to add a feature"

1. [.claude/skills/rag-framework.md](.claude/skills/rag-framework.md)
2. [ARCHITECTURE.md#extension-points](ARCHITECTURE.md#extension-points)
3. [services/](services/) - Relevant service
4. [models.py](models.py) - Add models if needed

---

## 📦 File Structure Reference

### Source Code

```
production-rag/
├── main.py                     # FastAPI application
├── config.py                   # Configuration
├── models.py                   # Pydantic models
└── services/
    ├── __init__.py             # Service exports
    ├── rag_service.py          # Main orchestrator
    ├── vector_store.py         # Pinecone
    ├── query_generation.py     # Multi-query
    ├── reranker.py             # Cohere
    ├── chunking.py             # Document chunking
    ├── llm_service.py          # OpenAI GPT-4
    └── query_router.py         # Routing logic
```

### Configuration

```
├── pyproject.toml              # uv dependencies
├── requirements.txt            # pip dependencies (backup)
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── Dockerfile                  # Container image
└── docker-compose.yml          # Docker Compose
```

### Documentation

```
├── README.md                   # Main documentation
├── SUMMARY.md                  # Quick overview
├── QUICKSTART.md              # 5-minute guide
├── ARCHITECTURE.md            # System design
├── API_DOCUMENTATION.md       # API reference
├── DEPLOYMENT.md              # Deployment guide
├── TROUBLESHOOTING.md         # Problem solving
├── INDEX.md                   # This file
└── example_usage.py           # Code examples
```

### Claude Integration

```
└── .claude/
    ├── memory.md               # Project context
    └── skills/
        └── rag-framework.md    # Development skills
```

---

## 🎯 Common Workflows

### First Time Setup

```
QUICKSTART.md → Install dependencies → Configure .env → Run server → example_usage.py
```

### Learning the System

```
SUMMARY.md → README.md → ARCHITECTURE.md → services/ code
```

### Developing Features

```
.claude/skills/rag-framework.md → services/ → models.py → Test → Deploy
```

### Debugging Issues

```
TROUBLESHOOTING.md → Enable debug logs → Test components → Fix → Verify
```

### Deploying

```
DEPLOYMENT.md → Choose platform → Configure → Deploy → Monitor
```

---

## 📊 Documentation Stats

- **Total Documents:** 12 main files
- **Code Files:** 9 Python files
- **Config Files:** 5 files
- **Total Lines:** ~4,000+ lines of code
- **Documentation Lines:** ~3,000+ lines

---

## 🔗 Quick Navigation

### Most Important Files

1. **[QUICKSTART.md](QUICKSTART.md)** - Start here
2. **[README.md](README.md)** - Complete guide
3. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - API reference
4. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix issues

### For Developers

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design
2. **[.claude/skills/rag-framework.md](.claude/skills/rag-framework.md)** - Dev skills
3. **[services/](services/)** - Source code
4. **[models.py](models.py)** - Data models

### For DevOps

1. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy guide
2. **[docker-compose.yml](docker-compose.yml)** - Docker config
3. **[.env.example](.env.example)** - Environment
4. **[Dockerfile](Dockerfile)** - Container image

---

## 🌟 Key Concepts

### The 5 Blog Learnings

All implemented in this framework:

1. **Query Generation** → [services/query_generation.py](services/query_generation.py)
2. **Reranking** → [services/reranker.py](services/reranker.py)
3. **Chunking** → [services/chunking.py](services/chunking.py)
4. **Metadata** → Throughout all services
5. **Query Routing** → [services/query_router.py](services/query_router.py)

See [.claude/memory.md](.claude/memory.md) for detailed explanations.

---

## 💡 Tips

### Reading Order for New Users

1. **Quick understanding:** SUMMARY.md → QUICKSTART.md
2. **Deep dive:** README.md → ARCHITECTURE.md
3. **Hands-on:** example_usage.py → API_DOCUMENTATION.md
4. **Production:** DEPLOYMENT.md → TROUBLESHOOTING.md

### Reading Order for Developers

1. **Context:** .claude/memory.md → ARCHITECTURE.md
2. **Code:** services/ → models.py → main.py
3. **Skills:** .claude/skills/rag-framework.md
4. **Deploy:** DEPLOYMENT.md

### Search Tips

Use your IDE's search (Cmd+Shift+F / Ctrl+Shift+F):

- Search for `TODO` to find improvement areas
- Search for `FIXME` to find known issues
- Search for `# Learning` to find blog references
- Search for `Example:` to find code examples

---

## 📞 Support

### Self-Service

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Search documentation with Cmd+F
3. Try the interactive docs at `/docs`
4. Run [example_usage.py](example_usage.py)

### External Resources

- **FastAPI:** https://fastapi.tiangolo.com
- **Pinecone:** https://docs.pinecone.io
- **OpenAI:** https://platform.openai.com/docs
- **Cohere:** https://docs.cohere.com

---

## 🔄 Keep Updated

This documentation is current as of the initial release (v1.0.0).

When you make changes:

1. Update relevant documentation files
2. Update this INDEX.md if adding new files
3. Update [.claude/memory.md](.claude/memory.md) with learnings
4. Update version numbers in files

---

## ✅ Checklist for New Users

- [ ] Read [SUMMARY.md](SUMMARY.md)
- [ ] Complete [QUICKSTART.md](QUICKSTART.md)
- [ ] Run [example_usage.py](example_usage.py)
- [ ] Read [README.md](README.md)
- [ ] Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [ ] Understand [ARCHITECTURE.md](ARCHITECTURE.md)
- [ ] Bookmark [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [ ] Plan [DEPLOYMENT.md](DEPLOYMENT.md)

---

*Last Updated: 2024*
*Documentation Version: 1.0.0*
*Project Status: Complete ✅*
