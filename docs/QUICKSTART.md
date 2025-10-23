# Quick Start Guide

Get your Production RAG system running in 5 minutes!

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- API keys for:
  - OpenAI
  - Pinecone
  - Cohere

## Step 1: Install Dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
cd production-rag
uv pip install -e .
```

## Step 2: Set Up Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required keys in `.env`:
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-index
COHERE_API_KEY=...
```

## Step 3: Start the Server

```bash
# Start the FastAPI server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload
```

You should see:
```
Initializing Production RAG Framework...
Connected to Pinecone index: rag-index
RAG Framework ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test It Out

Open a new terminal and run the example script:

```bash
python example_usage.py
```

This will:
1. Check API health ✅
2. Index sample documents about AI/ML 📄
3. Run various query types 🔍
4. Demonstrate conversation history 💬
5. Show query routing in action 🔀

## Step 5: Explore the API

Visit the interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Your First Custom Query

```python
import httpx

# Index your document
response = httpx.post("http://localhost:8000/index", json={
    "documents": [{
        "id": "my-doc-1",
        "content": "Your document content here...",
        "metadata": {
            "title": "My Document",
            "author": "Your Name"
        }
    }]
})

# Query it
response = httpx.post("http://localhost:8000/query", json={
    "query": "What is this document about?"
})

print(response.json()["answer"])
```

## What's Happening Under the Hood?

When you query, the system:

1. **Routes** the query (RAG, summarization, metadata, or general)
2. **Generates** 3-5 query variants for better coverage
3. **Searches** Pinecone with all queries in parallel
4. **Reranks** from 50 chunks → 15 using Cohere
5. **Generates** answer with GPT-4, including metadata

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize chunking in [services/chunking.py](services/chunking.py)
- Adjust configuration in [config.py](config.py)
- Deploy to production (see deployment guide below)

## Common Issues

### "Could not connect to Pinecone"
- Check your API key and environment in `.env`
- Verify your Pinecone account is active
- The system will auto-create the index if it doesn't exist

### "Import errors" in IDE
- Run `uv pip install -e .` to install dependencies
- Restart your IDE/language server

### Rate limits
- OpenAI: Upgrade tier or add delays between requests
- Cohere: Free tier has limits, consider paid plan
- Pinecone: Serverless tier has generous limits

## Production Deployment

For production:

1. Set `API_HOST=0.0.0.0` and `API_PORT=8000` in `.env`
2. Use a production ASGI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
3. Add authentication middleware
4. Set up monitoring and logging
5. Use environment-specific `.env` files
6. Consider adding Redis for caching reranking results

## Support

Questions? Check:
- [README.md](README.md) for full documentation
- [example_usage.py](example_usage.py) for code examples
- FastAPI docs at `/docs` endpoint

Happy RAG building! 🚀
