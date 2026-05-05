from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OrderFlow API"
    database_path: str = "orderflow.db"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_retries: int = 3
    retry_ttl_ms: int = 5000
    rabbitmq_connection_attempts: int = 10
    rabbitmq_connection_retry_seconds: float = 2.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
