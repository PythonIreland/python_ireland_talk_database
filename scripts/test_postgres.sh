#!/bin/bash
# scripts/test_postgres.sh
# Simple test runner for the Postgres migration

echo "🧪 Running tests for Postgres migration..."

# Set environment variables for testing
export DATABASE_URL="sqlite:///:memory:"

# Run Ring 1 tests (pure Python logic)
echo "📝 Testing Ring 1 (Business Logic)..."
python -m pytest tests/test_ring1.py -v

# Run Ring 2 tests (Database layer) 
echo "📝 Testing Ring 2 (Database Layer)..."
python -m pytest tests/test_postgres_client.py -v

echo "✅ All tests completed!"
