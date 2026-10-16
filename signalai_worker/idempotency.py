import json
from typing import Any


class IdempotencyStore:
    """Redis-backed idempotency state shared by all worker instances."""

    def __init__(self, redis: Any, ttl_seconds: int, lock_seconds: int) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds
        self.lock_seconds = lock_seconds

    def _key(self, tenant_id: str, key: str) -> str:
        return f"signalai:idempotency:{tenant_id}:{key}"

    async def claim(self, tenant_id: str, key: str) -> bool:
        return bool(
            await self.redis.set(
                self._key(tenant_id, key),
                json.dumps({"status": "processing"}),
                ex=self.lock_seconds,
                nx=True,
            )
        )

    async def get(self, tenant_id: str, key: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._key(tenant_id, key))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    async def complete(self, tenant_id: str, key: str, result: dict[str, Any]) -> None:
        await self.redis.set(
            self._key(tenant_id, key),
            json.dumps({"status": "completed", "result": result}),
            ex=self.ttl_seconds,
        )

    async def fail(self, tenant_id: str, key: str, error_code: str, message: str) -> None:
        await self.redis.set(
            self._key(tenant_id, key),
            json.dumps({"status": "failed", "error_code": error_code, "error_message": message}),
            ex=self.ttl_seconds,
        )
