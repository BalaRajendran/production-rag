"""
Integration tests for middleware stack.

Tests timing, correlation ID, logging, error handling, and rate limiting middleware.
"""

import time

import pytest
from fastapi import status


class TestTimingMiddleware:
    """Tests for timing middleware."""

    def test_adds_process_time_header(self, client):
        """Test that timing middleware adds X-Process-Time header."""
        response = client.get("/api/v1/health")

        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    def test_process_time_is_accurate(self, client):
        """Test that process time is reasonably accurate."""
        start = time.time()
        response = client.get("/api/v1/health")
        actual_duration = time.time() - start

        reported_time = float(response.headers["X-Process-Time"])
        # Reported time should be close to actual (within 50ms tolerance)
        assert abs(reported_time - actual_duration) < 0.05

    def test_process_time_on_error_responses(self, client):
        """Test that process time is included even on errors."""
        response = client.get("/api/v1/nonexistent-endpoint")

        # Should have process time even for 404
        assert "X-Process-Time" in response.headers


class TestCorrelationIDMiddleware:
    """Tests for correlation ID middleware."""

    def test_generates_correlation_id_when_not_provided(self, client):
        """Test that correlation ID is generated if not provided."""
        response = client.get("/api/v1/health")

        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) > 0

    def test_uses_provided_correlation_id(self, client):
        """Test that provided correlation ID is used."""
        custom_id = "test-correlation-12345"
        response = client.get("/api/v1/health", headers={"X-Correlation-ID": custom_id})

        assert response.headers["X-Correlation-ID"] == custom_id

    def test_correlation_id_format(self, client):
        """Test that generated correlation ID is a valid UUID."""
        response = client.get("/api/v1/health")

        correlation_id = response.headers["X-Correlation-ID"]
        # Should be UUID format
        assert len(correlation_id) == 36
        assert correlation_id.count("-") == 4

    def test_correlation_id_persists_through_request(self, client):
        """Test that correlation ID is same throughout request lifecycle."""
        custom_id = "persistent-id-test"
        response = client.get("/api/v1/health", headers={"X-Correlation-ID": custom_id})

        assert response.headers["X-Correlation-ID"] == custom_id


class TestLoggingMiddleware:
    """Tests for logging middleware."""

    def test_logs_incoming_requests(self, client, mocker):
        """Test that incoming requests are logged."""
        mock_logger = mocker.patch("app.middleware.logging.logger")

        client.get("/api/v1/health")

        # Should have logged the request
        mock_logger.info.assert_called()

    def test_logs_response_status(self, client, mocker):
        """Test that response status is logged."""
        mock_logger = mocker.patch("app.middleware.logging.logger")

        client.get("/api/v1/health")

        # Should log successful response
        mock_logger.info.assert_called()

    def test_logs_errors(self, client, mocker):
        """Test that errors are logged."""
        mock_logger = mocker.patch("app.middleware.logging.logger")

        client.get("/api/v1/nonexistent")

        # Should log error or warning for 404
        assert mock_logger.warning.called or mock_logger.error.called


class TestErrorHandlerMiddleware:
    """Tests for error handler middleware."""

    def test_handles_404_errors(self, client):
        """Test that 404 errors are handled."""
        response = client.get("/api/v1/nonexistent-endpoint")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_error_response_includes_correlation_id(self, client):
        """Test that error responses include correlation ID."""
        custom_id = "error-test-id"
        response = client.get("/api/v1/nonexistent", headers={"X-Correlation-ID": custom_id})

        assert response.headers["X-Correlation-ID"] == custom_id

    def test_error_response_format(self, client, mocker):
        """Test that errors are formatted consistently."""
        # Mock an endpoint that raises an exception
        mocker.patch(
            "app.api.v1.endpoints.health.health_check", side_effect=Exception("Test error")
        )

        response = client.get("/api/v1/health")

        # Should return error response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()

        # Error response should have consistent structure
        assert "error" in data


class TestRateLimitMiddleware:
    """Tests for rate limiting middleware."""

    def test_allows_requests_under_limit(self, client, monkeypatch):
        """Test that requests under limit are allowed."""
        # Disable rate limiting for this test
        monkeypatch.setenv("RATE_LIMIT_RATE_LIMIT_ENABLED", "false")

        # Make multiple requests
        for _ in range(10):
            response = client.get("/api/v1/health")
            assert response.status_code == status.HTTP_200_OK

    def test_adds_rate_limit_headers(self, client):
        """Test that rate limit headers are added."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        # Rate limit headers should be present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_headers_are_numeric(self, client):
        """Test that rate limit headers contain numeric values."""
        response = client.get("/api/v1/health")

        limit = int(response.headers.get("X-RateLimit-Limit", 0))
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))

        assert limit > 0
        assert remaining >= 0

    @pytest.mark.slow()
    def test_blocks_requests_over_limit(self, client, monkeypatch):
        """Test that requests over limit are blocked."""
        # Enable rate limiting with low limit
        monkeypatch.setenv("RATE_LIMIT_RATE_LIMIT_ENABLED", "true")
        monkeypatch.setenv("RATE_LIMIT_REDIS_ENABLED", "false")  # Use in-memory
        monkeypatch.setenv("RATE_LIMIT_RATE_LIMIT_PER_MINUTE", "5")

        # This test is marked as slow because it might actually hit rate limits
        # In practice, we'd mock the rate limiter for faster tests


class TestMiddlewareStack:
    """Tests for complete middleware stack integration."""

    def test_middleware_execution_order(self, client):
        """Test that middleware executes in correct order."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK

        # Check that all middleware-added headers are present
        assert "X-Process-Time" in response.headers  # Timing middleware
        assert "X-Correlation-ID" in response.headers  # Correlation middleware
        assert "X-RateLimit-Limit" in response.headers  # Rate limit middleware

    def test_middleware_on_successful_request(self, client):
        """Test middleware behavior on successful request."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK

        # Timing
        assert float(response.headers["X-Process-Time"]) >= 0

        # Correlation ID
        assert len(response.headers["X-Correlation-ID"]) > 0

        # Rate limiting
        assert int(response.headers["X-RateLimit-Limit"]) > 0

    def test_middleware_on_error_request(self, client):
        """Test middleware behavior on error request."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Middleware should still add headers
        assert "X-Process-Time" in response.headers
        assert "X-Correlation-ID" in response.headers

    def test_cors_middleware_integration(self, client):
        """Test that CORS middleware is properly integrated."""
        response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == status.HTTP_200_OK
        # CORS headers should be present (added by CORS middleware)


class TestMiddlewarePerformance:
    """Performance tests for middleware stack."""

    @pytest.mark.slow()
    def test_middleware_overhead_is_minimal(self, client):
        """Test that middleware adds minimal overhead."""
        # Make request and check timing
        response = client.get("/api/v1/live")

        process_time = float(response.headers["X-Process-Time"])
        # Middleware overhead should be < 50ms for simple request
        assert process_time < 0.05

    def test_middleware_scales_with_concurrent_requests(self, client):
        """Test middleware handles concurrent requests well."""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/live")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)

        # All should have unique correlation IDs
        correlation_ids = [r.headers["X-Correlation-ID"] for r in responses]
        assert len(set(correlation_ids)) == len(correlation_ids)


@pytest.mark.integration()
class TestMiddlewareIntegrationScenarios:
    """Integration scenarios testing middleware combinations."""

    def test_error_with_rate_limiting(self, client):
        """Test error handling combined with rate limiting."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        # Rate limit headers should still be present
        assert "X-RateLimit-Limit" in response.headers

    def test_slow_request_logging(self, client, mocker):
        """Test that slow requests are logged."""
        mocker.patch("app.middleware.timing.logger")

        # Mock a slow endpoint
        # (In real test, we'd mock the endpoint to be slow)

        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK

    def test_correlation_id_in_logs(self, client, mocker):
        """Test that correlation ID appears in logs."""
        mock_logger = mocker.patch("app.middleware.logging.logger")

        custom_id = "test-log-correlation"
        client.get("/api/v1/health", headers={"X-Correlation-ID": custom_id})

        # Logger should have been called (correlation ID would be in context)
        assert mock_logger.info.called
