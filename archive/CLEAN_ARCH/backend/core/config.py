# backend/core/config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/talks_db"
    )

    # Legacy Elasticsearch settings (for backward compatibility during migration)
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200

    # API settings
    api_v1_str: str = "/api/v1"
    project_name: str = "Python Ireland Talk Database"

    # CORS settings
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
