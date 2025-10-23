"""
Langfuse observability integration for LLM tracing.

Provides optional LLM observability with:
- Trace all LLM calls with token usage
- Track RAG pipeline stages (retrieval, reranking, generation)
- Cost tracking and performance monitoring
- Graceful fallback when not configured
"""

from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

from .config import get_settings
from .logging import get_logger, get_correlation_id

logger = get_logger(__name__)

# Optional imports - gracefully handle if Langfuse is not installed
LANGFUSE_AVAILABLE = False
Langfuse = None

try:
    from langfuse import Langfuse as LangfuseClient
    Langfuse = LangfuseClient
    LANGFUSE_AVAILABLE = True
except ImportError:
    logger.warning("Langfuse not installed. LLM observability will be disabled.")


class ObservabilityManager:
    """
    Manager for LLM observability using Langfuse.

    Gracefully handles missing credentials and provides no-op implementations
    when Langfuse is not configured.
    """

    def __init__(self):
        self.settings = get_settings()
        self._langfuse_client: Optional[Any] = None
        self._enabled = False

        if LANGFUSE_AVAILABLE and self.settings.observability.langfuse_enabled:
            self._initialize_langfuse()

    def _initialize_langfuse(self) -> None:
        """Initialize Langfuse client if credentials are provided."""
        if not self.settings.observability.langfuse_public_key or \
           not self.settings.observability.langfuse_secret_key:
            logger.info("Langfuse credentials not provided. Observability disabled.")
            return

        try:
            if Langfuse is None:
                logger.warning("Langfuse client not available")
                return

            self._langfuse_client = Langfuse(
                public_key=self.settings.observability.langfuse_public_key,
                secret_key=self.settings.observability.langfuse_secret_key,
                host=self.settings.observability.langfuse_host,
            )
            self._enabled = True
            logger.info("Langfuse observability initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Langfuse", error=str(e))
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if observability is enabled."""
        return self._enabled

    def should_sample(self) -> bool:
        """Determine if current request should be sampled based on sample rate."""
        if not self._enabled:
            return False
        import random
        return random.random() < self.settings.observability.langfuse_sample_rate

    def create_trace(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Create a trace for tracking.

        Args:
            name: Trace name
            metadata: Additional metadata

        Returns:
            Trace object or None
        """
        if not self._enabled or not self._langfuse_client:
            return None

        try:
            correlation_id = get_correlation_id()
            trace_metadata = metadata or {}
            if correlation_id:
                trace_metadata["correlation_id"] = correlation_id

            trace = self._langfuse_client.trace(
                name=name,
                metadata=trace_metadata,
                session_id=correlation_id
            )
            return trace
        except Exception as e:
            logger.error("Error creating trace", error=str(e))
            return None

    def log_event(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None
    ) -> None:
        """
        Log an event (simplified tracking).

        Args:
            name: Event name
            metadata: Event metadata
            input_data: Input data
            output_data: Output data
        """
        if not self._enabled:
            return

        try:
            logger.info(
                f"Observability event: {name}",
                metadata=metadata,
                input_sample=str(input_data)[:100] if input_data else None,
                output_sample=str(output_data)[:100] if output_data else None
            )
        except Exception as e:
            logger.error("Error logging event", name=name, error=str(e))

    def flush(self) -> None:
        """Flush any pending traces to Langfuse."""
        if self._enabled and self._langfuse_client:
            try:
                self._langfuse_client.flush()
            except Exception as e:
                logger.error("Error flushing Langfuse", error=str(e))

    def shutdown(self) -> None:
        """Shutdown observability and flush pending traces."""
        if self._enabled and self._langfuse_client:
            try:
                self._langfuse_client.shutdown()
                logger.info("Langfuse observability shut down")
            except Exception as e:
                logger.error("Error shutting down Langfuse", error=str(e))


# Global observability manager instance
_obs_manager: Optional[ObservabilityManager] = None


def get_observability_manager() -> ObservabilityManager:
    """
    Get global observability manager instance.

    Returns:
        Singleton ObservabilityManager instance
    """
    global _obs_manager
    if _obs_manager is None:
        _obs_manager = ObservabilityManager()
    return _obs_manager
