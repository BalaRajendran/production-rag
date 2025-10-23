"""Comprehensive Logging Configuration

Production-grade logging setup with structured logging using structlog.
Enhanced with beautiful console output for development and JSON for production.
"""

import logging
import logging.config
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import structlog

from .config import get_settings

# Define log levels
LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

# Context variable for correlation ID
_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return _correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    _correlation_id_var.set(correlation_id)


def correlation_id_processor(_logger: Any, _method_name: str, event_dict: Any) -> Any:
    """Add correlation ID to log entries for request tracing."""
    cid = get_correlation_id()
    if cid:
        event_dict["correlation_id"] = cid

    return event_dict


def add_app_context(_logger: Any, _method_name: str, event_dict: Any) -> Any:
    """Add application context to log entries."""
    settings = get_settings()
    event_dict["app"] = settings.app.app_name
    event_dict["environment"] = settings.app.environment
    return event_dict


def setup_logging() -> None:
    """Set up comprehensive logging configuration.

    Automatically configures logging based on settings:
    - Development: Colored console output with structlog
    - Production: JSON format for log aggregation
    """
    settings = get_settings()

    log_level = settings.observability.log_level
    log_format = settings.observability.log_format
    log_file = settings.observability.log_file

    # Configure standard library logging first
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "stream": sys.stdout,
        },
    }

    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
        }

    # Basic logging config
    basic_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        "handlers": {
            name: {**handler, "formatter": "simple"} for name, handler in handlers.items()
        },
        "loggers": {
            "": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": True,
            },
            # Silence noisy third-party loggers
            "uvicorn": {
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "propagate": False,
            },
            "httpcore": {
                "level": "WARNING",
                "propagate": False,
            },
            "qdrant_client": {
                "level": "WARNING",
                "propagate": False,
            },
            "openai": {
                "level": "WARNING",
                "propagate": False,
            },
            "cohere": {
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(basic_config)

    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add correlation ID processor if enabled
    if settings.observability.enable_correlation_id:
        shared_processors.insert(0, correlation_id_processor)

    # Add app context
    shared_processors.insert(0, add_app_context)

    if log_format == "json":
        # JSON formatting for production
        final_processor = structlog.processors.JSONRenderer()
    else:
        # Console formatting for development with colors
        final_processor = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Update handlers with structlog formatting
    structlog_formatter = structlog.stdlib.ProcessorFormatter(
        processor=final_processor,
        foreign_pre_chain=shared_processors,
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(structlog_formatter)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", user_id=123, action="query")
    """
    return structlog.get_logger(name)


def log_api_request(
    method: str, path: str, status_code: int, duration_ms: float, **kwargs: Any
) -> None:
    """Log API request with timing and status.

    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional context
    """
    logger = get_logger("api")

    # Determine log level based on status code
    if status_code >= 500:
        logger.error(
            "API request failed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )
    elif status_code >= 400:
        logger.warning(
            "API request error",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )
    else:
        logger.info(
            "API request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log errors with full context and stack trace.

    Args:
        error: Exception that occurred
        context: Additional context information
    """
    logger = get_logger("errors")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True,
    )


# Convenience logger for module-level usage
logger = get_logger(__name__)
