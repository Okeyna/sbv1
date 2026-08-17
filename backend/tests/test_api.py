"""Basic API tests for StudyBuddy backend"""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.database as database_module
from app.config import Config
from app.database import Base
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    """Create a test client against a temporary SQLite database."""
    db_path = tmp_path / "studybuddy_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    database_module.engine = engine
    database_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    Config.JWT_SECRET_KEY = "test-secret-key"
    Config.JWT_ALGORITHM = "HS256"
    Config.SECRET_KEY = "test-secret-key"

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def register_user(client, email: str = "newuser@example.com", password: str = "securepass123"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client, email: str, password: str):
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "StudyBuddy" in data["message"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client):
    data = register_user(client)
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"


def test_register_duplicate_email(client):
    register_user(client, "duplicate@example.com", "securepass123")

    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "anotherpass123"},
    )

    assert response.status_code == 409
    assert "detail" in response.json()


def test_login_user(client):
    register_user(client, "loginuser@example.com", "loginpass123")
    data = login_user(client, "loginuser@example.com", "loginpass123")
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@example.com"


def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_protected_endpoint_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_token(client):
    register_data = register_user(client, "authuser@example.com", "testpass123")
    token = register_data["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "authuser@example.com"


def test_file_upload_success(client):
    register_data = register_user(client, "fileuser@example.com", "securepass123")
    token = register_data["access_token"]

    pdf_path = Path(__file__).with_name("sample.pdf")
    if not pdf_path.exists():
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 65 >>\nstream\nBT\n/F1 18 Tf\n50 100 Td\n(StudyBuddy Test PDF) Tj\nET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000123 00000 n \n0000000246 00000 n \n0000000617 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n760\n%%EOF\n"
        pdf_path.write_bytes(pdf_content)

    with pdf_path.open("rb") as fh:
        response = client.post(
            "/files/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (pdf_path.name, fh.read(), "application/pdf")},
        )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["filename"].endswith(".pdf")
    assert data["status"] in {"processing", "ready", "error"}
