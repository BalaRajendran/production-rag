"""
Test script to demonstrate beautiful production-grade logging.

Run this to see the new logging output in action.
"""

import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging import setup_logging, get_logger
from app.core.config import get_settings

# Setup logging
settings = get_settings()
setup_logging()

# Get logger
logger = get_logger(__name__)

def demo_logging():
    """Demonstrate various log levels and formats."""

    print("\n" + "="*80)
    print("PRODUCTION-GRADE LOGGING DEMONSTRATION")
    print("="*80 + "\n")

    # Basic log levels
    logger.debug("This is a debug message", module="test", function="demo_logging")
    logger.info("Application started successfully", version="1.0.0", environment="development")
    logger.warning("This is a warning message", threshold=0.7, actual=0.65)
    logger.error("An error occurred", error_code="E001", severity="medium")

    # Feature flags
    logger.info(
        "Feature flags configured",
        rate_limiting=True,
        langfuse=False,
        metrics=True,
        query_routing=True
    )

    # Simulated HTTP requests
    print("\n--- HTTP Request Logs ---\n")

    # GET request
    logger.info(
        "Successful response",
        method="GET",
        path="/api/v1/health",
        status_code=200,
        duration_ms=23.45,
        client_host="127.0.0.1"
    )

    # POST request with query params
    logger.info(
        "Successful response",
        method="POST",
        path="/api/v1/rag/query",
        status_code=200,
        duration_ms=456.78,
        client_host="127.0.0.1",
        query_params={"stream": "true", "limit": "10"}
    )

    # Slow request (warning color)
    logger.info(
        "Successful response",
        method="GET",
        path="/api/v1/documents",
        status_code=200,
        duration_ms=1234.56,
        client_host="192.168.1.10"
    )

    # Client error
    logger.warning(
        "Client error response",
        method="POST",
        path="/api/v1/documents/upload",
        status_code=400,
        duration_ms=12.34,
        client_host="127.0.0.1"
    )

    # Server error
    logger.error(
        "Server error response",
        method="GET",
        path="/api/v1/rag/query",
        status_code=500,
        duration_ms=89.12,
        client_host="127.0.0.1"
    )

    # Different HTTP methods
    print("\n--- Different HTTP Methods ---\n")

    for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
        logger.info(
            "Successful response",
            method=method,
            path=f"/api/v1/resource/123",
            status_code=200,
            duration_ms=45.67,
            client_host="127.0.0.1"
        )

    # Complex log entry
    print("\n--- Complex Log Entry ---\n")

    logger.info(
        "RAG query completed",
        query="What is machine learning?",
        chunks_retrieved=50,
        chunks_reranked=15,
        chunks_used=5,
        total_duration_ms=567.89,
        embedding_time_ms=123.45,
        retrieval_time_ms=234.56,
        reranking_time_ms=89.12,
        generation_time_ms=120.76,
        model="gpt-4-turbo-preview",
        tokens_used=450
    )

    # Database operations
    print("\n--- Database Operations ---\n")

    logger.info(
        "Connected to Qdrant collection",
        collection="rag_collection",
        host="localhost",
        port=6333,
        vectors_count=15000
    )

    logger.info(
        "Redis connection established for rate limiting",
        host="localhost",
        port=6379,
        db=0
    )

    # Performance metrics
    print("\n--- Performance Metrics ---\n")

    logger.info(
        "Performance snapshot",
        requests_per_second=125,
        avg_response_time_ms=234.56,
        p95_response_time_ms=567.89,
        p99_response_time_ms=1234.56,
        cache_hit_rate=0.87,
        error_rate=0.001
    )

    print("\n" + "="*80)
    print("END OF DEMONSTRATION")
    print("="*80 + "\n")

    print("\nTips:")
    print("- Set OBS_LOG_FORMAT=text in .env for colored output (development)")
    print("- Set OBS_LOG_FORMAT=json in .env for machine-readable logs (production)")
    print("- Adjust OBS_LOG_LEVEL to control verbosity (DEBUG, INFO, WARNING, ERROR)")
    print()


if __name__ == "__main__":
    demo_logging()
