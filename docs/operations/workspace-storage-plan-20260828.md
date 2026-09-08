# Workspace storage plan (2026-08-28)

## Purpose

The workspace cleanup planner separates rebuildable output from AI datasets without deleting
anything. It reads file path metadata and sizes only, and never reads file contents.

## Current storage snapshot

- `datasets`: about 1.87 GiB
- root `node_modules`: about 435 MiB
- `.venv`: about 433 MiB
- `frontend`: about 157 MiB, including about 143 MiB in `.next`
- `frontend/test-results`: about 12 MiB

Most dataset usage comes from historical training experiments. Those directories remain marked
`manual_review_required`; the planner does not infer that an unreferenced experiment is disposable.
`datasets/local-ai` and `datasets/local-ai-incremental` are always protected as active data.

## Run the planner

```powershell
python scripts/operations/plan_workspace_cleanup.py
```

The command writes `artifacts/workspace-cleanup/latest.json`. Only entries classified as
`rebuildable_cache` are counted as potentially reclaimable. Dependencies are retained so the
development environment remains ready, and datasets require a separate human review.

There is deliberately no delete or apply option. Any later deletion must use the reviewed JSON
report, verify resolved paths remain inside this workspace, and receive explicit approval.

## Audit exact dataset duplicates

```powershell
python scripts/operations/audit_dataset_duplicates.py
```

The audit hashes only files that share the same size, then reports a duplicate only when their
SHA-256 values also match. Active datasets are selected as keepers before historical copies; if
all copies are historical, the newest file is selected. The generated
`artifacts/workspace-cleanup/dataset-duplicates.json` remains a review report and cannot delete
files.

The 2026-08-28 audit inspected 184 files and found 15 exact duplicate groups. Removing every
reported review candidate would potentially reclaim about 269.2 MiB, but no file was removed.
Several duplicates live in experiment-specific paths, so path consumers and reproducibility must
be checked before approving any deletion.

## Audit duplicate path references

```powershell
python scripts/operations/audit_dataset_references.py
```

This audit searches bounded source files, documentation, and dataset JSON metadata for duplicate
candidate paths. It excludes `.env` files, dependencies, generated output, and file contents from
the report. Runtime or metadata references are retained; documentation references require a
reproducibility review; candidates with no references remain manual review candidates. There is no
automatic deletion mode.

The 2026-08-28 reference audit classified 22 exact-duplicate candidates:

- 0 runtime or metadata references
- 11 documentation references requiring reproducibility review
- 11 unreferenced review candidates totaling about 114.1 MiB

The unreferenced result narrows the review set but is not deletion approval. The selected keeper
must still open successfully and training commands must be checked before any candidate is removed.
