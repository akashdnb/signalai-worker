import asyncio
import logging
import os
import socket
import uuid
from typing import Any

from signalai_worker.config import settings
from signalai_worker.contracts import JobEnvelope
from signalai_worker.db import create_pool
from signalai_worker.handlers import HANDLERS
from signalai_worker.job_repository import JobRepository

logger = logging.getLogger(__name__)


class WorkerRuntime:
    def __init__(self) -> None:
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4()}"
        self._stop = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()

    def stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        pool = await create_pool()
        repository = JobRepository(pool, self.worker_id)
        try:
            await repository.recover_stale_jobs(settings.lease_seconds)
            logger.info("worker_started worker_id=%s", self.worker_id)
            while not self._stop.is_set():
                await self._reap_tasks()
                capacity = settings.max_jobs - len(self._tasks)
                claimed = 0
                for _ in range(max(capacity, 0)):
                    job = await repository.claim()
                    if not job:
                        break
                    task = asyncio.create_task(self._execute(repository, job))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
                    claimed += 1

                if claimed == 0:
                    try:
                        await asyncio.wait_for(self._stop.wait(), timeout=settings.poll_interval_seconds)
                    except asyncio.TimeoutError:
                        pass

            await self._shutdown_tasks()
        finally:
            await pool.close()
            logger.info("worker_stopped worker_id=%s", self.worker_id)

    async def _execute(self, repository: JobRepository, row: dict[str, Any]) -> None:
        job = JobEnvelope(
            job_id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            type=str(row["type"]),
            payload=dict(row["payload"] or {}),
            attempt=int(row["attempt"]),
            idempotency_key=str(row["idempotency_key"]),
            correlation_id=str(row["correlation_id"]),
            created_at=row["created_at"],
        )
        handler = HANDLERS.get(job.type)
        try:
            if handler is None:
                raise RuntimeError(f"unknown_job_type:{job.type}")
            result = await handler(job)
            if not await repository.complete(job.job_id, result):
                logger.warning("job_completion_lost job_id=%s", job.job_id)
        except Exception as exc:
            error_code = "UNKNOWN_JOB_TYPE" if str(exc).startswith("unknown_job_type:") else "JOB_EXECUTION_FAILED"
            await repository.fail_or_retry(
                job.job_id,
                job.attempt,
                int(row["max_attempts"]),
                error_code,
                str(exc),
                settings.retry_backoff_seconds * job.attempt,
            )
            logger.exception(
                "job_failed job_id=%s type=%s attempt=%s correlation_id=%s",
                job.job_id,
                job.type,
                job.attempt,
                job.correlation_id,
            )

    async def _reap_tasks(self) -> None:
        done = {task for task in self._tasks if task.done()}
        for task in done:
            self._tasks.discard(task)
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("worker_task_failed")

    async def _shutdown_tasks(self) -> None:
        if not self._tasks:
            return
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
