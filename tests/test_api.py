from environment.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_reset():
    response = client.post("/reset", json={"task_id": "task1"})
    assert response.status_code == 200
    assert "observation" in response.json()

def test_reset_without_body_defaults_to_task1():
    response = client.post("/reset")
    assert response.status_code == 200
    payload = response.json()
    assert payload["observation"]["task_id"] == "task1"
    assert "session_id" in payload
