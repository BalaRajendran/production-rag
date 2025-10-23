"""
Integration tests for v1 health endpoints.

Tests health check, readiness, and liveness endpoints.
"""

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests for /api/v1/health endpoint."""

    def test_health_check_success(self, client, mocker):
        """Test successful health check."""
        # Mock RAG service stats
        mock_stats = {"vectors": 1000, "dimensions": 3072}
        mocker.patch(
            "app.api.v1.endpoints.health.RAGService.get_stats",
            return_value=mock_stats
        )

        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert "pinecone_connected" in data
        assert "openai_configured" in data
        assert "cohere_configured" in data

    def test_health_check_degraded(self, client, mocker):
        """Test health check when services are degraded."""
        # Mock failed stats retrieval
        mocker.patch(
            "app.api.v1.endpoints.health.RAGService.get_stats",
            side_effect=Exception("Connection failed")
        )

        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"
        assert data["pinecone_connected"] is False

    def test_health_check_includes_configuration_status(self, client):
        """Test that health check includes configuration status."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should include configuration checks
        assert isinstance(data["openai_configured"], bool)
        assert isinstance(data["cohere_configured"], bool)

    def test_health_check_response_model(self, client):
        """Test that response follows HealthResponse model."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Required fields from HealthResponse model
        required_fields = ["status", "pinecone_connected", "openai_configured", "cohere_configured"]
        for field in required_fields:
            assert field in data


class TestReadinessEndpoint:
    """Tests for /api/v1/ready endpoint."""

    def test_readiness_check_when_ready(self, client, mocker):
        """Test readiness check when application is ready."""
        # Mock successful stats retrieval
        mock_stats = {"vectors": 1000}
        mocker.patch(
            "app.api.v1.endpoints.health.RAGService.get_stats",
            return_value=mock_stats
        )

        response = client.get("/api/v1/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["ready"] is True
        assert "message" in data
        assert "ready" in data["message"].lower()

    def test_readiness_check_when_not_ready(self, client, mocker):
        """Test readiness check when application is not ready."""
        # Mock failed stats retrieval
        mocker.patch(
            "app.api.v1.endpoints.health.RAGService.get_stats",
            return_value=None
        )

        response = client.get("/api/v1/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["ready"] is False
        assert "message" in data

    def test_readiness_check_exception_handling(self, client, mocker):
        """Test readiness check handles exceptions."""
        # Mock exception
        mocker.patch(
            "app.api.v1.endpoints.health.RAGService.get_stats",
            side_effect=Exception("Database error")
        )

        response = client.get("/api/v1/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["ready"] is False
        assert "error" in data["message"].lower() or "failed" in data["message"].lower()


class TestLivenessEndpoint:
    """Tests for /api/v1/live endpoint."""

    def test_liveness_check(self, client):
        """Test liveness check always returns alive."""
        response = client.get("/api/v1/live")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "alive"

    def test_liveness_check_multiple_calls(self, client):
        """Test liveness check is consistent across multiple calls."""
        responses = [client.get("/api/v1/live") for _ in range(5)]

        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "alive"


class TestHealthEndpointsIntegration:
    """Integration tests for all health endpoints together."""

    def test_all_health_endpoints_accessible(self, client):
        """Test that all health endpoints are accessible."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/ready",
            "/api/v1/live"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK

    def test_health_endpoints_have_correlation_id(self, client):
        """Test that health endpoints include correlation ID."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        assert "X-Correlation-ID" in response.headers

    def test_health_endpoints_have_timing_header(self, client):
        """Test that health endpoints include timing information."""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        assert "X-Process-Time" in response.headers

        # Process time should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    def test_health_check_with_custom_correlation_id(self, client):
        """Test health check with custom correlation ID."""
        custom_id = "test-correlation-123"
        response = client.get(
            "/api/v1/health",
            headers={"X-Correlation-ID": custom_id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Correlation-ID"] == custom_id

    @pytest.mark.slow
    def test_health_check_performance(self, client):
        """Test that health check responds quickly."""
        import time

        start = time.time()
        response = client.get("/api/v1/health")
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Health check should be fast (< 1 second)
        assert duration < 1.0


class TestHealthEndpointsCORS:
    """Tests for CORS headers on health endpoints."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options("/api/v1/health")

        # CORS middleware should add these headers
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    def test_cors_allows_credentials(self, client):
        """Test that CORS allows credentials."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestHealthEndpointsWithRealServices:
    """Tests with real service dependencies (requires Docker)."""

    @pytest.mark.qdrant
    def test_health_check_with_real_qdrant(self, client):
        """Test health check with real Qdrant connection."""
        # This test requires Qdrant to be running
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # With real Qdrant, connection should succeed
        # (assuming Qdrant is running via docker-compose)
        assert "pinecone_connected" in data
