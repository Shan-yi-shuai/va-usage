# Working Artifacts

## Goal

Use working artifacts as persistent extraction state. Do not use the final accepted `SystemSpec` JSON as the only scratchpad.

## Suggested Layout

Create a run directory like:

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
```

Adjust paths if the repository already has a preferred run directory.

Treat the repository-level preprocess summary as the preferred entry artifact for extraction. Do not create a second authoritative copy inside the `system-spec/` run directory. The summary should point to the stable evidence layer such as passages, figures, captions, and interface-view crops that remain stored in their own repository-level directories.

## `system-map.json`

Use this file to hold the stable interface topology.

Suggested contents:

- paper identifier
- list of top-level views
- provisional `viewId`
- optional `viewName`
- `nameSource`
- aliases
- associated figure references
- crop paths
- status notes

Do not store detailed style or coordination here. Keep it as the canonical map of interface entities.

## `view-dossiers/<viewId>.json`

Use one dossier per view.

Suggested contents:

- `viewId`
- linked sub-view records
- selected passages
- figure and caption evidence
- alias evidence
- provisional extraction result
- unresolved questions
- verification notes

Use the dossier to keep local context small when working on one view.

## `coordination-candidates.json`

Use this file to track candidate coordination items before final acceptance.

Suggested contents:

- candidate identifier
- source `ViewRef`
- target `ViewRef` list
- evidence bundle
- status: `candidate`, `verified`, `rejected`
- rejection reason if dropped

Keep rejected candidates. They are useful for debugging failure modes.

## `system-info-draft.json`

Use this file for system-level metadata extracted from the paper as a whole.

Keep:

- system name candidates
- ontology candidates
- system category candidates
- supporting evidence
- unresolved conflicts

## `extraction-log.md`

Use a human-readable log for:

- contradictions between text and figures
- unresolved naming ambiguity
- why a candidate coordination was removed
- remaining confidence concerns before any optional review

## Assembly Rule

Write `system-spec/output/system-spec.draft.json` once the working artifacts are stable enough for a separate draft artifact.

If `review-va-system-spec` or `revise-va-system-spec` is run later as a separate explicit step, those skills may add their own artifacts to the same `system-spec/output/` directory. They are not part of the default extract-stage output.
