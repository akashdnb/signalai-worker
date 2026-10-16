from typing import Any

from signalai_worker.contracts import JobEnvelope, JobResult
from signalai_worker.idempotency import InMemoryIdempotencyStore


idempotency_store = InMemoryIdempotencyStore()


async def execute_job(_ctx: dict[str, Any], raw_job: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a job after contract validation and idempotency lookup."""
    job = JobEnvelope.model_validate(raw_job)

    existing = await idempotency_store.get(job.idempotency_key)
    if existing is not None:
        return existing

    # Business-specific handlers will be added behind this boundary. The worker
    # intentionally does not access SignalAI persistence directly.
    result = JobResult(
        job_id=job.job_id,
        status="completed",
        result={"accepted_type": job.type, "idempotency_key": job.idempotency_key},
    ).model_dump(mode="json")
    await idempotency_store.put(job.idempotency_key, result)
    return result
