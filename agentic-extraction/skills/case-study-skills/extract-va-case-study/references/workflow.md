# Case Study Extraction Workflow

Use this sequence.

## Evidence Selection

1. Use passages, section headings, and captions to determine how many distinct case studies or scenarios the paper presents.
2. Check whether the preprocess summary contains any figure with primary role `case_study`.
3. If it does, use that figure and its caption to support the text-based case interpretation, boundary selection, and local step grounding.
4. Do not infer the number of cases from the number of `case_study` figures alone.
5. Exclude intended-workflow sections and author-recommended workflow descriptions from the case-study evidence set.
6. If no `case_study` figure exists, fall back to passages and captions only.

## Phase 1: Skeleton

1. Locate the paper sections that actually contain case-study narrative.
2. Explicitly determine the number of independent cases from text evidence before segmenting inside any one case.
3. Separate independent cases when the paper presents more than one scenario.
4. Segment each case into episodes using local goals, topic shifts, or explicit subheadings.
5. Segment each episode into semantic steps.
6. Fill only `Core` fields during this phase:
   - `scenario`
   - `episodes`
   - `steps`
   - `rawNarrative`
   - `intent`
   - `operation`
   - `usedViews`
   - `observations`
   - `producedInsights`
   - `decision`
   - `evidence`

Do not try to stabilize every question, hypothesis, state, or friction field in phase 1.

When the text suggests another case but the figure evidence is sparse, keep the additional case as a coarse boundary judgment rather than silently dropping it.

Apply the following segmentation rules while building the skeleton:

- an `Episode` is a local subtask or phase inside the case
- a `UsageStep` is the smallest process unit that still has independent analytic meaning
- a step is not the smallest UI action
- a step should ideally capture one local analytic advance rather than a mini-summary of several advances
- a step may involve multiple sub-views when they jointly support one local purpose
- a step may involve observing multiple sub-views when they jointly support one local purpose
- if there is a clear sequential move to a different local purpose across sub-views, split it into multiple steps
- if one narrative chunk contains observe -> interact -> read updated result, split it into multiple steps
- do not compress an entire stage into one macro-step
- do not split a step only because the analyst compares two sub-views simultaneously for the same local purpose
- record directly involved views/sub-views in `usedViews`
- if one sub-view is named explicitly but a sibling sub-view in the same parent view is clearly part of the same local purpose, add both to `usedViews` rather than treating the sibling as absent
- use `usedCapabilities` for subview capabilities that the analyst directly used or directly read from
- keep `usedCapabilities` minimal; do not list every typical capability of a referenced sub-view
- do not treat coordination as a core extracted step field; represent the process through accurate `usedViews` and `usedCapabilities`
- if source `A` triggers target `B`, and a later step reads `B` to produce insight, split those into two steps so the target-side reading is explicit

## Phase 2: Reasoning Enrichment

1. Review each episode dossier and identify question or hypothesis events.
2. Normalize repeated questions or hypotheses into case-level inventories.
3. Add `producedInsights`, `DecisionItem`, and `StepTransition` only when the narrative supports them.
4. Add `usedCapabilities` only when the system-spec linkage is grounded.
5. Add `stateBefore`, `stateAfter`, `friction`, and `workaround` only with clear support.

## Final Draft Assembly

1. Assemble the paper-level wrapper.
2. Validate IDs, step order, and internal references with `../../../schemas/case_study_schema.py`.
3. Save `case-study/output/paper-usage-spec.draft.json`.
4. Stop at the validated draft. Use `review-va-case-study` only as a separate, explicitly requested audit step.
