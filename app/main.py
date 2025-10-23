"""
Production RAG Framework - Main Application.

FastAPI application with production-grade architecture including:
- API versioning (/api/v1)
- Structured logging with correlation IDs
- Redis-backed rate limiting
- Langfuse observability (optional)
- Global error handling
- Request timing and monitoring
"""

from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.observability import get_observability_manager
from app.middleware import (
    TimingMiddleware,
    CorrelationIDMiddleware,
    LoggingMiddleware,
    ErrorHandlerMiddleware,
    RateLimitMiddleware,
)
from app.api.v1 import api_router
from app.api.deps import get_rag_service


# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize RAG service, log configuration
    - Shutdown: Flush observability traces, cleanup resources
    """
    # Startup
    logger.info(
        "Starting Production RAG Framework",
        environment=settings.app.environment,
        version=settings.app.app_version,
        debug=settings.app.debug
    )

    # Initialize RAG service
    rag_service = get_rag_service()
    await rag_service.initialize()
    logger.info("RAG service initialized successfully")

    # Log feature flags
    logger.info(
        "Feature flags",
        rate_limiting=settings.rate_limit.rate_limit_enabled,
        langfuse=settings.observability.langfuse_enabled,
        metrics=settings.observability.enable_metrics
    )

    yield

    # Shutdown
    logger.info("Shutting down Production RAG Framework")

    # Flush observability traces
    obs_manager = get_observability_manager()
    obs_manager.shutdown()

    logger.info("Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.app.app_name,
    description="Production-grade RAG system with query generation, reranking, and smart routing",
    version=settings.app.app_version,
    lifespan=lifespan,
    debug=settings.app.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Add middleware in correct order (reverse of execution order)
# Middleware executes in LIFO order: last added = first executed

# 1. CORS (should be last so it handles all responses)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=settings.app.cors_credentials,
    allow_methods=settings.app.cors_methods,
    allow_headers=settings.app.cors_headers,
)

# 2. Rate limiting
app.add_middleware(RateLimitMiddleware)

# 3. Error handling (catch all errors)
app.add_middleware(ErrorHandlerMiddleware)

# 4. Request/response logging
app.add_middleware(LoggingMiddleware)

# 5. Correlation ID (early so all logs have it)
app.add_middleware(CorrelationIDMiddleware)

# 6. Timing (first in execution, last in response)
app.add_middleware(TimingMiddleware)


# Include API v1 router
app.include_router(
    api_router,
    prefix=f"{settings.app.api_prefix}/v1"
)


# Root endpoint (outside versioning)
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.

    Returns:
        Basic API information and links
    """
    return {
        "name": settings.app.app_name,
        "version": settings.app.app_version,
        "environment": settings.app.environment,
        "docs": "/docs",
        "health": f"{settings.app.api_prefix}/v1/health",
        "api_v1": f"{settings.app.api_prefix}/v1"
    }


# Run application (for development)
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app.api_host,
        port=settings.app.api_port,
        reload=settings.app.debug,
        log_level=settings.observability.log_level.lower()
    )
