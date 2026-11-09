# ForgeLab — Remote Development Repository

ForgeLab is a local-first R&D workbench evolving toward a governed autonomous research and software-engineering platform.

## Current state

- Stable baseline: **0.3.0**
- Active development preview: **0.4.0.dev1**
- Local source commit: `260d7141c22b63a5d2b2f5c5dafd9d34c3afb365`
- Development tag: `v0.4.0-dev1`
- Review exercise: **2,000 structured improvement cycles**
- 0.4.0 preview validation: **47 tests passed; 3/3 offline benchmarks passed**

## Remote documents

- [2,000-cycle improvement review](docs/IMPROVEMENT_REVIEW_2000.md)
- [50-domain cycle register and decisions](docs/IMPROVEMENT_CYCLES_50.md)
- [0.4.0 implementation plan](docs/IMPLEMENTATION_PLAN_0.4.md)
- [0.4.0.dev1 implementation snapshot](docs/IMPLEMENTATION_0.4.0_DEV1.md)
- [Development roadmap](docs/ROADMAP.md)
- [Forex Monitor 20-cycle improvement plan](docs/FOREX_IMPROVEMENT_PLAN_20_CYCLES.md)
- [Forex Monitor zero-subscription market-data research](docs/FOREX_FREE_DATA_STACK.md)
- [Artifact and source handoff notes](artifacts/README.md)

## What is implemented in 0.4.0.dev1

SQLite-backed stage-attempt checkpoints, SHA-256 output integrity, input fingerprints, reuse of completed stage outputs on retries, a stage-inspection CLI command, and a read-only stage API endpoint.

**Important:** This is a development preview. It is not yet a stable or production-ready 0.4.0. Budgets, stage dependency invalidation, atomic external artifact publishing, provider telemetry, cancellation/deadline propagation, worker fencing, a complete migration/restore framework, append-only audit, and strict output schemas remain release gates.

## Improvement-loop methodology

The 2,000-cycle exercise is generated as a reproducible matrix of **50 improvement domains × 40 engineering review lenses**. Each record carries the requested sequence: find a gap, plan an implementation, expand the improvement surface, review existing plans, and update the accumulated plan. It is not a claim of 2,000 separate LLM conversations. The generator and validator are included in the source handoff archive.

## Source snapshot

The complete source code remains preserved in the local Git bundle and source archive from the development session. A binary source archive has **not yet been committed to this GitHub repository**. The handoff instructions in `artifacts/README.md` explain the remaining publication step. The planning and implementation status documents in this repository are saved remotely on `main`.

## Development policy

Changes should be made against the tested source revision, committed in small increments, and accompanied by focused tests. External publishing, deployment, destructive operations, arbitrary execution, and spending remain subject to explicit authorization and appropriate safeguards.
