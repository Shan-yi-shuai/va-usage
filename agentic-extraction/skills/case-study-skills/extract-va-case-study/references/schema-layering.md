# Schema Layering

Use the schema in three priority layers.

## Core

These fields should be attempted first and should drive the initial extraction pass.

- `PaperUsageSpec.caseStudies`
- `CaseStudySpec.scenario`
- `CaseStudySpec.episodes`
- `Episode.localGoal`
- `Episode.steps`
- `UsageStep.rawNarrative`
- `UsageStep.intentCanonical` or `intentText`
- `UsageStep.operationCanonical` or `operationText`
- `UsageStep.usedViews`
- `UsageStep.observations`
- `UsageStep.producedInsights`
- `UsageStep.decision`
- `UsageStep.evidence`

## Advanced

These fields are valuable but can be added in a second pass.

- `CaseStudySpec.questions`
- `CaseStudySpec.hypotheses`
- `UsageStep.questionEvents`
- `UsageStep.hypothesisEvents`
- `UsageStep.strategyCanonical`
- `UsageStep.usedCapabilities`
- `Episode.transitions`
- `CaseOutcome`
- `PaperUsageSpec.systemSpecPath`
- `PaperUsageSpec.systemSpecId`

Notes:

- `UsageStep.usedViews` should capture directly involved views or sub-views.
- `UsageStep.usedCapabilities` should capture the subview capabilities the analyst directly used or directly read from.

## Optional / High-Inference

These fields should be left empty unless the evidence is good enough.

- `stateBefore`
- `stateAfter`
- `frictionTypes`
- `workaround`
- `unresolvedQuestionIds`
- most `inferenceType` values when the item is already explicit
- `analyst`
- `overallStrategySummary`
- `caseNarrativeSummary`
- `paperLevelUsageClaims`
