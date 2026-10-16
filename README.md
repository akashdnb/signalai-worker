# SignalAI Worker

Python execution service for SignalAI background workloads.

## Boundary

`signalai-server` remains the source of truth for product state, authorization, domain rules and persistence. The worker executes asynchronous jobs and must not directly implement product business rules.

The queue is a durable PostgreSQL `execution_jobs` table owned by `signalai-server`. This intentionally reuses the existing SignalAI/Postgres infrastructure rather than introducing another broker solely for the Python worker.

Initial responsibilities:

- long-running jobs
- bulk processing
- scheduled execution
- retries and delayed work
- connector-heavy work
- research and enrichment workloads

## Stack

- Python 3.12+
- FastAPI for health/readiness
- asyncpg for the durable PostgreSQL execution queue
- Pydantic for versioned job contracts
- pytest for tests

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export SIGNALAI_DATABASE_URL='postgres://...'
python -m signalai_worker.worker
```

The health/readiness process can be run separately:

```bash
uvicorn signalai_worker.app:app --host 0.0.0.0 --port 8000
```

## Execution semantics

1. `signalai-server` inserts an `execution_jobs` row.
2. One worker claims it using `FOR UPDATE SKIP LOCKED`.
3. The worker increments the attempt and owns a lease.
4. A heartbeat keeps long-running jobs leased.
5. Successful work is committed as `completed`.
6. Failures are re-queued with bounded exponential-style backoff until `max_attempts` is reached.
7. Expired leases are recovered by another worker.
8. `(tenant_id, idempotency_key)` prevents duplicate job creation.
9. `locked_by` prevents a stale worker from completing a job it no longer owns.

## Contract rule

Workers receive explicit, versioned job envelopes. Domain decisions belong to `signalai-server`; Python services consume contracts rather than importing server internals.
