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

    claimed = await store.claim(job.tenant_id, job.idempotency_key)
    if not claimed:
        existing = await store.get(job.tenant_id, job.idempotency_key)
        return JobResult(
            job_id=job.job_id,
            status="failed" if existing and existing.get("status") == "failed" else "completed",
            result=existing.get("result", {}) if existing else {"status": "in_progress"},
            error_code=existing.get("error_code") if existing else None,
            error_message=existing.get("error_message") if existing else None,
        ).model_dump(mode="json")

    try:
        result = {
            "accepted_type": job.type,
            "idempotency_key": job.idempotency_key,
            "attempt": job.attempt,
        }
        await store.complete(job.tenant_id, job.idempotency_key, result)
        return JobResult(job_id=job.job_id, status="completed", result=result).model_dump(mode="json")
    except Exception as exc:
        if job.attempt < settings.max_attempts:
            raise Retry(defer=settings.retry_backoff_seconds * job.attempt) from exc
        await store.fail(job.tenant_id, job.idempotency_key, "JOB_EXECUTION_FAILED", str(exc))
        return JobResult(
            job_id=job.job_id,
            status="failed",
            error_code="JOB_EXECUTION_FAILED",
            error_message=str(exc),
        ).model_dump(mode="json")
