# ForgeLab 0.4.0.dev1 — Implementation Snapshot

**Status:** development preview; not a stable 0.4.0 release  
**Source commit:** `260d7141c22b63a5d2b2f5c5dafd9d34c3afb365`  
**Tag:** `v0.4.0-dev1`  
**Review baseline:** ForgeLab 0.3.0  
**Review matrix:** 2,000 generated cycles = 50 improvement domains × 40 engineering review lenses

## Implemented in this preview

- SQLite-backed immutable stage-attempt records.
- Per-stage input fingerprints and SHA-256 output integrity hashes.
- Reuse of completed stage outputs when a run is retried with unchanged inputs.
- Orchestrator resume support using an existing run ID; the original research question is checked before resume.
- Stage-attempt inspection through the `forgelab stages RUN_ID` CLI command.
- Read-only dashboard API endpoint: `GET /api/runs/{run_id}/stages`.
- Worker retry path retains and resumes the existing run rather than creating an unrelated new run.

The checkpoint layer currently wraps planning, research, synthesis, design, architecture review, development, evaluation, and independent review.

## Validation recorded for this source revision

- 47 automated unit/integration tests passed.
- Three offline benchmark scenarios passed.
- Python bytecode compilation passed.
- A wheel was built and installed into a clean target environment.
- The 2,000-cycle JSONL register validator reported 2,000 records, 50 domains, 40 lenses, five review stages per cycle, and no validation failures.
- The source-only archive is approximately 105 KB compressed (XZ-compressed tar archive).

These are development-environment checks; live model providers, Docker execution, multi-process crash injection, and production deployment are not claimed as verified.

## What is still required for stable 0.4.0

1. A complete checkpoint state machine and schema transition policy.
2. Dependency-aware invalidation when upstream inputs or prompts change.
3. Atomic publication for filesystem/object-store artifacts.
4. Hard token, spend, time, retry, and tool-call budget enforcement.
5. Provider request telemetry and failure classification.
6. Cooperative cancellation and deadline propagation.
7. Worker lease fencing against stale workers.
8. Ordered database migration registry plus backup/restore drills.
9. Append-only audit records and secret redaction.
10. Strict versioned contracts for stage/model outputs.

The release must pass fault-injection, kill-and-restart, duplicate-worker, migration, restore, and budget-concurrency tests before it is described as fully resumable or production-ready.

## Review loop methodology

The 2,000 cycles are not represented as 2,000 independent LLM conversations. They are generated as a reproducible matrix: each of 50 domains is evaluated against 40 review lenses. Each record includes the requested loop stages: find an improvement, create an implementation plan, expand the improvement surface, review existing plans, and update the accumulated plan. The source archive includes the generator and validator so the detailed Markdown and JSONL registers can be regenerated.
