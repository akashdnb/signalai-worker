from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SIGNALAI_", env_file=".env", extra="ignore"
    )

    redis_url: str = "redis://localhost:6379/0"
    service_name: str = "signalai-worker"
    service_version: str = "0.1.0"
    job_timeout_seconds: int = Field(default=300, ge=1, le=3600)
    max_jobs: int = Field(default=10, ge=1, le=100)
    idempotency_ttl_seconds: int = Field(default=86400, ge=60, le=604800)
    execution_lock_seconds: int = Field(default=900, ge=30, le=86400)
    retry_backoff_seconds: int = Field(default=10, ge=1, le=3600)
    max_attempts: int = Field(default=5, ge=1, le=20)


settings = Settings()
