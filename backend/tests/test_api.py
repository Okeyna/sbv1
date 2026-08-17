"""Basic API tests for StudyBuddy backend"""
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_app
from app.database import db
from app.config import Config


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create authenticated test client"""
    # First register a user
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Login to get token
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    token = response.get_json()['access_token']
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    
    return client


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'StudyBuddy' in data['message']


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_register_user(client):
    """Test user registration"""
    response = client.post('/api/auth/register', json={
        'email': 'newuser@example.com',
        'password': 'securepass123'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == 'newuser@example.com'


def test_register_duplicate_email(client):
    """Test registering with duplicate email"""
    # First registration
    client.post('/api/auth/register', json={
        'email': 'duplicate@example.com',
        'password': 'securepass123'
    })
    
    # Second registration with same email
    response = client.post('/api/auth/register', json={
        'email': 'duplicate@example.com',
        'password': 'anotherpass123'
    })
    
    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_login_user(client):
    """Test user login"""
    # Register first
    client.post('/api/auth/register', json={
        'email': 'loginuser@example.com',
        'password': 'loginpass123'
    })
    
    # Login
    response = client.post('/api/auth/login', json={
        'email': 'loginuser@example.com',
        'password': 'loginpass123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'wrongpass'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_protected_endpoint_without_token(client):
    """Test protected endpoint without authentication"""
    response = client.get('/api/auth/me')
    assert response.status_code == 401


def test_protected_endpoint_with_token(auth_client):
    """Test protected endpoint with authentication"""
    response = auth_client.get('/api/auth/me')
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'


def test_file_upload_validation(auth_client):
    """Test file upload validation"""
    # Try to upload without file
    response = auth_client.post('/api/files/upload')
    assert response.status_code == 400
    
    # Try to upload non-PDF (would need actual file for full test)
    # This is a basic test - full test would require test file


def test_docs_endpoint(client):
    """Test API docs endpoint"""
    response = client.get('/docs')
    assert response.status_code == 200
    data = response.get_json()
    assert 'endpoints' in data
