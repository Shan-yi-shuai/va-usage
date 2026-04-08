# Step 1: Preprocessing

This directory contains the preprocessing artifacts that exist before agentic extraction begins.

The role of this step is to organize the raw paper into a compact evidence layer that can later be used by the extraction skills.

The preprocessing scripts that generate these artifacts are released under `../preprocessing/`.

Included subdirectories:

- `passages/`
- `figures/`
- `view-images/`
- `preprocess-summaries/`
- `knowledge-base/`

## What Each Artifact Means

### `preprocess-summaries/`

This directory contains agent-oriented entry summaries for each paper.

Each summary file gives a compact overview of:

- the paper identity
- the passage file
- the figure inventory
- the interface-view crops

These files function as an index over the preprocessing artifacts and are primarily useful for understanding how the agent enters the extraction workflow.

They are not intended to be the main human-facing explanation of the preprocessing results.

If the goal is to inspect the agent-facing entry summary for the anchor paper, see:

- `preprocess-summaries/ConceptViz.md`

### `passages/`

This directory stores paragraph-level paper text extracted from the PDF.

These files support evidence grounding for:

- `passageIds` referenced in schema JSON
- extraction-time text lookup
- review-time verification

### `figures/`

This directory stores copied figure metadata and figure crops for the four example papers.

Typical contents include:

- `figures.json`
- `figure-manifest.json`
- cropped figure images

These artifacts are used to:

- inspect interface and case-study figures
- ground `figureRefs`
- identify which figures function as interface, workflow, case-study, or evaluation figures

### `view-images/`

This directory stores interface-view crops derived from the selected interface figure.

These artifacts are especially important for system extraction because they make view decomposition and view grounding more stable.

### `knowledge-base/`

This directory contains the released four-paper subset of the structured extraction outputs:

- `paper-usage-spec.json`
- `paper-workflow-spec.json`
- `system-spec.json`

These files make the released extraction package self-contained for the four showcase papers.

## Why This Step Matters

The paper emphasizes that the evidence is multimodal and distributed across passages and figures.

This preprocessing step makes that evidence explicit and reviewable before the extraction process starts.

## Suggested Reading Path

For `ConceptViz`, a good order is:

1. `figures/ConceptViz/`
2. `view-images/ConceptViz/`
3. `passages/ConceptViz_passages.json`
4. `preprocess-summaries/ConceptViz.md` if the goal is to inspect the agent-oriented entry file
