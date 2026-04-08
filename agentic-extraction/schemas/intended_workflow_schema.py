from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.schemas.schema_common import (
    CapabilityRef,
    CoordinationRef,
    EvidenceReference,
    IdentifierString,
    OthersString,
    ViewRef,
    _dedupe_strings,
    _make_unique_identifier,
    _slugify_identifier,
)


WorkflowKind = Union[
    Literal[
        "OverviewToDetail",
        "ComparativeAnalysis",
        "HypothesisTesting",
        "MonitoringAndTriaging",
        "ExploratoryAnalysis",
        "ScenarioWalkthrough",
        "DecisionSupport",
    ],
    OthersString,
]

WorkflowTransitionType = Union[
    Literal[
        "Next",
        "Branch",
        "Iterate",
        "Backtrack",
        "Refine",
        "Confirm",
        "Abandon",
        "DrillDown",
        "Broaden",
        "Synthesize",
        "Report",
    ],
    OthersString,
]

InferenceType = Union[
    Literal[
        "Explicit",
        "WeakInference",
        "StrongInference",
        "FigureGroundedInference",
        "CrossModalSynthesis",
    ],
    OthersString,
]


def _dedupe_view_refs(values: Optional[List[ViewRef]]) -> Optional[List[ViewRef]]:
    if not values:
        return None

    result: List[ViewRef] = []
    seen: set[tuple[str, Optional[str]]] = set()
    for item in values:
        key = (item.viewId, item.subViewId)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result or None


def _dedupe_capability_refs(values: Optional[List[CapabilityRef]]) -> Optional[List[CapabilityRef]]:
    if not values:
        return None

    result: List[CapabilityRef] = []
    seen: set[tuple[str, str, str]] = set()
    for item in values:
        key = (
            item.viewId,
            item.subViewId,
            item.capabilityId,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result or None


class WorkflowCoordinationRef(CoordinationRef):
    """Lightweight coordination linkage for intended workflow stages."""


def _dedupe_coordination_refs(
    values: Optional[List["WorkflowCoordinationRef"]],
) -> Optional[List["WorkflowCoordinationRef"]]:
    if not values:
        return None

    result: List[WorkflowCoordinationRef] = []
    seen: set[tuple[object, ...]] = set()
    for item in values:
        key = (
            item.coordinationId,
            item.description,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result or None


class WorkflowStage(BaseModel):
    """A design-intended local phase, expressed as a stage-level usage summary."""

    stageId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable identifier of the workflow stage.",
    )

    stageIndex: Optional[int] = Field(
        default=None,
        ge=1,
        description="1-based order of the stage within the workflow.",
    )

    stageTitle: Optional[str] = Field(
        default=None,
        description="Short title of the intended stage when the paper names it explicitly.",
    )

    stageGoal: Optional[str] = Field(
        default=None,
        description="Main analytic goal of this intended stage.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Free-text description of what the stage is meant to accomplish.",
    )

    usedViews: Optional[List[ViewRef]] = Field(
        default=None,
        description=(
            "Views or sub-views expected to be used during this stage. "
            "This is a stage-level intended usage summary, not a step-level trace."
        ),
    )

    usedCapabilities: Optional[List[CapabilityRef]] = Field(
        default=None,
        description=(
            "Subview capabilities expected to be used in this stage. "
            "These capture intended usage of subview-internal functions."
        ),
    )

    usedCoordinations: Optional[List[WorkflowCoordinationRef]] = Field(
        default=None,
        description=(
            "Coordinations the stage is expected to rely on. "
            "These capture intended cross-view behavior beyond individual subviews."
        ),
    )

    expectedOutcome: Optional[str] = Field(
        default=None,
        description="Expected result or decision support outcome of the stage.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence supporting this intended stage.",
    )

    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the stage is directly stated or inferred from the paper.",
    )

    @model_validator(mode="after")
    def validate_payload(self):
        self.usedViews = _dedupe_view_refs(self.usedViews)
        self.usedCapabilities = _dedupe_capability_refs(self.usedCapabilities)
        self.usedCoordinations = _dedupe_coordination_refs(self.usedCoordinations)

        used_view_keys = {
            (view.viewId, view.subViewId)
            for view in self.usedViews or []
        }

        for capability in self.usedCapabilities or []:
            used_view_keys.add((capability.viewId, capability.subViewId))

        if used_view_keys:
            self.usedViews = [
                ViewRef(viewId=view_id, subViewId=subview_id)
                for view_id, subview_id in sorted(used_view_keys)
            ]

        if (
            not self.stageTitle
            and not self.stageGoal
            and not self.description
            and not self.usedViews
            and not self.usedCapabilities
            and not self.usedCoordinations
            and not self.expectedOutcome
        ):
            raise ValueError(
                "WorkflowStage requires at least one semantic content field."
            )
        return self


class WorkflowTransition(BaseModel):
    """A transition between intended workflow stages."""

    sourceStageId: IdentifierString = Field(
        ...,
        description="Source stage identifier.",
    )

    targetStageId: IdentifierString = Field(
        ...,
        description="Target stage identifier.",
    )

    transitionType: WorkflowTransitionType = Field(
        ...,
        description="Type of intended transition between stages.",
    )

    rationale: Optional[str] = Field(
        default=None,
        description="Why the workflow is expected to move from the source stage to the target stage.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence supporting the transition.",
    )

    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the transition is explicit or inferred.",
    )


class WorkflowClaim(BaseModel):
    """Paper-level claim about the intended workflow."""

    claimText: str = Field(
        ...,
        description="High-level author claim about how the system is intended to be used.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence supporting the workflow-level claim.",
    )

    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the claim is directly stated or inferred.",
    )


class WorkflowSpec(BaseModel):
    """A single author-intended workflow described in a paper."""

    workflowId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable identifier of the intended workflow.",
    )

    workflowTitle: Optional[str] = Field(
        default=None,
        description="Title or name of the intended workflow.",
    )

    workflowKind: Optional[WorkflowKind] = Field(
        default=None,
        description="High-level type of intended workflow.",
    )

    workflowGoal: str = Field(
        ...,
        description="Main goal of the intended workflow.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Free-text summary of the author-intended workflow.",
    )

    targetUsers: Optional[List[str]] = Field(
        default=None,
        description="Target user group(s) for this intended workflow when stated in the paper.",
    )

    stages: List[WorkflowStage] = Field(
        ...,
        description="Ordered stages of the intended workflow.",
    )

    transitions: Optional[List[WorkflowTransition]] = Field(
        default=None,
        description="Explicit or inferred transitions between workflow stages.",
    )

    expectedFinalOutcome: Optional[str] = Field(
        default=None,
        description="Expected final outcome if the workflow completes successfully.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence supporting the workflow as a whole.",
    )

    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the workflow is explicitly described or synthesized.",
    )

    @field_validator("targetUsers", mode="before")
    @classmethod
    def normalize_target_users(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_workflow(self):
        self.targetUsers = _dedupe_strings(self.targetUsers)
        if not self.stages:
            raise ValueError("WorkflowSpec requires at least one stage.")

        self.workflowId = self.workflowId or _slugify_identifier(
            self.workflowTitle or self.workflowGoal,
            "workflow",
        )

        seen_stage_ids: set[str] = set()
        for index, stage in enumerate(self.stages, start=1):
            if stage.stageIndex is None:
                stage.stageIndex = index
            elif stage.stageIndex != index:
                raise ValueError(
                    "WorkflowStage.stageIndex must be contiguous and match the list order."
                )

            if stage.stageId is None:
                base = _slugify_identifier(
                    stage.stageTitle or stage.stageGoal or f"stage-{index}",
                    f"stage-{index}",
                )
                stage.stageId = _make_unique_identifier(base, seen_stage_ids)
            else:
                stage.stageId = _make_unique_identifier(stage.stageId, seen_stage_ids)

        stage_ids = {stage.stageId for stage in self.stages}
        if self.transitions:
            seen_edges: set[tuple[str, str, str]] = set()
            deduped_transitions: List[WorkflowTransition] = []
            for transition in self.transitions:
                if transition.sourceStageId not in stage_ids:
                    raise ValueError(
                        f"Transition sourceStageId '{transition.sourceStageId}' does not exist."
                    )
                if transition.targetStageId not in stage_ids:
                    raise ValueError(
                        f"Transition targetStageId '{transition.targetStageId}' does not exist."
                    )
                key = (
                    transition.sourceStageId,
                    transition.targetStageId,
                    str(transition.transitionType),
                )
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                deduped_transitions.append(transition)
            self.transitions = deduped_transitions or None

        return self


class PaperWorkflowSpec(BaseModel):
    """All author-intended workflows extracted from one VA paper."""

    paperName: str = Field(
        ...,
        description="Short paper identifier used in the project.",
    )

    systemName: Optional[str] = Field(
        default=None,
        description="Name of the system discussed in the paper.",
    )

    systemSpecPath: Optional[str] = Field(
        default=None,
        description="Relative path to the corresponding system specification file, if available.",
    )

    workflows: List[WorkflowSpec] = Field(
        ...,
        description="Author-intended workflows described in the paper.",
    )

    paperLevelClaims: Optional[List[WorkflowClaim]] = Field(
        default=None,
        description="Higher-level claims about intended usage that apply across workflows.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence supporting the workflow extraction at paper level.",
    )

    @model_validator(mode="after")
    def validate_payload(self):
        if not self.workflows:
            raise ValueError("PaperWorkflowSpec requires at least one workflow.")

        seen_workflow_ids: set[str] = set()
        for workflow in self.workflows:
            workflow.workflowId = _make_unique_identifier(workflow.workflowId, seen_workflow_ids)
        return self
