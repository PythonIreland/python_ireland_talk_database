from backend.db import repo


def test_repo_upsert_and_search_sqlite():
    # Create
    tid = repo.db_save_talk(
        {
            "title": "Searchable Title",
            "description": "Something descriptive",
            "talk_type": "lightning",
            "source_type": "manual",
            "source_id": "1",
        }
    )
    assert tid

    # Upsert by source
    tid2 = repo.db_save_talk(
        {
            "title": "Updated Title",
            "description": "Updated",
            "talk_type": "lightning",
            "source_type": "manual",
            "source_id": "1",
        }
    )
    assert tid2 == tid

    # Search
    res = repo.db_search_talks("updated", {}, limit=10, offset=0)
    assert res["total"] >= 1
    assert any(t["id"] == tid for t in res["items"])

    # Get one
    one = repo.db_get_talk(tid)
    assert one and one["title"].startswith("Updated")
