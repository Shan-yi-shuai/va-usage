# Review Checklist

Use this checklist in order.

## 0. Evidence Priority

- use passages and captions first for segmentation, reasoning structure, transition logic, and local-goal interpretation
- use case-study figures first for step boundaries, used views, and visually grounded observations
- use `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` first for canonical view and capability linkage
- when evidence sources conflict, record the conflict and explain which source is stronger for the field under review

## 1. Structural Integrity

- validate the JSON against `../../../schemas/case_study_schema.py`
- confirm every case has at least one episode
- confirm every episode has at least one step
- confirm `stepIndex` is unique and ordered within each episode

## 2. Segmentation

- does each `CaseStudySpec` correspond to one coherent analysis scenario
- are episode boundaries driven by local goals rather than paragraph count
- are steps semantic rather than click-level
- is the extraction under-segmented into overly long macro-steps
- is it over-segmented into brittle micro-steps
- does one step bundle multiple local analytic advances that should be split
- if source-side interaction in `A` is followed by a later target-side insight in `B`, were those split into two steps
- when multiple sub-views appear in one step, do they jointly support one local purpose rather than hiding sequential source-to-target progression
- when one sub-view appears alone, is there a sibling sub-view in the same parent view that the paper likely omitted by default even though the local purpose depends on both

## 3. Reasoning Structure

- are observations really observations instead of insights
- are insights really supported, rather than generic paraphrases
- are decisions explicit or clearly inferable
- are question or hypothesis events grounded in the text
- are `inferenceType` values commensurate with the evidence

## 4. Workflow Modeling

- do transitions represent real workflow moves, not just sentence order
- are branch / iterate / backtrack labels actually supported
- are friction and workaround claims grounded rather than speculative
- are `stateBefore` and `stateAfter` fields overfilled

## 5. System Linkage

- do `usedViews` map to real system-spec views
- are `usedViews` complete enough to cover all sub-views that jointly support the local purpose
- do `usedCapabilities` rely on grounded capability references
- are `usedCapabilities` minimal rather than an inventory of everything the referenced sub-view can do
- are capability links stronger than the evidence supports

## 6. Outputs

- write machine-readable findings to `case-study/output/review-findings.json`
- write a concise report to `case-study/output/review-report.md`
- if a reusable failure pattern is found, write a new candidate file or append to an existing paper-named `.jsonl` file under `../../knowledge/va-case-study/experience-candidates/`
