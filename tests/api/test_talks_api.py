from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_and_version():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.get("/api/v1/version")
    assert r.status_code == 200
    assert "version" in r.json()


def test_create_search_get_and_types():
    # Create
    payload = {
        "title": "Intro to FastAPI",
        "description": "We build a simple API",
        "talk_type": "talk",
        "speaker_names": ["Alice", "Bob"],
    }
    r = client.post("/api/v1/talks", json=payload)
    assert r.status_code == 200
    talk_id = r.json()["id"]
    assert talk_id

    # Search
    r = client.get("/api/v1/talks/search", params={"q": "fastapi"})
    assert r.status_code == 200
    data = r.json()
    assert "talks" in data
    assert data["total"] >= 1
    ids = {t["id"] for t in data["talks"]}
    assert talk_id in ids

    # Get by id
    r = client.get(f"/api/v1/talks/{talk_id}")
    assert r.status_code == 200
    talk = r.json()
    assert talk["title"].strip() == "Intro to FastAPI"
    assert "Web Development" in talk.get("auto_tags", [])

    # Types endpoint
    r = client.get("/api/v1/talks/types")
    assert r.status_code == 200
    assert "talk" in r.json()["types"]
