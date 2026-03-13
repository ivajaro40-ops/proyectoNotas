import os
import sys
import tempfile
import pytest

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app import create_app  # noqa: E402


@pytest.fixture
def app():
    """Create a test application with a temporary database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    test_config = {
        "TESTING": True,
        "DATABASE_URL": db_path,
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
        "password": "password123",
        "password_confirm": "password123",
    })
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def auth_headers_user2(client):
    """Register and login a SECOND user, return auth headers."""
    client.post("/api/auth/register", json={
        "email": "other@example.com",
        "password": "password456",
        "password_confirm": "password456",
    })
    response = client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password": "password456",
    })
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
