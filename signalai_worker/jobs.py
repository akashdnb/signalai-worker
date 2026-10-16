from typing import Any

from arq import Retry

from signalai_worker.config import settings
from signalai_worker.contracts import JobEnvelope, JobResult
from signalai_worker.idempotency import IdempotencyStore


async def execute_job(ctx: dict[str, Any], raw_job: dict[str, Any]) -> dict[str, Any]:
    """Validate and execute a job envelope.

    The first implementation intentionally has no domain handlers. The execution
    boundary is production-safe: duplicate deliveries are idempotent and transient
    failures are retried by ARQ. Domain handlers will be registered behind this API.
    """
    job = JobEnvelope.model_validate(raw_job)
    attempt = int(ctx.get("job_try", job.attempt))
    redis = ctx["redis"]
    store = IdempotencyStore(
        redis,
        ttl_seconds=settings.idempotency_ttl_seconds,
        lock_seconds=settings.execution_lock_seconds,
    )

    existing = await store.get(job.tenant_id, job.idempotency_key)
    if existing and existing.get("status") == "completed":
        return JobResult(
            job_id=job.job_id,
            status="completed",
            result=existing.get("result", {}),
        ).model_dump(mode="json")
    if existing and existing.get("status") == "failed":
        return JobResult(
            job_id=job.job_id,
            status="failed",
            error_code=existing.get("error_code"),
            error_message=existing.get("error_message"),
        ).model_dump(mode="json")

    claimed = await store.claim(job.tenant_id, job.idempotency_key)
    if not claimed:
        return JobResult(
            job_id=job.job_id,
            status="running",
            result={"status": "in_progress"},
        ).model_dump(mode="json")

    try:
        result = {
            "accepted_type": job.type,
            "idempotency_key": job.idempotency_key,
            "attempt": attempt,
        }
        await store.complete(job.tenant_id, job.idempotency_key, result)
        return JobResult(job_id=job.job_id, status="completed", result=result).model_dump(mode="json")
    except Exception as exc:
        if attempt < settings.max_attempts:
            raise Retry(defer=settings.retry_backoff_seconds * attempt) from exc
        await store.fail(job.tenant_id, job.idempotency_key, "JOB_EXECUTION_FAILED", str(exc))
        return JobResult(
            job_id=job.job_id,
            status="failed",
            error_code="JOB_EXECUTION_FAILED",
            error_message=str(exc),
        ).model_dump(mode="json")
