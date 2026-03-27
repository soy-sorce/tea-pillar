"""Application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    gcp_project_id: str = Field(default="")
    gcp_region: str = Field(default="asia-northeast1")

    model_service_url: str = Field(default="")
    model_service_timeout_seconds: int = Field(default=30)

    gemini_model: str = Field(default="gemini-2.5-flash")
    gemini_timeout: int = Field(default=15)

    veo_model: str = Field(default="veo-3.1-fast-generate-001")
    veo_timeout: int = Field(default=300)
    veo_polling_interval: int = Field(default=5)

    gcs_bucket_name: str = Field(default="")
    reaction_video_bucket_name: str = Field(default="")
    gcs_signed_url_expiration_hours: int = Field(default=1)
    gcs_signing_service_account_file: str = Field(default="")
    reaction_video_upload_url_expires_seconds: int = Field(default=900)

    firestore_database_id: str = Field(default="(default)")

    thompson_default_alpha: float = Field(default=1.0)
    thompson_default_beta: float = Field(default=1.0)
    reward_success_threshold: float = Field(default=1.0)

    environment: str = Field(default="development")
    frontend_origin: str = Field(default="http://localhost:5173")
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
