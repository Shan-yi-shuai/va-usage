# VA System Spec Skill Guide

This document describes how to use the three-skill workflow for extracting reliable visual analytics system specifications.

## Overview

The workflow is split into three stages:

- `extract-va-system-spec`
  - produces a draft `SystemSpec`
- `review-va-system-spec`
  - audits the draft against paper evidence
- `revise-va-system-spec`
  - repairs the draft using explicit review findings

All outputs must conform to [system_spec_schema.py](../../schemas/system_spec_schema.py).

Shared knowledge lives under:

- [knowledge/va-system-spec/failure-patterns.md](../knowledge/va-system-spec/failure-patterns.md)
- [knowledge/va-system-spec/experience-candidates](../knowledge/va-system-spec/experience-candidates)
- [knowledge/va-system-spec/promotion-log.md](../knowledge/va-system-spec/promotion-log.md)

## Inputs

Preferred entry file:

- `agentic-extraction/data/preprocess-summaries/<Paper>.md`

Underlying artifacts typically include:

- `data/papers/<Paper>.pdf`
- `data/passages/<Paper>_passages.json`
- `data/view-images/<Paper>/`

Typical paper-level run directory:

- `agentic-extraction/data/agentic/extract-results/<Paper>/`

Recommended schema-layer layout:

- `system-spec/working/`
- `system-spec/output/`
- `intended-workflow/working/`
- `intended-workflow/output/`
- `case-study/working/`
- `case-study/output/`

## Standard Invocation Templates

If a session does not automatically resolve `$extract-va-system-spec`-style names, use the repository skill paths explicitly:

- `agentic-extraction/skills/system-spec/extract-va-system-spec`
- `agentic-extraction/skills/system-spec/review-va-system-spec`
- `agentic-extraction/skills/system-spec/revise-va-system-spec`

### Extract

```text
Use the skill at agentic-extraction/skills/system-spec/extract-va-system-spec to extract a draft SystemSpec.
Inputs:
- agentic-extraction/data/preprocess-summaries/<Paper>.md
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.draft.json
Constraints:
- treat the preprocess summary as the single entry file
- write working artifacts under agentic-extraction/data/agentic/extract-results/<Paper>/system-spec
- stop at the draft stage
- do not run review
```

### Review

```text
Use the skill at agentic-extraction/skills/system-spec/review-va-system-spec to review agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.draft.json.
Inputs:
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/review-findings.json
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/review-report.md
Constraints:
- treat the preprocess summary as the single entry file for repository-level evidence
- use the run directory as the primary working-state evidence layer
- do not revise the draft
```

### Revise

```text
Use the skill at agentic-extraction/skills/system-spec/revise-va-system-spec to revise agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.draft.json.
Inputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/review-findings.json
- HumanFeedback: agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/working/human-feedback.md
- agentic-extraction/data/preprocess-summaries/<Paper>.md
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec
Outputs:
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/system-spec.json
- agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/revision-log.md
Constraints:
- treat the preprocess summary as the single entry file for repository-level evidence
- use the run directory as the primary working-state evidence layer
- if `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/working/human-feedback.md` exists, read it; otherwise ignore human feedback
- revise from findings instead of re-extracting from scratch
```

## Skill Roles

### `extract-va-system-spec`

Entry file:

- [system-spec/extract-va-system-spec/SKILL.md](../skills/system-spec/extract-va-system-spec/SKILL.md)

Related files:

- [workflow.md](../skills/system-spec/extract-va-system-spec/references/workflow.md)
- [artifacts.md](../skills/system-spec/extract-va-system-spec/references/artifacts.md)

Responsibilities:

- build the system map
- resolve views and subviews
- assemble evidence-backed draft fields
- write `system-spec.draft.json`

Not responsible for:

- final claim review
- repairing reviewed findings

### `review-va-system-spec`

Entry file:

- [system-spec/review-va-system-spec/SKILL.md](../skills/system-spec/review-va-system-spec/SKILL.md)

Related files:

- [checklist.md](../skills/system-spec/review-va-system-spec/references/checklist.md)
- [artifacts.md](../skills/system-spec/review-va-system-spec/references/artifacts.md)
- [failure-patterns.md](../knowledge/va-system-spec/failure-patterns.md)
- [experience-candidates](../knowledge/va-system-spec/experience-candidates)

Responsibilities:

- audit evidence support
- use passages and captions first for semantic and relational checks
- use figures and crops for `markType`, layout, and subview-boundary checks
- audit `markType` with image-first checking
- audit coordination validity
- audit system-level metadata for overfilling
- write findings and review report

Not responsible for:

- modifying the draft

### `revise-va-system-spec`

Entry file:

- [system-spec/revise-va-system-spec/SKILL.md](../skills/system-spec/revise-va-system-spec/SKILL.md)

Related files:

- [revision-policy.md](../skills/system-spec/revise-va-system-spec/references/revision-policy.md)
- [artifacts.md](../skills/system-spec/revise-va-system-spec/references/artifacts.md)
- `agentic-extraction/data/agentic/extract-results/<Paper>/system-spec/output/review-findings.json`
- [failure-patterns.md](../knowledge/va-system-spec/failure-patterns.md)

Responsibilities:

- apply accepted findings
- preserve stable IDs when possible
- use passages and captions first for semantic and relational repairs
- use figures and crops for `markType`, layout, and subview-boundary repairs
- weaken or remove unsupported claims
- write `system-spec.json` and `revision-log.md`
- add new candidate files or append to existing paper-level files under `experience-candidates/` when justified
- update `failure-patterns.md` only when the explicit promotion conditions are met

Not responsible for:

- re-extracting from scratch
- changing shared rules during repair

## Collaboration Flow

The skills form a sequential pipeline:

```text
preprocessed inputs
  -> extract
  -> system-spec.draft.json + working artifacts
  -> review
  -> review-findings.json + review-report.md
  -> revise
  -> system-spec.json + revision-log.md
```

If revision is substantial, run review again.

## Shared Knowledge

Shared knowledge is separate from the skills:

- `failure-patterns.md`
  - stable reusable failure patterns
- `experience-candidates/`
  - self-review and human-review lesson candidates
- `promotion-log.md`
  - records candidate promotion into stable shared rules

Skills read this layer. They do not directly replace it.

## Recommended Usage

Use the three skills explicitly and separately:

1. run `extract`
2. run `review`
3. run `revise` if needed
4. record reusable lessons only when justified

Do not combine extraction, review, revision, and knowledge updates into a single request.
