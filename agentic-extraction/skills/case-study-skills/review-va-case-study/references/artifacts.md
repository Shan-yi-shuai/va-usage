# Review Artifacts

## Goal

Use the case-study run directory as the primary working-state evidence layer for review. Do not treat review as a fresh extraction pass.

## Expected Layout

Review usually works in a directory like:

```text
agentic-extraction/data/agentic/extract-results/<paper-slug>/
  case-study/
    working/
      case-boundaries.json
      case-skeleton.json
      episode-dossiers/
      reasoning-candidates.json
      linkage-candidates.json
      extraction-log.md
    output/
      paper-usage-spec.draft.json
      review-findings.json
      review-report.md
```

Treat the repository-level preprocess summary as the entry file for passages, figures, and captions. Treat the `case-study/` run directory as the primary source for prior extraction decisions, localized evidence, and segmentation context.

## Review Inputs

Use these sources in order:

- the draft `PaperUsageSpec`
- the preprocess summary and the repository-level evidence it references
- the case-study run directory and its working artifacts
- `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` for canonical linkage checks

Do not rebuild local extraction context from scratch if a relevant dossier, boundary record, candidate file, or extraction log entry already exists.

## Review Outputs

When a run directory exists, write:

- `case-study/output/review-findings.json`
- `case-study/output/review-report.md`

## Artifact Roles During Review

### `working/case-boundaries.json`

Use to check:

- case-study section selection
- case / episode segmentation decisions
- section exclusions and ambiguities

### `working/case-skeleton.json`

Use to check:

- step order
- episode grouping
- whether the core structure is over- or under-segmented

### `working/episode-dossiers/`

Use to inspect local evidence for:

- step-level reasoning
- question or hypothesis emergence
- observations, insights, and decisions

### `working/reasoning-candidates.json`

Use to check:

- whether reasoning structure was overfilled
- whether transitions were promoted too aggressively

### `working/linkage-candidates.json`

Use to check:

- whether view and capability links are grounded in the system specification
- whether canonical references are stronger than the evidence supports
