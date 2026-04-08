# Working Artifacts

Recommended run layout:

```text
agentic-extraction/data/agentic/extract-results/<Paper>/
  intended-workflow/
    working/
      workflow-boundaries.json
      workflow-skeleton.json
      stage-dossiers/
      linking-candidates.json
    output/
      paper-workflow-spec.draft.json
```

Treat the repository-level preprocess summary as the preferred entry artifact for extraction. Do not create a second authoritative copy inside the run directory.

Use the paper-level shared workspace, but keep intended-workflow working artifacts and outputs under the dedicated `intended-workflow/` subdirectory. Do not mix them into `system-spec/working/` or `system-spec/output/`, even though intended-workflow extraction depends on `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`.

## Artifact Roles

- `workflow-boundaries.json`
  - records which passages or figures were treated as intended workflow evidence
  - records whether any `intended_workflow` figure was available and prioritized
  - records which sections were excluded as case-study evidence
- `workflow-skeleton.json`
  - stores the current workflow and stage structure before full enrichment
- `stage-dossiers/`
  - one file per stage with evidence, candidate titles, goals, and feature links
- `linking-candidates.json`
  - stores tentative view and feature linkage before canonicalization against `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`
