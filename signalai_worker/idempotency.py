from collections.abc import MutableMapping


class InMemoryIdempotencyStore:
    """Development-only idempotency store.

    Production will use a durable Redis-backed implementation so retries and
    duplicate deliveries across worker processes share the same state.
    """

    def __init__(self) -> None:
        self._results: MutableMapping[str, dict] = {}

    async def get(self, key: str) -> dict | None:
        return self._results.get(key)

    async def put(self, key: str, result: dict) -> None:
        self._results[key] = result
