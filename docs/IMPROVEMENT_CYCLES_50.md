# ForgeLab — 50-Cycle Improvement Review

**Review date:** 2026-11-03  
**Baseline:** ForgeLab 0.3.0; local source commit `a8abaf90892bec57e265a5dfb722f6e688d8cf74`  
**Purpose:** Preserve the 50-cycle improvement exploration and decisions in this GitHub repository.

This is a planning artifact. The improvements below are proposals and prioritized design work; they are not claims that the future capabilities have already shipped. Each cycle follows the requested loop: identify a gap, plan an implementation, expand the improvement surface, and review how it fits the accumulated plans.

## Cycles

### Execution durability
1. **Stage-level checkpoints** — persist each pipeline stage and its outputs so a recovered run can resume from the last valid stage.
2. **Atomic phase output commits** — publish stage artifacts atomically; never expose partial results as completed output.
3. **Checkpoint invalidation and fingerprints** — hash inputs, configuration, prompts, and dependencies; invalidate downstream stages when these change.
4. **Safe replay and side-effect journal** — record side effects and idempotency keys so retries do not duplicate external actions.
5. **Checkpoint schema evolution** — version checkpoint payloads and add tested migrations between versions.
6. **Hard per-run budgets** — enforce maximum wall time, tokens, provider spend, retries, and tool calls with preflight reservations.
7. **Provider telemetry and usage accounting** — record request IDs, latency, token usage, cost estimates, retries, and errors per stage.
8. **Deadline propagation and cancellation** — propagate deadlines and cooperative cancellation through every stage and provider call.
9. **Fenced worker leases** — use lease generations/fencing tokens so stale workers cannot commit results after lease loss.
10. **Job/run state reconciliation** — define invariants and repair routines for interrupted or inconsistent job and run states.
11. **Idempotent job submission** — support client-supplied idempotency keys and deduplicate repeated submissions.
12. **Retry taxonomy and dead-letter handling** — distinguish transient, permanent, budget, policy, and malformed-output failures.
13. **Queue scheduling and fairness** — prioritize work while preventing starvation across users, projects, and job classes.
14. **Backpressure and admission control** — cap queued work and worker concurrency before resource exhaustion.
15. **Database migration discipline** — add ordered migrations, compatibility checks, rollback strategy, and migration tests.
16. **SQLite health, backup, and restore** — test integrity checks, online backups, retention, and disaster recovery.
17. **Artifact store integrity and immutability** — content-address artifacts, verify checksums, and prevent silent overwrite.
18. **Append-only audit history** — retain actor, decision, inputs, outputs, and timestamps for important state transitions.

### Model and security controls
19. **Versioned structured output contracts** — validate provider responses against versioned schemas with bounded repair attempts.
20. **Prompt/template registry** — version prompts, model settings, and evaluation fixtures; record the exact template used by each run.
21. **Prompt injection boundary controls** — treat retrieved content as untrusted data and isolate instructions from evidence.
22. **Privacy and secret redaction** — redact credentials and sensitive values in logs, traces, artifacts, and model context.
23. **Provider resilience and rate limits** — implement bounded retries, concurrency limits, circuit breakers, and per-provider quotas.

### Research integrity
24. **Full-page source retrieval** — retrieve and preserve the relevant source text, not only search snippets.
25. **SSRF-safe fetch and network egress** — block private, loopback, link-local, and metadata addresses; restrict redirects and protocols.
26. **Safe content parsing and snapshotting** — sanitize and snapshot parsed source material with provenance and content hashes.
27. **Source quality classification** — score primary/secondary status, authority, recency, and methodological quality.
28. **Syndication and independence detection** — identify copied or syndicated sources so they are not counted as independent corroboration.
29. **Claim-to-evidence entailment** — verify that cited passages actually support each generated claim.
30. **Evidence freshness and revalidation** — mark stale claims and schedule or request source rechecks.
31. **Research coverage and stopping criteria** — define coverage targets, contradiction handling, and transparent stop reasons.

### Evaluation and experimentation
32. **Behavioral evaluation oracles** — test observable behavior against explicit acceptance criteria rather than vague quality scores.
33. **Independent evaluator calibration** — calibrate evaluator consistency against human-reviewed examples and known failure cases.
34. **Statistical experiment methodology** — use repeated trials, confidence intervals, effect sizes, and controls where appropriate.
35. **Experiment environment fingerprinting** — record code, dependencies, hardware, data, seeds, and configuration for reproducibility.
36. **Benchmark suite and regression gates** — maintain stable benchmark datasets and prevent quality/performance regressions from shipping.

### Software engineering autonomy
37. **Isolated Git workspaces** — create per-task worktrees/branches with explicit base commits and cleanup policies.
38. **Diff-first patch application** — review proposed diffs before applying them; reject out-of-scope or unexpectedly broad changes.
39. **Static analysis and dependency security** — run formatters, type checks, lint, vulnerability scans, and license checks.
40. **SBOM and build provenance** — generate software bills of materials and bind artifacts to source commits and build metadata.
41. **Hardened code execution sandbox** — isolate execution with resource limits, no network by default, read-only mounts, and unprivileged identities.
42. **Execution telemetry and result capture** — capture command, exit code, logs, resource usage, and artifact hashes for every run.

### Platform governance and scale
43. **Capability-based tool authorization** — scope permissions to task, project, tool, and operation; deny by default.
44. **Plugin contracts and isolation** — require typed schemas, bounded permissions, timeouts, and explicit approval for side-effecting plugins.
45. **MCP interoperability** — expose and consume tool capabilities through documented MCP contracts with allowlists and audit records.
46. **Model routing and provider failover** — route by task capability, quality, latency, privacy, and budget; support safe failover.
47. **Authenticated operator dashboard** — add authentication, CSRF-safe mutations, secure sessions, and operator audit trails.
48. **Workspace isolation and RBAC** — separate projects and users with least-privilege roles and explicit artifact access controls.
49. **Scalable backend and operational readiness** — define PostgreSQL/object-storage deployment, observability, backups, load tests, and SLOs.
50. **Release governance and autonomy envelope** — define which actions can be automatic, which require approval, and what evidence is required for release.

## Consolidated review decisions

1. Prioritize reliability and controls before increasing agent autonomy.
2. Deliver stage checkpointing, cost budgets, state invariants, migrations, and auditability in 0.4.0.
3. Deliver full-source evidence verification and reproducible experiments before treating research outputs as decision-grade.
4. Introduce code-writing autonomy only with isolated workspaces, diff review, sandboxing, and security checks.
5. Defer multi-host scale until authentication, workspace isolation, durable storage, and operational controls are designed.
6. Keep external publishing, deployment, spending, and destructive actions behind explicit authorization.
7. Treat each roadmap milestone as incomplete until its acceptance tests and release gates pass.

## Scope and validation note

The previous 0.3.0 implementation was validated with 38 automated tests and three offline benchmark scenarios. These 50 cycles extend the implementation plan; they do not mean the proposed 0.4.0–1.0.0 capabilities are already implemented. Stage-level checkpoint resumption remains a 0.4.0 target.
