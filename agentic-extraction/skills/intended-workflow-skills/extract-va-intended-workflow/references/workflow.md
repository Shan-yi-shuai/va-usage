# Workflow

Use this skill in two phases.

Before phase 1, do two setup checks:

- load the preprocess summary and identify whether any figure is labeled `intended_workflow`
- load `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` and treat it as the canonical source for views and system features

If an `intended_workflow` figure exists, prioritize that figure and its caption before expanding to passages.
If no such figure exists, rely on passages and captions only.

Do not use case-study sections as intended-workflow evidence.

## Phase 1: Workflow Skeleton

Build only the intended workflow backbone:

- detect whether the paper actually presents an author-intended workflow
- segment the workflow into one or more `WorkflowSpec`
- segment each workflow into ordered `WorkflowStage`
- recover supported `WorkflowTransition`

Prioritize:

- `workflowGoal`
- `workflowTitle`
- `stageGoal`
- `stageTitle`
- `description`
- `transitionType`

Avoid feature-level overfitting in this phase.

## Phase 2: Design Linking

After the skeleton is stable:

- connect stages to `usedViews`
- connect stages to `usedCapabilities`
- connect stages to `usedCoordinations`
- fill `expectedOutcome`
- add `evidence` and `inferenceType`

Prefer canonical `ViewRef` and system-feature linkage from `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`. Otherwise keep textual linkage and do not rebuild structure independently.

## Stop Condition

Stop at a validated draft:

- `intended-workflow/output/paper-workflow-spec.draft.json`

Do not revise unsupported fields inside this skill. Leave that to review and revise.
