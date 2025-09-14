from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_taxonomy_crud_and_tagging_flow():
    # Create a talk
    r = client.post(
        "/api/v1/talks",
        json={
            "title": "Tagged Talk",
            "description": "About tags",
            "talk_type": "talk",
        },
    )
    assert r.status_code == 200
    talk_id = r.json()["id"]

    # Create taxonomy
    r = client.post(
        "/api/v1/talks/taxonomies",
        json={"name": "Topic", "description": "Topic taxonomy"},
    )
    assert r.status_code == 200
    taxonomy = r.json()
    taxonomy_id = taxonomy["id"]

    # Add a value
    r = client.post(
        f"/api/v1/talks/taxonomies/{taxonomy_id}/values",
        json={"value": "Python", "color": "#3572A5"},
    )
    assert r.status_code == 200
    value = r.json()
    value_id = value["id"]

    # Tag talk (add)
    r = client.post(
        f"/api/v1/talks/{talk_id}/tags/add",
        json={"value_ids": [value_id]},
    )
    assert r.status_code == 200

    # Get tags
    r = client.get(f"/api/v1/talks/{talk_id}/tags")
    assert r.status_code == 200
    data = r.json()
    assert data["tags"] and any(g["taxonomy_name"] == "Topic" for g in data["tags"])  # type: ignore

    # Replace tags (no-op)
    r = client.put(
        f"/api/v1/talks/{talk_id}/tags",
        json={"value_ids": [value_id]},
    )
    assert r.status_code == 200

    # Remove tag
    r = client.delete(f"/api/v1/talks/{talk_id}/tags/{value_id}")
    assert r.status_code == 200

    # Update taxonomy
    r = client.put(
        f"/api/v1/talks/taxonomies/{taxonomy_id}",
        json={"description": "Updated desc"},
    )
    assert r.status_code == 200

    # Delete taxonomy
    r = client.delete(f"/api/v1/talks/taxonomies/{taxonomy_id}")
    assert r.status_code == 200
