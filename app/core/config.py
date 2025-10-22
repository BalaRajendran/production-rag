from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4-turbo-preview"

    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "rag_collection"

    # Cohere Configuration
    cohere_api_key: str

    # RAG Configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 50
    top_k_rerank: int = 15

    # Query Generation
    max_queries_generated: int = 5

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
