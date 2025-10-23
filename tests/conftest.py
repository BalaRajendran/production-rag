"""
Pytest configuration and fixtures for testing.

This file contains shared fixtures and configuration for all tests.
"""

import os
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment variables before importing app
os.environ["APP_ENVIRONMENT"] = "development"
os.environ["APP_DEBUG"] = "true"
os.environ["LLM_OPENAI_API_KEY"] = "test-openai-key"
os.environ["LLM_COHERE_API_KEY"] = "test-cohere-key"
os.environ["VECTOR_QDRANT_HOST"] = "localhost"
os.environ["VECTOR_QDRANT_PORT"] = "6333"
os.environ["RATE_LIMIT_RATE_LIMIT_ENABLED"] = "false"  # Disable rate limiting in tests
os.environ["RATE_LIMIT_REDIS_ENABLED"] = "false"  # Use in-memory rate limiting
os.environ["OBS_LANGFUSE_ENABLED"] = "false"  # Disable Langfuse in tests

from app.core.config import Settings, get_settings  # noqa: E402
from app.main import app  # noqa: E402

# ==============================================================================
# Session Fixtures
# ==============================================================================


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Get test settings instance."""
    return get_settings()


# ==============================================================================
# Test Client Fixtures
# ==============================================================================


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous test client for FastAPI application.

    Usage:
        def test_endpoint(client):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous test client for FastAPI application.

    Usage:
        async def test_endpoint(async_client):
            response = await async_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ==============================================================================
# Mock Fixtures
# ==============================================================================


@pytest.fixture()
def mock_redis(mocker):
    """Mock Redis client for rate limiting tests."""
    mock_client = mocker.Mock()
    mock_client.ping.return_value = True
    mock_client.pipeline.return_value = mock_client
    mock_client.zremrangebyscore.return_value = None
    mock_client.zcard.return_value = 0
    mock_client.zadd.return_value = 1
    mock_client.expire.return_value = True
    mock_client.execute.return_value = [None, 0, 1, True]
    return mock_client


@pytest.fixture()
def mock_qdrant(mocker):
    """Mock Qdrant client for vector store tests."""
    mock_client = mocker.Mock()
    mock_client.get_collections.return_value = mocker.Mock(collections=[])
    mock_client.create_collection.return_value = True
    mock_client.upsert.return_value = True
    mock_client.search.return_value = []
    mock_client.delete.return_value = True
    return mock_client


@pytest.fixture()
def mock_openai(mocker):
    """Mock OpenAI client for LLM tests."""
    mock_client = mocker.Mock()

    # Mock embeddings
    mock_embedding_response = mocker.Mock()
    mock_embedding_response.data = [mocker.Mock(embedding=[0.1] * 3072)]
    mock_embedding_response.usage = mocker.Mock(total_tokens=100)
    mock_client.embeddings.create.return_value = mock_embedding_response

    # Mock chat completions
    mock_completion_response = mocker.Mock()
    mock_choice = mocker.Mock()
    mock_choice.message.content = "Test response"
    mock_completion_response.choices = [mock_choice]
    mock_completion_response.usage = mocker.Mock(
        prompt_tokens=50, completion_tokens=20, total_tokens=70
    )
    mock_client.chat.completions.create.return_value = mock_completion_response

    return mock_client


@pytest.fixture()
def mock_cohere(mocker):
    """Mock Cohere client for reranking tests."""
    mock_client = mocker.Mock()

    # Mock rerank response
    mock_result = mocker.Mock()
    mock_result.index = 0
    mock_result.relevance_score = 0.95

    mock_response = mocker.Mock()
    mock_response.results = [mock_result]

    mock_client.rerank.return_value = mock_response

    return mock_client


# ==============================================================================
# Data Fixtures
# ==============================================================================


@pytest.fixture()
def sample_document():
    """Sample document for testing."""
    return {
        "id": "test-doc-1",
        "content": "This is a test document about Python programming. "
        "Python is a high-level programming language known for its simplicity.",
        "metadata": {
            "title": "Python Programming Guide",
            "author": "Test Author",
            "source": "test.com",
            "category": "programming",
        },
    }


@pytest.fixture()
def sample_documents():
    """Multiple sample documents for testing."""
    return [
        {
            "id": "doc-1",
            "content": "FastAPI is a modern web framework for building APIs with Python.",
            "metadata": {"title": "FastAPI Guide", "category": "web"},
        },
        {
            "id": "doc-2",
            "content": "Redis is an in-memory data structure store used as a database and cache.",
            "metadata": {"title": "Redis Overview", "category": "database"},
        },
        {
            "id": "doc-3",
            "content": "Qdrant is a vector similarity search engine for machine learning.",
            "metadata": {"title": "Qdrant Introduction", "category": "ml"},
        },
    ]


@pytest.fixture()
def sample_query_request():
    """Sample query request for testing."""
    return {
        "query": "What is Python programming?",
        "conversation_history": [
            {"role": "user", "content": "Tell me about programming languages"},
            {
                "role": "assistant",
                "content": "There are many programming languages like Python, Java, etc.",
            },
        ],
    }


@pytest.fixture()
def sample_index_request(sample_documents):
    """Sample index request for testing."""
    return {"documents": sample_documents}


# ==============================================================================
# Environment Fixtures
# ==============================================================================


@pytest.fixture()
def _clean_environment(monkeypatch):
    """Clean environment for testing configuration."""
    # Remove all environment variables with our prefixes
    for key in list(os.environ.keys()):
        if key.startswith(("APP_", "LLM_", "VECTOR_", "RAG_", "RATE_LIMIT_", "OBS_", "SECURITY_")):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def _test_env_vars(monkeypatch):
    """Set test environment variables."""
    test_vars = {
        "APP_ENVIRONMENT": "development",
        "APP_DEBUG": "true",
        "LLM_OPENAI_API_KEY": "test-key",
        "LLM_COHERE_API_KEY": "test-key",
        "VECTOR_QDRANT_HOST": "localhost",
        "RATE_LIMIT_RATE_LIMIT_ENABLED": "false",
        "OBS_LANGFUSE_ENABLED": "false",
    }
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)


# ==============================================================================
# Utility Fixtures
# ==============================================================================


@pytest.fixture()
def correlation_id():
    """Generate a test correlation ID."""
    return "test-correlation-id-12345"


@pytest.fixture()
def mock_logger(mocker):
    """Mock logger for testing logging functionality."""
    return mocker.Mock()


# ==============================================================================
# Pytest Configuration Hooks
# ==============================================================================


def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test location."""
    for item in items:
        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in integration directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add e2e marker to tests in e2e directory
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
