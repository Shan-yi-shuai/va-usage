# Revision Policy

## Goal

Repair an intended workflow draft using explicit findings and paper evidence while preserving defensibility, then update the knowledge base only when the revision justifies it.

## 1. Load Inputs

- draft `PaperWorkflowSpec`
- review findings
- human feedback from `working/human-feedback.md` when present
- preprocess summary
- working artifacts
- passages, figures, captions, and system-spec references used during extraction

Treat explicit human feedback as the highest-priority revision input. Use review findings as secondary guidance.

## 2. Triage Findings

For each finding, assign one status:

- `accepted`: evidence supports the finding and the draft should change
- `rejected`: the finding is not supported after rechecking the evidence
- `blocked`: the finding cannot be resolved because evidence is missing or ambiguous

Record the status in `revision-log.md`.

## 3. Apply Minimal Repairs

Prefer:

- correcting a stage title, goal, or transition
- deleting an unsupported stage or transition
- merging or splitting stages only when the finding and evidence justify it
- downgrading unsupported feature links to textual descriptions
- leaving an outcome or inference field empty when the finding is right but replacement evidence is still too weak

Avoid:

- broad rewrites unrelated to the findings
- changing stable IDs without necessity
- adding new unsupported detail just to keep the workflow looking complete

## 4. Update Working Artifacts

When a repair materially changes the interpretation:

- update the relevant stage dossier
- update `workflow-skeleton.json` when stage structure or ordering changes
- update `linking-candidates.json` when feature grounding changes
- record the rationale in the revision log

## 5. Knowledge Capture

If the revision reveals a reusable issue:

- write a new candidate file or append to an existing paper-named file under `../../knowledge/va-intended-workflow/experience-candidates/`
- use `<paper>.jsonl` as the default filename
- include enough context to show whether it is new, weakly covered, or already well covered

Default to writing an `experience-candidates` entry when:

- explicit human feedback identifies a problem that is not clearly covered by current stable patterns
- the revision requires a new boundary judgment or repair strategy that is not clearly covered by current stable patterns
- the issue appears to be a new subtype or new location of an existing pattern, even if it may later remain below the promotion threshold for `failure-patterns.md`

Update `../../knowledge/va-intended-workflow/failure-patterns.md` only when:

- the issue is a stable new pattern not yet covered, or
- the issue is already covered but still rare enough that the current wording should be strengthened

Do not update `failure-patterns.md` when:

- the issue is already clearly covered, and
- the pattern is already observed often enough that another mention adds little value

## 6. Finalize

- write `intended-workflow/output/paper-workflow-spec.json`
- write `intended-workflow/output/revision-log.md`
- validate against `../../../schemas/intended_workflow_schema.py`
- use a fresh `$review-va-intended-workflow` pass only when a separate additional audit is explicitly requested or clearly warranted by substantial changes
