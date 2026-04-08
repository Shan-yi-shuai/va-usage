---
name: extract-va-intended-workflow
description: Agentic extraction of author-intended visual analytics workflows from research papers into the repository's PaperWorkflowSpec schema. Use when Codex needs to recover stage-based intended workflows from system descriptions, overview figures, captions, and method sections.
---

# Extract VA Intended Workflow

## Overview

Build a draft `PaperWorkflowSpec` from a VA paper. Treat a preprocess summary as the single entry file for repository-level evidence, and treat `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` as the required structural grounding source. Keep extraction state on disk rather than in runtime memory.

Do not ask a model to emit the full final workflow schema in one shot.

## Use This Skill

Follow this skill when the user asks to:

- extract an author-intended workflow from a VA paper
- recover the recommended stage sequence of system use
- connect intended workflow stages to system views or features
- prepare a draft workflow representation that may later be audited by a separate review step when explicitly requested

## Required Inputs

Expect these artifacts before extraction starts:

- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- a validated system specification at `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`, which will be used as the canonical source for views and system features
- `../../../schemas/intended_workflow_schema.py`

Treat the preprocess summary as the single entry file for repository-level evidence. It should point to passages, figures, captions, and any other preprocessed artifacts.

Treat `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` as a required grounding artifact. Intended workflow extraction should reuse its views and feature structure rather than reconstructing system structure independently.

If the preprocess summary is missing, if `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` is missing, or if the summary points to missing prerequisite artifacts, stop and report the exact missing file instead of improvising a substitute inside extraction.

## Operating Rules

- Extract in two phases: `workflow-skeleton` first, `design-linking` second.
- Build `workflow -> stage -> transition` structure before filling optional high-inference fields.
- Prefer author-intended workflow over actual case-study behavior.
- Do not use case-study sections as intended workflow evidence.
- Do not confuse processing pipelines with intended user workflows.
- Do not confuse case-study narrative order with normative workflow order.
- Keep stage granularity semantic rather than interaction-level.
- Do not over-segment stages based on minor interaction differences or superficial UI changes.
- Do not create a transition just because two stages are narratively adjacent; require evidence of a recommended workflow move.
- If the preprocess summary contains figures labeled `intended_workflow`, use those figures and their captions as the primary workflow evidence before expanding to passages.
- If no `intended_workflow` figure exists, fall back to passages and captions only.
- Reuse `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` directly for `ViewRef` and system-feature grounding. Do not independently rebuild views, controls, coordination, or feature structure inside this skill.
- Do not invent unsupported canonical feature links when `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` does not support them.
- Keep a persistent working state on disk. Do not rely on long conversational memory.
- Run only structural validation in this skill. Do not perform the full review pass here.
- Treat [../../knowledge/va-intended-workflow/failure-patterns.md](../../knowledge/va-intended-workflow/failure-patterns.md) as extraction-time guidance for stage segmentation, transition strength, and design linkage.
- Shared knowledge is limited to abstract guidance under `../../knowledge/va-intended-workflow/`, such as `failure-patterns.md` and `experience-candidates/`.
- Do not read other papers' files under `agentic-extraction/data/agentic/extract-results/` during extraction unless the user explicitly asks for cross-paper comparison or debugging. Use only the current paper's run directory, its grounded system spec, and shared knowledge.
- A separate [$review-va-intended-workflow](../review-va-intended-workflow/SKILL.md) skill exists for optional deeper audit when explicitly requested.

## Workflow

Use the detailed procedure in [workflow.md](references/workflow.md). Read the following references as needed:

- [schema-layering.md](references/schema-layering.md) for `Core` / `Advanced` / `Optional` field priority
- [segmentation.md](references/segmentation.md) for workflow and stage boundaries
- [inference-policy.md](references/inference-policy.md) for explicit vs inferred workflow structure
- [artifacts.md](references/artifacts.md) for working-state layout

Typical sequence:

1. Read the preprocess summary, inspect the referenced artifacts, and initialize a run directory.
2. Load `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` and treat it as the canonical source for views and available design elements.
3. Check whether the preprocess summary contains any figure with primary role `intended_workflow`. If it does, prioritize that figure and its caption before reading passages.
4. Exclude case-study sections and examples from the intended-workflow evidence set.
5. Build a workflow skeleton with `WorkflowSpec`, `WorkflowStage`, and `WorkflowTransition` core fields.
6. Link stages to views or system features by directly reusing `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` references where supported.
7. Add expected outcomes, rationale, and conservative inference metadata.
8. Write `intended-workflow/output/paper-workflow-spec.draft.json`.
9. Run schema validation and stop at the draft stage.

## Outputs

Produce:

- `intended-workflow/output/paper-workflow-spec.draft.json`
- working artifacts such as `workflow-boundaries.json`, `workflow-skeleton.json`, `stage-dossiers/`, and `linking-candidates.json`

## Failure Handling

- If no defensible intended workflow exists, record that explicitly instead of forcing one.
- If passages mix system walkthrough and case-study narrative, separate the two and privilege normative descriptions here.
- If stage granularity is unstable, prefer fewer semantically meaningful stages over micro-stages.
- If feature linkage is not defensible, keep it textual and leave canonical refs empty.
