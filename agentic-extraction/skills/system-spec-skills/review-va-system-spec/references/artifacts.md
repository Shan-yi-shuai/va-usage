# Review Artifacts

## Goal

Use the extraction run directory as the primary working-state evidence layer for review. Do not rely only on the draft JSON when the run directory is available.

## Expected Layout

Review usually consumes a directory like:

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
```

Treat the repository-level preprocess summary as the entry file for passages, figures, captions, and interface-view crops. Treat the `system-spec/` run directory as the primary source for localized extraction evidence and unresolved decisions.

## Review Inputs

Use these sources in order:

- the draft `SystemSpec` under review
- the preprocess summary and the repository-level evidence it references
- the extraction run directory and its working artifacts

Do not require every working artifact to exist, but when they are available, use them before reconstructing local extraction context from scratch.

## Review Outputs

When a run directory exists, write:

- `system-spec/output/review-findings.json`
- `system-spec/output/review-report.md`

These are review-stage artifacts, not extract-stage defaults.

## Artifact Roles

### `working/system-map.json`

Use this to audit stable view and sub-view identity, naming, crop linkage, and unresolved topology decisions.

### `working/view-dossiers/<viewId>.json`

Use these to audit local evidence grounding for names, style, processing, and sub-view decomposition without rereading the full paper every time.

### `working/coordination-candidates.json`

Use this to see which coordination claims were considered, rejected, or accepted during extraction.

### `working/system-info-draft.json`

Use this to audit whether system-level taxonomy or ontology fields were overfilled relative to the available evidence.

### `working/extraction-log.md`

Use this to inspect unresolved conflicts between text and figures, naming ambiguity, and deleted coordination candidates before turning them into findings.
