# Revision Artifacts

## Goal

Use the extraction run directory as the primary working-state evidence layer for revision. Do not treat revision as a fresh extraction pass.

## Expected Layout

Revision usually works in a directory like:

```text
agentic-extraction/data/agentic/extract-results/<paper-slug>/
  inputs/
  system-spec/
    working/
      system-map.json
      view-dossiers/
        <viewId>.json
      coordination-candidates.json
      system-info-draft.json
      extraction-log.md
    output/
      system-spec.draft.json
      review-findings.json
      review-report.md
      system-spec.json
      revision-log.md
```

Treat the repository-level preprocess summary as the entry file for passages, figures, captions, and interface-view crops. Treat the `system-spec/` run directory as the primary source for prior extraction decisions, localized evidence, and review outputs.

## Revision Inputs

Use these sources in order:

- the draft `SystemSpec`
- the review findings
- the preprocess summary and the repository-level evidence it references
- the extraction run directory and its working artifacts

Do not rebuild local extraction context from scratch if a relevant dossier, candidate record, or extraction log entry already exists.

## Revision Outputs

When a run directory exists, write:

- `system-spec/output/system-spec.json`
- `system-spec/output/revision-log.md`

Keep `system-spec/output/system-spec.draft.json` as the pre-revision snapshot unless the user explicitly asks to replace it.

## Artifact Update Rules

### `working/system-map.json`

Update when a repair changes:

- `viewName` or `subViewName`
- `nameSource`
- view or sub-view grouping
- crop-to-entity mapping

### `working/view-dossiers/<viewId>.json`

Update when a repair changes local interpretation of:

- sub-view decomposition
- style or non-visual view modeling
- view-linked processing
- evidence selection

### `working/coordination-candidates.json`

Update when:

- a reviewed coordination is deleted
- a rejected candidate is restored
- a candidate status changes because of accepted findings

### `working/system-info-draft.json`

Update when system-level metadata is weakened, deleted, or replaced during revision.

### `system-spec/output/revision-log.md`

Record for each finding:

- accepted / rejected / blocked status
- what changed
- what evidence supported the change
- whether any ambiguity remains

Also record any knowledge-base action:

- whether a new or updated file under `experience-candidates/` was added
- whether `failure-patterns.md` was updated
- which promotion rule justified the update
