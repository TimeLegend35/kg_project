"""
Test Suite für Chat Service
"""
import pytest
from fastapi.testclient import TestClient
from chat_api.main import app

client = TestClient(app)


def test_root():
    """Test Root Endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


def test_health_check():
    """Test Health Check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_session():
    """Test Session Creation"""
    response = client.post(
        "/sessions",
        json={"user_id": "test_user", "title": "Test Session"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["user_id"] == "test_user"
    assert data["title"] == "Test Session"


# TODO: Weitere Tests hinzufügen
# - test_chat_stream()
# - test_get_history()
# - test_tool_calls()

