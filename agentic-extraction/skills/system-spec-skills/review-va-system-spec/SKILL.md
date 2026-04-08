---
name: review-va-system-spec
description: Review draft or completed visual analytics system specifications against paper evidence and report unsupported claims, weak view modeling, over-precise style annotations, and invalid coordination. Use when Codex needs to audit a VA SystemSpec rather than extract or repair it.
---

# Review VA System Spec

## Overview

Review an existing VA `SystemSpec` draft or final artifact without repairing it. Findings are the primary output. Prefer a preprocess summary as the entry file, then use the referenced passages, captions, interface crops, working artifacts, and the repository schema to identify unsupported or weak claims.

Do not silently patch the draft in review mode.

## Use This Skill

Follow this skill when the user asks to:

- review a draft or completed VA `SystemSpec`
- verify whether an extraction overstates the evidence
- audit mark types, sub-view decomposition, or coordination claims
- check whether a `SystemSpec` is defensible before acceptance

## Required Inputs

Expect these artifacts before the review loop starts:

- a draft or completed `SystemSpec` JSON
- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- the system-spec extraction run directory when available, preferably `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec`
- `../../../schemas/system_spec_schema.py`

Treat the preprocess summary as the entry file for repository-level evidence, and treat the `system-spec` run directory as the primary working-state evidence layer when it exists.

If the preprocess summary is missing, or if the run directory points to missing supporting artifacts, report the exact missing file instead of issuing weak findings.

## Operating Rules

- Findings come first. Do not revise the draft unless the user explicitly switches to `$revise-va-system-spec`.
- Use passages and captions as the primary evidence for semantic claims, naming, and coordination logic.
- Use interface figures and crops as the primary evidence for `markType`, coarse layout, sub-view boundaries, and visually grounded control placement.
- When text and figure evidence conflict, record the conflict explicitly and explain which source is stronger for the field under review.
- Treat workflow sequence and case-study narration as weak evidence unless the paper supports an actual UI dependency.
- Check whether coordination targets point to the component that the text says actually updates.
- Distinguish paper-specific problems from general failure patterns.
- When a new reusable failure pattern is discovered, write a candidate file or append to an existing paper-named file under [../../knowledge/va-system-spec/experience-candidates](../../knowledge/va-system-spec/experience-candidates) instead of editing any skill directly. Use `<paper>.jsonl` as the default naming rule.
- Read [../../knowledge/va-system-spec/failure-patterns.md](../../knowledge/va-system-spec/failure-patterns.md) before finalizing the review.

## Workflow

Use the detailed procedure in [checklist.md](references/checklist.md).
Read [artifacts.md](references/artifacts.md) before the first review step.

Typical sequence:

1. Load the draft plus supporting artifacts.
2. Run schema validation and basic integrity checks.
3. Audit view and sub-view identity, naming, and evidence grounding.
4. Audit style claims against the crops.
5. Audit view-linked processing claims, including suspicious `null` values.
6. Audit coordination claims against passages first, then use figure evidence to confirm or challenge spatial assumptions, including likely omissions.
7. Audit system-level metadata for overfilling or drift.
8. Write findings to `system-spec/output/review-findings.json` and `system-spec/output/review-report.md`.
9. Append new lesson candidates to the shared experience pool when justified.

## Outputs

Produce:

- structured findings in `<run-dir>/system-spec/output/review-findings.json` when working in a run directory
- a human-readable report in `<run-dir>/system-spec/output/review-report.md`
- optional new or updated candidate files under [../../knowledge/va-system-spec/experience-candidates](../../knowledge/va-system-spec/experience-candidates)

## Failure Handling

- If the draft cannot be grounded because inputs are missing, report the missing artifact rather than issuing weak findings.
- If a claim is ambiguous, downgrade confidence rather than turning the ambiguity into a false positive.
- If a finding suggests the draft should be fixed, report the finding and use [$revise-va-system-spec](../revise-va-system-spec/SKILL.md) only as a separate, explicitly requested step.
