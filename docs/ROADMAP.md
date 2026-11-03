# ForgeLab Development Roadmap

**Current release:** 0.3.0  
**Next release:** 0.4.0  
**Planning basis:** 50-cycle improvement review (see `IMPROVEMENT_CYCLES_50.md`).

| Release | Focus | Primary outcomes |
|---|---|---|
| 0.4.0 | Recoverable execution | Stage checkpoints, safe replay, strict budgets, provider telemetry, cancellation, worker fencing, migrations, audit log, structured contracts |
| 0.5.0 | Research integrity | Full-page source capture, safe fetching, source-quality scoring, syndication detection, claim/evidence entailment, freshness, research coverage |
| 0.6.0 | Software engineering | Isolated Git worktrees, patch review, test/lint/security pipeline, sandbox hardening, SBOM and build provenance, draft PR generation |
| 0.7.0 | Agent and tool orchestration | Model routing, provider failover, specialist review, capability-based authorization, plugin contracts, MCP interop |
| 0.8.0 | Team platform | Authenticated operator dashboard, workspace isolation, RBAC, PostgreSQL option, durable artifact storage, team audit |
| 0.9.0 | Production operations | Load and fault testing, monitoring, SLOs, backup/restore automation, deployment profiles, incident runbooks |
| 1.0.0 | Governed autonomous R&D | Reproducible end-to-end research and engineering workflows, release governance, controlled autonomy, documented security posture |

## Sequencing principles

1. Reliability and resource controls precede more autonomous agents.
2. Evidence verification precedes decision-grade research claims.
3. Isolated workspaces and sandboxing precede code-writing autonomy.
4. Authentication and workspace isolation precede multi-user operation.
5. Operational readiness precedes multi-host production deployment.
6. External publishing, deployment, destructive operations, and spending remain approval-gated unless a narrowly scoped policy explicitly authorizes them.

## Release discipline

A roadmap item is not complete because a module or CLI command exists. Each release requires acceptance criteria, tests, threat review, migration/restore evidence where relevant, updated docs, and a versioned changelog. Stage resumption, for example, must pass process-kill and restart tests before it is described as supported.

## Deferred architecture

- Multi-host distributed scheduling until a transactional backend and fencing design are in place.
- Unrestricted network egress or arbitrary shell execution.
- Automatic production deployment.
- Unbounded agent loops or uncontrolled model/provider spending.
- Treating LLM evaluators as sole arbiters for high-impact decisions.
