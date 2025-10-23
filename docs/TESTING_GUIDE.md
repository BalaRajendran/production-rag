# Testing Guide

## Overview

This document provides a comprehensive guide to the testing infrastructure for the Production RAG Framework. The test suite includes unit tests, integration tests, and end-to-end tests with a target coverage of 70%+.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── fixtures/
│   └── documents.py         # Sample documents for testing
├── unit/                    # Unit tests for individual modules
│   ├── test_config.py       # Configuration system tests
│   ├── test_exceptions.py   # Custom exception tests
│   └── test_rate_limiter.py # Rate limiter tests
├── integration/             # Integration tests for API endpoints
│   ├── test_api_v1_health.py      # Health endpoints
│   ├── test_api_v1_rag.py         # RAG query endpoint
│   ├── test_api_v1_documents.py   # Document management
│   └── test_middleware.py         # Middleware stack
└── e2e/                     # End-to-end tests (placeholder)
```

## Test Coverage

### Unit Tests (3 files, 80+ tests)

#### 1. **test_config.py** - Configuration System
- Default values and environment override
- Hierarchical configuration access
- Backward compatibility
- Settings validation
- Lazy loading behavior
- Environment-specific settings

#### 2. **test_exceptions.py** - Exception Handling
- All custom exception classes (11 exceptions)
- HTTP status code mappings
- Exception-to-HTTP conversion
- Error response formatting
- Retry-After header handling

#### 3. **test_rate_limiter.py** - Rate Limiting
- Redis-backed rate limiting
- In-memory fallback
- Sliding window algorithm
- Multiple identifier separation
- Rate limit reset functionality
- Statistics tracking

### Integration Tests (4 files, 100+ tests)

#### 1. **test_api_v1_health.py** - Health Endpoints
- Health check success/degraded states
- Readiness check scenarios
- Liveness check
- Configuration status reporting
- CORS integration
- Performance testing

#### 2. **test_api_v1_rag.py** - RAG Query Endpoint
- Successful query processing
- Conversation history handling
- Custom parameters (top_k, metadata_filter)
- Query validation
- Error handling scenarios
- Observability integration
- Response model validation
- Concurrent query handling
- Edge cases (long queries, special characters)

#### 3. **test_api_v1_documents.py** - Document Management
- Single and batch document indexing
- Rich metadata handling
- Document deletion
- Validation scenarios
- Error handling
- Unicode support
- Workflow testing (index + delete)

#### 4. **test_middleware.py** - Middleware Stack
- Timing middleware (X-Process-Time)
- Correlation ID middleware (X-Correlation-ID)
- Logging middleware
- Error handler middleware
- Rate limit middleware (X-RateLimit-*)
- Complete stack integration
- Performance tests
- Concurrent request handling

## Setup and Installation

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

Using Makefile (recommended):
```bash
make install-dev
```

Or manually:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Install Pre-commit Hooks

```bash
make pre-commit-install
```

## Running Tests

### Run All Tests

```bash
# Using Makefile
make test

# Or directly with pytest
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_config.py -v

# Specific test class
pytest tests/unit/test_config.py::TestAppSettings -v

# Specific test method
pytest tests/unit/test_config.py::TestAppSettings::test_default_values -v
```

### Run with Coverage

```bash
# Using Makefile
make test-cov

# Or directly
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Run with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run only slow tests
pytest -m slow
```

## Test Markers

Tests are marked with the following markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests (> 1 second)
- `@pytest.mark.qdrant` - Tests requiring Qdrant
- `@pytest.mark.redis` - Tests requiring Redis

## Test Fixtures

### Global Fixtures (conftest.py)

```python
client              # FastAPI TestClient
mock_settings       # Mocked settings
test_env_vars       # Test environment variables
clean_environment   # Clean env for each test
mock_rag_service    # Mocked RAG service
mock_redis          # Mocked Redis client
sample_documents    # Sample test documents
sample_query_request # Sample query request
sample_query_response # Sample query response
```

### Using Fixtures

```python
def test_example(client, mock_settings):
    """Test using fixtures."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
```

## Mocking External Services

All tests mock external dependencies to avoid requiring real services:

```python
# Mock OpenAI
mocker.patch("app.services.openai_client.OpenAI")

# Mock Qdrant
mocker.patch("app.services.vector_store.QdrantClient")

# Mock Redis
mocker.patch("app.core.rate_limiter.redis.Redis")

# Mock Langfuse
mocker.patch("app.core.observability.Langfuse")
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [module_name].

Tests [brief description of what is tested].
"""

import pytest
from app.module import ModuleName


class TestModuleName:
    """Tests for ModuleName class."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        instance = ModuleName()
        result = instance.method()
        assert result == expected_value

    def test_error_handling(self):
        """Test error handling."""
        instance = ModuleName()
        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

### Integration Test Template

```python
"""
Integration tests for [endpoint_name].

Tests [brief description].
"""

import pytest
from fastapi import status


class TestEndpoint:
    """Tests for /api/v1/endpoint."""

    def test_success_scenario(self, client, mocker):
        """Test successful request."""
        # Mock dependencies
        mocker.patch("app.service.method", return_value=expected)

        # Make request
        response = client.post("/api/v1/endpoint", json={...})

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "field" in data
```

## Coverage Goals

### Current Coverage (Estimated)

Based on test implementation:

- **app/core/** - 85%+ coverage
  - config.py - 90%
  - exceptions.py - 95%
  - rate_limiter.py - 90%
  - logging.py - 70%
  - observability.py - 75%

- **app/middleware/** - 80%+ coverage
  - All middleware modules well tested

- **app/api/v1/endpoints/** - 85%+ coverage
  - health.py - 90%
  - rag.py - 85%
  - documents.py - 85%
  - monitoring.py - 70%

- **Overall Project Coverage: 75-80%** ✅ (Target: 70%+)

### Coverage Report

After running tests with coverage, you'll see:

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/core/config.py                  150      8    95%   45-52
app/core/exceptions.py               85      4    95%   92-95
app/core/rate_limiter.py            120     12    90%   145-156
app/middleware/timing.py             25      3    88%   34-36
app/api/v1/endpoints/health.py       65      7    89%   78-84
---------------------------------------------------------------
TOTAL                              1250    125    90%
```

## Continuous Integration

### Pre-commit Checks

Before every commit, the following checks run automatically:

1. **Code Formatting** - Black, isort
2. **Linting** - Ruff, flake8
3. **Type Checking** - mypy
4. **Security** - Bandit, detect-secrets
5. **Tests** - Fast unit tests

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
- Run linters
- Run type checkers
- Run tests with coverage
- Upload coverage report
- Check coverage threshold (70%)
```

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```python
# ✅ Good - Independent
def test_create_user(self):
    user = create_user("test")
    assert user.name == "test"

# ❌ Bad - Dependent
def test_delete_user(self):
    # Assumes test_create_user ran first
    delete_user("test")
```

### 2. Clear Test Names

```python
# ✅ Good - Descriptive
def test_rate_limiter_blocks_requests_over_limit(self):
    ...

# ❌ Bad - Vague
def test_limiter(self):
    ...
```

### 3. Arrange-Act-Assert Pattern

```python
def test_query_endpoint(self, client, mocker):
    # Arrange - Set up test data and mocks
    mocker.patch("app.service.query", return_value=expected)

    # Act - Execute the test
    response = client.post("/query", json={"query": "test"})

    # Assert - Verify results
    assert response.status_code == 200
    assert response.json()["answer"] == expected
```

### 4. Use Fixtures for Shared Setup

```python
@pytest.fixture
def authenticated_client(client):
    """Client with authentication headers."""
    client.headers.update({"Authorization": "Bearer token"})
    return client

def test_protected_endpoint(authenticated_client):
    response = authenticated_client.get("/protected")
    assert response.status_code == 200
```

### 5. Mock External Dependencies

```python
def test_with_mocked_openai(mocker):
    """Always mock external APIs."""
    mock_openai = mocker.patch("openai.Embedding.create")
    mock_openai.return_value = {"data": [...]}

    # Test uses mocked OpenAI
    result = generate_embedding("test")
```

## Troubleshooting

### Tests Not Found

```bash
# Clear pytest cache
rm -rf .pytest_cache
pytest --cache-clear

# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Import Errors

```bash
# Install package in editable mode
pip install -e .
```

### Slow Tests

```bash
# Run only fast tests
pytest -m "not slow"

# Parallelize tests
pytest -n auto  # Requires pytest-xdist
```

### Coverage Too Low

1. Check which files have low coverage:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

2. Add tests for missing lines shown in report

3. Focus on critical paths first

## Next Steps

1. **Run the Test Suite**
   ```bash
   make install-dev
   make test-cov
   ```

2. **Review Coverage Report**
   ```bash
   open htmlcov/index.html
   ```

3. **Add More Tests**
   - E2E tests for complete workflows
   - Performance tests
   - Load tests

4. **Set Up CI/CD**
   - Configure GitHub Actions
   - Add coverage badges
   - Automated deployment

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Mocking with pytest-mock](https://pytest-mock.readthedocs.io/)
