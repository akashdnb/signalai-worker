from datetime import datetime, timezone

import pytest

from signalai_worker.contracts import JobEnvelope
from signalai_worker.handlers import HANDLERS, echo_handler


@pytest.mark.asyncio
async def test_echo_handler_preserves_payload():
    job = JobEnvelope(
        job_id="job-1",
        tenant_id="tenant-1",
        type="system.echo",
        payload={"value": 42},
        idempotency_key="echo-1",
        correlation_id="corr-1",
        created_at=datetime.now(timezone.utc),
    )
    assert await echo_handler(job) == {"accepted_type": "system.echo", "payload": {"value": 42}}
    assert HANDLERS["system.echo"] is echo_handler
