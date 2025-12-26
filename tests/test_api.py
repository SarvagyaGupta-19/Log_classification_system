"""
Integration Tests for API Endpoints
Owner: QA Engineer
Critical: End-to-end API testing
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
import io

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from server import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and monitoring endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_classifications" in data
        assert "average_processing_time_ms" in data


class TestClassificationEndpoint:
    """Test classification endpoint"""
    
    def test_classification_invalid_file_type(self):
        """Test invalid file type rejection"""
        file_content = b"test content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/classify/", files=files)
        assert response.status_code == 400
        assert "CSV" in response.json()["detail"]
    
    def test_classification_missing_columns(self):
        """Test missing columns validation"""
        csv_content = b"col1,col2\nval1,val2"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post("/classify/", files=files)
        assert response.status_code == 400
        assert "source" in response.json()["detail"] or "log_message" in response.json()["detail"]
    
    def test_classification_valid_csv(self):
        """Test valid CSV classification"""
        csv_content = b"source,log_message\nWebServer,User User123 logged in.\nDatabase,Backup completed successfully."
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post("/classify/", files=files)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


class TestPlotEndpoint:
    """Test visualization endpoint"""
    
    def test_plot_without_data(self):
        """Test plot generation without data"""
        # Remove output file if exists
        if os.path.exists("resources/output.csv"):
            os.remove("resources/output.csv")
        
        response = client.get("/plot/")
        # Should fail gracefully
        assert response.status_code in [404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
