---
name: review-va-intended-workflow
description: Review a draft intended workflow extraction for evidence quality, segmentation quality, and confusion with processing pipelines or actual case-study usage.
---

# Review VA Intended Workflow

## Overview

Audit a draft `PaperWorkflowSpec`. Do not revise the draft in this skill. Produce findings and supporting evidence only.

## Use This Skill

Follow this skill when the user asks to:

- review an intended workflow draft
- verify workflow-stage segmentation
- check whether workflow transitions and feature linkage are evidence-backed
- separate author-intended workflow from processing pipeline or actual case-study behavior

## Required Inputs

- draft `paper-workflow-spec.draft.json`
- a preprocess summary markdown file, preferably `agentic-extraction/data/preprocess-summaries/<Paper>.md`
- an existing system specification at `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`
- the intended-workflow run directory when available, preferably `agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow`
- `../../../schemas/intended_workflow_schema.py`

Treat the preprocess summary as the entry file for repository-level evidence, and treat the `intended-workflow` run directory as the primary working-state evidence layer when it exists.

## Operating Rules

- Findings are the primary output.
- Do not silently fix the draft.
- Review from an adversarial perspective.
- Prefer deletion or downgrade over unsupported precision.
- Use [checklist.md](references/checklist.md) as the default audit sequence.
- Read [../../knowledge/va-intended-workflow/failure-patterns.md](../../knowledge/va-intended-workflow/failure-patterns.md) before concluding the review.

## Outputs

Produce:

- `intended-workflow/output/review-findings.json`
- `intended-workflow/output/review-report.md`

If a new recurring issue is discovered, record it under `../../knowledge/va-intended-workflow/experience-candidates/` rather than editing skill rules directly.
