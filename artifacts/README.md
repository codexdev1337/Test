# Source and artifact handoff

The repository currently contains the 2,000-cycle methodology/review docs and the 0.4.0 implementation status. It does not yet contain a committed copy of the complete ForgeLab source bundle.

## Exact source revision

- Source repository commit: `260d7141c22b63a5d2b2f5c5dafd9d34c3afb365`
- Development tag: `v0.4.0-dev1`
- Source archive checksum is recorded in the local handoff package.
- The project has been tested with 47 automated tests and 3/3 offline benchmark scenarios.

## Local source handoff

The source archive and Git bundle were built in the development workspace and are available from the conversation's file links. To publish the exact source, download the source archive, extract it, add this repository as a Git remote, and push the extracted source to a dedicated branch (not `main`, which contains this remote project record):

```bash
tar -xJf forgelab-source-only.tar.gz.xz
cd forgelab
git remote add origin https://github.com/codexdev1337/Test.git
git push origin HEAD:refs/heads/forgelab-source
git push origin --tags
```

For the full preserved Git history, use the separate Git bundle and clone it directly before adding the remote.

## 2,000-cycle register

The 2,000 records are generated deterministically by `tools/improvement_review.py` in the source snapshot. Run the generator with its validation mode to regenerate the detailed Markdown and JSONL register. The remote planning documents summarize the methodology and consolidated priorities.

## Important status distinction

A planning artifact or implementation report is not a substitute for committed source code. This repository's `main` branch currently records the status and engineering plan; the full source archive still needs to be pushed to `forgelab-source` to make the application source directly browsable here.
