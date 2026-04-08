---
name: revise-va-intended-workflow
description: Revise a draft intended workflow extraction using review findings while preserving stable identifiers and conservative evidence standards.
---

# Revise VA Intended Workflow

## Overview

Revise a draft `PaperWorkflowSpec` using explicit findings from review, optional human feedback from the run directory, working artifacts, and paper evidence. This skill has three responsibilities:

1. apply supported fixes to the current draft
2. record new candidate experience when the revision reveals a reusable issue
3. update stable failure patterns only when the revision justifies a knowledge-base change

It does not silently ignore review findings or turn revision into a fresh extraction pass.

## Use This Skill

Follow this skill when the user asks to:

- revise an intended workflow draft after review
- apply human review findings to an extraction
- remove unsupported stages or transitions
- tighten feature linkage and inference strength
- produce a final intended workflow JSON
- record reusable lessons discovered during revision

## Required Inputs

- draft `paper-workflow-spec.draft.json`
- review findings
- optional human feedback file at `agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/working/human-feedback.md`
- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- an existing system specification at `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`
- the intended-workflow run directory when available, preferably `agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow`
- `../../../schemas/intended_workflow_schema.py`

Treat the preprocess summary as the entry file for repository-level evidence, and treat the `intended-workflow` run directory as the primary working-state evidence layer when it exists.
If `intended-workflow/working/human-feedback.md` exists, read it and treat it as explicit human revision guidance. If it does not exist, continue without it.

## Operating Rules

- Treat explicit human feedback as the highest-priority revision input. Use review findings as secondary guidance, and do not override explicit human feedback unless the paper evidence clearly contradicts it.
- Apply only changes that the accepted findings, human feedback, and paper evidence support.
- Prefer deleting unsupported structure to preserving speculative detail.
- Preserve stable ids when a stage survives revision.
- If a stage is split or merged, document the change in the revision log.
- Record a new candidate file or append to an existing paper-named file under [../../knowledge/va-intended-workflow/experience-candidates](../../knowledge/va-intended-workflow/experience-candidates) whenever human feedback or revision work reveals a reusable issue that is not already captured clearly enough by the current stable rules. Use `<paper>.jsonl` as the default naming rule.
- If explicit human feedback exposes a gap that is not clearly covered by current `failure-patterns.md`, default to writing an `experience-candidates` entry even when the issue has not yet been promoted to a stable pattern.
- Update [../../knowledge/va-intended-workflow/failure-patterns.md](../../knowledge/va-intended-workflow/failure-patterns.md) only when one of these conditions holds:
  - the revision reveals a stable failure pattern that is not yet covered
  - the pattern is already covered but the current wording is too weak for a still-rare issue
  - do not update it when the pattern is already clearly covered and repeatedly observed
- Keep `failure-patterns.md` updates minimal and local to the affected pattern rather than rewriting the whole file.

## Workflow

Use the detailed procedure in [revision-policy.md](references/revision-policy.md).

Typical sequence:

1. Load the draft, findings, and supporting artifacts.
2. Confirm which findings are accepted, disputed, or blocked by missing evidence.
3. Apply the minimal supported changes to the draft and working artifacts.
4. Record reusable new issues under `experience-candidates/` when justified.
5. Update `failure-patterns.md` only when the revision meets the explicit promotion conditions above.
6. Write `intended-workflow/output/paper-workflow-spec.json` and `intended-workflow/output/revision-log.md`.
7. Revalidate the repaired output against `../../../schemas/intended_workflow_schema.py`.
8. Stop at the revised output. Use `$review-va-intended-workflow` again only as a separate, explicitly requested step when an additional audit is needed.

## Outputs

Produce:

- `intended-workflow/output/paper-workflow-spec.json`
- `intended-workflow/output/revision-log.md`
- optional new or updated candidate files under [../../knowledge/va-intended-workflow/experience-candidates](../../knowledge/va-intended-workflow/experience-candidates)
- optional targeted updates to [../../knowledge/va-intended-workflow/failure-patterns.md](../../knowledge/va-intended-workflow/failure-patterns.md) when the promotion conditions are met

## Failure Handling

- If a review finding cannot be evaluated because evidence is missing, record it as unresolved rather than guessing.
- If a repair would require changing stable stage IDs, explain why before doing so.
- If multiple repairs conflict, prefer the one with stronger evidence and record the conflict in the revision log.
