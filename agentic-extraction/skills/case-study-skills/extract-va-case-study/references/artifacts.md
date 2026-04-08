# Working Artifacts

Do not use the final `PaperUsageSpec` as the scratchpad. Use working artifacts.

Recommended run layout:

```text
agentic-extraction/data/agentic/extract-results/<Paper>/
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
```

## Artifact Roles

- `case-boundaries.json`
  - candidate case-study section spans and segmentation notes
- `case-skeleton.json`
  - case / episode / step structure with only core fields
- `episode-dossiers/`
  - evidence bundles for each episode
- `reasoning-candidates.json`
  - candidate questions, hypotheses, insights, and transitions
- `linkage-candidates.json`
  - tentative links to views and subview capabilities
- `extraction-log.md`
  - unresolved ambiguities and important decisions

Use the paper-level shared workspace, but keep case-study working artifacts and outputs under the dedicated `case-study/` subdirectory. Keep these artifacts stable across extraction, review, and revise steps.

If `review-va-case-study` or `revise-va-case-study` is run later as a separate explicit step, those skills may add their own artifacts to the same `case-study/output/` directory. They are not part of the default extract-stage output.
