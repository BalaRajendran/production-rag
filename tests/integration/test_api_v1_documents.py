"""
Integration tests for v1 document management endpoints.

Tests document indexing and deletion endpoints.
"""

import pytest
from fastapi import status


class TestDocumentIndexing:
    """Tests for /api/v1/index endpoint."""

    def test_index_single_document(self, client, mocker):
        """Test indexing a single document."""
        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 5,
            "message": "Successfully indexed 1 documents"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "This is a test document about machine learning.",
                        "metadata": {
                            "title": "ML Intro",
                            "author": "Test Author"
                        }
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["documents_processed"] == 1
        assert data["chunks_created"] > 0
        assert "message" in data

    def test_index_multiple_documents(self, client, mocker):
        """Test indexing multiple documents."""
        mock_response = {
            "success": True,
            "documents_processed": 3,
            "chunks_created": 15,
            "message": "Successfully indexed 3 documents"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": f"doc-{i}",
                        "content": f"Document {i} content",
                        "metadata": {"title": f"Doc {i}"}
                    }
                    for i in range(3)
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["documents_processed"] == 3

    def test_index_document_with_rich_metadata(self, client, mocker):
        """Test indexing document with comprehensive metadata."""
        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 10,
            "message": "Successfully indexed 1 documents"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-rich",
                        "content": "Comprehensive document content",
                        "metadata": {
                            "title": "Comprehensive Guide",
                            "author": "John Doe",
                            "source": "https://example.com/doc",
                            "category": "tutorial",
                            "tags": ["ml", "ai", "tutorial"],
                            "date": "2024-01-01",
                            "version": "1.0"
                        }
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_index_document_with_minimal_metadata(self, client, mocker):
        """Test indexing document with minimal metadata."""
        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 3,
            "message": "Successfully indexed 1 documents"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-minimal",
                        "content": "Minimal document",
                        "metadata": {}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_index_validation_missing_documents(self, client):
        """Test validation when documents field is missing."""
        response = client.post(
            "/api/v1/index",
            json={}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_index_validation_empty_documents_list(self, client):
        """Test validation with empty documents list."""
        response = client.post(
            "/api/v1/index",
            json={"documents": []}
        )

        # Should still process (though no actual indexing happens)
        # The service layer would handle this appropriately
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_index_validation_missing_document_id(self, client):
        """Test validation when document ID is missing."""
        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "content": "Document without ID",
                        "metadata": {}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_index_validation_missing_content(self, client):
        """Test validation when document content is missing."""
        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-no-content",
                        "metadata": {}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_index_service_error_handling(self, client, mocker):
        """Test error handling when indexing fails."""
        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            side_effect=Exception("Vector store connection failed")
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "Test",
                        "metadata": {}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower()

    def test_index_response_includes_correlation_id(self, client, mocker):
        """Test that index responses include correlation ID."""
        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 5,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        custom_id = "test-index-123"
        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "Test",
                        "metadata": {}
                    }
                ]
            },
            headers={"X-Correlation-ID": custom_id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Correlation-ID"] == custom_id


class TestDocumentDeletion:
    """Tests for /api/v1/documents/{document_id} DELETE endpoint."""

    def test_delete_existing_document(self, client, mocker):
        """Test deleting an existing document."""
        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            return_value=True
        )

        response = client.delete("/api/v1/documents/doc-1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert "message" in data
        assert "doc-1" in data["message"]

    def test_delete_nonexistent_document(self, client, mocker):
        """Test deleting a document that doesn't exist."""
        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            return_value=False
        )

        response = client.delete("/api/v1/documents/nonexistent-doc")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_delete_with_special_characters_in_id(self, client, mocker):
        """Test deleting document with special characters in ID."""
        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            return_value=True
        )

        doc_id = "doc-123_special-chars.pdf"
        response = client.delete(f"/api/v1/documents/{doc_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_delete_service_error_handling(self, client, mocker):
        """Test error handling when deletion fails."""
        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            side_effect=Exception("Database connection error")
        )

        response = client.delete("/api/v1/documents/doc-1")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower()

    def test_delete_response_includes_correlation_id(self, client, mocker):
        """Test that delete responses include correlation ID."""
        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            return_value=True
        )

        custom_id = "test-delete-123"
        response = client.delete(
            "/api/v1/documents/doc-1",
            headers={"X-Correlation-ID": custom_id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Correlation-ID"] == custom_id


class TestDocumentEndpointsLogging:
    """Tests for logging integration."""

    def test_index_logging(self, client, mocker):
        """Test that indexing operations are logged."""
        mock_logger = mocker.patch("app.api.v1.endpoints.documents.logger")

        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 5,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "Test",
                        "metadata": {}
                    }
                ]
            }
        )

        # Should log indexing operation
        assert mock_logger.info.called

    def test_delete_logging(self, client, mocker):
        """Test that deletion operations are logged."""
        mock_logger = mocker.patch("app.api.v1.endpoints.documents.logger")

        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            return_value=True
        )

        client.delete("/api/v1/documents/doc-1")

        # Should log deletion operation
        assert mock_logger.info.called

    def test_index_error_logging(self, client, mocker):
        """Test that indexing errors are logged."""
        mock_logger = mocker.patch("app.api.v1.endpoints.documents.logger")

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            side_effect=Exception("Test error")
        )

        client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "Test",
                        "metadata": {}
                    }
                ]
            }
        )

        # Should log error
        mock_logger.error.assert_called()


class TestDocumentEndpointsEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_index_very_long_document(self, client, mocker):
        """Test indexing a very long document."""
        long_content = "Lorem ipsum " * 10000  # Very long document

        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 50,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-long",
                        "content": long_content,
                        "metadata": {}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_index_document_with_unicode(self, client, mocker):
        """Test indexing document with Unicode characters."""
        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 3,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-unicode",
                        "content": "Document with emoji 🚀 and special chars: ñáéíóú",
                        "metadata": {"title": "Unicode Test 中文"}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_index_duplicate_document_ids(self, client, mocker):
        """Test indexing documents with duplicate IDs."""
        mock_response = {
            "success": True,
            "documents_processed": 2,
            "chunks_created": 10,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "First version",
                        "metadata": {}
                    },
                    {
                        "id": "doc-1",
                        "content": "Second version",
                        "metadata": {}
                    }
                ]
            }
        )

        # Should succeed (service layer handles duplicates)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestDocumentEndpointsIntegrationScenarios:
    """Integration scenarios for document endpoints."""

    def test_index_and_delete_workflow(self, client, mocker):
        """Test complete workflow of indexing and then deleting a document."""
        # Mock indexing
        mock_index_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 5,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_index_response)
        )

        # Index document
        index_response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-workflow",
                        "content": "Test document",
                        "metadata": {}
                    }
                ]
            }
        )

        assert index_response.status_code == status.HTTP_200_OK

        # Mock deletion
        mocker.patch(
            "app.services.rag_service.RAGService.delete_document",
            return_value=True
        )

        # Delete document
        delete_response = client.delete("/api/v1/documents/doc-workflow")

        assert delete_response.status_code == status.HTTP_200_OK

    def test_document_endpoints_with_rate_limiting(self, client, mocker):
        """Test that document endpoints respect rate limiting."""
        mock_response = {
            "success": True,
            "documents_processed": 1,
            "chunks_created": 5,
            "message": "Success"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": "doc-1",
                        "content": "Test",
                        "metadata": {}
                    }
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        # Rate limit headers should be present
        assert "X-RateLimit-Limit" in response.headers

    def test_batch_indexing_performance(self, client, mocker):
        """Test indexing multiple documents for performance."""
        num_docs = 10

        mock_response = {
            "success": True,
            "documents_processed": num_docs,
            "chunks_created": num_docs * 5,
            "message": f"Successfully indexed {num_docs} documents"
        }

        mocker.patch(
            "app.services.rag_service.RAGService.index_documents",
            return_value=mocker.Mock(**mock_response)
        )

        response = client.post(
            "/api/v1/index",
            json={
                "documents": [
                    {
                        "id": f"doc-{i}",
                        "content": f"Document {i} content with some text",
                        "metadata": {"index": i}
                    }
                    for i in range(num_docs)
                ]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["documents_processed"] == num_docs

        # Should have reasonable processing time
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
