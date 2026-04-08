# Inference Policy

Use `EvidenceReference` and `inferenceType` to control overreach.

## Explicit

Use `Explicit` when the paper directly states the item.

Examples:

- a question is quoted or paraphrased from the text
- a transition is stated as "then", "next", "to verify this"
- a view or feature is explicitly named

## Weak Inference

Use `WeakInference` when the structure is plausible but only loosely supported.

Examples:

- a local goal is implied by the surrounding narrative
- a decision is suggested but not stated directly

Prefer leaving the field empty over filling many weak inferences.

## StrongInference

Use `StrongInference` when the structure is not explicit but is necessary and well supported by multiple clues.

Examples:

- a repeated emerging question clearly drives multiple steps
- a hypothesis is not quoted but is strongly evidenced by the reasoning chain

## FigureGroundedInference

Use this when case-study figures or annotated screenshots clarify step boundaries, views, or observations that the text under-specifies.

## CrossModalSynthesis

Use this when the conclusion depends on combining text, figure evidence, and existing system-spec knowledge.

## Hard Rules

- Do not fill a field just because the schema has space for it.
- Do not treat narrative order as an explicit transition by default.
- Do not infer stable capability linkage from a vague textual mention.
- When the item is high-inference and not important for the current analysis pass, leave it empty.
