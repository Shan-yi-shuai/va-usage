# Inference Policy

The intended workflow layer often mixes explicit and inferred structure.

## Use `Explicit`

When the paper directly states:

- the workflow
- the stage goal
- the sequence of use
- the purpose of a stage

## Use Conservative Inference

Use `WeakInference`, `FigureGroundedInference`, or `CrossModalSynthesis` only when:

- the workflow structure is strongly implied by multiple passages
- captions and figures clarify stage boundaries
- the system spec helps ground view usage

## Do Not Over-Infer

Do not invent:

- extra workflow branches
- stage rationale absent from the paper
- canonical feature links unsupported by system spec
- a workflow when the paper only provides a concrete example
