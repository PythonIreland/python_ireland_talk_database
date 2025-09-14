"""Lightweight tagging helpers.

Very simple keyword-based auto-tagging to bootstrap data; may be
replaced later by a proper taxonomy service or ML model.
"""

from typing import List
import re

# Extremely simple keyword-based tagging; expand as needed later
_KEYWORDS = {
    "AI/ML": ["machine learning", "deep learning", "neural", "llm", "ai"],
    "Web Development": ["fastapi", "django", "flask", "web", "http", "api"],
    "Data Science": ["pandas", "numpy", "dataframe", "visualization", "plot"],
    "Testing": ["pytest", "tdd", "unit test", "integration test", "coverage"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def extract_auto_tags(title: str, description: str) -> List[str]:
    text = f"{_normalize(title)} {_normalize(description)}"
    tags: List[str] = []
    for tag, words in _KEYWORDS.items():
        if any(w in text for w in words):
            tags.append(tag)
    return tags
