# Promotion Log

Use this log to record when candidate experiences are promoted into shared failure patterns or into a skill's always-on rules.

## Entry Template

- candidate ids:
- source:
- promoted to:
- rationale:
- affected files:

## History

- Bootstrap state: the shared `failure-patterns.md` was initialized during the three-skill refactor using recurring issues surfaced in the ConceptViz extraction and review cycle.
- candidate ids: `conceptviz-coordination-omission-001`
- source: human-review plus revision follow-up in ConceptViz
- promoted to: `failure-patterns.md`
- rationale: The omission of selected-feature dependencies from explorer/detail views into validation views is reusable beyond one paper and is not covered by the existing style-only failure-patterns file. The new rule keeps the boundary clear: workflow order alone is still insufficient, but explicit downstream `target feature` semantics plus grounded upstream selection should trigger a coordination audit.
- affected files: `experience-candidates/`, `failure-patterns.md`
