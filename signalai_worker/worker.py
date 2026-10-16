from arq.connections import RedisSettings

from signalai_worker.config import settings
from signalai_worker.jobs import execute_job


async def startup(_ctx: dict) -> None:
    return None


async def shutdown(_ctx: dict) -> None:
    return None


class WorkerSettings:
    functions = [execute_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = settings.max_jobs
    job_timeout = settings.job_timeout_seconds
    health_check_interval = 30
    max_tries = settings.max_attempts
    retry_jobs = True
    on_startup = startup
    on_shutdown = shutdown
