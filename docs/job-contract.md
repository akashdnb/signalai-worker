# Execution Job Contract

The server-owned `execution_jobs` row is the durable transport. The worker maps it into this language-neutral envelope:

```json
{
  "schema_version": 1,
  "job_id": "uuid",
  "tenant_id": "uuid",
  "type": "company.research",
  "payload": {},
  "attempt": 1,
  "idempotency_key": "company-research:company-id:v1",
  "correlation_id": "uuid",
  "created_at": "2026-10-16T00:00:00Z"
}
```

## Rules

- `schema_version` is additive/versioned; breaking changes require a new version.
- `tenant_id` is authoritative context supplied by the server.
- `job_id` is globally unique.
- `idempotency_key` is unique per tenant at the queue boundary.
- `correlation_id` must be preserved in logs and downstream calls.
- `attempt` is the durable execution attempt, not a client retry counter.
- Handlers must be safe to retry or must enforce their own downstream idempotency.
- A worker must never infer authorization from `payload`.

## Lifecycle

```text
queued -> running -> completed
                 \-> queued (retry)
                 \-> failed (terminal)
```

A running job has a lease owner. The worker refreshes the lease while the handler is executing. Another worker may recover a job only after the lease expires.
