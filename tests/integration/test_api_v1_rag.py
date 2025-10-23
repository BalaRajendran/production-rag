"""
Integration tests for v1 RAG endpoints.

Tests RAG query endpoint with full pipeline integration.
"""

import pytest
from fastapi import status

from app.models.models import QueryType


class TestRAGQueryEndpoint:
    """Tests for /api/v1/query endpoint."""

    def test_successful_query(self, client, mocker):
        """Test successful RAG query."""
        # Mock RAG service response
        mock_response = {
            "answer": "Exercise has numerous health benefits including improved cardiovascular health.",
            "chunks": [
                {
                    "id": "chunk-1",
                    "text": "Regular exercise improves heart health",
                    "score": 0.95,
                    "metadata": {"source": "health-guide.pdf"}
                }
            ],
            "generated_queries": [
                {"query": "benefits of exercise", "query_type": "semantic"}
            ],
            "query_type": QueryType.RAG,
            "metadata": {"num_queries": 1}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "What are the benefits of exercise?"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "answer" in data
        assert "chunks" in data
        assert "query_type" in data
        assert data["answer"] == mock_response["answer"]
        assert len(data["chunks"]) > 0

    def test_query_with_conversation_history(self, client, mocker):
        """Test query with conversation history."""
        mock_response = {
            "answer": "Based on our previous discussion, exercise also improves mental health.",
            "chunks": [
                {
                    "id": "chunk-2",
                    "text": "Exercise reduces stress and anxiety",
                    "score": 0.92,
                    "metadata": {}
                }
            ],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={
                "query": "What about mental health benefits?",
                "conversation_history": [
                    {"role": "user", "content": "Tell me about exercise"},
                    {"role": "assistant", "content": "Exercise is great for health"}
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data

    def test_query_with_top_k_parameter(self, client, mocker):
        """Test query with custom top_k parameter."""
        mock_response = {
            "answer": "Test answer",
            "chunks": [
                {
                    "id": f"chunk-{i}",
                    "text": f"Content {i}",
                    "score": 0.9 - (i * 0.1),
                    "metadata": {}
                }
                for i in range(5)
            ],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "top_k": 5
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["chunks"]) == 5

    def test_query_with_metadata_filter(self, client, mocker):
        """Test query with metadata filters."""
        mock_response = {
            "answer": "Filtered results",
            "chunks": [
                {
                    "id": "chunk-1",
                    "text": "Relevant content",
                    "score": 0.95,
                    "metadata": {"source": "specific-doc.pdf"}
                }
            ],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "metadata_filter": {"source": "specific-doc.pdf"}
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["chunks"][0]["metadata"]["source"] == "specific-doc.pdf"

    def test_query_validation_empty_query(self, client):
        """Test validation for empty query."""
        response = client.post(
            "/api/v1/query",
            json={"query": ""}
        )

        # FastAPI/Pydantic validation should catch this
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_validation_missing_query(self, client):
        """Test validation when query field is missing."""
        response = client.post(
            "/api/v1/query",
            json={}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_service_error_handling(self, client, mocker):
        """Test error handling when RAG service fails."""
        # Mock service to raise exception
        mocker.patch(
            "app.services.rag_service.RAGService.query",
            side_effect=Exception("Vector store connection failed")
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test query"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower()

    def test_query_response_includes_correlation_id(self, client, mocker):
        """Test that query responses include correlation ID."""
        mock_response = {
            "answer": "Test answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        custom_id = "test-rag-query-123"
        response = client.post(
            "/api/v1/query",
            json={"query": "Test"},
            headers={"X-Correlation-ID": custom_id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Correlation-ID"] == custom_id

    def test_query_response_includes_timing(self, client, mocker):
        """Test that query responses include timing information."""
        mock_response = {
            "answer": "Test answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0


class TestRAGQueryObservability:
    """Tests for observability integration."""

    def test_query_with_observability_enabled(self, client, mocker):
        """Test that observability traces are created when enabled."""
        mock_obs_manager = mocker.Mock()
        mock_obs_manager.is_enabled.return_value = True
        mock_trace = mocker.Mock()
        mock_obs_manager.create_trace.return_value = mock_trace

        mocker.patch(
            "app.api.v1.endpoints.rag.get_observability_manager",
            return_value=mock_obs_manager
        )

        mock_response = {
            "answer": "Test answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test query"}
        )

        assert response.status_code == status.HTTP_200_OK
        # Verify trace was created
        mock_obs_manager.create_trace.assert_called_once()

    def test_query_with_observability_disabled(self, client, mocker):
        """Test query works when observability is disabled."""
        mock_obs_manager = mocker.Mock()
        mock_obs_manager.is_enabled.return_value = False

        mocker.patch(
            "app.api.v1.endpoints.rag.get_observability_manager",
            return_value=mock_obs_manager
        )

        mock_response = {
            "answer": "Test answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test query"}
        )

        assert response.status_code == status.HTTP_200_OK
        # Trace should not be created when disabled
        mock_obs_manager.create_trace.assert_not_called()


class TestRAGQueryResponseStructure:
    """Tests for response model structure and validation."""

    def test_response_includes_all_required_fields(self, client, mocker):
        """Test that response includes all required fields."""
        mock_response = {
            "answer": "Complete answer",
            "chunks": [
                {
                    "id": "chunk-1",
                    "text": "Content",
                    "score": 0.9,
                    "metadata": {"key": "value"}
                }
            ],
            "generated_queries": [
                {"query": "variant 1", "query_type": "semantic"}
            ],
            "query_type": QueryType.RAG,
            "metadata": {"processing_time": 1.5}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Required fields
        assert "answer" in data
        assert "chunks" in data
        assert "query_type" in data

        # Optional fields
        assert "generated_queries" in data
        assert "metadata" in data

    def test_chunk_structure(self, client, mocker):
        """Test that chunks have correct structure."""
        mock_response = {
            "answer": "Answer",
            "chunks": [
                {
                    "id": "test-chunk-1",
                    "text": "This is chunk content",
                    "score": 0.95,
                    "metadata": {
                        "source": "doc.pdf",
                        "page": 1
                    }
                }
            ],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        chunk = data["chunks"][0]
        assert "id" in chunk
        assert "text" in chunk
        assert "score" in chunk
        assert "metadata" in chunk
        assert isinstance(chunk["score"], float)
        assert 0 <= chunk["score"] <= 1

    def test_query_type_enum_values(self, client, mocker):
        """Test that query_type uses valid enum values."""
        for query_type in [QueryType.RAG, QueryType.SUMMARIZATION, QueryType.GENERAL]:
            mock_response = {
                "answer": "Answer",
                "chunks": [],
                "generated_queries": [],
                "query_type": query_type,
                "metadata": {}
            }

            mocker.patch(
                "app.services.rag_service.RAGService.query",
                return_value=mocker.Mock(**mock_response)
            )

            response = client.post(
                "/api/v1/query",
                json={"query": "Test"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["query_type"] in [qt.value for qt in QueryType]


class TestRAGQueryEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_query(self, client, mocker):
        """Test handling of very long queries."""
        long_query = "What is " + ("very " * 1000) + "important?"

        mock_response = {
            "answer": "Answer for long query",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": long_query}
        )

        assert response.status_code == status.HTTP_200_OK

    def test_query_with_special_characters(self, client, mocker):
        """Test query with special characters."""
        special_query = "What is the formula for E=mc²? 🔬 How does it work?"

        mock_response = {
            "answer": "Einstein's equation",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": special_query}
        )

        assert response.status_code == status.HTTP_200_OK

    def test_query_with_empty_conversation_history(self, client, mocker):
        """Test query with empty conversation history list."""
        mock_response = {
            "answer": "Answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test",
                "conversation_history": []
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_query_with_no_chunks_returned(self, client, mocker):
        """Test when no relevant chunks are found."""
        mock_response = {
            "answer": "I couldn't find relevant information.",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.GENERAL,
            "metadata": {"reason": "no_relevant_chunks"}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Obscure topic"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["chunks"]) == 0
        assert "answer" in data


class TestRAGQueryLogging:
    """Tests for logging integration."""

    def test_query_logging(self, client, mocker):
        """Test that queries are logged."""
        mock_logger = mocker.patch("app.api.v1.endpoints.rag.logger")

        mock_response = {
            "answer": "Answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        client.post(
            "/api/v1/query",
            json={"query": "Test query"}
        )

        # Should log query processing
        assert mock_logger.info.called

    def test_error_logging(self, client, mocker):
        """Test that errors are logged."""
        mock_logger = mocker.patch("app.api.v1.endpoints.rag.logger")

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            side_effect=Exception("Test error")
        )

        client.post(
            "/api/v1/query",
            json={"query": "Test"}
        )

        # Should log error
        mock_logger.error.assert_called()


@pytest.mark.integration
class TestRAGQueryIntegrationScenarios:
    """Integration scenarios testing RAG query with middleware."""

    def test_query_with_rate_limiting(self, client, mocker):
        """Test RAG query respects rate limiting."""
        mock_response = {
            "answer": "Answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test"}
        )

        assert response.status_code == status.HTTP_200_OK
        # Rate limit headers should be present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_concurrent_queries(self, client, mocker):
        """Test handling of concurrent queries."""
        import concurrent.futures

        mock_response = {
            "answer": "Answer",
            "chunks": [],
            "generated_queries": [],
            "query_type": QueryType.RAG,
            "metadata": {}
        }

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            return_value=mocker.Mock(**mock_response)
        )

        def make_query(i):
            return client.post(
                "/api/v1/query",
                json={"query": f"Query {i}"}
            )

        # Make 5 concurrent queries
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_query, i) for i in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)

        # Each should have unique correlation ID
        correlation_ids = [r.headers["X-Correlation-ID"] for r in responses]
        assert len(set(correlation_ids)) == len(correlation_ids)

    @pytest.mark.slow
    def test_query_timeout_handling(self, client, mocker):
        """Test handling of query timeouts."""
        import time

        # Mock service to simulate slow processing
        def slow_query(*args, **kwargs):
            time.sleep(0.5)
            return mocker.Mock(
                answer="Slow answer",
                chunks=[],
                generated_queries=[],
                query_type=QueryType.RAG,
                metadata={}
            )

        mocker.patch(
            "app.services.rag_service.RAGService.query",
            side_effect=slow_query
        )

        response = client.post(
            "/api/v1/query",
            json={"query": "Test"}
        )

        # Should still succeed but with higher process time
        assert response.status_code == status.HTTP_200_OK
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0.5
