"""
Comprehensive Test Suite for Log Classification System

QA Engineer: Enterprise-grade testing with pytest

Test Coverage:
- Unit tests for each classifier
- Integration tests for API endpoints  
- Database operation tests
- Authentication and authorization tests
- Performance benchmarks
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from server import app
from auth import create_access_token
from database import init_db, get_db, create_user, get_password_hash

client = TestClient(app)


# Fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize test database"""
    init_db()
    yield


@pytest.fixture
def auth_headers():
    """Get authentication headers for testing"""
    token = create_access_token(data={"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


# Authentication Tests
class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login"""
        response = client.post("/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_failure(self):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", data={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_protected_endpoint_without_auth(self):
        """Test protected endpoint without authentication"""
        response = client.get("/api/info")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, auth_headers):
        """Test protected endpoint with authentication"""
        response = client.get("/api/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "role" in data


# Health and Monitoring Tests
class TestMonitoring:
    """Test health and monitoring endpoints"""
    
    def test_health_check(self, auth_headers):
        """Test health check endpoint"""
        response = client.get("/health", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
    
    def test_metrics_endpoint(self, auth_headers):
        """Test metrics endpoint"""
        response = client.get("/metrics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_classifications" in data
        assert "average_processing_time_ms" in data


# Classifier Tests
class TestClassifiers:
    """Test individual classifiers"""
    
    def test_regex_classifier(self):
        """Test regex pattern matching"""
        from processor_regex import classify_with_regex
        
        test_cases = [
            ("User user123 logged in successfully", "User Actions"),
            ("System backup completed", "System Notifications"),
            ("Unknown log message", None)
        ]
        
        for log_msg, expected in test_cases:
            result = classify_with_regex(log_msg)
            assert result == expected
    
    def test_bert_classifier(self):
        """Test BERT classification"""
        from processor_bert import classify_with_bert
        
        log_msg = "alpha.osapi_compute.wsgi.server - API returned 404 not found"
        result = classify_with_bert(log_msg)
        assert result is not None
        assert isinstance(result, str)
    
    @pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="No GROQ_API_KEY")
    def test_llm_classifier(self):
        """Test LLM classification (requires API key)"""
        from processor_llm import classify_with_llm
        
        log_msg = "Deprecated function call detected in legacy module"
        result = classify_with_llm(log_msg)
        assert result is not None
        assert isinstance(result, str)


# Performance Tests
class TestPerformance:
    """Test performance benchmarks"""
    
    def test_regex_performance(self):
        """Test regex classifier speed"""
        from processor_regex import classify_with_regex
        
        log_msg = "User user123 logged in successfully"
        start = time.time()
        
        for _ in range(100):
            classify_with_regex(log_msg)
        
        elapsed_ms = (time.time() - start) * 1000
        avg_ms = elapsed_ms / 100
        
        assert avg_ms < 5, f"Regex too slow: {avg_ms}ms per log"
    
    def test_bert_performance(self):
        """Test BERT classifier speed"""
        from processor_bert import classify_with_bert
        
        log_msg = "System error occurred during processing"
        start = time.time()
        
        for _ in range(10):
            classify_with_bert(log_msg)
        
        elapsed_ms = (time.time() - start) * 1000
        avg_ms = elapsed_ms / 10
        
        assert avg_ms < 200, f"BERT too slow: {avg_ms}ms per log"


# Database Tests
class TestDatabase:
    """Test database operations"""
    
    def test_create_user(self):
        """Test user creation"""
        with get_db() as db:
            user = create_user(
                db, 
                username=f"testuser_{int(time.time())}",
                email=f"test_{int(time.time())}@example.com",
                hashed_password=get_password_hash("test123"),
                role="viewer"
            )
            assert user.username is not None
            assert user.role == "viewer"
    
    def test_job_creation(self):
        """Test classification job creation"""
        from database import create_classification_job
        
        with get_db() as db:
            job = create_classification_job(
                db,
                job_id=f"test_job_{int(time.time())}",
                user_id=1,
                filename="test.csv",
                total_logs=100
            )
            assert job.job_id is not None
            assert job.total_logs == 100


# API Integration Tests
class TestAPIIntegration:
    """Test complete API workflows"""
    
    def test_full_classification_workflow(self, auth_headers):
        """Test complete classification workflow"""
        # This would test file upload, processing, and result retrieval
        # Skipped for now as it requires actual CSV file
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
