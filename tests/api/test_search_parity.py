from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_search_id_prefix_and_multi_types():
    # Create multiple talks
    t1 = client.post(
        "/api/v1/talks",
        json={"title": "T1", "description": "A", "talk_type": "talk"},
    ).json()["id"]
    t2 = client.post(
        "/api/v1/talks",
        json={"title": "T2", "description": "B", "talk_type": "lightning"},
    ).json()["id"]

    # id: prefix
    r = client.get("/api/v1/talks/search", params={"q": f"id:{t1}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["talks"][0]["id"] == t1

    # multi types
    r = client.get(
        "/api/v1/talks/search",
        params=[("talk_types", "talk"), ("talk_types", "lightning")],
    )
    assert r.status_code == 200
    data = r.json()
    ids = {t["id"] for t in data["talks"]}
    assert {t1, t2}.issubset(ids)
