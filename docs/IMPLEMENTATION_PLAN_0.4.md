# ForgeLab 0.4.0 — Implementation Plan

**Milestone theme:** resumable, budgeted, observable execution.  
**Current stable baseline:** 0.3.0. **Current development snapshot:** 0.4.0.dev1.  
**Planning basis:** 2,000 structured review cycles (50 subsystem areas × 40 engineering lenses), plus the prior 50-cycle review.

## 0.4.0.dev1 progress

An initial FL-401 implementation slice is included in the remote source snapshot:
- Additive SQLite `run_stage_attempts` table and `PRAGMA user_version=1`.
- Immutable stage attempt history; completed outputs include SHA-256 digests.
- Fingerprinted output reuse for plan, research, synthesis, design, architecture review, development, evaluation, and independent review.
- Worker retries resume the existing run and skip matching completed stages.
- CLI `forgelab stages RUN_ID` and read-only `/api/runs/{run_id}/stages` inspection.

The development preview has passing regression tests for checkpoint reuse, changed inputs, immutable outputs, additive upgrade, and worker retry resume. This is not a complete 0.4.0 release.

## Remaining work packages

1. **FL-401 completion:** explicit transition graph, payload schema IDs/migrations, complete input/provider/prompt fingerprints, dependency DAG and invalidation reasons.
2. **FL-402:** atomic artifact staging/publication and orphan reconciliation.
3. **FL-403:** downstream invalidation by dependency graph and content hashes.
4. **FL-404:** hard wall-clock, request, token, byte, and estimated spend budgets with preflight reservations.
5. **FL-405:** typed provider error taxonomy, request telemetry, Retry-After, backoff, and circuit breakers.
6. **FL-406:** cancellation/deadline propagation through every stage and provider call.
7. **FL-407:** monotonic lease fencing and job/run invariant reconciliation.
8. **FL-408:** ordered/checksummed migrations, backup, integrity check, and restore drills.
9. **FL-409:** append-only, redacted audit records and verifiable exports.
10. **FL-410:** versioned structured output contracts and bounded repair.

## Release gates

- Process-kill/restart tests prove completed stages are not repeated.
- Stage outputs and artifact manifests pass checksum verification.
- No stale worker can publish after losing its lease.
- Hard budget limits hold under concurrent reservations.
- Migrations and restore drills preserve legacy records.
- All existing and new tests pass; offline benchmarks remain green.
- Security review confirms no default network access or unapproved external side effects.

## Known implementation boundary

The current preview stores serialized stage outputs in SQLite and adds the checkpoint table additively. Filesystem/DB atomic artifact publication, full migration registry, budgets, provider telemetry, lease fencing, and audit hash chains remain incomplete. Do not describe them as shipped.
