# tests/conftest.py
"""
Shared test configuration and fixtures
"""
import pytest
import os
import subprocess
import time
import socket
from backend.database.postgres_client import PostgresClient


def _is_port_open(host: str, port: int) -> bool:
    """Check if a port is open"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


@pytest.fixture(scope="session")
def test_database_url():
    """Get the test database URL from environment or use default"""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:testpass@localhost:5433/talks_test_db",
    )


@pytest.fixture(scope="session")
def ensure_test_db():
    """Ensure test PostgreSQL database is running"""
    # Check if database is already running
    if _is_port_open("localhost", 5433):
        print("Test database already running")
        yield
        return

    print("Starting test database...")

    # Start the test database
    try:
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d", "--wait"],
            check=True,
            cwd="/home/jcurry/repos/python_ireland_talk_database",
        )

        # Wait for PostgreSQL to be ready
        max_retries = 30
        for i in range(max_retries):
            if _is_port_open("localhost", 5433):
                time.sleep(2)  # Extra time for PostgreSQL to fully initialize
                break
            time.sleep(1)
        else:
            raise RuntimeError("Test database failed to start")

        print("Test database ready")
        yield

    finally:
        # Clean up: stop the test database
        print("Stopping test database...")
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"],
            cwd="/home/jcurry/repos/python_ireland_talk_database",
        )


@pytest.fixture
def postgres_client(test_database_url, ensure_test_db):
    """Create a PostgresClient with test PostgreSQL database"""
    client = PostgresClient(connection_string=test_database_url)

    # Initialize database tables and indexes
    client.init_database()

    # Clean slate before each test
    client.delete_all_talks()

    yield client

    # Clean up after each test
    client.delete_all_talks()
