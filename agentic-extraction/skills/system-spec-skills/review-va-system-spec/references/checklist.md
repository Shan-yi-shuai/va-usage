# Review Checklist

## Goal

Find unsupported or weak claims in a VA `SystemSpec` draft without repairing the draft.

## 1. Load And Sanity Check

- validate the JSON against `../../../schemas/system_spec_schema.py`
- confirm all required supporting artifacts are available
- confirm the run directory contains the expected working artifacts when they exist
- treat passages and captions as the primary evidence for semantic and relational claims
- treat figures and crops as the primary evidence for visual-form, layout, and boundary claims

## 2. View Identity And Critical Naming

For every view or sub-view:

- confirm the crop is mapped to the correct entity
- confirm that the chosen `viewName` or `subViewName` is not misleading enough to distort structure or references
- use text, caption, or callout evidence first for naming; use crop-visible labels only as a fallback when they are obvious and stable
- treat `nameSource` provenance issues as secondary unless they also indicate a deeper entity-mapping problem

## 3. Style Audit

For every visual sub-view:

- check the crop before accepting `markType`
- reject any mark type that is more specific than the image supports
- use text to confirm semantics, not to force a primitive from words like `chart`, `graph`, `distribution`, `overview`, or `map`
- flag overly precise channel encodings that are not image- or text-supported

## 4. Sub-View Capability Audit

For every sub-view:

- check whether the draft captures the user-visible capabilities of the sub-view, not just its structural presence
- distinguish interaction capabilities from information capabilities
- reject capabilities that merely restate backend processing invisible to the user

## 5. View-Linked Processing Audit

For every view or sub-view:

- if `viewProcessingInfo` is present, verify that the paper really binds that processing step to this specific view or sub-view rather than only describing a global model or backend pipeline
- if `viewProcessingInfo` is `null`, check whether the paper actually describes view-specific processing that should have been attached here
- treat missing processing bindings as findings only when the evidence is specific to this interface component, not when the paper only describes system-wide computation

## 6. Coordination Audit

Audit both existing and potentially missing coordination.

For every coordination item already present in the draft:

- ground the source `ViewRef`
- ground every target `ViewRef`
- verify from passages and captions that the interaction exists in the paper, not just in the analyst's workflow summary
- verify source and target capabilities when the draft models coordination through capability refs
- verify that the modeled target is the component that actually updates
- verify that source and target are modeled at the right granularity, especially inside compound views
- verify that the claimed coordination effect matches the evidence rather than merely asserting that "something updates"
- use figure evidence mainly to verify plausible source and target placement, not to invent missing coordination semantics
- reject coordination based only on narrative sequence, case-study order, or panel adjacency

Then check for omitted coordination by scanning:

- explicit interaction descriptions in passages and captions
- extraction working artifacts such as `coordination-candidates.json` when available
- interface figures for obvious source controls or linked panels that the text clearly supports
- repeated view-pair descriptions that imply a stable interaction pattern rather than a one-off walkthrough

Only flag a missing coordination when the paper supports an actual UI dependency rather than a generic workflow step or repeated multi-view usage.

## 7. System-Level Audit

- verify system name from title, abstract, or system overview
- verify domain/task classification from global sections, not local case studies
- keep taxonomy fields sparse unless the evidence is direct

## 8. Findings Format

Report findings with:

- severity
- file and field reference
- brief explanation of the problem
- supporting evidence
- suggested repair direction when obvious

## 9. Experience Recording

Write a new candidate file or append to an existing paper-named file under `../../knowledge/va-system-spec/experience-candidates/` only when:

- the failure pattern is reusable beyond this paper, or
- human review confirms a previously missed issue

Use:

- `source=self-review` for Codex-discovered issues
- `source=human-review` for user-supplied review findings
- `<paper>.jsonl` as the default filename
