"""
Unit tests for configuration module.

Tests hierarchical configuration system, environment variable loading,
validation, and backward compatibility.
"""

import pytest
from pydantic import ValidationError

from app.core.config import (
    AppSettings,
    LLMSettings,
    ObservabilitySettings,
    RAGSettings,
    RateLimitSettings,
    SecuritySettings,
    Settings,
    VectorDBSettings,
    get_settings,
)


class TestAppSettings:
    """Tests for AppSettings."""

    def test_default_values(self, clean_environment):
        """Test default configuration values."""
        settings = AppSettings()
        assert settings.app_name == "Production RAG Framework"
        assert settings.app_version == "1.0.0"
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_prefix == "/api"

    def test_environment_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        monkeypatch.setenv("APP_DEBUG", "false")
        monkeypatch.setenv("APP_API_PORT", "9000")

        settings = AppSettings()
        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.api_port == 9000

    def test_cors_configuration(self):
        """Test CORS settings."""
        settings = AppSettings()
        assert settings.cors_origins == ["*"]
        assert settings.cors_credentials is True
        assert settings.cors_methods == ["*"]


class TestLLMSettings:
    """Tests for LLMSettings."""

    def test_required_api_keys(self, clean_environment):
        """Test that API keys are required."""
        with pytest.raises(ValidationError):
            LLMSettings()

    def test_valid_configuration(self, monkeypatch):
        """Test valid LLM configuration."""
        monkeypatch.setenv("LLM_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_COHERE_API_KEY", "test-cohere-key")

        settings = LLMSettings()
        assert settings.openai_api_key == "test-key"
        assert settings.cohere_api_key == "test-cohere-key"
        assert settings.embedding_model == "text-embedding-3-large"
        assert settings.llm_model == "gpt-4-turbo-preview"

    def test_temperature_validation(self, monkeypatch):
        """Test temperature value validation."""
        monkeypatch.setenv("LLM_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_COHERE_API_KEY", "test-key")

        # Valid temperature
        monkeypatch.setenv("LLM_LLM_TEMPERATURE", "0.5")
        settings = LLMSettings()
        assert settings.llm_temperature == 0.5

        # Invalid temperature (too high)
        monkeypatch.setenv("LLM_LLM_TEMPERATURE", "3.0")
        with pytest.raises(ValidationError):
            LLMSettings()


class TestVectorDBSettings:
    """Tests for VectorDBSettings."""

    def test_default_values(self):
        """Test default Qdrant configuration."""
        settings = VectorDBSettings()
        assert settings.qdrant_host == "localhost"
        assert settings.qdrant_port == 6333
        assert settings.qdrant_collection_name == "rag_collection"
        assert settings.vector_dimension == 3072
        assert settings.distance_metric == "cosine"

    def test_environment_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("VECTOR_QDRANT_HOST", "qdrant.example.com")
        monkeypatch.setenv("VECTOR_QDRANT_PORT", "7333")
        monkeypatch.setenv("VECTOR_QDRANT_API_KEY", "secret-key")

        settings = VectorDBSettings()
        assert settings.qdrant_host == "qdrant.example.com"
        assert settings.qdrant_port == 7333
        assert settings.qdrant_api_key == "secret-key"


class TestRAGSettings:
    """Tests for RAGSettings."""

    def test_default_values(self):
        """Test default RAG configuration."""
        settings = RAGSettings()
        assert settings.chunk_size == 512
        assert settings.chunk_overlap == 50
        assert settings.top_k_retrieval == 50
        assert settings.top_k_rerank == 15
        assert settings.max_queries_generated == 5

    def test_chunk_overlap_validation(self, monkeypatch):
        """Test chunk overlap validation."""
        # Valid: overlap < chunk_size  # noqa: ERA001
        monkeypatch.setenv("RAG_CHUNK_SIZE", "512")
        monkeypatch.setenv("RAG_CHUNK_OVERLAP", "50")
        settings = RAGSettings()
        assert settings.chunk_overlap == 50

        # Invalid: overlap >= chunk_size  # noqa: ERA001
        monkeypatch.setenv("RAG_CHUNK_SIZE", "512")
        monkeypatch.setenv("RAG_CHUNK_OVERLAP", "512")
        with pytest.raises(ValidationError):
            RAGSettings()


class TestRateLimitSettings:
    """Tests for RateLimitSettings."""

    def test_default_values(self):
        """Test default rate limit configuration."""
        settings = RateLimitSettings()
        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_per_minute == 60
        assert settings.rate_limit_per_hour == 1000
        assert settings.redis_enabled is True
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379

    def test_redis_configuration(self, monkeypatch):
        """Test Redis configuration."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("RATE_LIMIT_REDIS_PORT", "6380")
        monkeypatch.setenv("RATE_LIMIT_REDIS_PASSWORD", "secret")

        settings = RateLimitSettings()
        assert settings.redis_host == "redis.example.com"
        assert settings.redis_port == 6380
        assert settings.redis_password == "secret"


class TestObservabilitySettings:
    """Tests for ObservabilitySettings."""

    def test_default_values(self):
        """Test default observability configuration."""
        settings = ObservabilitySettings()
        assert settings.langfuse_enabled is True
        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
        assert settings.enable_metrics is True
        assert settings.enable_correlation_id is True

    def test_langfuse_sample_rate_validation(self, monkeypatch):
        """Test Langfuse sample rate validation."""
        # Valid sample rate
        monkeypatch.setenv("OBS_LANGFUSE_SAMPLE_RATE", "0.5")
        settings = ObservabilitySettings()
        assert settings.langfuse_sample_rate == 0.5

        # Invalid sample rate (too high)
        monkeypatch.setenv("OBS_LANGFUSE_SAMPLE_RATE", "1.5")
        with pytest.raises(ValidationError):
            ObservabilitySettings()


class TestSecuritySettings:
    """Tests for SecuritySettings."""

    def test_default_values(self):
        """Test default security configuration."""
        settings = SecuritySettings()
        assert settings.api_key_enabled is False
        assert settings.max_request_size == 10 * 1024 * 1024  # 10MB
        assert settings.request_timeout == 300  # 5 minutes
        assert settings.enable_security_headers is True


class TestHierarchicalSettings:
    """Tests for hierarchical Settings class."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_hierarchical_access(self, test_env_vars):
        """Test accessing nested settings."""
        settings = get_settings()

        # Test app settings
        assert settings.app.environment == "development"
        assert settings.app.debug is True

        # Test LLM settings
        assert settings.llm.openai_api_key == "test-key"

        # Test vector DB settings
        assert settings.vector_db.qdrant_host == "localhost"

        # Test RAG settings
        assert settings.rag.chunk_size == 512

        # Test rate limit settings
        assert settings.rate_limit.rate_limit_enabled is False

    def test_environment_checks(self, monkeypatch):
        """Test environment checking properties."""
        # Development environment
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False

        # Production environment
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        settings = Settings()
        settings.reload()  # Force reload
        assert settings.is_production is True
        assert settings.is_development is False

    def test_backward_compatibility(self, test_env_vars):
        """Test backward compatibility with legacy code."""
        settings = get_settings()

        # Test legacy property access
        assert settings.openai_api_key == settings.llm.openai_api_key
        assert settings.cohere_api_key == settings.llm.cohere_api_key
        assert settings.embedding_model == settings.llm.embedding_model
        assert settings.qdrant_host == settings.vector_db.qdrant_host
        assert settings.chunk_size == settings.rag.chunk_size
        assert settings.api_host == settings.app.api_host

    def test_settings_reload(self, monkeypatch):
        """Test settings reload functionality."""
        settings = Settings()

        # Initial value
        assert settings.app.environment == "development"

        # Change environment variable
        monkeypatch.setenv("APP_ENVIRONMENT", "production")

        # Reload settings
        settings.reload()

        # Should reflect new value
        assert settings.app.environment == "production"

    def test_lazy_loading(self):
        """Test that settings are loaded lazily."""
        settings = Settings()

        # Settings should be None initially
        assert settings._app is None
        assert settings._llm is None

        # Access triggers loading
        _ = settings.app
        assert settings._app is not None

        # Other settings still None
        assert settings._llm is None


@pytest.mark.parametrize(
    ("env_var", "expected_value"),
    [
        ("development", "development"),
        ("staging", "staging"),
        ("production", "production"),
    ],
)
def test_environment_values(monkeypatch, env_var, expected_value):
    """Test different environment values."""
    monkeypatch.setenv("APP_ENVIRONMENT", env_var)
    settings = AppSettings()
    assert settings.environment == expected_value
