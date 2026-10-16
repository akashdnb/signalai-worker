import pytest

from signalai_worker.jobs import execute_job


@pytest.mark.asyncio
async def test_duplicate_job_returns_same_result() -> None:
    payload = {
        "job_id": "job_123",
        "tenant_id": "tenant_123",
        "type": "company.research",
        "payload": {"company_id": "company_123"},
        "idempotency_key": "research:company_123:v1",
        "correlation_id": "corr_123",
    }

    first = await execute_job({}, payload)
    second = await execute_job({}, payload)

    assert first == second
    assert first["status"] == "completed"
