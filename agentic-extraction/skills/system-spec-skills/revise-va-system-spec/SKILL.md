---
name: revise-va-system-spec
description: Revise draft visual analytics system specifications using explicit review findings and paper evidence. Use when Codex needs to repair a VA SystemSpec after review rather than extract or audit it from scratch.
---

# Revise VA System Spec

## Overview

Revise a VA `SystemSpec` draft using explicit review findings, optional human feedback from the run directory, working artifacts, and paper evidence. This skill has three responsibilities:

1. apply supported fixes to the current draft
2. record new candidate experience when the revision reveals a reusable issue
3. update stable failure patterns only when the revision justifies a knowledge-base change

It does not silently ignore review findings or turn revision into a fresh extraction pass.

## Use This Skill

Follow this skill when the user asks to:

- fix a VA `SystemSpec` after review
- apply human review findings to an extraction
- repair unsupported claims while preserving stable IDs and evidence discipline
- record reusable lessons discovered during revision

## Required Inputs

Expect these artifacts before revision starts:

- the draft `SystemSpec`
- review findings from Codex or a human
- optional human feedback file at `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/working/human-feedback.md`
- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- the system-spec extraction run directory, preferably `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec`
- `../../../schemas/system_spec_schema.py`

Treat the preprocess summary as the entry file for repository-level evidence, and treat the `system-spec` run directory as the primary working-state evidence layer for localized context and prior decisions.
If `system-spec/working/human-feedback.md` exists, read it and treat it as explicit human revision guidance. If it does not exist, continue without it.

If the preprocess summary is missing, or if the run directory points to missing supporting artifacts, report the exact missing file instead of improvising a broad re-extraction.

## Operating Rules

- Treat explicit human feedback as the highest-priority revision input. Use review findings as secondary guidance, and do not override explicit human feedback unless the paper evidence clearly contradicts it.
- Apply only changes that the accepted findings, human feedback, and paper evidence support.
- Preserve `viewId` and `subViewId` whenever possible.
- Prefer deleting or weakening unsupported claims to inventing replacement details.
- Record a new candidate file or append to an existing paper-named file under [../../knowledge/va-system-spec/experience-candidates](../../knowledge/va-system-spec/experience-candidates) whenever human feedback or revision work reveals a reusable issue that is not already captured clearly enough by the current stable rules. Use `<paper>.jsonl` as the default naming rule.
- If explicit human feedback exposes a gap that is not clearly covered by current `failure-patterns.md`, default to writing an `experience-candidates` entry even when the issue has not yet been promoted to a stable pattern.
- Update [../../knowledge/va-system-spec/failure-patterns.md](../../knowledge/va-system-spec/failure-patterns.md) only when one of these conditions holds:
  - the revision reveals a stable failure pattern that is not yet covered
  - the pattern is already covered but the current wording is too weak for a still-rare issue
  - do not update it when the pattern is already clearly covered and repeatedly observed
- Keep `failure-patterns.md` updates minimal and local to the affected pattern rather than rewriting the whole file.

## Workflow

Use the detailed procedure in [revision-policy.md](references/revision-policy.md).
Read [artifacts.md](references/artifacts.md) before the first revision step.

Typical sequence:

1. Load the draft, findings, and supporting artifacts.
2. Confirm which findings are accepted, disputed, or blocked by missing evidence.
3. Apply the minimal supported changes to the draft and working artifacts.
4. Record reusable new issues under `experience-candidates/` when justified.
5. Update `failure-patterns.md` only when the revision meets the explicit promotion conditions above.
6. Write `system-spec/output/system-spec.json` and `system-spec/output/revision-log.md`.
7. Revalidate the repaired output against `../../../schemas/system_spec_schema.py`.
8. Stop at the revised output. Use `$review-va-system-spec` again only as a separate, explicitly requested step when an additional audit is needed.

## Outputs

Produce:

- revised `<run-dir>/system-spec/output/system-spec.json`
- `<run-dir>/system-spec/output/revision-log.md`
- optional new or updated candidate files under [../../knowledge/va-system-spec/experience-candidates](../../knowledge/va-system-spec/experience-candidates)
- optional targeted updates to [../../knowledge/va-system-spec/failure-patterns.md](../../knowledge/va-system-spec/failure-patterns.md) when the promotion conditions are met

## Failure Handling

- If a review finding cannot be evaluated because evidence is missing, record it as unresolved rather than guessing.
- If a repair would require changing stable IDs, explain why before doing so.
- If multiple repairs conflict, prefer the one with stronger evidence and record the conflict in the revision log.
