# Revision Artifacts

## Goal

Use the case-study run directory as the primary working-state evidence layer for revision. Do not treat revision as a fresh extraction pass.

## Expected Layout

Revision usually works in a directory like:

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
      paper-usage-spec.json
      revision-log.md
```

Treat the repository-level preprocess summary as the entry file for passages, figures, and captions. Treat the `case-study/` run directory as the primary source for prior extraction decisions, localized evidence, and review outputs.

## Revision Inputs

Use these sources in order:

- the draft `PaperUsageSpec`
- the review findings
- the preprocess summary and the repository-level evidence it references
- the case-study run directory and its working artifacts
- `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` for canonical linkage checks

Do not rebuild local extraction context from scratch if a relevant dossier, boundary record, candidate file, or extraction log entry already exists.

## Revision Outputs

When a run directory exists, write:

- `case-study/output/paper-usage-spec.json`
- `case-study/output/revision-log.md`

Keep `case-study/output/paper-usage-spec.draft.json` as the pre-revision snapshot unless the user explicitly asks to replace it.

## Artifact Update Rules

### `working/case-boundaries.json`

Update when a repair changes:

- case-study boundary selection
- case or episode segmentation
- section inclusion or exclusion

### `working/case-skeleton.json`

Update when a repair changes:

- case, episode, or step structure
- step ordering
- local-goal segmentation

### `working/episode-dossiers/`

Update when a repair changes local interpretation of:

- question or hypothesis events
- observations, insights, or decisions
- evidence selection

### `working/reasoning-candidates.json`

Update when:

- a transition is deleted or downgraded
- an insight or hypothesis candidate is rejected
- reasoning structure is weakened or clarified

### `working/linkage-candidates.json`

Update when:

- a view or feature link is deleted
- a textual linkage replaces a canonical reference
- linkage strength changes because of accepted findings

### `case-study/output/revision-log.md`

Record for each finding:

- accepted / rejected / blocked status
- what changed
- what evidence supported the change
- whether any ambiguity remains

Also record any knowledge-base action:

- whether a new or updated file under `experience-candidates/` was added
- whether `failure-patterns.md` was updated
- which promotion rule justified the update
