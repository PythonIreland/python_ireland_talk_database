from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_ingest_status_flow():
    # Initially empty
    r = client.get("/api/v1/ingest/status")
    assert r.status_code == 200
    assert r.json()["statuses"] == []

    # Run full ingest
    r = client.post("/api/v1/ingest/full")
    assert r.status_code == 200
    statuses = r.json()["sources"]
    assert any(s["source_type"] == "sessionize" for s in statuses)
    assert any(s["source_type"] == "meetup" for s in statuses)

    # If we actually saved items, types should reflect them
    r = client.get("/api/v1/talks/types")
    assert r.status_code == 200
    types = r.json().get("types", [])
    for s in statuses:
        if s.get("source_type") == "sessionize" and s.get("saved", 0) > 0:
            assert "talk" in types
        if s.get("source_type") == "meetup" and s.get("saved", 0) > 0:
            assert "meetup" in types

    # Status endpoint now shows at least both sources
    r = client.get("/api/v1/ingest/status")
    assert r.status_code == 200
    all_statuses = r.json()["statuses"]
    assert len(all_statuses) >= 2
    assert any(s["source_type"] == "sessionize" for s in all_statuses)
    assert any(s["source_type"] == "meetup" for s in all_statuses)
