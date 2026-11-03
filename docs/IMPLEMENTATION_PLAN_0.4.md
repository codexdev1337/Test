# ForgeLab 0.4.0 — Implementation Plan

**Goal:** Make long-running R&D jobs recoverable, bounded, auditable, and safe before expanding autonomy.

## Outcome and non-goals

0.4.0 should allow a job to survive worker interruption and resume from the last valid stage, while enforcing hard budgets and ensuring stale or duplicate workers cannot publish results. It is not a multi-host release, does not automatically deploy software, and does not enable unrestricted tool execution.

## Work packages

### FL-401 — Stage state machine and checkpoint schema
Define explicit stage states (pending, running, completed, failed, skipped, cancelled), stage attempt IDs, schema versions, timestamps, input fingerprints, and output artifact references. Add migration tests and invalid-transition tests.

**Acceptance:** a run has deterministic stage order; every transition is validated; checkpoint state can be loaded after process restart; unknown schema versions fail closed.

### FL-402 — Atomic artifact publication
Write stage output to a temporary content-addressed location, verify its checksum, then atomically publish its manifest/reference. Keep completed artifacts immutable.

**Acceptance:** crash injection before publication leaves no completed artifact; checksum mismatch is detected; repeated publication is idempotent.

### FL-403 — Input fingerprints and dependency invalidation
Fingerprint source inputs, prompts, model/provider settings, code version, and upstream artifacts. Invalidate only affected downstream stages when an input changes.

**Acceptance:** identical inputs reuse valid completed stages; a changed upstream input invalidates dependent stages and preserves unrelated artifacts.

### FL-404 — Budget ledger and preflight reservations
Enforce run-level limits for wall-clock time, tokens, estimated spend, model calls, tool calls, retries, and generated artifact size. Reserve budget before provider calls and reconcile with actual usage afterward.

**Acceptance:** no call starts when its reservation would exceed a hard limit; concurrent calls cannot overspend through races; budget exhaustion produces a clear terminal reason.

### FL-405 — Provider telemetry and error taxonomy
Store provider/model, request ID, latency, usage, cost estimate, retry count, and classified failure reason. Add rate-limit-aware backoff and circuit breakers.

**Acceptance:** each provider attempt is traceable; transient failures retry within budget; permanent and policy failures do not retry endlessly.

### FL-406 — Cooperative cancellation and deadlines
Propagate a cancellation token and deadline through orchestration, research, synthesis, evaluation, and provider adapters. Define safe stage boundaries and cleanup behavior.

**Acceptance:** cancellation prevents new work, records a terminal state, keeps completed outputs, cleans temporary artifacts, and does not falsely mark unfinished work complete.

### FL-407 — Lease fencing and job invariants
Add monotonically increasing lease generations and require the active fencing token on every state/artifact commit. Define job/run invariants and reconciliation routines.

**Acceptance:** a stale worker cannot commit after lease expiry/reassignment; duplicate workers cannot publish conflicting outputs; reconciliation is idempotent.

### FL-408 — Migrations, backup, and restore
Introduce ordered database migrations with checksums and a recorded schema version. Add verified backups, restore drills, and integrity checks.

**Acceptance:** migration from every supported prior schema passes; migration interruption is recoverable; a backup can be restored and pass integrity checks.

### FL-409 — Append-only execution audit
Record job submission, claim, lease renewal, stage transition, budget reservation/reconciliation, cancellation, approval, artifact publication, and failure. Include actor and correlation IDs; redact secrets.

**Acceptance:** audit entries are append-only, correlated to run/stage, useful for incident reconstruction, and contain no credentials or raw secret values.

### FL-410 — Structured schemas and contract tests
Version JSON contracts for plans, evidence, experiments, and stage outputs. Validate model outputs, reject malformed data, and allow only bounded repair attempts.

**Acceptance:** invalid output cannot advance a stage; schema version is recorded; prompt/provider contract fixtures pass across supported adapters.

## Implementation order and dependencies

1. FL-401 establishes the stage model.
2. FL-402 and FL-403 build on stage identity and artifact references.
3. FL-404 and FL-405 add budget and provider observability.
4. FL-406 and FL-407 harden cancellation and concurrency.
5. FL-408 and FL-409 provide operational durability and audit.
6. FL-410 is integrated across each stage and finalized before release.

The implementation should keep SQLite as the supported single-host backend. Multi-host coordination and PostgreSQL are explicitly deferred.

## Test strategy

- Unit tests for state transitions, fingerprints, budget math, retry classification, cancellation, migration, and schemas.
- Fault-injection tests around every stage/artifact commit boundary.
- Concurrency tests with duplicate and stale workers.
- Restart/recovery tests that kill a worker between stages and during publication.
- Property-based tests for state invariants and budget non-negativity.
- Integration tests with deterministic fake providers; no real paid provider calls in CI.
- Regression run of the existing 0.3.0 test suite and offline benchmarks.

## Metrics and release gates

- 100% of successful stages have durable, verifiable checkpoint records.
- 0 stale-worker commits accepted in fencing tests.
- 0 budget overshoots in concurrency tests.
- Cancellation reaches a safe terminal state in all injected fault points.
- Restore drill succeeds from a generated backup.
- Existing 0.3.0 tests and benchmarks remain green.
- Security review confirms no default network access or automatic external side effects.

## Risks and mitigations

- **Checkpoint corruption:** checksums, atomic manifest swaps, and recovery tests.
- **Duplicate side effects:** idempotency keys and explicit side-effect journal.
- **Budget races:** atomic reservations under database transactions.
- **Migration data loss:** backup-before-migrate, forward-only migrations, restore rehearsal.
- **Stale worker writes:** lease generation/fencing checks at commit time.
- **Overly broad autonomy:** deny-by-default tools, approvals, and no deployment in this release.

## Definition of done

All work packages are implemented and reviewed; tests and fault-injection suites pass; migration and restore drills are documented; dashboards/CLI expose job and stage state; costs and limits are visible; release notes explain recovery semantics and limitations; no feature is called resumable until it has passed kill-and-restart acceptance tests.
