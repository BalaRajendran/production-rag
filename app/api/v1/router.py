"""
API v1 router.

Aggregates all v1 endpoint routers into a single router.
"""

from fastapi import APIRouter

from .endpoints import health, rag, documents, monitoring

# Create v1 API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(rag.router, prefix="", tags=["RAG"])
api_router.include_router(documents.router, prefix="", tags=["Documents"])
api_router.include_router(monitoring.router, prefix="", tags=["Monitoring"])
