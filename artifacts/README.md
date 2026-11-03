# Remote ForgeLab artifacts

The binary source snapshot and full 2,000-cycle JSONL register are stored as split raw-byte parts.

## Reassemble source snapshot

Download `forgelab-source.tar.gz.xz.part00` through `part04` and concatenate in numeric order:

```bash
cat forgelab-source.tar.gz.xz.part00 forgelab-source.tar.gz.xz.part01 forgelab-source.tar.gz.xz.part02 forgelab-source.tar.gz.xz.part03 forgelab-source.tar.gz.xz.part04 > forgelab-source.tar.gz.xz
xz -dc forgelab-source.tar.gz.xz > forgelab-source.tar.gz
tar -xzf forgelab-source.tar.gz
```

## Reassemble the 2,000-cycle register

Download `improvement-review-2000.jsonl.xz.part00` through `part02`:

```bash
cat improvement-review-2000.jsonl.xz.part00 improvement-review-2000.jsonl.xz.part01 improvement-review-2000.jsonl.xz.part02 > improvement-review-2000.jsonl.xz
xz -dc improvement-review-2000.jsonl.xz > improvement-review-2000.jsonl
```

Each line records five loop stages: finding, implementation plan, expansion, plan review, and plan update.

## Regenerate full reports

After extracting the source snapshot:

```bash
python tools/improvement_review.py --root .
```

The generator validates the 50 × 40 matrix and recreates the full Markdown and JSONL reports. This is a systematic planning review, not 2,000 independent model conversations.
