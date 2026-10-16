from datetime import datetime, timezone

import pytest

from signalai_worker.runtime import WorkerRuntime


class FakeRepository:
    def __init__(self) -> None:
        self.completed: list[tuple[str, dict]] = []
        self.failures: list[tuple] = []

    async def heartbeat(self, _job_id: str) -> bool:
        return True

    async def complete(self, job_id: str, result: dict) -> bool:
        self.completed.append((job_id, result))
        return True

    async def fail_or_retry(self, *args) -> bool:
        self.failures.append(args)
        return True


@pytest.mark.asyncio
async def test_runtime_executes_registered_handler():
    runtime = WorkerRuntime()
    repository = FakeRepository()
    row = {
        "id": "job-1",
        "tenant_id": "tenant-1",
        "type": "system.echo",
        "payload": {"hello": "world"},
        "attempt": 1,
        "max_attempts": 3,
        "idempotency_key": "echo-1",
        "correlation_id": "corr-1",
        "created_at": datetime.now(timezone.utc),
    }

    await runtime._execute(repository, row)

    assert repository.failures == []
    assert repository.completed == [("job-1", {"accepted_type": "system.echo", "payload": {"hello": "world"}})]
