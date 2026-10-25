"""Environment configuration. Secrets come from the environment, never from code."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://tarot:tarot@localhost:5432/tarot"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    db_echo: bool = False
    app_name: str = "Tarot Reading API"
    interpretation_provider: str = "mock"
    interpretation_base_url: str = ""
    interpretation_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    interpretation_model: str = ""
    interpretation_timeout_seconds: float = 60.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
