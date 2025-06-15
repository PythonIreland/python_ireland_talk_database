# backend/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200

    class Config:
        env_file = ".env"


settings = Settings()
