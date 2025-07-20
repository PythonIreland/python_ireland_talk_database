FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --dev

# Copy application code
COPY . .

# Set Python path for our package imports
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/talks/health || exit 1

# Run the application
CMD ["uvicorn", "backend.run:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
