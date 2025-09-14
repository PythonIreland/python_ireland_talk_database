from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _create_talk(title: str) -> str:
    r = client.post(
        "/api/v1/talks",
        json={
            "title": title,
            "description": "desc",
            "talk_type": "talk",
        },
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_taxonomy(name: str) -> int:
    r = client.post(
        "/api/v1/talks/taxonomies",
        json={"name": name, "description": f"{name} taxonomy"},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_taxonomy_value(taxonomy_id: int, value: str) -> int:
    r = client.post(
        f"/api/v1/talks/taxonomies/{taxonomy_id}/values",
        json={"value": value},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _tag_talk(talk_id: str, value_ids: list[int]):
    r = client.post(f"/api/v1/talks/{talk_id}/tags/add", json={"value_ids": value_ids})
    assert r.status_code == 200


def test_taxonomy_usage_and_popular_tags():
    # Setup data
    t1 = _create_talk("A")
    t2 = _create_talk("B")
    topic_id = _create_taxonomy("Topic")
    level_id = _create_taxonomy("Level")

    py = _create_taxonomy_value(topic_id, "Python")
    web = _create_taxonomy_value(topic_id, "Web")
    beg = _create_taxonomy_value(level_id, "Beginner")

    # Tag talks: t1 -> Python + Beginner, t2 -> Web
    _tag_talk(t1, [py, beg])
    _tag_talk(t2, [web])

    # All taxonomy usage
    r = client.get("/api/v1/talks/analytics/taxonomy-usage")
    assert r.status_code == 200
    usage = r.json().get("usage", [])
    assert isinstance(usage, list)
    # Ensure Topic and Level present
    names = {g.get("taxonomy_name") for g in usage}
    assert {"Topic", "Level"}.issubset(names)

    # Usage by taxonomy id
    r = client.get(f"/api/v1/talks/analytics/taxonomies/{topic_id}/usage")
    assert r.status_code == 200
    topic_usage = r.json().get("usage", [])
    assert len(topic_usage) == 1
    vals = {v["value"]: v["count"] for v in topic_usage[0].get("values", [])}
    # Python used once, Web used once
    assert vals.get("Python", 0) == 1
    assert vals.get("Web", 0) == 1

    # Popular tags
    r = client.get("/api/v1/talks/analytics/popular-tags", params={"limit": 10})
    assert r.status_code == 200
    tags = r.json().get("tags", [])
    assert any(t["value"] in ("Python", "Web", "Beginner") for t in tags)
