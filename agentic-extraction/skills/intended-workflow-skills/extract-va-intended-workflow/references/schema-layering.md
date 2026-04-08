# Schema Layering

Use the intended workflow schema in layers.

## Core

These fields should be extracted first:

- `PaperWorkflowSpec.paperName`
- `PaperWorkflowSpec.workflows`
- `WorkflowSpec.workflowGoal`
- `WorkflowSpec.stages`
- `WorkflowStage.stageGoal`
- `WorkflowStage.description`
- `WorkflowTransition.transitionType`

## Advanced

Fill after the skeleton is stable:

- `workflowTitle`
- `workflowKind`
- `usedViews`
- `usedCapabilities`
- `usedCoordinations`
- `expectedFinalOutcome`
- `WorkflowTransition.rationale`

## Optional / High-Inference

Only fill when the evidence is strong:

- `targetUsers`
- `paperLevelClaims`
- `inferenceType`
- workflow-level `description` synthesized across multiple passages

If support is weak, leave these fields empty rather than over-committing.
