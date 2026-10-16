# Worker Job Contracts

## Contract goals

Job contracts are the stable boundary between `signalai-server` and `signalai-worker`. Contracts must be language-neutral and versioned so Python execution can evolve independently of the TypeScript product backend.

## Envelope

Every job uses the following logical envelope:

```json
{
  "jobId": "job_123",
  "type": "company.research",
  "version": 1,
  "workspaceId": "ws_123",
  "requestedBy": "usr_123",
  "correlationId": "corr_123",
  "idempotencyKey": "research:company_123:v1",
  "createdAt": "2026-10-16T10:00:00Z",
  "attempt": 1,
  "payload": {}
}
```

`type` identifies the operation. `version` identifies the payload contract and must not be inferred from application deployment version.

## Rules

1. Unknown versions fail closed.
2. Required fields are validated before execution.
3. `workspaceId` is mandatory for product work.
4. `idempotencyKey` is mandatory for side-effecting jobs.
5. Handlers must tolerate duplicate delivery.
6. Payloads must contain identifiers rather than copied authoritative domain state whenever practical.
7. Contracts must be backward-compatible within a supported version window.
8. Breaking changes require a new version.

## Initial job families

### `journey.execution.requested`

Starts or resumes execution of a published journey version.

Payload should identify the journey, immutable published version, execution/recipient context and requested action. The worker must never execute an arbitrary mutable draft.

### `research.company`

Runs company research/enrichment. The payload identifies the target company and requested research profile. Results are returned as structured facts with provenance rather than opaque model text.

### `lead.enrichment`

Enriches a lead using approved connector/research capabilities. The job must preserve the source of each enriched field and must not overwrite user-entered authoritative values without an explicit policy.

### `bulk.operation`

Processes a bounded batch of records. The contract must include a stable batch identifier and item-level result semantics so partial success is recoverable.

## Result envelope

```json
{
  "jobId": "job_123",
  "status": "SUCCEEDED",
  "attempt": 1,
  "startedAt": "2026-10-16T10:00:02Z",
  "completedAt": "2026-10-16T10:00:09Z",
  "result": {},
  "error": null
}
```

Errors use:

```json
{
  "code": "PROVIDER_RATE_LIMITED",
  "message": "Provider temporarily rate limited the request",
  "retryable": true,
  "requestId": "req_123"
}
```

Do not return stack traces or secrets in external result payloads.

## Versioning

Contract definitions should live in a machine-readable schema directory as implementation progresses. Recommended layout:

```text
contracts/
  jobs/
    company-research.v1.json
    lead-enrichment.v1.json
    journey-execution.v1.json
  results/
    job-result.v1.json
```

Generate/validate Pydantic models from the contract source where practical; do not let implementation-only Python types silently become the cross-service contract.

## Cancellation

Cancellation is cooperative. A cancelled job must stop starting new external work, finish safe cleanup, and publish a terminal `CANCELLED` result. Long-running handlers should periodically check cancellation state.

## Progress

Long-running jobs may emit progress events using a stable shape:

```json
{
  "jobId": "job_123",
  "status": "RUNNING",
  "completed": 420,
  "total": 1000,
  "message": "Enriched 420 records"
}
```

Progress is informational and must never be treated as authoritative product state.
