from arq.connections import RedisSettings

from signalai_worker.config import settings
from signalai_worker.jobs import execute_job


class WorkerSettings:
    functions = [execute_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = settings.max_jobs
    job_timeout = settings.job_timeout_seconds
    health_check_interval = 30
