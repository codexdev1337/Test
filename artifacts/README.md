# Source and artifact handoff

This repository's `main` branch contains the remote project record: the 2,000-cycle review documentation, the 0.4.0 implementation plan, the 0.4.0.dev1 implementation status, and the roadmap.

**The complete application source is not yet committed to this GitHub repository.** It remains preserved in the local development source archive and Git bundle delivered in this conversation.

## Exact source revision

- Source repository commit: `260d7141c22b63a5d2b2f5c5dafd9d34c3afb365`
- Development tag: `v0.4.0-dev1`
- Validation: 47 automated tests passed; 3/3 offline benchmark scenarios passed.
- The source snapshot includes the stage checkpoint implementation and the improvement-review generator.

## Publish the preserved Git history into this repository

Download the **Git bundle** from the conversation files, then run:

```bash
git clone forgelab-0.4.0-dev1.bundle forgelab
cd forgelab
git remote add github https://github.com/codexdev1337/Test.git
git push github main:forgelab-source --tags
```

This puts the full source history on a dedicated `forgelab-source` branch. It does not overwrite the documentation on `main`.

## Restore from the source-only archive

The source-only archive is an XZ-compressed gzip tar archive. Extract it with:

```bash
xz -dc forgelab-source-only.tar.gz.xz | tar -xzf -
```

It does not contain the original Git history; use the Git bundle when history matters.

## Regenerate the 2,000-cycle register

The source archive includes `tools/improvement_review.py`. Run its generation and validation commands to regenerate the detailed Markdown and JSONL cycle register. The repository's `docs/IMPROVEMENT_REVIEW_2000.md` records the 50-domain × 40-lens methodology and the planning decisions.

## Status distinction

The remote plans and status records are committed to GitHub. The original application source bundle still needs to be pushed to `forgelab-source` to make the source tree directly browsable on GitHub. The 0.4.0.dev1 implementation is a development preview, not a stable or production-ready release.
