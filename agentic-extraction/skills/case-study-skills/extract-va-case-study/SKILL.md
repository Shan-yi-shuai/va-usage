---
name: extract-va-case-study
description: Agentic extraction of visual analytics case study drafts from research papers into the repository's PaperUsageSpec schema. Use when Codex needs to segment case study narratives into cases, episodes, and analytic steps, then build an evidence-backed usage draft linked to an existing system specification.
---

# Extract VA Case Study

## Overview

Build a draft `PaperUsageSpec` from a VA paper's case study narrative. Treat a preprocess summary as the single entry file for repository-level evidence, and treat `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` as the structural grounding source for design linkage. Keep extraction state on disk, not in runtime memory.

Do not ask a model to emit the full final case study schema in one shot.

## Use This Skill

Follow this skill when the user asks to:

- extract case study knowledge from a VA paper
- segment a case study into cases, episodes, and steps
- recover questions, hypotheses, insights, and transitions from narrative text
- link case study behavior to views or subview capabilities from an existing system spec
- prepare a draft that may later be audited by a separate review step when explicitly requested

## Required Inputs

Expect these artifacts before extraction starts:

- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- a validated system specification at `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` when available
- `../../../schemas/case_study_schema.py`

Treat the preprocess summary as the single entry file. It should point to the underlying evidence layer, including passages, case-study figures, and captions.

Use text first to determine how many case studies the paper actually presents. Treat figures labeled `case_study` as supporting evidence for boundaries, local steps, and view usage, not as the primary basis for counting cases.

If the preprocess summary contains figures labeled `case_study`, use those figures and their captions to refine and ground the text-based case interpretation before expanding further.

If one or more prerequisites are missing, degrade gracefully:

- without case-study figures, continue using passages only
- without `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`, keep design linkage textual rather than inventing canonical references

## Operating Rules

- Extract in two phases: `skeleton` first, `reasoning-enrichment` second.
- Build the case / episode / step structure before filling higher-inference fields.
- Before segmenting episodes or steps, explicitly determine how many distinct case studies or scenarios the paper presents from text evidence. Prioritize avoiding missed cases over prematurely collapsing them into one narrative.
- Prioritize the `Core` layer before `Advanced` or `Optional` fields.
- Keep step granularity semantic, not click-level.
- Treat a step as the smallest process unit with independent analytic meaning, not the smallest UI action.
- Prefer one local analytic advance per step. If one narrative chunk contains multiple advances such as observe -> interact -> read updated result, split it into multiple steps instead of keeping one summarized macro-step.
- Treat an episode as a local subtask or phase that contains one or more steps.
- Do not force every narrative sentence into a step.
- Avoid both micro-step over-segmentation and macro-step under-segmentation. Prefer semantically meaningful steps that preserve local goals and transition structure.
- A step does not need to map one-to-one to a single sub-view, but it should explicitly record the directly involved sub-views in `usedViews`.
- If multiple sub-views jointly support the same local purpose, they may remain in one step.
- If a step contains a clear sequential shift to a different local purpose across sub-views, split it into multiple steps instead of storing the whole sequence in one macro-step.
- A step may involve observing multiple sub-views when they jointly support the same local purpose.
- Use `usedViews` for directly involved views or sub-views.
- Let `usedViews` be slightly inclusive rather than under-complete when a local purpose clearly depends on multiple jointly involved sub-views.
- If one sub-view appears alone but belongs to a parent view whose sibling sub-views usually work together, check whether the narrative likely omitted the sibling relationship by default. Add the jointly involved sibling sub-views to `usedViews` when the local purpose clearly depends on them.
- Use `usedCapabilities` for subview capabilities that the analyst directly used or directly read from.
- Keep `usedCapabilities` minimal. Only keep a capability when removing it would lose an essential part of what the analyst directly did or directly read in that step.
- Do not encode coordination usage as a core step field. In case-study extraction, prioritize accurate `usedViews` and `usedCapabilities` instead.
- If the analyst first acts in source sub-view `A`, updates target sub-view `B`, and only then reads `B` to produce an insight, split that into two steps so the target-side reading is represented explicitly in `usedViews` and `usedCapabilities`.
- A step may still include multiple sub-views when they jointly support one local purpose, even when no explicit coordination field is recorded.
- Do not upgrade plain observations or descriptive paraphrases into `InsightItem` objects without clear reasoning or consequence.
- Do not convert plain story order into explicit `StepTransition` unless the narrative supports a workflow move.
- Do not use intended-workflow sections or author-recommended workflow descriptions as case-study evidence.
- Do not force question or hypothesis inventories up front; allow them to emerge from step events.
- Prefer explicit evidence. Leave high-inference fields empty when support is weak.
- Use existing system spec references when grounded; otherwise preserve textual linkage and mark inference conservatively.
- Do not link a step to a view or capability more specifically than the evidence supports.
- Do not reconstruct `stateBefore`, `stateAfter`, friction, or workaround fields from intuition alone.
- Keep a persistent working state on disk. Do not rely on long conversational memory.
- Run only structural validation in this skill. Do not perform the full review pass here.
- Treat [../../knowledge/va-case-study/failure-patterns.md](../../knowledge/va-case-study/failure-patterns.md) as extraction-time guidance for segmentation, inference, and linkage decisions.
- Shared knowledge is limited to abstract guidance under `../../knowledge/va-case-study/`, such as `failure-patterns.md` and `experience-candidates/`.
- Do not read other papers' files under `agentic-extraction/data/agentic/extract-results/` during extraction unless the user explicitly asks for cross-paper comparison or debugging. Use only the current paper's run directory plus shared knowledge.
- A separate [$review-va-case-study](../review-va-case-study/SKILL.md) skill exists for optional deeper audit when explicitly requested.

## Workflow

Use the detailed procedure in [workflow.md](references/workflow.md). Read the following references as needed:

- [schema-layering.md](references/schema-layering.md) for `Core` / `Advanced` / `Optional` field priority
- [segmentation.md](references/segmentation.md) for case / episode / step boundaries
- [inference-policy.md](references/inference-policy.md) for explicit vs inferred fields
- [artifacts.md](references/artifacts.md) for working-state layout

Typical sequence:

1. Read the preprocess summary, inspect the referenced artifacts, and initialize a run directory.
2. Use passages, section structure, and captions to determine how many distinct case studies or scenarios the paper presents.
3. Check whether the preprocess summary contains any figure with primary role `case_study`. If it does, use that figure and its caption to support the text-based case interpretation rather than to decide the case count on their own.
4. Exclude intended-workflow sections and author-recommended workflow descriptions from the case-study evidence set.
5. Detect case-study sections and define case boundaries.
6. Build a case skeleton with `CaseStudySpec`, `Episode`, and `UsageStep` core fields.
7. Enrich the skeleton with question and hypothesis events, observations, insights, decisions, and transitions.
8. Link steps to system views or capabilities when the evidence supports stable references.
9. Write `case-study/output/paper-usage-spec.draft.json`.
10. Run schema validation and stop at the draft stage.

## Outputs

Produce:

- `case-study/output/paper-usage-spec.draft.json`
- working artifacts such as `case-boundaries.json`, `case-skeleton.json`, `episode-dossiers/`, and `reasoning-candidates.json`

## Failure Handling

- If the case-study boundary is unclear, record the ambiguity in working artifacts instead of forcing one segmentation.
- If step granularity is unstable, prefer fewer semantically meaningful steps over micro-steps.
- If a question, hypothesis, or insight is weakly implied, keep the evidence and `inferenceType` but do not over-commit the structure.
- If capability linkage is not defensible, keep it textual and leave canonical refs empty.
