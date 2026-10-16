import json
from typing import Any

import asyncpg


class JobRepository:
    def __init__(self, pool: asyncpg.Pool, worker_id: str) -> None:
        self.pool = pool
        self.worker_id = worker_id

    async def recover_stale_jobs(self, lease_seconds: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                update execution_jobs
                set status = case when attempt >= max_attempts then 'failed' else 'queued' end,
                    available_at = case when attempt >= max_attempts then available_at else now() end,
                    locked_at = null,
                    locked_by = null,
                    error_code = case when attempt >= max_attempts then 'LEASE_EXPIRED' else null end,
                    error_message = case when attempt >= max_attempts then 'worker lease expired' else null end,
                    updated_at = now(),
                    completed_at = case when attempt >= max_attempts then now() else completed_at end
                where status = 'running'
                  and locked_at < now() - ($1 * interval '1 second')
                """,
                lease_seconds,
            )

    async def claim(self) -> dict[str, Any] | None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    with candidate as (
                      select id
                      from execution_jobs
                      where status = 'queued'
                        and available_at <= now()
                        and attempt < max_attempts
                      order by available_at asc, created_at asc
                      for update skip locked
                      limit 1
                    )
                    update execution_jobs j
                    set status = 'running',
                        attempt = j.attempt + 1,
                        locked_at = now(),
                        locked_by = $1,
                        updated_at = now()
                    from candidate
                    where j.id = candidate.id
                    returning j.*
                    """,
                    self.worker_id,
                )
                return dict(row) if row else None

    async def heartbeat(self, job_id: str) -> bool:
        async with self.pool.acquire() as conn:
            command = await conn.execute(
                """
                update execution_jobs
                set locked_at = now(), updated_at = now()
                where id = $1 and status = 'running' and locked_by = $2
                """,
                job_id,
                self.worker_id,
            )
            return command.endswith(" 1")

    async def complete(self, job_id: str, result: dict[str, Any]) -> bool:
        async with self.pool.acquire() as conn:
            command = await conn.execute(
                """
                update execution_jobs
                set status = 'completed',
                    result = $1::jsonb,
                    locked_at = null,
                    locked_by = null,
                    completed_at = now(),
                    updated_at = now()
                where id = $2 and status = 'running' and locked_by = $3
                """,
                json.dumps(result),
                job_id,
                self.worker_id,
            )
            return command.endswith(" 1")

    async def fail_or_retry(
        self,
        job_id: str,
        attempt: int,
        max_attempts: int,
        error_code: str,
        error_message: str,
        retry_after_seconds: int,
    ) -> bool:
        terminal = attempt >= max_attempts
        async with self.pool.acquire() as conn:
            command = await conn.execute(
                """
                update execution_jobs
                set status = case when $4 then 'failed' else 'queued' end,
                    available_at = case when $4 then available_at else now() + ($6 * interval '1 second') end,
                    locked_at = null,
                    locked_by = null,
                    error_code = $5,
                    error_message = $7,
                    completed_at = case when $4 then now() else completed_at end,
                    updated_at = now()
                where id = $1 and status = 'running' and locked_by = $2
                  and attempt = $3
                """,
                job_id,
                self.worker_id,
                attempt,
                terminal,
                error_code,
                retry_after_seconds,
                error_message,
            )
            return command.endswith(" 1")
