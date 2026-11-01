from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_rejects_unsupported_domain():
    response = client.post("/api/bypass", json={"url": "https://example.com/"})
    assert response.status_code == 422

def test_rejects_extra_request_fields():
    response = client.post("/api/bypass", json={"url": "https://link4m.net/a", "extra": True})
    assert response.status_code == 422
