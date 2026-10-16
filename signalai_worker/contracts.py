from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "completed", "failed"]


class JobEnvelope(BaseModel):
    """Language-neutral envelope exchanged between server and workers."""

    schema_version: Literal[1] = 1
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    attempt: int = Field(default=1, ge=1)
    idempotency_key: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    result: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
