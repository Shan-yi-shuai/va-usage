# Revision Policy

## Goal

Repair a case-study draft using explicit findings and paper evidence while preserving defensibility, then update the knowledge base only when the revision justifies it.

## 1. Load Inputs

- draft `PaperUsageSpec`
- review findings
- human feedback from `working/human-feedback.md` when present
- preprocess summary
- working artifacts
- passages, figures, captions, and system-spec references used during extraction

Treat explicit human feedback as the highest-priority revision input. Use review findings as secondary guidance.

## 2. Revision Priorities

1. Remove unsupported claims.
2. Fix segmentation errors that invalidate downstream structure.
3. Repair wrong question, hypothesis, or insight linkage.
4. Repair wrong capability linkage.
5. Only then add missing supported details.

## 3. Preferred Repair Actions

- split or merge steps only when the evidence clearly supports it
- downgrade `StepTransition` to narrative order when explicit workflow evidence is weak
- delete weak `usedCapabilities` entries instead of guessing canonical references
- keep `stateBefore`, `stateAfter`, `frictionTypes`, and `workaround` empty when support is weak
- preserve IDs when possible; if an ID must change, record the reason in `revision-log.md`

## 4. Update Working Artifacts

When a repair materially changes the interpretation:

- update `case-boundaries.json` when segmentation changes
- update `case-skeleton.json` when case, episode, or step structure changes
- update the relevant episode dossier when reasoning or evidence selection changes
- update `reasoning-candidates.json` and `linkage-candidates.json` when transitions or system links change
- record the rationale in `revision-log.md`

## 5. Knowledge Capture

If the revision reveals a reusable issue:

- write a new candidate file or append to an existing paper-named file under `../../knowledge/va-case-study/experience-candidates/`
- use `<paper>.jsonl` as the default filename
- include enough context to show whether it is new, weakly covered, or already well covered

Default to writing an `experience-candidates` entry when:

- explicit human feedback identifies a problem that is not clearly covered by current stable patterns
- the revision requires a new boundary judgment or repair strategy that is not clearly covered by current stable patterns
- the issue appears to be a new subtype or new location of an existing pattern, even if it may later remain below the promotion threshold for `failure-patterns.md`

Update `../../knowledge/va-case-study/failure-patterns.md` only when:

- the issue is a stable new pattern not yet covered, or
- the issue is already covered but still rare enough that the current wording should be strengthened

Do not update `failure-patterns.md` when:

- the issue is already clearly covered, and
- the pattern is already observed often enough that another mention adds little value

## 6. Finalize

- revised `case-study/output/paper-usage-spec.json`
- `case-study/output/revision-log.md`
- updated working artifacts when segmentation or linkage changes
- validate against `../../../schemas/case_study_schema.py`
- use a fresh `$review-va-case-study` pass only when a separate additional audit is explicitly requested or clearly warranted by substantial changes
