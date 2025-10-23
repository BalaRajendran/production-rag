"""
Production-grade hierarchical configuration system.

Supports multiple environments (dev, staging, production) with validation,
secrets management, and feature flags.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-level settings."""

    # Application Metadata
    app_name: str = "Production RAG Framework"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"

    # CORS Configuration
    cors_origins: list[str] = Field(default=["*"])
    cors_credentials: bool = True
    cors_methods: list[str] = Field(default=["*"])
    cors_headers: list[str] = Field(default=["*"])

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_", case_sensitive=False, extra="ignore"
    )


class LLMSettings(BaseSettings):
    """LLM and Embedding configuration."""

    # OpenAI Configuration
    openai_api_key: str
    openai_base_url: str | None = None
    openai_organization: str | None = None

    # Model Configuration
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    llm_timeout: int = 60

    # Cohere Configuration (for reranking)
    cohere_api_key: str
    reranker_model: str = "rerank-english-v3.0"

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="LLM_", case_sensitive=False, extra="ignore"
    )


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""

    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "rag_collection"
    qdrant_timeout: int = 30

    # Vector Configuration
    vector_dimension: int = 3072
    distance_metric: Literal["cosine", "euclidean", "dot"] = "cosine"

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="VECTOR_", case_sensitive=False, extra="ignore"
    )


class RAGSettings(BaseSettings):
    """RAG pipeline configuration."""

    # Chunking Configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 100

    # Retrieval Configuration
    top_k_retrieval: int = 50
    top_k_rerank: int = 15
    similarity_threshold: float = 0.7

    # Query Generation
    max_queries_generated: int = 5
    enable_query_routing: bool = True

    # Generation Configuration
    include_sources: bool = True
    max_context_length: int = 8000

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 512)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="RAG_", case_sensitive=False, extra="ignore"
    )


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_burst: int = 10

    # Redis Configuration (for distributed rate limiting)
    redis_enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_ssl: bool = False
    redis_timeout: int = 5

    # Strategy
    rate_limit_strategy: Literal["fixed-window", "sliding-window", "token-bucket"] = (
        "sliding-window"
    )
    rate_limit_key_prefix: str = "ratelimit"

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="RATE_LIMIT_", case_sensitive=False, extra="ignore"
    )


class ObservabilitySettings(BaseSettings):
    """Observability and monitoring configuration."""

    # Langfuse Configuration
    langfuse_enabled: bool = True
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_sample_rate: float = 1.0  # 1.0 = trace everything

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text", "console"] = "console"
    log_file: str | None = None
    log_rotation: str = "100 MB"
    log_retention: int = 30  # days

    # Metrics
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Tracing
    enable_request_logging: bool = True
    enable_correlation_id: bool = True
    log_request_body: bool = False  # Security: disable in production
    log_response_body: bool = False

    @field_validator("langfuse_sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("langfuse_sample_rate must be between 0 and 1")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="OBS_", case_sensitive=False, extra="ignore"
    )


class SecuritySettings(BaseSettings):
    """Security configuration."""

    # API Key Authentication (optional)
    api_key_enabled: bool = False
    api_keys: list[str] = Field(default=[])

    # Request Security
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 300  # 5 minutes

    # Security Headers
    enable_security_headers: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SECURITY_", case_sensitive=False, extra="ignore"
    )


class Settings:
    """
    Hierarchical settings manager.

    Combines all setting groups into a single interface with lazy loading.
    """

    def __init__(self):
        self._app: AppSettings | None = None
        self._llm: LLMSettings | None = None
        self._vector_db: VectorDBSettings | None = None
        self._rag: RAGSettings | None = None
        self._rate_limit: RateLimitSettings | None = None
        self._observability: ObservabilitySettings | None = None
        self._security: SecuritySettings | None = None

    @property
    def app(self) -> AppSettings:
        if self._app is None:
            self._app = AppSettings()
        return self._app

    @property
    def llm(self) -> LLMSettings:
        if self._llm is None:
            self._llm = LLMSettings()
        return self._llm

    @property
    def vector_db(self) -> VectorDBSettings:
        if self._vector_db is None:
            self._vector_db = VectorDBSettings()
        return self._vector_db

    @property
    def rag(self) -> RAGSettings:
        if self._rag is None:
            self._rag = RAGSettings()
        return self._rag

    @property
    def rate_limit(self) -> RateLimitSettings:
        if self._rate_limit is None:
            self._rate_limit = RateLimitSettings()
        return self._rate_limit

    @property
    def observability(self) -> ObservabilitySettings:
        if self._observability is None:
            self._observability = ObservabilitySettings()
        return self._observability

    @property
    def security(self) -> SecuritySettings:
        if self._security is None:
            self._security = SecuritySettings()
        return self._security

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment == "development"

    # Backward compatibility properties for legacy code
    @property
    def openai_api_key(self) -> str:
        return self.llm.openai_api_key

    @property
    def cohere_api_key(self) -> str:
        return self.llm.cohere_api_key

    @property
    def embedding_model(self) -> str:
        return self.llm.embedding_model

    @property
    def llm_model(self) -> str:
        return self.llm.llm_model

    @property
    def qdrant_host(self) -> str:
        return self.vector_db.qdrant_host

    @property
    def qdrant_port(self) -> int:
        return self.vector_db.qdrant_port

    @property
    def qdrant_collection_name(self) -> str:
        return self.vector_db.qdrant_collection_name

    @property
    def chunk_size(self) -> int:
        return self.rag.chunk_size

    @property
    def chunk_overlap(self) -> int:
        return self.rag.chunk_overlap

    @property
    def top_k_retrieval(self) -> int:
        return self.rag.top_k_retrieval

    @property
    def top_k_rerank(self) -> int:
        return self.rag.top_k_rerank

    @property
    def max_queries_generated(self) -> int:
        return self.rag.max_queries_generated

    @property
    def api_host(self) -> str:
        return self.app.api_host

    @property
    def api_port(self) -> int:
        return self.app.api_port

    def reload(self) -> None:
        """Reload all settings (useful for testing)."""
        self._app = None
        self._llm = None
        self._vector_db = None
        self._rag = None
        self._rate_limit = None
        self._observability = None
        self._security = None


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Singleton Settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
