# SignalAI Worker Service Architecture

## 1. Purpose

`signalai-worker` is the asynchronous execution runtime for SignalAI. It owns work that should not block the product API: long-running jobs, bulk processing, scheduled work, retries, research/enrichment execution, connector-heavy tasks, and other background workloads.

The worker is an execution service, not a second product backend.

### Source of truth

`signalAI` / `signalai-server` remains authoritative for:

- authentication and workspace authorization
- product state and persistence
- CRM and conversation truth
- journey definitions and published versions
- business rules and validation
- billing and usage accounting
- audit records

The worker must not become an alternate database writer or reimplement those rules.

## 2. Runtime

- Python 3.12+
- ARQ for asynchronous jobs
- Redis as the job queue/state transport
- FastAPI for health/readiness and operational HTTP endpoints
- Pydantic for typed versioned contracts
- pytest for unit/contract tests

The HTTP process and ARQ worker process are separate runtime concerns and may scale independently.

## 3. Responsibilities

### In scope

- dequeue and execute versioned jobs
- validate job envelopes
- enforce idempotency
- retries with bounded backoff
- dead-letter handling
- cancellation and timeout handling
- progress reporting for long jobs
- scheduled/background execution
- orchestration of connector and research work
- publishing execution results/events back to the server
- structured logs, metrics and traces

### Out of scope

- direct product-domain ownership
- direct mutation of the SignalAI product database
- authentication policy decisions
- journey authoring/publication rules
- CRM business rules
- provider-specific protocol logic that belongs in `signalai-connectors`
- LLM planning/reasoning that belongs in `signalai-agent`
- MCP tool exposure that belongs in `signalai-mcp`

## 4. Job lifecycle

```text
server/capability
      |
      v
create versioned job envelope
      |
      v
Redis / ARQ queue
      |
      v
validate -> acquire idempotency -> execute
      |
      +---- retryable failure ---> backoff ---> execute
      |
      +---- permanent failure ---> DLQ/result
      |
      v
publish result/event
      |
      v
server records authoritative state
```

A worker execution is successful only when its externally visible side effects and result publication satisfy the job contract.

## 5. Service interaction

The worker communicates with `signalai-server` through explicit APIs and event/job contracts. It may call `signalai-connectors` for provider operations and may invoke approved research/agent capabilities where the contract permits it.

The worker must propagate:

- `requestId`
- `correlationId`
- `jobId`
- `workspaceId`
- `requestedBy`
- `idempotencyKey`

No Python package should import TypeScript server internals.

## 6. Isolation and tenancy

Every job is scoped to a workspace. The worker must validate the workspace context before executing work and must never accept workspace identity from untrusted provider payloads.

A job handler should be structured as:

```text
parse envelope
  -> validate schema/version
  -> authorize execution context
  -> acquire idempotency
  -> load required state through server capabilities/APIs
  -> perform execution
  -> publish result/event
```

## 7. Scaling model

Scale by workload characteristics rather than by product domain.

Examples:

- high-volume message/research jobs: more worker processes
- CPU-heavy enrichment: dedicated worker pool
- slow provider calls: higher I/O concurrency with provider limits
- scheduled jobs: dedicated scheduler/queue configuration

Concurrency must be bounded at both worker and provider levels.

## 8. Failure model

Every handler must classify failures as:

- `retryable`: transient network, provider 5xx, temporary rate limit
- `non_retryable`: invalid contract, authorization failure, unsupported operation
- `terminal`: business outcome that should be recorded without another attempt

Retries must use bounded exponential backoff and a maximum attempt count. Poison jobs must not loop forever.

## 9. Idempotency

Handlers must be safe to execute more than once. Use the contract's `idempotencyKey` and provider-specific idempotency mechanisms where available.

For side effects without native idempotency, persist an execution marker through an authoritative server capability before repeating the side effect.

## 10. Observability

Every job should emit structured lifecycle signals:

- queued
- started
- succeeded
- retried
- failed
- dead-lettered
- cancelled

Metrics should include queue depth, wait time, execution duration, success/failure rate, retry count, DLQ count and provider latency/error rate.

Secrets, access tokens and message contents must not appear in logs by default.

## 11. Testing strategy

- unit tests for handlers and failure classification
- contract tests for job schemas
- idempotency tests
- retry/backoff tests
- tenant-isolation tests
- integration tests against Redis
- provider contract tests through connector interfaces
- end-to-end tests for critical server -> queue -> worker -> result flows

## 12. Future extension rule

Add a new job type when the work has a distinct execution lifecycle. Do not create a new worker service merely because a new product domain appears.

The extraction boundary is justified only when a workload has materially different scaling, security, runtime, deployment, or failure characteristics.
