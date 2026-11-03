# ForgeLab — Development Snapshot

This repository is the GitHub home for the ForgeLab development plans and project handoff.

## Current state

- Product version: **0.3.0**
- Source repository commit: `a8abaf90892bec57e265a5dfb722f6e688d8cf74`
- Source release tag: `v0.3.0`
- Improvement review: **50 cycles completed**
- Next target: **0.4.0 — recoverable autonomous execution**

## Published in this repository

- `docs/IMPROVEMENT_CYCLES_50.md` — concise register of all 50 improvement cycles and their key design decisions
- `docs/IMPLEMENTATION_PLAN_0.4.md` — ten 0.4.0 work packages, dependencies, acceptance criteria, tests, risks, and release gates
- `docs/ROADMAP.md` — roadmap through 1.0.0

## Source-code status

The complete ForgeLab 0.3.0 source tree and its original Git history are preserved in a separate Git bundle from the development handoff. **That binary bundle has not yet been uploaded into this GitHub repository.** The source commit above identifies the exact snapshot to publish. The files committed here are the 50-cycle planning deliverables, not the complete application source.

To publish the source history after downloading the handoff bundle:

```bash
git clone forgelab-50-cycle-review.bundle forgelab
cd forgelab
git remote add github https://github.com/codexdev1337/Test.git
git push github main:forgelab-source --tags
```

This uses a separate `forgelab-source` branch so the documentation on `main` is not overwritten by the independent source repository history.

## Scope and validation

The 50-cycle review is a planning deliverable; it does not mean all proposed future features have shipped. The 0.3.0 implementation was previously validated with 38 automated tests and three offline benchmark scenarios. Stage-level checkpoint resumption remains planned for 0.4.0.

External publishing, deployment, destructive operations, arbitrary execution, and spending remain subject to explicit authorization and appropriate safeguards.
