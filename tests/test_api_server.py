import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data

def test_get_job_status_not_found():
    response = client.get("/api/jobs/nonexistent_job")
    # Because there's no auth provided and no API_SECRET_TOKEN set by default in test, 
    # it might return 404. Let's check 404.
    assert response.status_code == 404
    assert response.json()["detail"] == "Job no encontrado"
