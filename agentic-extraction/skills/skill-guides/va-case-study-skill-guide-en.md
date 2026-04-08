# VA Case Study Skill Guide

This document is for people who are new to the current architecture. Its purpose is to explain how to use the three case-study skills and the shared knowledge layer to produce a reliable VA case study specification.

## 1. Overview

The workflow is split into three stages:

- `extract-va-case-study`
  - builds a draft
- `review-va-case-study`
  - audits the draft
- `revise-va-case-study`
  - repairs the draft using review findings

Compared with system-spec extraction, case-study extraction places more weight on:

- case / episode / step segmentation
- reasoning structure recovery
- conservative inference
- grounded linkage to an existing system specification

Shared knowledge lives in:

- [failure-patterns.md](../knowledge/va-case-study/failure-patterns.md)
- [experience-candidates](../knowledge/va-case-study/experience-candidates)
- [promotion-log.md](../knowledge/va-case-study/promotion-log.md)

All outputs must conform to [case_study_schema.py](../../schemas/case_study_schema.py).

## 2. Expected Inputs

Preferred entry file:

- `agentic-extraction/data/preprocess-summaries/<Paper>.md`

Underlying artifacts typically include:

- `data/papers/<Paper>.pdf`
- `data/passages/<Paper>_passages.json`
- case-study figure or caption artifacts when available
- `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json`

Recommended paper-level run directory:

- `agentic-extraction/data/agentic/extract-results/<Paper>/`

Recommended case-study layout:

- `case-study/working/`
- `case-study/output/`

## 3. Standard Invocation Templates

If the session does not automatically resolve `$extract-va-case-study`-style names, use explicit repository paths:

- `agentic-extraction/skills/case-study/extract-va-case-study`
- `agentic-extraction/skills/case-study/review-va-case-study`
- `agentic-extraction/skills/case-study/revise-va-case-study`

### Extract

```text
Use the skill at agentic-extraction/skills/case-study/extract-va-case-study to extract a draft PaperUsageSpec.
Inputs:
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/paper-usage-spec.draft.json
Constraints:
- treat the preprocess summary as the single entry file
- write working artifacts under agentic-extraction/data/agentic/extract-results/<Paper>/case-study
- stop at the draft stage
- do not run review
```

### Review

```text
Use the skill at agentic-extraction/skills/case-study/review-va-case-study to review agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/paper-usage-spec.draft.json.
Inputs:
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/review-findings.json
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/review-report.md
Constraints:
- treat the preprocess summary as the single entry file for repository-level evidence
- use the run directory as the primary working-state evidence layer
- do not revise the draft
```

### Revise

```text
Use the skill at agentic-extraction/skills/case-study/revise-va-case-study to revise agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/paper-usage-spec.draft.json.
Inputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/review-findings.json
- HumanFeedback: agentic-extraction/data/agentic/extract-results/<Paper>/case-study/working/human-feedback.md
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/paper-usage-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/case-study/output/revision-log.md
Constraints:
- treat the preprocess summary as the single entry file for repository-level evidence
- use the run directory as the primary working-state evidence layer
- if `agentic-extraction/data/agentic/extract-results/<Paper>/case-study/working/human-feedback.md` exists, read it; otherwise ignore human feedback
- revise from findings instead of re-extracting from scratch
```

## 4. Skill Roles

### `extract-va-case-study`

Entry file:

- [case-study/extract-va-case-study/SKILL.md](../skills/case-study/extract-va-case-study/SKILL.md)

Key references:

- [workflow.md](../skills/case-study/extract-va-case-study/references/workflow.md)
- [schema-layering.md](../skills/case-study/extract-va-case-study/references/schema-layering.md)
- [segmentation.md](../skills/case-study/extract-va-case-study/references/segmentation.md)
- [inference-policy.md](../skills/case-study/extract-va-case-study/references/inference-policy.md)
- [artifacts.md](../skills/case-study/extract-va-case-study/references/artifacts.md)

Responsibilities:

- detect case-study boundaries
- build case / episode / step skeletons
- enrich reasoning structure
- link supported steps to the system specification
- write `paper-usage-spec.draft.json`

### `review-va-case-study`

Entry file:

- [case-study/review-va-case-study/SKILL.md](../skills/case-study/review-va-case-study/SKILL.md)

Key references:

- [checklist.md](../skills/case-study/review-va-case-study/references/checklist.md)
- [artifacts.md](../skills/case-study/review-va-case-study/references/artifacts.md)
- [failure-patterns.md](../knowledge/va-case-study/failure-patterns.md)

Responsibilities:

- audit segmentation quality
- audit reasoning inflation
- audit transition validity
- audit view and capability linkage
- write findings and a review report
- write reusable issues to `experience-candidates/<paper>.jsonl` when justified

### `revise-va-case-study`

Entry file:

- [case-study/revise-va-case-study/SKILL.md](../skills/case-study/revise-va-case-study/SKILL.md)

Key references:

- [revision-policy.md](../skills/case-study/revise-va-case-study/references/revision-policy.md)
- [artifacts.md](../skills/case-study/revise-va-case-study/references/artifacts.md)
- [failure-patterns.md](../knowledge/va-case-study/failure-patterns.md)

Responsibilities:

- repair the draft using findings
- preserve stable identifiers when possible
- delete unsupported high-inference fields
- write `paper-usage-spec.json` and `revision-log.md`
- write reusable issues to `experience-candidates/<paper>.jsonl` when justified
- update `failure-patterns.md` only when the explicit promotion conditions are met
