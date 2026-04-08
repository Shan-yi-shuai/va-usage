# VA Intended Workflow Skill Guide

This document is for readers who are new to the current architecture. Its goal is to explain how to use the three skills and the shared knowledge layer to extract a reliable author-intended VA workflow specification.

## 1. Overview

The workflow is split into three stages:

- `extract-va-intended-workflow`
  - produces a draft, not a final result
- `review-va-intended-workflow`
  - audits the draft and reports findings
- `revise-va-intended-workflow`
  - revises the draft using review findings

This layer focuses on:

- author-intended usage paths
- stage-based workflow structure
- recommended transitions between stages
- linkage to system-spec design elements

It is not:

- a backend processing pipeline
- the actual path taken in a concrete case study

Shared knowledge lives in:

- [failure-patterns.md](../knowledge/va-intended-workflow/failure-patterns.md)
- [experience-candidates](../knowledge/va-intended-workflow/experience-candidates)
- [promotion-log.md](../knowledge/va-intended-workflow/promotion-log.md)

All outputs must conform to [intended_workflow_schema.py](../../schemas/intended_workflow_schema.py).

## 2. Required Inputs

Preferred entry file:

- `agentic-extraction/data/preprocess-summaries/<Paper>.md`

Underlying artifacts typically include:

- `data/papers/<Paper>.pdf`
- `data/passages/<Paper>_passages.json`
- overview, interface, or workflow figures and captions
- `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`

A typical paper-level run directory is:

- `agentic-extraction/data/agentic/extract-results/<Paper>/`

Recommended intended-workflow layout:

- `intended-workflow/working/`
- `intended-workflow/output/`

## 3. Invocation Templates

If the session does not resolve skill names automatically, use explicit paths:

- `agentic-extraction/skills/intended-workflow/extract-va-intended-workflow`
- `agentic-extraction/skills/intended-workflow/review-va-intended-workflow`
- `agentic-extraction/skills/intended-workflow/revise-va-intended-workflow`

### 3.1 Extract

```text
Use the skill at agentic-extraction/skills/intended-workflow/extract-va-intended-workflow to extract a draft PaperWorkflowSpec.
Inputs:
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/paper-workflow-spec.draft.json
Constraints:
- treat the preprocess summary as the single entry file
- write working artifacts under agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow
- stop at the draft stage
- do not run review
```

### 3.2 Review

```text
Use the skill at agentic-extraction/skills/intended-workflow/review-va-intended-workflow to review agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/paper-workflow-spec.draft.json.
Inputs:
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/review-findings.json
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/review-report.md
Constraints:
- treat the preprocess summary as the single entry file for repository-level evidence
- use the run directory as the primary working-state evidence layer
- do not revise the draft
```

### 3.3 Revise

```text
Use the skill at agentic-extraction/skills/intended-workflow/revise-va-intended-workflow to revise agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/paper-workflow-spec.draft.json.
Inputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/review-findings.json
- HumanFeedback: agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/working/human-feedback.md
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/paper-workflow-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/output/revision-log.md
Constraints:
- treat the preprocess summary as the single entry file for repository-level evidence
- use the run directory as the primary working-state evidence layer
- if `agentic-extraction/data/agentic/extract-results/<Paper>/intended-workflow/working/human-feedback.md` exists, read it; otherwise ignore human feedback
- revise from findings instead of re-extracting from scratch
```

## 4. The Three Skills

### 4.1 `extract-va-intended-workflow`

Entry file:

- [SKILL.md](../skills/intended-workflow/extract-va-intended-workflow/SKILL.md)

Related files:

- [workflow.md](../skills/intended-workflow/extract-va-intended-workflow/references/workflow.md)
- [schema-layering.md](../skills/intended-workflow/extract-va-intended-workflow/references/schema-layering.md)
- [segmentation.md](../skills/intended-workflow/extract-va-intended-workflow/references/segmentation.md)
- [inference-policy.md](../skills/intended-workflow/extract-va-intended-workflow/references/inference-policy.md)
- [artifacts.md](../skills/intended-workflow/extract-va-intended-workflow/references/artifacts.md)
- [intended_workflow_schema.py](../../schemas/intended_workflow_schema.py)

Responsibilities:

- detect intended workflow evidence
- build workflow, stage, and transition structure
- distinguish intended workflow from processing pipeline
- link stages to views or system features when supported
- write `paper-workflow-spec.draft.json`

### 4.2 `review-va-intended-workflow`

Entry file:

- [SKILL.md](../skills/intended-workflow/review-va-intended-workflow/SKILL.md)

Related files:

- [checklist.md](../skills/intended-workflow/review-va-intended-workflow/references/checklist.md)
- [failure-patterns.md](../knowledge/va-intended-workflow/failure-patterns.md)
- [experience-candidates](../knowledge/va-intended-workflow/experience-candidates)
- [intended_workflow_schema.py](../../schemas/intended_workflow_schema.py)

Responsibilities:

- verify that an intended workflow really exists
- detect confusion with processing pipelines
- audit stage segmentation
- audit transition quality
- audit system-spec linkage

### 4.3 `revise-va-intended-workflow`

Entry file:

- [SKILL.md](../skills/intended-workflow/revise-va-intended-workflow/SKILL.md)

Related files:

- [revision-policy.md](../skills/intended-workflow/revise-va-intended-workflow/references/revision-policy.md)
- [failure-patterns.md](../knowledge/va-intended-workflow/failure-patterns.md)
- [experience-candidates](../knowledge/va-intended-workflow/experience-candidates)
- [intended_workflow_schema.py](../../schemas/intended_workflow_schema.py)

Responsibilities:

- revise the draft using findings
- remove unsupported stages, transitions, or links
- preserve stable ids where possible
- write `paper-workflow-spec.json` and `revision-log.md`

## 5. How the Skills Fit Together

The basic flow is:

- `extract` produces a draft
- `review` evaluates the draft
- `revise` updates the draft

This layer sits between the other two schema families:

- `system specification`
  - what the system contains
- `intended workflow`
  - how the designers expect it to be used
- `usage case`
  - how it is actually used in a concrete analysis
