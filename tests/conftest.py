import os
import sys
import tempfile
import pytest
from sqlalchemy import text

# Add project root to sys.path so 'backend' and 'lib' can be imported in tests
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def pytest_sessionstart(session):
    """Configure an isolated SQLite DB for the whole test session before imports."""
    tmpdir = tempfile.mkdtemp(prefix="talkdb_tests_")
    db_path = os.path.join(tmpdir, "app_test.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    # Disable outbound network for ingestion to keep tests deterministic
    os.environ["INGEST_DISABLE_NETWORK"] = "1"


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure a clean DB before each test (on the test database)."""
    # Import here to ensure engine binds to DATABASE_URL set above
    from backend.db.engine import get_engine, init_db  # noqa: WPS433

    init_db()
    engine = get_engine()
    with engine.begin() as conn:
        try:
            conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
        except Exception:
            pass
        for table in (
            "talk_taxonomy_values",
            "taxonomy_values",
            "taxonomies",
            "talks",
            "sync_status",
        ):
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        try:
            conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        except Exception:
            pass
    yield
