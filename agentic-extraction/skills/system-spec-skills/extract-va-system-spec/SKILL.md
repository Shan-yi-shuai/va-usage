---
name: extract-va-system-spec
description: Agentic extraction of visual analytics system specification drafts from research papers into the repository's SystemSpec schema. Use when Codex needs to build a draft covering system-level metadata, views and sub-views, per-view specifications, processing steps, or cross-view coordination from a VA paper using precomputed passages, figures, captions, and interface-view crops.
---

# Extract VA System Spec

## Overview

Build a draft `SystemSpec` from a visual analytics system paper by combining deterministic preprocessing artifacts with model-driven evidence collection. Treat a preprocess summary as the preferred entry file, and passages, figure metadata, and interface-view crops as the underlying evidence layer. Keep extraction state on disk, not in runtime memory.

Do not ask a model to emit the full final schema in one shot.

## Use This Skill

Follow this skill when the user asks to:

- extract a VA system specification from a paper
- reconstruct views or sub-views from interface figures
- align view crops with paper terminology and aliases
- extract view specifications, coordination, or system-level metadata into `../../../schemas/system_spec_schema.py`
- prepare a draft that may later be audited by a separate review step when explicitly requested

## Required Inputs

Expect a preprocess summary markdown file before the agentic extraction loop starts, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`.

Treat the preprocess summary as the single entry file. It should point to the underlying evidence layer, including passages, figure and caption metadata, and interface figure crops. Keep alias resolution, evidence alignment, view decomposition, and semantic extraction inside the agentic workflow.

If the preprocess summary is missing, or if it points to missing prerequisite artifacts, stop and report the exact missing file instead of improvising a substitute inside extraction.

## Operating Rules

- Use `viewId` and `subViewId` as the canonical identity layer as early as possible.
- Treat sub-view capabilities as the user-visible feature layer. Extract what a user can directly do in a sub-view and what a user can directly read from it.
- Stabilize sub-view capabilities before extracting coordination. Do not invent coordination until the relevant source and target capabilities are identified.
- Allow `viewName` and `subViewName` to be absent. Generate names only when needed and mark `nameSource` accurately.
- Prefer interface figures as the primary source of UI topology.
- Treat interface crops as the primary evidence for `markType` and coarse layout. Use passages to confirm semantics, not to force a more specific visual primitive than the image supports.
- Use case-study figures only as supporting evidence unless they reveal interface details absent from the interface figure.
- Keep a persistent working state on disk. Do not rely on long conversational memory.
- Require evidence before filling fields. Omit unsupported claims rather than guessing.
- Require explicit evidence for every coordination item.
- Do not convert workflow sequence into coordination unless the paper supports an actual UI dependency or interaction.
- Model coordination as a relationship between sub-view capabilities. Do not fall back to ungrounded interaction labels.
- If capability grounding remains unstable, defer the coordination claim instead of forcing a coordination edge.
- Do not fill system-level taxonomy fields more specifically than the paper supports.
- Do not infer a precise `markType` from generic text such as `chart`, `graph`, `distribution`, `overview`, or `map` when the image does not support that precision.
- When a compound view contains multiple internal regions, attach coordination only to the component the evidence actually names or depicts. If the real target is not modeled yet, add the missing sub-view or drop the claim.
- Do not mark a name as `explicit` or `caption` unless the paper text, figure callout, or caption really supplies that name. Use `inferred` and `generated` conservatively.
- Run only local structural validation in this skill. Do not perform the full review pass here.
- Treat [../../knowledge/va-system-spec/failure-patterns.md](../../knowledge/va-system-spec/failure-patterns.md) as extraction-time guidance, not as a post-hoc audit checklist.
- Shared knowledge is limited to abstract guidance under `../../knowledge/va-system-spec/`, such as `failure-patterns.md` and `experience-candidates/`.
- Do not read other papers' files under `agentic-extraction/data/agentic/extract-results/` during extraction unless the user explicitly asks for cross-paper comparison or debugging. Use only the current paper's preprocessing artifacts, run directory, and shared knowledge.
- A separate [$review-va-system-spec](../review-va-system-spec/SKILL.md) skill exists for optional deeper audit when explicitly requested.

## Workflow

Use the detailed procedure in [workflow.md](references/workflow.md). Follow this sequence:

1. Read the preprocess summary, inspect the referenced artifacts, and initialize a run directory.
2. Build a `system-map` from interface-view crops with provisional `viewId` and `subViewId` anchors.
3. Resolve names and aliases from captions, callouts, and nearby text.
4. Build a dossier for each view from crop evidence plus retrieved passages.
5. Extract view and sub-view structure, visual or non-visual specifications, and view-linked processing.
6. Extract coordination by generating candidates and verifying them pairwise, not by one global pass over the full paper.
7. Extract system-level metadata separately from view-level details.
8. Assemble `system-spec/output/system-spec.draft.json`.
9. Run schema validation and resolve broken references or malformed evidence payloads.
10. Stop at the draft stage. Use [$review-va-system-spec](../review-va-system-spec/SKILL.md) only as a separate, explicitly requested audit step.

## Working State

Do not fill the final `SystemSpec` file incrementally as the agent's scratchpad. Use intermediate working artifacts instead. Read [artifacts.md](references/artifacts.md) before the first extraction step.

Use the working artifacts to:

- externalize state across long extraction sessions
- record provisional decisions and unresolved questions
- attach evidence to every important decision
- support re-entry after failures or model drift

## Inputs

This skill assumes preprocessing has already been completed. During extraction, treat the existing artifacts as the authoritative evidence layer and focus on:

- image inspection for figure and crop review
- passage lookup and evidence alignment
- JSON working-state read/write
- schema validation against `../../../schemas/system_spec_schema.py`

## Failure Handling

- If preprocessing artifacts are incomplete or unreliable, stop and report the exact missing or suspect artifact.
- If view naming remains ambiguous, keep stable IDs and continue with `generated` or `inferred` names rather than forcing a confident label.
- If passages conflict with figure evidence, record the conflict in the working state and leave it for review rather than forcing a premature resolution.
- If a coordination candidate cannot be verified, drop it from the final `SystemSpec`.
