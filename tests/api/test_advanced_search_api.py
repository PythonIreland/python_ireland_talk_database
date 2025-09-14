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


def test_advanced_search_by_taxonomy_ids_any_and_all():
    # Setup: talks and taxonomies
    t1 = _create_talk("Talk One")
    t2 = _create_talk("Talk Two")
    t3 = _create_talk("Talk Three")

    topic_id = _create_taxonomy("Topic")
    level_id = _create_taxonomy("Level")

    py_id = _create_taxonomy_value(topic_id, "Python")
    web_id = _create_taxonomy_value(topic_id, "Web")

    beg_id = _create_taxonomy_value(level_id, "Beginner")
    adv_id = _create_taxonomy_value(level_id, "Advanced")

    # Tagging:
    # t1: Topic=Python, Level=Beginner
    _tag_talk(t1, [py_id, beg_id])
    # t2: Topic=Python, Level=Advanced
    _tag_talk(t2, [py_id, adv_id])
    # t3: Topic=Web, Level=Beginner
    _tag_talk(t3, [web_id, beg_id])

    # ANY match: taxonomy_value_ids=[Python] -> t1, t2
    r = client.get(
        "/api/v1/talks/search/advanced",
        params={"taxonomy_value_ids": [py_id], "match": "any"},
    )
    assert r.status_code == 200
    data = r.json()
    ids = {t["id"] for t in data["talks"]}
    assert ids == {t1, t2}
    assert data["total"] == 2

    # ALL match: [Python, Beginner] -> t1 only
    r = client.get(
        "/api/v1/talks/search/advanced",
        params={"taxonomy_value_ids": [py_id, beg_id], "match": "all"},
    )
    assert r.status_code == 200
    data = r.json()
    ids = {t["id"] for t in data["talks"]}
    assert ids == {t1}
    assert data["total"] == 1


def test_advanced_search_by_taxonomy_name_filters():
    # Setup: talks and taxonomies
    t1 = _create_talk("Alpha Talk")
    t2 = _create_talk("Beta Talk")

    topic_id = _create_taxonomy("Topic")
    level_id = _create_taxonomy("Level")

    py_id = _create_taxonomy_value(topic_id, "Python")
    beg_id = _create_taxonomy_value(level_id, "Beginner")

    # t1: Topic=Python, Level=Beginner; t2: Level=Beginner
    _tag_talk(t1, [py_id, beg_id])
    _tag_talk(t2, [beg_id])

    # taxonomy_Topic=Python -> t1 only
    r = client.get(
        "/api/v1/talks/search/advanced",
        params=[("taxonomy_Topic", "Python")],
    )
    assert r.status_code == 200
    data = r.json()
    ids = {t["id"] for t in data["talks"]}
    assert ids == {t1}

    # taxonomy_Level=Beginner -> t1, t2
    r = client.get(
        "/api/v1/talks/search/advanced",
        params=[("taxonomy_Level", "Beginner")],
    )
    assert r.status_code == 200
    data = r.json()
    ids = {t["id"] for t in data["talks"]}
    assert ids == {t1, t2}

    # AND across names with match=all -> t1 only
    r = client.get(
        "/api/v1/talks/search/advanced",
        params=[
            ("taxonomy_Topic", "Python"),
            ("taxonomy_Level", "Beginner"),
            ("match", "all"),
        ],
    )
    assert r.status_code == 200
    data = r.json()
    ids = {t["id"] for t in data["talks"]}
    assert ids == {t1}
