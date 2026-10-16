import json

import pytest

from signalai_worker.idempotency import IdempotencyStore


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def get(self, key):
        return self.values.get(key)

    async def eval(self, _script, _keys, key, expected):
        if self.values.get(key) == expected:
            del self.values[key]
            return 1
        return 0


@pytest.mark.asyncio
async def test_claim_is_atomic_and_complete_is_durable():
    redis = FakeRedis()
    store = IdempotencyStore(redis, ttl_seconds=60, lock_seconds=30)

    token = await store.claim("tenant", "request-1")
    assert token
    assert await store.claim("tenant", "request-1") is None

    await store.complete("tenant", "request-1", {"ok": True})
    state = await store.get("tenant", "request-1")
    assert state == {"status": "completed", "result": {"ok": True}}


@pytest.mark.asyncio
async def test_release_only_removes_owned_lock():
    redis = FakeRedis()
    store = IdempotencyStore(redis, ttl_seconds=60, lock_seconds=30)

    token = await store.claim("tenant", "request-2")
    assert token
    key = "signalai:idempotency:tenant:request-2"
    assert json.loads(redis.values[key])["token"] == token

    await store.release("tenant", "request-2", "wrong-token")
    assert key in redis.values

    await store.release("tenant", "request-2", token)
    assert key not in redis.values
