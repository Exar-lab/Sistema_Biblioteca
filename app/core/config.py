"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for infrastructure settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
