from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite+aiosqlite:///./hosted.db"

    openai_base_url: str | None = None
    openai_api_key: str | None = None
    anthropic_base_url: str | None = None
    anthropic_api_key: str | None = None
    llm_provider: str | None = None

    max_upload_size_mb: int = 5
    upload_dir: str = "uploads"

    demo_auto_seed: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
