"""
API Health Check Integration Tests
==================================

Tests for the /health endpoint and basic API functionality.
"""

import pytest
from fastapi.testclient import TestClient

from kai_erp.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_correct_structure(self, client):
        """Health endpoint should return expected structure."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "version" in data
    
    def test_health_status_is_healthy(self, client):
        """Health endpoint should report healthy status."""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
    
    def test_health_service_name(self, client):
        """Health endpoint should report correct service name."""
        response = client.get("/health")
        data = response.json()
        
        assert data["service"] == "kai-erp-connector"
    
    def test_health_version_format(self, client):
        """Health endpoint should report a valid version string."""
        response = client.get("/health")
        data = response.json()
        
        # Version should be a non-empty string
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema_available(self, client):
        """OpenAPI schema should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_docs_endpoint_available(self, client):
        """Swagger UI docs should be available."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint_available(self, client):
        """ReDoc documentation should be available."""
        response = client.get("/redoc")
        assert response.status_code == 200
