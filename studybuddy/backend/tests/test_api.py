import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Use SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client with test database."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    
    # Drop tables
    Base.metadata.drop_all(bind=engine)
    
    # Clean up test database
    if os.path.exists("./test.db"):
        os.remove("./test.db")


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "StudyBuddy" in data["message"]
    assert data["version"] == "1.0.0"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "role" in data


def test_register_duplicate_email(client):
    """Test registering with duplicate email fails."""
    # First registration
    client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpass123"
        }
    )
    
    # Second registration with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client):
    """Test successful login."""
    # Register first
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpass123"
        }
    )
    
    # Login
    response = client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "testpass123",
            "grant_type": "password"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
            "grant_type": "password"
        }
    )
    assert response.status_code == 401


def test_protected_endpoint_without_token(client):
    """Test that protected endpoints reject missing token."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_token(client):
    """Test that protected endpoints work with valid token."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "protected@example.com",
            "password": "testpass123"
        }
    )
    
    login_response = client.post(
        "/auth/login",
        data={
            "username": "protected@example.com",
            "password": "testpass123",
            "grant_type": "password"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "protected@example.com"


def test_file_upload_non_pdf(client):
    """Test that non-PDF file uploads are rejected."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "upload@example.com",
            "password": "testpass123"
        }
    )
    
    login_response = client.post(
        "/auth/login",
        data={
            "username": "upload@example.com",
            "password": "testpass123",
            "grant_type": "password"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Try to upload a text file (should fail)
    response = client.post(
        "/files/upload",
        files={"file": ("test.txt", b"test content", "text/plain")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]


def test_mock_summary_generation():
    """Test that mock summary is generated when no OpenAI key."""
    from app.services.ai_service import generate_summary
    
    summary = generate_summary("Test content")
    assert summary is not None
    assert len(summary) > 0
    assert "•" in summary  # Bullet points


def test_mock_quiz_generation():
    """Test that mock quiz is generated when no OpenAI key."""
    from app.services.ai_service import generate_quiz
    
    quiz = generate_quiz("Test content", num_questions=5)
    assert quiz is not None
    assert len(quiz) == 5
    
    # Check structure
    for question in quiz:
        assert "question" in question
        assert "options" in question
        assert len(question["options"]) == 4
        assert "correct_answer" in question
        assert 0 <= question["correct_answer"] <= 3
        assert "explanation" in question
