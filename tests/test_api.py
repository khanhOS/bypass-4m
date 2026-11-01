from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert response.json()["component"] == "api"

def test_frontend_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "AUTO BYPASS" in response.text

def test_github_pages_cors_preflight():
    response = client.options(
        "/api/bypass",
        headers={
            "Origin": "https://khanhos.github.io",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://khanhos.github.io"

def test_rejects_unsupported_domain():
    response = client.post("/api/bypass", json={"url": "https://example.com/"})
    assert response.status_code == 422

def test_rejects_extra_request_fields():
    response = client.post("/api/bypass", json={"url": "https://link4m.net/a", "extra": True})
    assert response.status_code == 422
