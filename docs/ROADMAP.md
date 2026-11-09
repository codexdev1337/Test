# ForgeLab Development Roadmap

**Last stable release:** 0.3.0  
**Current development snapshot:** 0.4.0.dev1  
**Planning basis:** 2,000 structured review cycles across 50 subsystem areas and 40 engineering lenses.

| Release | Focus | Primary outcomes |
|---|---|---|
| 0.4.0 | Recoverable execution | Initial stage checkpoints, fingerprinted reuse, same-run worker retries, stage inspection; hard budgets, atomic file publication, fencing, migration registry, audit log and structured contracts remain in progress |
| 0.5.0 | Research integrity | Full-page source capture, safe fetching, source-quality scoring, syndication detection, claim/evidence entailment, freshness, research coverage |
| 0.6.0 | Software engineering | Isolated Git worktrees, patch review, test/lint/security pipeline, sandbox hardening, SBOM and build provenance, draft PR generation |
| 0.7.0 | Agent and tool orchestration | Model routing, provider failover, specialist review, capability-based authorization, plugin contracts |
| 0.8.0 | Team platform | Authenticated operator dashboard, workspace isolation, RBAC, PostgreSQL option, durable artifact storage, team audit |
| 0.9.0 | Production operations | Load and fault testing, monitoring, SLOs, backup/restore automation, deployment profiles, incident runbooks |
| 1.0.0 | Governed autonomous R&D | Reproducible end-to-end research and engineering workflows, release governance, controlled autonomy, documented security posture |

## Current implementation snapshot

The 0.4.0.dev1 preview implements an initial subset of FL-401: versioned stage-attempt rows, output digests, input fingerprints, cache reuse on retry, worker reuse of the run ID, and stage inspection through CLI/API. It has 47 passing automated tests and the three offline benchmark cases pass in the current environment. The preview does not satisfy all 0.4.0 release gates.


## Forex Monitor improvement track (proposed; separate workstream)

The Forex Monitor roadmap is maintained as a parallel track to the ForgeLab core releases above. It does not change the ForgeLab release numbering and does not mean any trading feature is already implemented.

Detailed specification: [20-Cycle Improvement Research and Implementation Plan](FOREX_IMPROVEMENT_PLAN_20_CYCLES.md).

| Track | Focus | Primary outcomes |
|---|---|---|
| FM-0 | Operational truth | Verify activation, scan execution, email test, heartbeat, schedule lag and provider/API health |
| FM-1 | Research data foundation | Point-in-time data contracts, immutable signal/candidate ledger, replayable snapshots and multi-horizon outcome evaluator |
| FM-2 | Execution realism | Intended-broker bid/ask pricing, spread/slippage/latency model and cost-aware target/stop evaluation |
| FM-3 | Technical and market context | Indicator parity, genuine 1h bars, market regimes, currency-factor model and pair-correlation controls |
| FM-4 | Fundamental and news | Economic calendar, consensus surprises/revisions, licensed headline ingestion, currency-aware sentiment and event-risk veto |
| FM-5 | Decision quality | Calibrated outcome probabilities, entry/expiry lifecycle and portfolio exposure limits |
| FM-6 | Validation and operations | Walk-forward/holdout/PBO/DSR research, forward paper gate, quota guard, durable storage, alert outbox, monitoring and rollback |

### Forex workstream sequencing and release gates

1. Do not modify production signal thresholds before FM-1 can record all candidates and evaluate subsequent outcomes.
2. Do not make ACTIONABLE alerts dependent on a new feed until the provider has passed provenance, freshness, latency, historical availability, cost and licensing checks.
3. Do not treat candle mid/close as an executable broker quote; FM-2 is required for net-performance claims.
4. News sentiment and macro surprises must be point-in-time replayable, and initially operate in shadow/reporting mode.
5. Calibrated probabilities require held-out outcomes and must be monitored by pair, regime and session.
6. No signal expansion or strategy promotion without realistic costs, chronological out-of-sample results and forward paper evidence.
7. The scanner remains analysis-only and does not place or manage broker orders.


## Sequencing principles

1. Reliability and resource controls precede more autonomous agents.
2. Evidence verification precedes decision-grade research claims.
3. Isolated workspaces and sandboxing precede code-writing autonomy.
4. Authentication and workspace isolation precede multi-user operation.
5. Operational readiness precedes multi-host production deployment.
6. External publishing, deployment, destructive operations, and spending remain approval-gated unless a narrowly scoped policy explicitly authorizes them.

## Deferred architecture

- Multi-host distributed scheduling until a transactional backend and fencing design are in place.
- Unrestricted network egress or arbitrary shell execution.
- Automatic production deployment.
- Unbounded agent loops or uncontrolled model/provider spending.
- Treating LLM evaluators as sole arbiters for high-impact decisions.
