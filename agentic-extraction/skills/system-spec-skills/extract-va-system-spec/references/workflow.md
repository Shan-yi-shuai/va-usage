# Workflow

## Purpose

Use this workflow to extract a draft VA `SystemSpec` from a paper without relying on a single long prompt or on conversational memory.

## 1. Inspect Inputs

Confirm that a preprocess summary exists and that it points to:

- paragraph-level passages
- figure and caption metadata
- interface-view crops

Create a run directory before any semantic extraction. Use the structure in `artifacts.md`.

## 2. Build The System Map

Treat interface-view crops as the initial map of the interface.

For each crop:

- create a provisional `viewId`
- decide whether the crop is a top-level view or part of a larger grouped view
- record crop path, figure reference, caption text, and any nearby labels
- defer naming if evidence is weak

When a crop clearly contains multiple internal regions, create provisional sub-view entries. When evidence is weak, keep one default sub-view and refine later.

## 3. Resolve Names And Aliases

Resolve names after the system map exists.

Collect candidate names and aliases from:

- caption labels such as `Fig. 1a`
- textual mentions such as `cluster view`, `detail panel`, `view A`
- explicit callouts in interface figures
- repeated nearby noun phrases that consistently co-refer to one crop

Do not force a polished final name. Use:

- `explicit` when the paper gives the name directly
- `caption` when the name comes from figure labels or caption wording
- `inferred` when the name is strongly implied
- `generated` when no real name exists and a placeholder is necessary

## 4. Build View Dossiers

Build one dossier per `viewId`.

Start retrieval from high-precision signals:

- direct alias or caption matches
- passages that mention the relevant figure region
- passages adjacent to explicit view descriptions

Expand only after the seed evidence is established. Use semantic similarity as a supplement, not as the first retrieval step.

For each dossier, keep:

- the crop and figure evidence
- the best passages
- unresolved questions
- provisional judgments about top-level view role, sub-view structure, capabilities, and likely coordination

## 5. Extract View And Sub-View Specifications

For each dossier:

- decide the sub-view decomposition
- mark each sub-view as visual or non-visual
- extract `ViewStyleInfo` only for visual sub-views
- extract `NonVisualViewSpec` only for non-visual sub-views
- extract sub-view capabilities:
  - interaction capabilities for what the user can directly do in the sub-view
  - information capabilities for what the user can directly read or obtain from the sub-view
- attach `ViewProcessingInfo` only when evidence ties a processing step to that view or sub-view

Do not attach generic pipeline stages to every view. If the paper describes a global model but not its binding to a view, keep that uncertainty out of the per-view processing field.

## 6. Extract Coordination

Only start this phase after the relevant source and target sub-view capabilities are stable enough to reference.

Do not ask the model to infer all coordination in one global pass over the entire paper.

Instead:

1. generate candidate relationships from dossiers, captions, explicit interaction descriptions, and interface layout
2. verify each candidate pair or small group independently
3. require evidence for source, target, and the involved sub-view capabilities when they can be identified

Use interface figures to identify likely source controls and likely target views. Use text to confirm that the interaction really exists.

Defer or drop any candidate whose capability grounding is still unstable. Do not force a coordination edge first and try to explain the capabilities later.

## 7. Extract System-Level Metadata

Extract `SystemInfo` separately from the paper-level evidence.

Prefer:

- title and abstract
- introduction and system overview sections
- design goals or task framing sections
- dataset and domain descriptions

Do not let local view evidence distort system-level classification.

## 8. Assemble The Draft SystemSpec

Assemble the draft object after view dossiers, coordination candidates, and system-level metadata are stable enough for a draft artifact.

When assembling:

- preserve stable IDs
- keep names optional when evidence is weak
- keep evidence attached where the schema allows it
- ensure every coordination reference resolves to an existing view or sub-view

Write the result as `system-spec/output/system-spec.draft.json`, not as an accepted final artifact.

## 9. Validate Structure And Stop

Run schema validation and obvious integrity checks such as:

- every `ViewRef` resolves
- every required evidence payload is present
- no duplicated view or sub-view IDs exist

Do not perform the full claim-by-claim review here. Stop at the validated draft. Use `$review-va-system-spec` only when a separate deeper audit is explicitly requested.
