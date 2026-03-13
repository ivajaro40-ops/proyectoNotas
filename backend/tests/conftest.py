import os
import sys
import tempfile
import pytest

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Set secrets to bypass strict environment heuristics in config.py
os.environ["TESTING"] = "true"
os.environ.setdefault("JWT_SECRET", "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90")
os.environ.setdefault("ENCRYPTION_MASTER_KEY", "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff")

from app import create_app  # noqa: E402
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_recaptcha():
    """Mock the reCAPTCHA verification to always succeed in tests."""
    with patch("auth.verify_recaptcha", return_value=True):
        yield


@pytest.fixture
def app():
    """Create a test application with a temporary database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    test_config = {
        "TESTING": True,
        "DATABASE_URL": db_path,
        # Provide a valid JWT_SECRET for tests (bypasses env validation)
        "JWT_SECRET": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
        "ENCRYPTION_MASTER_KEY": "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        "RATELIMIT_ENABLED": False,
    }
    app = create_app(test_config)
    yield app
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register and login a user, return auth headers."""
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def auth_headers_user2(client):
    """Register and login a SECOND user, return auth headers."""
    client.post("/api/auth/register", json={
        "email": "other@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    response = client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
