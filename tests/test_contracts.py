from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from signalai_worker.contracts import JobEnvelope


def test_job_envelope_accepts_valid_payload() -> None:
    job = JobEnvelope(
        job_id="job_123",
        tenant_id="tenant_123",
        type="company.research",
        payload={"company_id": "company_123"},
        idempotency_key="research:company_123:v1",
        correlation_id="corr_123",
        created_at=datetime.now(UTC),
    )

    assert job.schema_version == 1
    assert job.type == "company.research"


def test_job_envelope_requires_idempotency_key() -> None:
    with pytest.raises(ValidationError):
        JobEnvelope(
            job_id="job_123",
            tenant_id="tenant_123",
            type="company.research",
            payload={},
            idempotency_key="",
            correlation_id="corr_123",
        )
