from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from loader import (
    _build_step_lookup,
    build_case_manifest,
    build_samples,
    load_system_spec,
    load_workflow_spec,
    resolve_usage_case,
)
from schema_common import IdentifierString


SCHEMA_VERSION = "next-analytic-move.v1"
TASK_NAME = "next_analytic_move_prediction"
DEFAULT_TASK_INSTRUCTION = (
    "Given the system context, intended workflow context, current case background, "
    "ordered prefix episodes, and the corresponding episode images, predict the next "
    "meaningful analytic move. Use canonical ids from the provided context and return "
    "JSON only."
)


def _dedupe_identifiers(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def _normalize_view_ref(ref: dict[str, Any]) -> Optional[str]:
    subview_id = ref.get("subViewId")
    view_id = ref.get("viewId")
    if subview_id:
        return str(subview_id)
    if view_id:
        return str(view_id)
    return None


def _normalize_capability_refs(capabilities: list[dict[str, Any]] | None) -> list[str]:
    capability_ids: list[str] = []
    for capability in capabilities or []:
        capability_id = capability.get("capabilityId")
        if capability_id:
            capability_ids.append(str(capability_id))
    return _dedupe_identifiers(capability_ids)


def _flatten_categories(system_info: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    for item in system_info.get("systemCategory", []) or []:
        level1 = item.get("level1")
        level2_values = item.get("level2", []) or []
        if level1 and level2_values:
            for level2 in level2_values:
                categories.append(f"{level1} > {level2}")
        elif level1:
            categories.append(str(level1))
    return categories


def _coerce_text_list(values: Any, key: str) -> list[str]:
    texts: list[str] = []
    for item in values or []:
        value = item.get(key)
        if value:
            texts.append(str(value))
    return texts


class SystemCapabilityOption(BaseModel):
    capability_id: IdentifierString
    capability_name: str
    capability_kind: Optional[str] = None
    description: Optional[str] = None


class SystemSubViewOption(BaseModel):
    subview_id: IdentifierString
    subview_name: str
    description: Optional[str] = None
    capabilities: list[SystemCapabilityOption] = Field(default_factory=list)


class SystemViewOption(BaseModel):
    view_id: IdentifierString
    view_name: str
    description: Optional[str] = None
    subviews: list[SystemSubViewOption] = Field(default_factory=list)


class CoordinationOption(BaseModel):
    coordination_id: IdentifierString
    coordination_type: Optional[str] = None
    description: Optional[str] = None
    source_id: Optional[IdentifierString] = None
    target_ids: list[IdentifierString] = Field(default_factory=list)

    @field_validator("target_ids", mode="after")
    @classmethod
    def dedupe_target_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class SystemContext(BaseModel):
    system_name: Optional[str] = None
    dataset_types: list[str] = Field(default_factory=list)
    system_categories: list[str] = Field(default_factory=list)
    views: list[SystemViewOption] = Field(default_factory=list)
    coordinations: list[CoordinationOption] = Field(default_factory=list)


class WorkflowStageContext(BaseModel):
    workflow_id: IdentifierString
    stage_id: IdentifierString
    stage_index: int
    stage_title: str
    stage_goal: Optional[str] = None
    description: Optional[str] = None
    used_views: list[IdentifierString] = Field(default_factory=list)
    used_capabilities: list[IdentifierString] = Field(default_factory=list)
    used_coordinations: list[IdentifierString] = Field(default_factory=list)
    expected_outcome: Optional[str] = None

    @field_validator("used_views", "used_capabilities", "used_coordinations", mode="after")
    @classmethod
    def dedupe_stage_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class WorkflowTransitionContext(BaseModel):
    source_stage_id: IdentifierString
    target_stage_id: IdentifierString
    transition_type: str
    rationale: Optional[str] = None


class WorkflowSummary(BaseModel):
    workflow_id: IdentifierString
    workflow_title: str
    workflow_goal: Optional[str] = None
    description: Optional[str] = None
    stages: list[WorkflowStageContext] = Field(default_factory=list)
    transitions: list[WorkflowTransitionContext] = Field(default_factory=list)


class WorkflowContext(BaseModel):
    workflows: list[WorkflowSummary] = Field(default_factory=list)


class ScenarioContext(BaseModel):
    domain_problem: Optional[str] = None
    analysis_goal: Optional[str] = None
    dataset_context: Optional[str] = None
    initial_question: Optional[str] = None


class CaseQuestionContext(BaseModel):
    question_id: IdentifierString
    question_text: str
    status: Optional[str] = None


class CaseHypothesisContext(BaseModel):
    hypothesis_id: IdentifierString
    hypothesis_text: str
    status: Optional[str] = None
    related_question_ids: list[IdentifierString] = Field(default_factory=list)

    @field_validator("related_question_ids", mode="after")
    @classmethod
    def dedupe_related_question_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class PrefixStepContext(BaseModel):
    step_id: IdentifierString
    step_index: int
    used_views: list[IdentifierString] = Field(default_factory=list)
    used_capabilities: list[IdentifierString] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    produced_insights: list[str] = Field(default_factory=list)
    outcome_summary: Optional[str] = None

    @field_validator("used_views", "used_capabilities", mode="after")
    @classmethod
    def dedupe_step_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class PrefixEpisodeImage(BaseModel):
    benchmark_episode_index: int
    episode_title: str
    image_path: str


class PrefixEpisodeContext(BaseModel):
    benchmark_episode_index: int
    episode_title: str
    local_goal: str
    used_views: list[IdentifierString] = Field(default_factory=list)
    used_capabilities: list[IdentifierString] = Field(default_factory=list)
    source_step_ids: list[IdentifierString] = Field(default_factory=list)
    steps: list[PrefixStepContext] = Field(default_factory=list)
    image_path: Optional[str] = None

    @field_validator("used_views", "used_capabilities", "source_step_ids", mode="after")
    @classmethod
    def dedupe_episode_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class CaseContext(BaseModel):
    scenario: ScenarioContext
    questions: list[CaseQuestionContext] = Field(default_factory=list)
    hypotheses: list[CaseHypothesisContext] = Field(default_factory=list)
    prefix_episodes: list[PrefixEpisodeContext] = Field(default_factory=list)


class VisualContext(BaseModel):
    input_mode: Literal["ordered_episode_images"] = "ordered_episode_images"
    prefix_episode_images: list[PrefixEpisodeImage] = Field(default_factory=list)


class ResponseRequirements(BaseModel):
    output_format: Literal["json"] = "json"
    predicted_views_unit: Literal["canonical_subview_or_view_id"] = "canonical_subview_or_view_id"
    predicted_capabilities_unit: Literal["canonical_capability_id"] = "canonical_capability_id"
    workflow_prediction_optional: bool = True
    use_only_ids_from_context: bool = True


class NextAnalyticMoveModelInput(BaseModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    task_name: Literal[TASK_NAME] = TASK_NAME
    sample_id: str
    task_instruction: str = DEFAULT_TASK_INSTRUCTION
    system_context: SystemContext
    workflow_context: WorkflowContext
    case_context: CaseContext
    visual_context: VisualContext
    response_requirements: ResponseRequirements = Field(default_factory=ResponseRequirements)


class PredictedWorkflowStage(BaseModel):
    workflow_id: IdentifierString
    stage_id: IdentifierString


class RetrievedEvidenceItem(BaseModel):
    paper_name: str
    source_type: str
    source_id: Optional[str] = None
    reason: str


class NextAnalyticMoveModelOutput(BaseModel):
    predicted_next_goal: str
    predicted_views: list[IdentifierString] = Field(default_factory=list)
    predicted_capabilities: list[IdentifierString] = Field(default_factory=list)
    predicted_workflow_stage: Optional[PredictedWorkflowStage] = None
    rationale: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    retrieved_evidence: list[RetrievedEvidenceItem] = Field(default_factory=list)

    @field_validator("predicted_views", "predicted_capabilities", mode="after")
    @classmethod
    def dedupe_prediction_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class NextAnalyticMoveGold(BaseModel):
    target_episode_index: int
    target_episode_title: str
    target_episode_image_path: Optional[str] = None
    gold_next_goal: str
    gold_next_views: list[IdentifierString] = Field(default_factory=list)
    gold_next_capabilities: list[IdentifierString] = Field(default_factory=list)

    @field_validator("gold_next_views", "gold_next_capabilities", mode="after")
    @classmethod
    def dedupe_gold_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_identifiers(values)


class BenchmarkRecordMetadata(BaseModel):
    sample_id: str
    benchmark_case_id: str
    paper_name: str
    case_index: int
    prefix_length: int
    prefix_episode_indices: list[int]
    target_episode_index: int


class NextAnalyticMoveBenchmarkRecord(BaseModel):
    metadata: BenchmarkRecordMetadata
    model_input: NextAnalyticMoveModelInput
    gold: NextAnalyticMoveGold


def summarize_system_context(system_spec: dict[str, Any]) -> SystemContext:
    system_info = system_spec.get("systemInfo", {}) or {}
    views: list[SystemViewOption] = []
    for view in system_spec.get("viewsInfo", []) or []:
        subviews: list[SystemSubViewOption] = []
        for subview in view.get("subViews", []) or []:
            capabilities = [
                SystemCapabilityOption(
                    capability_id=str(capability["capabilityId"]),
                    capability_name=str(capability.get("capabilityName") or capability["capabilityId"]),
                    capability_kind=str(capability.get("capabilityKind"))
                    if capability.get("capabilityKind")
                    else None,
                    description=str(capability.get("description"))
                    if capability.get("description")
                    else None,
                )
                for capability in subview.get("capabilities", []) or []
                if capability.get("capabilityId")
            ]
            subviews.append(
                SystemSubViewOption(
                    subview_id=str(subview["subViewId"]),
                    subview_name=str(subview.get("subViewName") or subview["subViewId"]),
                    description=str(subview.get("description"))
                    if subview.get("description")
                    else None,
                    capabilities=capabilities,
                )
            )

        views.append(
            SystemViewOption(
                view_id=str(view["viewId"]),
                view_name=str(view.get("viewName") or view["viewId"]),
                description=str(view.get("description")) if view.get("description") else None,
                subviews=subviews,
            )
        )

    coordinations = [
        CoordinationOption(
            coordination_id=str(coordination["coordinationId"]),
            coordination_type=str(coordination.get("coordinationType"))
            if coordination.get("coordinationType")
            else None,
            description=str(coordination.get("evidence", {}).get("reasoning"))
            if coordination.get("evidence", {}).get("reasoning")
            else None,
            source_id=_normalize_view_ref(coordination.get("source", {}) or {}),
            target_ids=[
                normalized
                for target in coordination.get("targets", []) or []
                if (normalized := _normalize_view_ref(target))
            ],
        )
        for coordination in system_spec.get("coordinationInfo", []) or []
        if coordination.get("coordinationId")
    ]

    return SystemContext(
        system_name=str(system_info.get("systemName")) if system_info.get("systemName") else None,
        dataset_types=[str(item) for item in (system_info.get("dataOntology", {}) or {}).get("datasetType", []) or []],
        system_categories=_flatten_categories(system_info),
        views=views,
        coordinations=coordinations,
    )


def summarize_workflow_context(workflow_spec: dict[str, Any]) -> WorkflowContext:
    workflows: list[WorkflowSummary] = []
    for workflow in workflow_spec.get("workflows", []) or []:
        workflow_id = workflow.get("workflowId")
        if not workflow_id:
            continue

        stages = [
            WorkflowStageContext(
                workflow_id=str(workflow_id),
                stage_id=str(stage["stageId"]),
                stage_index=int(stage["stageIndex"]),
                stage_title=str(stage.get("stageTitle") or stage["stageId"]),
                stage_goal=str(stage.get("stageGoal")) if stage.get("stageGoal") else None,
                description=str(stage.get("description")) if stage.get("description") else None,
                used_views=[
                    normalized
                    for ref in stage.get("usedViews", []) or []
                    if (normalized := _normalize_view_ref(ref))
                ],
                used_capabilities=_normalize_capability_refs(stage.get("usedCapabilities", [])),
                used_coordinations=[
                    str(coordination["coordinationId"])
                    for coordination in stage.get("usedCoordinations", []) or []
                    if coordination.get("coordinationId")
                ],
                expected_outcome=str(stage.get("expectedOutcome"))
                if stage.get("expectedOutcome")
                else None,
            )
            for stage in workflow.get("stages", []) or []
            if stage.get("stageId")
        ]
        transitions = [
            WorkflowTransitionContext(
                source_stage_id=str(transition["sourceStageId"]),
                target_stage_id=str(transition["targetStageId"]),
                transition_type=str(transition["transitionType"]),
                rationale=str(transition.get("rationale"))
                if transition.get("rationale")
                else None,
            )
            for transition in workflow.get("transitions", []) or []
            if transition.get("sourceStageId") and transition.get("targetStageId")
        ]
        workflows.append(
            WorkflowSummary(
                workflow_id=str(workflow_id),
                workflow_title=str(workflow.get("workflowTitle") or workflow_id),
                workflow_goal=str(workflow.get("workflowGoal"))
                if workflow.get("workflowGoal")
                else None,
                description=str(workflow.get("description"))
                if workflow.get("description")
                else None,
                stages=stages,
                transitions=transitions,
            )
        )

    return WorkflowContext(workflows=workflows)


def summarize_case_context(
    case_manifest_entry: dict[str, Any],
    sample: dict[str, Any],
) -> CaseContext:
    usage_case = resolve_usage_case(
        str(case_manifest_entry["paper_name"]),
        int(case_manifest_entry["case_index"]),
    )
    step_lookup = _build_step_lookup(usage_case)
    benchmark_episode_lookup = {
        int(episode["benchmark_episode_index"]): episode
        for episode in case_manifest_entry.get("benchmark_episodes", [])
    }

    prefix_episodes: list[PrefixEpisodeContext] = []
    for benchmark_episode_index in sample.get("prefix_episode_indices", []):
        benchmark_episode = benchmark_episode_lookup[int(benchmark_episode_index)]
        step_contexts: list[PrefixStepContext] = []
        for step_ref in benchmark_episode.get("source_step_refs", []):
            step = step_lookup.get(step_ref)
            if not step:
                continue
            step_contexts.append(
                PrefixStepContext(
                    step_id=str(step["stepId"]),
                    step_index=int(step["stepIndex"]),
                    used_views=[
                        normalized
                        for ref in step.get("usedViews", []) or []
                        if (normalized := _normalize_view_ref(ref))
                    ],
                    used_capabilities=_normalize_capability_refs(step.get("usedCapabilities", [])),
                    observations=_coerce_text_list(step.get("observations"), "description"),
                    produced_insights=_coerce_text_list(step.get("producedInsights"), "description"),
                    outcome_summary=str(step.get("outcomeSummary"))
                    if step.get("outcomeSummary")
                    else None,
                )
            )

        image_path = benchmark_episode.get("composite_path")
        prefix_episodes.append(
            PrefixEpisodeContext(
                benchmark_episode_index=int(benchmark_episode["benchmark_episode_index"]),
                episode_title=str(benchmark_episode["benchmark_episode_title"]),
                local_goal=str(benchmark_episode["local_goal"]),
                used_views=list(benchmark_episode.get("used_views", [])),
                used_capabilities=list(benchmark_episode.get("used_capabilities", [])),
                source_step_ids=list(benchmark_episode.get("source_step_ids", [])),
                steps=step_contexts,
                image_path=str(image_path) if image_path else None,
            )
        )

    scenario = usage_case.get("scenario", {}) or {}
    return CaseContext(
        scenario=ScenarioContext(
            domain_problem=str(scenario.get("domainProblem"))
            if scenario.get("domainProblem")
            else None,
            analysis_goal=str(scenario.get("analysisGoal"))
            if scenario.get("analysisGoal")
            else None,
            dataset_context=str(scenario.get("datasetContext"))
            if scenario.get("datasetContext")
            else None,
            initial_question=str(scenario.get("initialQuestion"))
            if scenario.get("initialQuestion")
            else None,
        ),
        questions=[
            CaseQuestionContext(
                question_id=str(question["questionId"]),
                question_text=str(question["questionText"]),
                status=str(question.get("status")) if question.get("status") else None,
            )
            for question in usage_case.get("questions", []) or []
            if question.get("questionId") and question.get("questionText")
        ],
        hypotheses=[
            CaseHypothesisContext(
                hypothesis_id=str(hypothesis["hypothesisId"]),
                hypothesis_text=str(hypothesis["hypothesisText"]),
                status=str(hypothesis.get("status")) if hypothesis.get("status") else None,
                related_question_ids=[
                    str(question_id)
                    for question_id in hypothesis.get("relatedQuestionIds", []) or []
                ],
            )
            for hypothesis in usage_case.get("hypotheses", []) or []
            if hypothesis.get("hypothesisId") and hypothesis.get("hypothesisText")
        ],
        prefix_episodes=prefix_episodes,
    )


def summarize_visual_context(
    case_context: CaseContext,
) -> VisualContext:
    return VisualContext(
        prefix_episode_images=[
            PrefixEpisodeImage(
                benchmark_episode_index=episode.benchmark_episode_index,
                episode_title=episode.episode_title,
                image_path=str(episode.image_path),
            )
            for episode in case_context.prefix_episodes
            if episode.image_path
        ]
    )


def build_model_record(
    case_manifest_entry: dict[str, Any],
    sample: dict[str, Any],
) -> NextAnalyticMoveBenchmarkRecord:
    system_context = summarize_system_context(
        load_system_spec(str(case_manifest_entry["paper_name"]))
    )
    workflow_context = summarize_workflow_context(
        load_workflow_spec(str(case_manifest_entry["paper_name"]))
    )
    case_context = summarize_case_context(case_manifest_entry, sample)
    visual_context = summarize_visual_context(case_context)

    model_input = NextAnalyticMoveModelInput(
        sample_id=str(sample["sample_id"]),
        system_context=system_context,
        workflow_context=workflow_context,
        case_context=case_context,
        visual_context=visual_context,
    )

    gold = NextAnalyticMoveGold(
        target_episode_index=int(sample["target_episode_index"]),
        target_episode_title=str(sample["target_episode_title"]),
        target_episode_image_path=str(sample["target_episode_composite_path"])
        if sample.get("target_episode_composite_path")
        else None,
        gold_next_goal=str(sample["gold_next_goal"]),
        gold_next_views=list(sample.get("gold_next_views", [])),
        gold_next_capabilities=list(sample.get("gold_next_capabilities", [])),
    )

    return NextAnalyticMoveBenchmarkRecord(
        metadata=BenchmarkRecordMetadata(
            sample_id=str(sample["sample_id"]),
            benchmark_case_id=str(sample["benchmark_case_id"]),
            paper_name=str(sample["paper_name"]),
            case_index=int(sample["case_index"]),
            prefix_length=int(sample["prefix_length"]),
            prefix_episode_indices=[int(index) for index in sample.get("prefix_episode_indices", [])],
            target_episode_index=int(sample["target_episode_index"]),
        ),
        model_input=model_input,
        gold=gold,
    )


def build_model_records() -> list[NextAnalyticMoveBenchmarkRecord]:
    case_manifest = build_case_manifest()
    samples = build_samples(case_manifest)
    case_lookup = {
        str(case["benchmark_case_id"]): case
        for case in case_manifest
    }
    return [
        build_model_record(case_lookup[str(sample["benchmark_case_id"])], sample)
        for sample in samples
    ]
