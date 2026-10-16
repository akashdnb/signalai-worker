from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIGNALAI_", env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    service_name: str = "signalai-worker"
    service_version: str = "0.1.0"
    job_timeout_seconds: int = 300
    max_jobs: int = 10


settings = Settings()
