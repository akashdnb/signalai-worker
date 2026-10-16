# SignalAI Worker

Python execution service for SignalAI background workloads.

## Boundary

`signalai-server` remains the source of truth for product state, authorization, domain rules and persistence. The worker executes asynchronous jobs and must not directly mutate the product database.

Initial responsibilities:

- long-running jobs
- bulk processing
- scheduled execution
- retries
- connector-heavy work
- research and enrichment workloads

## Stack

- Python 3.12+
- FastAPI for health/readiness and operational HTTP endpoints
- ARQ + Redis for asynchronous job execution
- Pydantic for versioned job contracts
- pytest for tests

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn signalai_worker.app:app --reload
```

Run the worker process separately:

```bash
arq signalai_worker.worker.WorkerSettings
```

Redis is required for job execution. The default development URL is `redis://localhost:6379/0`.

## Contract rule

Workers receive explicit, versioned job envelopes. Domain decisions belong to `signalai-server`; Python services consume contracts rather than importing server internals.
