from typing import Any

from signalai_worker.contracts import JobEnvelope, JobResult


async def execute_job(_ctx: dict[str, Any], raw_job: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a job after contract validation.

    Business-specific handlers will be added behind this boundary. The worker
    intentionally does not access SignalAI persistence directly.
    """
    job = JobEnvelope.model_validate(raw_job)

    # Idempotency is represented by the contract now. The durable idempotency
    # store will be added with the server/queue integration before production use.
    return JobResult(
        job_id=job.job_id,
        status="completed",
        result={"accepted_type": job.type, "idempotency_key": job.idempotency_key},
    ).model_dump(mode="json")
