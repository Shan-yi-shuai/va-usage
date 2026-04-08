# Segmentation

The core segmentation question is:

> What is the author-recommended sequence of analytic stages, not what happens in one concrete case?

## Workflow Boundary

Treat a description as intended workflow evidence when it uses language such as:

- users first do X, then Y
- analysts start from the overview and drill down
- the system supports a workflow where ...
- the interface is designed for ...

Do not treat the following as intended workflow by default:

- one-off case-study actions
- retrospective narration of a single example
- backend processing pipelines

## Stage Boundary

A new stage is justified when one or more of these changes:

- the analytic goal
- the primary view or feature set
- the expected outcome
- the role of the user action in the workflow

Do not create a new stage for every interaction detail.

## Transition Boundary

Create transitions only when the paper supports a meaningful workflow move:

- progression
- branching
- refinement
- drill-down
- synthesis

Narrative adjacency alone is not enough.
