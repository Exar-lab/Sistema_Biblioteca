"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for synchronous SQLAlchemy + Oracle access."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Example: oracle+oracledb://USER:PASSWORD@HOST:1521/?service_name=FREEPDB1
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
