---
name: review-va-case-study
description: Review draft or completed visual analytics case study specifications against paper evidence and report segmentation mistakes, over-inference, weak reasoning structure, and unsupported view/capability linkage. Use when Codex needs to audit a PaperUsageSpec rather than extract or repair it.
---

# Review VA Case Study

## Overview

Review an existing `PaperUsageSpec` draft or final artifact without repairing it. Findings are the primary output. Prefer a preprocess summary as the entry file, then use passages, case-study figures and captions, `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`, and working state to identify unsupported or weak claims.

Do not silently patch the draft in review mode.

## Use This Skill

Follow this skill when the user asks to:

- review a draft or completed case study extraction
- verify whether a case narrative was over-structured
- audit case / episode / step segmentation
- check whether reasoning, transitions, or design linkage are defensible

## Required Inputs

Expect these artifacts before review starts:

- a draft `agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/paper-usage-spec.draft.json` JSON
- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- the linked system specification when available, preferably `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`
- the case-study run directory when available, preferably `agentic-extraction/data/agentic/extract-results/<Paper>/case-study`
- `../../../schemas/case_study_schema.py`

Treat the preprocess summary as the entry file for repository-level evidence, and treat the `case-study` run directory as the primary working-state evidence layer when it exists.

## Operating Rules

- Findings come first. Do not revise the draft unless the user explicitly switches to `$revise-va-case-study`.
- Use passages and captions as the primary evidence for segmentation, reasoning structure, transition logic, and local goals.
- Use case-study figures as the primary evidence for step boundaries, used views, and visually grounded observations.
- Use `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json` as the primary evidence for canonical view and capability linkage.
- When text, figure, and system-spec evidence conflict, record the conflict explicitly and explain which source is stronger for the field under review.
- Treat segmentation quality as a first-class review target.
- Distinguish observation, insight, and decision; do not accept inflated reasoning structure.
- Treat plain narrative order as weak evidence for explicit transitions.
- Audit whether view and capability linkage is grounded in the system specification or merely guessed from prose.
- Separate paper-specific problems from reusable failure patterns.
- When a reusable new failure pattern is discovered, write a candidate file or append to an existing paper-named file under [../../knowledge/va-case-study/experience-candidates](../../knowledge/va-case-study/experience-candidates) instead of editing any skill directly. Use `<paper>.jsonl` as the default naming rule.
- Read [../../knowledge/va-case-study/failure-patterns.md](../../knowledge/va-case-study/failure-patterns.md) before finalizing the review.

## Workflow

Use the detailed procedure in [checklist.md](references/checklist.md).
Read [artifacts.md](references/artifacts.md) before the first review step.

Typical sequence:

1. Load the draft plus supporting artifacts.
2. Run schema validation and basic integrity checks.
3. Audit case / episode / step segmentation.
4. Audit core semantic fields and reasoning structure.
5. Audit transitions, friction, and state reconstruction.
6. Audit view and capability linkage against the system specification.
7. Write findings to `case-study/output/review-findings.json` and `case-study/output/review-report.md`.
8. Append new lesson candidates when justified.

## Outputs

Produce:

- structured findings in `<run-dir>/case-study/output/review-findings.json` when working in a run directory
- a human-readable report in `<run-dir>/case-study/output/review-report.md`
- optional new or updated candidate files under [../../knowledge/va-case-study/experience-candidates](../../knowledge/va-case-study/experience-candidates)

## Failure Handling

- If the draft cannot be grounded because inputs are missing, report the missing artifact rather than issuing weak findings.
- If a segmentation choice is plausible but ambiguous, record the ambiguity rather than forcing a hard failure.
- If a finding suggests the draft should be fixed, report the finding and use [$revise-va-case-study](../revise-va-case-study/SKILL.md) only as a separate, explicitly requested step.
