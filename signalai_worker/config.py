from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SIGNALAI_", env_file=".env", extra="ignore"
    )

    database_url: str
    service_name: str = "signalai-worker"
    service_version: str = "0.1.0"
    poll_interval_seconds: float = Field(default=1.0, gt=0, le=30)
    lease_seconds: int = Field(default=900, ge=30, le=86400)
    retry_backoff_seconds: int = Field(default=10, ge=1, le=3600)
    max_attempts: int = Field(default=5, ge=1, le=20)
    max_jobs: int = Field(default=10, ge=1, le=100)
    pool_min_size: int = Field(default=1, ge=1, le=20)
    pool_max_size: int = Field(default=10, ge=1, le=50)


settings = Settings()
