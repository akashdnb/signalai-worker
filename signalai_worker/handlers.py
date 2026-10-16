from collections.abc import Awaitable, Callable
from typing import Any

from signalai_worker.contracts import JobEnvelope

JobHandler = Callable[[JobEnvelope], Awaitable[dict[str, Any]]]


async def echo_handler(job: JobEnvelope) -> dict[str, Any]:
    """Small end-to-end contract handler used for smoke testing."""
    return {"accepted_type": job.type, "payload": job.payload}


HANDLERS: dict[str, JobHandler] = {
    "system.echo": echo_handler,
}
