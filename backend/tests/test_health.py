from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_devices_requires_auth():
    # No token supplied -> should be rejected, not silently return data
    response = client.get("/devices")
    assert response.status_code == 401
