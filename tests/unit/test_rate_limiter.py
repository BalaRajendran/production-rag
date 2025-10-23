"""
Unit tests for rate limiter module.

Tests Redis-backed rate limiting with sliding window algorithm
and in-memory fallback.
"""

import time
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import RateLimitError
from app.core.rate_limiter import RateLimiter, get_rate_limiter


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization_with_redis_disabled(self, monkeypatch):
        """Test initialization when Redis is disabled."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")
        limiter = RateLimiter()
        assert limiter._redis_client is None
        assert limiter._redis_available is False

    @patch("app.core.rate_limiter.redis.Redis")
    def test_initialization_with_redis_enabled(self, mock_redis_class, monkeypatch):
        """Test initialization when Redis is enabled."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "true")
        monkeypatch.setenv("RATE_LIMIT_REDIS_HOST", "localhost")

        # Mock successful connection
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        limiter = RateLimiter()
        assert limiter._redis_available is True

    @patch("app.core.rate_limiter.redis.Redis")
    def test_redis_connection_failure(self, mock_redis_class, monkeypatch):
        """Test fallback to in-memory when Redis connection fails."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "true")

        # Mock failed connection
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis

        limiter = RateLimiter()
        assert limiter._redis_available is False
        assert limiter._redis_client is None

    def test_in_memory_rate_limiting_allows_within_limit(self, monkeypatch):
        """Test that requests within limit are allowed."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")
        monkeypatch.setenv("RATE_LIMIT_RATE_LIMIT_PER_MINUTE", "10")

        limiter = RateLimiter()

        # Make 5 requests (under limit of 10)
        for _i in range(5):
            result = limiter.check_rate_limit("test-user", limit=10, window_seconds=60)
            assert result["allowed"] is True
            assert result["remaining"] >= 0

    def test_in_memory_rate_limiting_blocks_over_limit(self, monkeypatch):
        """Test that requests over limit are blocked."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()

        # Make requests up to limit
        limit = 5
        for _i in range(limit):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)

        # Next request should fail
        with pytest.raises(RateLimitError) as exc_info:
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after > 0

    def test_different_identifiers_separate_limits(self, monkeypatch):
        """Test that different identifiers have separate limits."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()
        limit = 5

        # User 1 makes requests
        for _i in range(limit):
            result = limiter.check_rate_limit("user-1", limit=limit, window_seconds=60)
            assert result["allowed"] is True

        # User 2 should have separate limit
        result = limiter.check_rate_limit("user-2", limit=limit, window_seconds=60)
        assert result["allowed"] is True

    def test_sliding_window_behavior(self, monkeypatch):
        """Test sliding window behavior (old requests expire)."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()
        limit = 3
        window = 1  # 1 second window

        # Make requests up to limit
        for _i in range(limit):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=window)

        # Should be at limit
        with pytest.raises(RateLimitError):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=window)

        # Wait for window to expire
        time.sleep(window + 0.1)

        # Should be allowed again
        result = limiter.check_rate_limit("test-user", limit=limit, window_seconds=window)
        assert result["allowed"] is True

    def test_rate_limit_disabled(self, monkeypatch):
        """Test that rate limiting can be disabled."""
        monkeypatch.setenv("RATE_LIMIT_RATE_LIMIT_ENABLED", "false")

        limiter = RateLimiter()

        # Should always allow requests
        for _i in range(1000):
            result = limiter.check_rate_limit("test-user")
            assert result["allowed"] is True
            assert result["remaining"] == 999999

    def test_check_rate_limit_return_value(self, monkeypatch):
        """Test check_rate_limit return value structure."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()
        result = limiter.check_rate_limit("test-user", limit=10, window_seconds=60)

        assert "allowed" in result
        assert "limit" in result
        assert "remaining" in result
        assert "retry_after" in result
        assert result["limit"] == 10

    def test_reset_limit(self, monkeypatch):
        """Test resetting rate limit for an identifier."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()
        limit = 3

        # Exhaust limit
        for _i in range(limit):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)

        # Reset limit
        limiter.reset_limit("test-user")

        # Should be allowed again
        result = limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)
        assert result["allowed"] is True

    def test_get_stats(self, monkeypatch):
        """Test getting rate limit statistics."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()
        limit = 10

        # Make some requests
        for _i in range(3):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)

        # Get stats
        stats = limiter.get_stats("test-user")

        assert stats["identifier"] == "test-user"
        assert stats["current_usage"] == 3
        assert stats["limit"] == limiter.settings.rate_limit.rate_limit_per_minute
        assert stats["backend"] == "memory"

    def test_get_redis_key_format(self, monkeypatch):
        """Test Redis key generation format."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")
        monkeypatch.setenv("RATE_LIMIT_RATE_LIMIT_KEY_PREFIX", "test_prefix")

        limiter = RateLimiter()
        key = limiter._get_redis_key("user-123", "60s")

        assert key == "test_prefix:user-123:60s"

    def test_retry_after_calculation(self, monkeypatch):
        """Test retry_after value calculation."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

        limiter = RateLimiter()
        limit = 2
        window = 10

        # Exhaust limit
        for _i in range(limit):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=window)

        # Check retry_after
        with pytest.raises(RateLimitError) as exc_info:
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=window)

        # retry_after should be <= window
        assert exc_info.value.retry_after <= window
        assert exc_info.value.retry_after > 0

    @patch("app.core.rate_limiter.redis.Redis")
    def test_redis_pipeline_usage(self, mock_redis_class, monkeypatch):
        """Test that Redis pipeline is used for atomic operations."""
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "true")

        # Mock Redis client with pipeline
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [None, 0, 1, True]
        mock_redis.pipeline.return_value = mock_pipeline
        mock_redis_class.return_value = mock_redis

        limiter = RateLimiter()
        limiter.check_rate_limit("test-user", limit=10, window_seconds=60)

        # Verify pipeline was used
        mock_redis.pipeline.assert_called()
        mock_pipeline.execute.assert_called()


class TestGetRateLimiter:
    """Tests for get_rate_limiter function."""

    def test_returns_singleton(self):
        """Test that get_rate_limiter returns singleton instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2

    def test_returns_rate_limiter_instance(self):
        """Test that it returns RateLimiter instance."""
        limiter = get_rate_limiter()
        assert isinstance(limiter, RateLimiter)


@pytest.mark.parametrize(
    ("limit", "requests", "should_allow"),
    [
        (10, 5, True),  # Under limit
        (10, 10, False),  # At limit
        (10, 15, False),  # Over limit
        (100, 50, True),  # Large limit
        (1, 1, False),  # Minimum limit
    ],
)
def test_rate_limiting_scenarios(monkeypatch, limit, requests, should_allow):
    """Test various rate limiting scenarios."""
    monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")

    limiter = RateLimiter()

    # Make requests
    for _i in range(requests - 1):
        limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)

    # Check final request
    if should_allow:
        result = limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)
        assert result["allowed"] is True
    else:
        with pytest.raises(RateLimitError):
            limiter.check_rate_limit("test-user", limit=limit, window_seconds=60)
