from backend.app.tagging import extract_auto_tags


def test_extract_auto_tags_basic():
    assert "Web Development" in extract_auto_tags("FastAPI intro", "")
    assert "AI/ML" in extract_auto_tags("", "Intro to LLMs and neural nets")
    assert "Data Science" in extract_auto_tags("Plotting with pandas", "")
    assert "Testing" in extract_auto_tags("Pytest best practices", "")


def test_extract_auto_tags_no_match():
    assert extract_auto_tags("Hello world", "Unrelated text") == []
