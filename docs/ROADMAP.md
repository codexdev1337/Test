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
