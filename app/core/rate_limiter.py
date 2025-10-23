"""
Redis-backed rate limiter with sliding window strategy.

Provides distributed rate limiting with:
- Sliding window algorithm for accurate rate limiting
- Redis backend for distributed systems
- In-memory fallback when Redis is unavailable
- Configurable limits per endpoint
"""

import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError

from .config import get_settings
from .logging import get_logger
from .exceptions import RateLimitError

logger = get_logger(__name__)


class RateLimiter:
    """
    Redis-backed rate limiter with sliding window.

    Uses Redis sorted sets for accurate sliding window rate limiting.
    Falls back to in-memory tracking if Redis is unavailable.
    """

    def __init__(self):
        self.settings = get_settings()
        self._redis_client: Optional[redis.Redis] = None
        self._in_memory_store: Dict[str, list] = {}  # Fallback storage
        self._redis_available = False

        if self.settings.rate_limit.redis_enabled:
            self._connect_redis()

    def _connect_redis(self) -> None:
        """Attempt to connect to Redis."""
        try:
            self._redis_client = redis.Redis(
                host=self.settings.rate_limit.redis_host,
                port=self.settings.rate_limit.redis_port,
                db=self.settings.rate_limit.redis_db,
                password=self.settings.rate_limit.redis_password,
                socket_timeout=self.settings.rate_limit.redis_timeout,
                socket_connect_timeout=self.settings.rate_limit.redis_timeout,
                decode_responses=True,
            )
            # Test connection
            self._redis_client.ping()
            self._redis_available = True
            logger.info("Redis connection established for rate limiting")
        except RedisError as e:
            logger.warning(
                "Redis connection failed, using in-memory rate limiting",
                error=str(e)
            )
            self._redis_available = False
            self._redis_client = None

    def _get_redis_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limit tracking."""
        prefix = self.settings.rate_limit.rate_limit_key_prefix
        return f"{prefix}:{identifier}:{window}"

    def _sliding_window_redis(
        self,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Sliding window rate limiting using Redis.

        Args:
            identifier: Unique identifier (e.g., IP address, user ID)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, remaining, retry_after_seconds)
        """
        if not self._redis_client or not self._redis_available:
            return self._sliding_window_memory(identifier, limit, window_seconds)

        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            key = self._get_redis_key(identifier, f"{window_seconds}s")

            pipe = self._redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request with timestamp as score
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(key, window_seconds * 2)

            results = pipe.execute()
            count = results[1]  # Result from zcard

            # Check if under limit
            allowed = count < limit
            remaining = max(0, limit - count - 1)  # -1 for current request

            # Calculate retry after if limit exceeded
            retry_after = 0
            if not allowed:
                # Get oldest request timestamp
                oldest = self._redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    retry_after = int(oldest_timestamp + window_seconds - current_time) + 1

            return allowed, remaining, retry_after

        except RedisError as e:
            logger.warning(
                "Redis error in rate limiter, falling back to memory",
                error=str(e)
            )
            self._redis_available = False
            return self._sliding_window_memory(identifier, limit, window_seconds)

    def _sliding_window_memory(
        self,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        In-memory sliding window rate limiting (fallback).

        Args:
            identifier: Unique identifier
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, remaining, retry_after_seconds)
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        # Get or create request list for this identifier
        if identifier not in self._in_memory_store:
            self._in_memory_store[identifier] = []

        # Remove old requests
        self._in_memory_store[identifier] = [
            ts for ts in self._in_memory_store[identifier]
            if ts > window_start
        ]

        # Count requests
        count = len(self._in_memory_store[identifier])

        # Check if under limit
        allowed = count < limit
        remaining = max(0, limit - count - 1)

        # Calculate retry after if limit exceeded
        retry_after = 0
        if not allowed and self._in_memory_store[identifier]:
            oldest_timestamp = min(self._in_memory_store[identifier])
            retry_after = int(oldest_timestamp + window_seconds - current_time) + 1

        # Add current request if allowed
        if allowed:
            self._in_memory_store[identifier].append(current_time)

        return allowed, remaining, retry_after

    def check_rate_limit(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (e.g., IP, user ID, API key)
            limit: Override default limit
            window_seconds: Override default window (60 for per-minute)

        Returns:
            Dict with rate limit info

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        if not self.settings.rate_limit.rate_limit_enabled:
            return {
                "allowed": True,
                "limit": 0,
                "remaining": 999999,
                "retry_after": 0
            }

        # Use defaults if not provided
        limit = limit or self.settings.rate_limit.rate_limit_per_minute
        window_seconds = window_seconds or 60

        allowed, remaining, retry_after = self._sliding_window_redis(
            identifier, limit, window_seconds
        )

        rate_limit_info = {
            "allowed": allowed,
            "limit": limit,
            "remaining": remaining,
            "retry_after": retry_after
        }

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                limit=limit,
                retry_after=retry_after
            )
            raise RateLimitError(
                message=f"Rate limit exceeded. Try again in {retry_after} seconds",
                retry_after=retry_after,
                details=rate_limit_info
            )

        return rate_limit_info

    def reset_limit(self, identifier: str) -> None:
        """
        Reset rate limit for an identifier (admin/testing use).

        Args:
            identifier: Identifier to reset
        """
        if self._redis_available and self._redis_client:
            try:
                # Remove all windows for this identifier
                pattern = f"{self.settings.rate_limit.rate_limit_key_prefix}:{identifier}:*"
                keys = self._redis_client.keys(pattern)
                if keys:
                    self._redis_client.delete(*keys)
                logger.info("Rate limit reset", identifier=identifier)
            except RedisError as e:
                logger.error("Failed to reset rate limit", identifier=identifier, error=str(e))

        # Also clear from memory
        if identifier in self._in_memory_store:
            del self._in_memory_store[identifier]

    def get_stats(self, identifier: str) -> Dict[str, any]:
        """
        Get rate limit statistics for an identifier.

        Args:
            identifier: Identifier to check

        Returns:
            Dict with current usage stats
        """
        window_seconds = 60
        key = self._get_redis_key(identifier, f"{window_seconds}s")

        if self._redis_available and self._redis_client:
            try:
                current_time = time.time()
                window_start = current_time - window_seconds

                # Get count in current window
                count = self._redis_client.zcount(key, window_start, current_time)

                return {
                    "identifier": identifier,
                    "current_usage": count,
                    "limit": self.settings.rate_limit.rate_limit_per_minute,
                    "window_seconds": window_seconds,
                    "backend": "redis"
                }
            except RedisError:
                pass

        # Fallback to memory stats
        count = 0
        if identifier in self._in_memory_store:
            current_time = time.time()
            window_start = current_time - window_seconds
            count = len([ts for ts in self._in_memory_store[identifier] if ts > window_start])

        return {
            "identifier": identifier,
            "current_usage": count,
            "limit": self.settings.rate_limit.rate_limit_per_minute,
            "window_seconds": window_seconds,
            "backend": "memory"
        }

    def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            try:
                self._redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error("Error closing Redis connection", error=str(e))


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance.

    Returns:
        Singleton RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
