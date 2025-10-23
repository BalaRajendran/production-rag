# Logging Guide

Production-grade structured logging with beautiful console output for development and JSON format for production.

## Overview

The application uses **structlog** for structured logging with the following features:

- ✅ **Structured logging** - All logs are key-value pairs for easy parsing
- ✅ **Colored console output** - Beautiful, readable logs in development
- ✅ **JSON format** - Machine-readable logs for production aggregation
- ✅ **Correlation IDs** - Track requests across distributed services
- ✅ **Context propagation** - Automatic app and environment context
- ✅ **Configurable levels** - Control verbosity with environment variables
- ✅ **Log rotation** - Automatic file rotation with configurable limits

## Configuration

Configure logging via environment variables in `.env`:

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
OBS_LOG_LEVEL=INFO

# Log format: "json" (production) or "text" (development with colors)
OBS_LOG_FORMAT=text

# Optional: Write logs to file
OBS_LOG_FILE=logs/app.log

# File rotation settings
OBS_LOG_ROTATION=100 MB
OBS_LOG_RETENTION=30

# Enable correlation ID tracking
OBS_ENABLE_CORRELATION_ID=true
```

### Development vs Production

**Development Mode** (`OBS_LOG_FORMAT=text`):
- Colored console output with syntax highlighting
- Easy to read for humans
- Shows log level with colors (green=info, yellow=warning, red=error)
- Includes ISO timestamps

**Production Mode** (`OBS_LOG_FORMAT=json`):
- Single-line JSON per log entry
- Easy to parse with log aggregators (ELK, Splunk, CloudWatch)
- Includes all structured data
- Machine-readable format

## Usage Examples

### Basic Logging

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple log messages
logger.info("User logged in", user_id=123, email="user@example.com")
logger.warning("Rate limit approaching", current=95, limit=100)
logger.error("Database connection failed", error="timeout", retry_count=3)
```

### HTTP Request Logging

The logging middleware automatically logs all HTTP requests:

```python
# Automatic logging via middleware
# GET /api/v1/health -> 200 OK (23ms)
```

Or use the helper function manually:

```python
from app.core.logging import log_api_request

log_api_request(
    method="POST",
    path="/api/v1/rag/query",
    status_code=200,
    duration_ms=456.78,
    user_id=123,
    query="What is RAG?"
)
```

### Error Logging

```python
from app.core.logging import log_error

try:
    result = risky_operation()
except Exception as e:
    log_error(e, context={
        "user_id": 123,
        "operation": "query_processing",
        "query": "What is machine learning?"
    })
```

### Structured Context

```python
logger = get_logger(__name__)

# All logs automatically include:
# - app: "Production RAG Framework"
# - environment: "development" or "production"
# - timestamp: ISO 8601 format
# - logger: module name

logger.info(
    "RAG query completed",
    query="What is ML?",
    chunks_retrieved=50,
    chunks_reranked=15,
    duration_ms=567.89,
    model="gpt-4-turbo"
)
```

## Log Output Examples

### Development Mode (Colored Console)

```
2025-10-23T14:52:31.164856Z [info     ] Application started successfully [__main__] app='Production RAG Framework' environment=development version=1.0.0
2025-10-23T14:52:31.165065Z [warning  ] This is a warning message      [__main__] actual=0.65 app='Production RAG Framework' environment=development threshold=0.7
2025-10-23T14:52:31.165204Z [error    ] An error occurred              [__main__] app='Production RAG Framework' environment=development error_code=E001 severity=medium
```

**Features:**
- Timestamps in ISO format
- Log levels color-coded (green, yellow, red)
- Key-value pairs aligned
- Module names in brackets
- Easy to scan visually

### Production Mode (JSON)

```json
{"event": "Application started successfully", "logger": "__main__", "level": "info", "timestamp": "2025-10-23T14:52:31.164856Z", "app": "Production RAG Framework", "environment": "production", "version": "1.0.0"}
{"event": "API request", "logger": "api", "level": "info", "timestamp": "2025-10-23T14:52:31.165296Z", "method": "GET", "path": "/api/v1/health", "status_code": 200, "duration_ms": 23.45, "client_host": "127.0.0.1"}
```

**Features:**
- One JSON object per line
- All fields included
- Easy to parse programmatically
- Compatible with log aggregation tools

## Best Practices

### 1. Use Structured Logging

❌ **Don't:**
```python
logger.info(f"User {user_id} logged in from {ip_address}")
```

✅ **Do:**
```python
logger.info("User logged in", user_id=user_id, ip_address=ip_address)
```

### 2. Choose Appropriate Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages (default)
- **WARNING**: Something unexpected but not an error
- **ERROR**: Error that doesn't stop the application
- **CRITICAL**: Serious error that may stop the application

### 3. Include Context

```python
logger.info(
    "RAG query processed",
    query=query_text,
    chunks_retrieved=50,
    chunks_used=15,
    duration_ms=456.78,
    user_id=user.id
)
```

### 4. Avoid Logging Sensitive Data

```python
# ❌ Don't log passwords, API keys, or PII
logger.info("User authenticated", password=password)

# ✅ Log identifiers and non-sensitive data
logger.info("User authenticated", user_id=user.id, method="oauth")
```

### 5. Use Log Helpers for Common Patterns

```python
from app.core.logging import log_api_request, log_error

# HTTP requests
log_api_request("POST", "/api/v1/query", 200, 123.45)

# Errors with context
log_error(exception, context={"user_id": 123})
```

## Integration with Log Aggregators

### ELK Stack (Elasticsearch, Logstash, Kibana)

1. Set `OBS_LOG_FORMAT=json`
2. Configure Filebeat or Logstash to read log files
3. Parse JSON logs in Logstash
4. Visualize in Kibana

### CloudWatch Logs

1. Set `OBS_LOG_FORMAT=json`
2. Use CloudWatch agent to ship logs
3. Create metric filters on structured fields
4. Set up alarms on error rates

### Splunk

1. Set `OBS_LOG_FORMAT=json`
2. Configure Splunk forwarder
3. Use spath command to extract JSON fields
4. Create dashboards and alerts

## Troubleshooting

### Logs not appearing

Check log level configuration:
```bash
# Set to DEBUG to see all logs
OBS_LOG_LEVEL=DEBUG
```

### Too many logs from third-party libraries

The logging configuration silences noisy libraries by default. Add more in [app/core/logging.py](../app/core/logging.py):

```python
"loggers": {
    "noisy_library": {
        "level": "WARNING",
        "propagate": False,
    },
}
```

### Cannot parse JSON logs

Ensure you're using `OBS_LOG_FORMAT=json` and each log entry is on a single line.

## Testing Logging

Run the logging demonstration:

```bash
uv run python test_logging.py
```

This shows examples of:
- Different log levels
- HTTP request logging
- Structured data
- Complex log entries
- Performance metrics

## Performance Considerations

- **Structured logging is fast** - Structlog is optimized for performance
- **JSON rendering is efficient** - Only formats when needed
- **File I/O is buffered** - Log writes are batched
- **Context variables are thread-safe** - Safe for async operations

## Summary

✅ Use `OBS_LOG_FORMAT=text` for development
✅ Use `OBS_LOG_FORMAT=json` for production
✅ Always use structured logging with key-value pairs
✅ Include relevant context in logs
✅ Use appropriate log levels
✅ Never log sensitive data
✅ Test with `python test_logging.py`
