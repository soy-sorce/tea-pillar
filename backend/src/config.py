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

    gcp_project_id: str = Field(
        default="",
        description="Set when the GCP project is decided.",
    )
    gcp_region: str = Field(default="asia-northeast1")

    vertex_endpoint_id: str = Field(
        default="",
        description="Set after the Vertex AI Custom Endpoint is deployed.",
    )
    vertex_endpoint_location: str = Field(default="asia-northeast1")
    vertex_prediction_timeout: int = Field(default=30)

    gemini_model: str = Field(default="gemini-2.5-flash")
    gemini_timeout: int = Field(default=15)

    veo_model: str = Field(default="veo-3.1-fast")
    veo_timeout: int = Field(default=300)
    veo_polling_interval: int = Field(default=5)

    gcs_bucket_name: str = Field(
        default="",
        description="Set after the Veo output bucket is provisioned.",
    )
    model_input_bucket_name: str = Field(
        default="video-gen4cat-model-inputs-94553428765",
        description="Temporary GCS bucket for model input images.",
    )
    gcs_signed_url_expiration_hours: int = Field(default=1)

    firestore_database_id: str = Field(default="(default)")
    bandit_ucb_alpha: float = Field(default=1.0)

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    default_candidate_video_ids: list[str] = Field(
        default_factory=lambda: [f"video-{index}" for index in range(1, 11)],
        description="v1 fixed candidate set from fixed_train_data/manifest.csv.",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
