# Worker Operations

## Processes

Run the FastAPI operational endpoint separately from ARQ worker processes.

```bash
uvicorn signalai_worker.app:app
arq signalai_worker.worker.WorkerSettings
```

## Required configuration

At minimum the runtime needs:

- Redis connection URL
- server API base URL
- service authentication credentials
- environment name
- telemetry configuration
- job retry/concurrency limits

Credentials must come from the deployment secret store, never from source control.

## Health

Expose:

- liveness: process is alive
- readiness: Redis and required dependencies are reachable

Readiness must fail when the worker cannot safely consume jobs.

## Queue safety

Monitor:

- queue depth
- oldest queued job age
- active jobs
- failed jobs
- retry rate
- DLQ depth
- execution latency
- Redis latency/errors

Alert on sustained queue growth rather than isolated spikes.

## Backpressure

Workers must apply bounded concurrency. A provider rate limit must reduce pressure rather than trigger unbounded retries.

For bulk workloads, prefer bounded batches and checkpoint progress. Never load an unbounded dataset into process memory.

## Deployment

A normal deployment sequence is:

1. deploy compatible contract version
2. deploy worker code that understands current and previous supported versions
3. migrate producers if required
4. monitor queue and error metrics
5. remove obsolete contract versions only after all queued jobs are drained

## Incident handling

For a failing job type:

1. identify the job type/version and affected workspace(s)
2. inspect correlation/request IDs
3. determine whether failures are provider, contract, authorization, infrastructure or code failures
4. stop or reduce the affected consumer if retry storms are possible
5. preserve failed jobs for diagnosis
6. replay only after the underlying issue is fixed

Never mass-replay a DLQ without checking idempotency and provider side effects.

## Security

- redact tokens and secrets
- avoid logging full message bodies or personal data
- enforce workspace isolation
- use least-privilege service credentials
- validate all server-provided identifiers
- do not expose internal job endpoints publicly without service authentication

## Cost controls

Worker cost is controlled through bounded concurrency, batching, queue backpressure and explicit model/provider budgets. Expensive research or AI jobs should expose usage metadata so the server can account for them.
