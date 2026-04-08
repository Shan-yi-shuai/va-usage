from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.schemas.schema_common import (
    CapabilityRef,
    EvidenceReference,
    IdentifierString,
    OthersString,
    ViewRef,
    _dedupe_strings,
    _make_unique_identifier,
    _slugify_identifier,
)


# =========================================================
# 1. Taxonomies
# =========================================================

CaseStudyKind = Union[
    Literal[
        "RealWorldCase",
        "ExpertWalkthrough",
        "ScenarioDemonstration",
        "RetrospectiveAnalysis",
        "LongitudinalUse",
    ],
    OthersString,
]

ActorRole = Union[
    Literal[
        "DomainExpert",
        "DataAnalyst",
        "DecisionMaker",
        "Researcher",
        "Operator",
        "Investigator",
        "Clinician",
        "Engineer",
        "Student",
        "AuthorSimulatedUser",
    ],
    OthersString,
]

ExpertiseLevel = Union[
    Literal[
        "Novice",
        "Intermediate",
        "Expert",
        "Unknown",
    ],
    OthersString,
]

QuestionStatus = Union[
    Literal[
        "Open",
        "PartiallyAnswered",
        "Answered",
        "Abandoned",
    ],
    OthersString,
]

QuestionEventAction = Union[
    Literal[
        "Introduce",
        "Refine",
        "Answer",
        "Reopen",
        "Abandon",
    ],
    OthersString,
]

HypothesisStatus = Union[
    Literal[
        "Proposed",
        "UnderInvestigation",
        "Supported",
        "Rejected",
        "Revised",
        "Deferred",
    ],
    OthersString,
]

HypothesisEventAction = Union[
    Literal[
        "Propose",
        "Refine",
        "Support",
        "Reject",
        "Reopen",
        "Defer",
    ],
    OthersString,
]

IntentCanonical = Union[
    Literal[
        "Browse",
        "Locate",
        "Explore",
        "Filter",
        "Select",
        "Compare",
        "Inspect",
        "DrillDown",
        "Contextualize",
        "Correlate",
        "Explain",
        "Validate",
        "Prioritize",
        "Monitor",
        "Summarize",
        "Report",
        "Annotate",
        "RefineQuery",
        "Reconfigure",
        "PlanAction",
    ],
    OthersString,
]

StrategyCanonical = Union[
    Literal[
        "OverviewFirst",
        "DrillDownThenExplain",
        "ComparativeAnalysis",
        "HypothesisGeneration",
        "HypothesisTesting",
        "EvidenceAccumulation",
        "AnomalyTriage",
        "IterativeRefinement",
        "SensemakingLoop",
        "WhatIfAnalysis",
        "NarrativeConstruction",
        "MonitoringAndFollowUp",
        "SearchThenInspect",
        "InspectThenCompare",
    ],
    OthersString,
]

OperationCanonical = Union[
    Literal[
        "OpenView",
        "Navigate",
        "Search",
        "FilterSubset",
        "Sort",
        "Group",
        "Aggregate",
        "Zoom",
        "Pan",
        "SelectItem",
        "SelectGroup",
        "Highlight",
        "Brush",
        "LinkAcrossViews",
        "InspectDetails",
        "ExpandContext",
        "CollapseContext",
        "CompareAlternatives",
        "ChangeParameter",
        "ChangeEncoding",
        "ChangeLayout",
        "RequestExplanation",
        "ReadAnnotation",
        "WriteAnnotation",
        "BookmarkState",
        "ExportResult",
    ],
    OthersString,
]

ObservationType = Union[
    Literal[
        "Pattern",
        "Anomaly",
        "Trend",
        "Distribution",
        "Cluster",
        "Outlier",
        "Comparison",
        "Relationship",
        "TemporalChange",
        "SpatialPattern",
        "ContextualCue",
        "MissingEvidence",
    ],
    OthersString,
]

InsightType = Union[
    Literal[
        "PatternFound",
        "AnomalyFound",
        "CandidateIdentified",
        "SubgroupCharacterized",
        "RelationshipIdentified",
        "HypothesisSupported",
        "HypothesisRejected",
        "ExplanationFormed",
        "DecisionMade",
        "UncertaintyReduced",
        "NeedMoreEvidence",
        "NoRelevantFinding",
        "ReportProduced",
    ],
    OthersString,
]

TransitionType = Union[
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

FrictionType = Union[
    Literal[
        "HighViewSwitching",
        "MissingContext",
        "AmbiguousMapping",
        "LimitedFiltering",
        "LimitedComparison",
        "LimitedExplanationSupport",
        "LimitedTraceability",
        "ManualCrossReferencing",
        "Overplotting",
        "CognitiveLoad",
        "UnclearState",
        "NoFriction",
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


# =========================================================
# 2. Scenario / actor / question / hypothesis
# =========================================================


class AnalystProfile(BaseModel):
    role: Optional[ActorRole] = Field(
        default=None,
        description="Role of the analyst/user in this case study.",
    )
    domainExpertise: Optional[ExpertiseLevel] = Field(
        default=None,
        description="Domain expertise level of the user.",
    )
    toolExpertise: Optional[ExpertiseLevel] = Field(
        default=None,
        description="Experience level with the VA system or similar tools.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Free-text characterization of the actor.",
    )


class ScenarioContext(BaseModel):
    domainProblem: str = Field(
        ...,
        description="Problem context in the domain.",
    )
    analysisGoal: str = Field(
        ...,
        description="Main goal of the case study analysis.",
    )
    datasetContext: Optional[str] = Field(
        default=None,
        description="Short description of the dataset involved.",
    )
    stakes: Optional[str] = Field(
        default=None,
        description="Why this analysis matters in the application context.",
    )
    initialQuestion: Optional[str] = Field(
        default=None,
        description="Initial question or problem framing stated in the case.",
    )


class QuestionItem(BaseModel):
    questionId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable identifier of the question.",
    )
    questionText: str = Field(
        ...,
        description="Canonical question phrasing.",
    )
    status: Optional[QuestionStatus] = Field(
        default="Open",
        description="Current status of the question at case level.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional elaboration of the question.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for extracting this question.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether this question is explicit or inferred.",
    )


class HypothesisItem(BaseModel):
    hypothesisId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable identifier of the hypothesis.",
    )
    hypothesisText: str = Field(
        ...,
        description="Canonical hypothesis statement.",
    )
    status: Optional[HypothesisStatus] = Field(
        default="Proposed",
        description="Status of the hypothesis at case level.",
    )
    relatedQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Question IDs that this hypothesis addresses.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional elaboration or scope of the hypothesis.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for extracting this hypothesis.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether this hypothesis is explicit or inferred.",
    )

    @field_validator("relatedQuestionIds", mode="before")
    @classmethod
    def normalize_related_question_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.relatedQuestionIds = _dedupe_strings(self.relatedQuestionIds)
        return self


class QuestionEvent(BaseModel):
    questionId: Optional[IdentifierString] = Field(
        default=None,
        description="Referenced question identifier, if already known.",
    )
    action: QuestionEventAction = Field(
        ...,
        description="How the step updates the question state.",
    )
    questionText: Optional[str] = Field(
        default=None,
        description="Question text when a new or refined question is introduced.",
    )
    note: Optional[str] = Field(
        default=None,
        description="Why this question event happened.",
    )
    statusAfter: Optional[QuestionStatus] = Field(
        default=None,
        description="Question status after the event when inferable.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for this event.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether this event is explicit or inferred.",
    )

    @model_validator(mode="after")
    def validate_payload(self):
        if self.questionId is None and not self.questionText:
            raise ValueError("QuestionEvent requires questionId or questionText.")
        if self.action == "Introduce" and not self.questionText:
            raise ValueError("QuestionEvent with action 'Introduce' requires questionText.")
        return self


class HypothesisEvent(BaseModel):
    hypothesisId: Optional[IdentifierString] = Field(
        default=None,
        description="Referenced hypothesis identifier, if already known.",
    )
    action: HypothesisEventAction = Field(
        ...,
        description="How the step updates the hypothesis state.",
    )
    hypothesisText: Optional[str] = Field(
        default=None,
        description="Hypothesis text when a new or refined hypothesis is introduced.",
    )
    relatedQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions linked to this hypothesis event.",
    )
    note: Optional[str] = Field(
        default=None,
        description="Why the hypothesis was proposed/refined/supported/rejected.",
    )
    statusAfter: Optional[HypothesisStatus] = Field(
        default=None,
        description="Hypothesis status after this event when inferable.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for this event.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether this event is explicit or inferred.",
    )

    @field_validator("relatedQuestionIds", mode="before")
    @classmethod
    def normalize_related_question_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.relatedQuestionIds = _dedupe_strings(self.relatedQuestionIds)
        if self.hypothesisId is None and not self.hypothesisText:
            raise ValueError("HypothesisEvent requires hypothesisId or hypothesisText.")
        if self.action == "Propose" and not self.hypothesisText:
            raise ValueError("HypothesisEvent with action 'Propose' requires hypothesisText.")
        return self


# =========================================================
# 3. State / data focus / feature use
# =========================================================


class FilterCondition(BaseModel):
    field: str = Field(
        ...,
        description="Field or attribute being filtered.",
    )
    operator: str = Field(
        ...,
        description="Filter operator, e.g., '=', '>', 'contains', 'top-k'.",
    )
    valueText: str = Field(
        ...,
        description="Textual representation of the filter value.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional explanation of the filter semantics.",
    )


class AnalyticState(BaseModel):
    activeQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions currently in focus.",
    )
    activeHypothesisIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Hypotheses currently under consideration.",
    )
    focusSummary: Optional[str] = Field(
        default=None,
        description="Short natural-language description of the current analytic focus.",
    )
    targetEntities: Optional[List[str]] = Field(
        default=None,
        description="Entities/items/groups currently being tracked.",
    )
    targetVariables: Optional[List[str]] = Field(
        default=None,
        description="Variables/attributes currently in focus.",
    )
    targetTimeRange: Optional[str] = Field(
        default=None,
        description="Time range currently under analysis, if relevant.",
    )
    targetSpatialRegion: Optional[str] = Field(
        default=None,
        description="Spatial region currently under analysis, if relevant.",
    )
    activeViews: Optional[List[ViewRef]] = Field(
        default=None,
        description="Views/sub-views currently in active use.",
    )
    appliedFilters: Optional[List[FilterCondition]] = Field(
        default=None,
        description="Active filters that define the current state.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional state notes.",
    )

    @field_validator(
        "activeQuestionIds",
        "activeHypothesisIds",
        "targetEntities",
        "targetVariables",
        mode="before",
    )
    @classmethod
    def normalize_string_lists(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.activeQuestionIds = _dedupe_strings(self.activeQuestionIds)
        self.activeHypothesisIds = _dedupe_strings(self.activeHypothesisIds)
        self.targetEntities = _dedupe_strings(self.targetEntities)
        self.targetVariables = _dedupe_strings(self.targetVariables)

        if self.activeViews:
            seen: set[tuple[str, Optional[str]]] = set()
            deduped: List[ViewRef] = []
            for ref in self.activeViews:
                key = (ref.viewId, ref.subViewId)
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(ref)
            self.activeViews = deduped

        return self


# =========================================================
# 4. Observation / insight / decision
# =========================================================


class ObservationItem(BaseModel):
    observationType: Optional[ObservationType] = Field(
        default=None,
        description="Type of observation made at this step.",
    )
    description: str = Field(
        ...,
        description="What the analyst noticed.",
    )
    basedOnViews: Optional[List[ViewRef]] = Field(
        default=None,
        description="Views that directly support the observation.",
    )
    targetDataDescription: Optional[List[str]] = Field(
        default=None,
        description="Data subset or objects involved in the observation.",
    )
    interpretation: Optional[str] = Field(
        default=None,
        description="Immediate interpretation attached to this observation, if local and explicit.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for this observation item.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the observation is explicit or inferred.",
    )

    @field_validator("targetDataDescription", mode="before")
    @classmethod
    def normalize_target_data(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.targetDataDescription = _dedupe_strings(self.targetDataDescription)
        if self.basedOnViews:
            seen: set[tuple[str, Optional[str]]] = set()
            deduped: List[ViewRef] = []
            for ref in self.basedOnViews:
                key = (ref.viewId, ref.subViewId)
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(ref)
            self.basedOnViews = deduped
        return self


class InsightItem(BaseModel):
    insightType: Optional[InsightType] = Field(
        default=None,
        description="Type of insight or result.",
    )
    description: str = Field(
        ...,
        description="Canonical statement of the insight.",
    )
    relatedQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions answered or affected by this insight.",
    )
    relatedHypothesisIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Hypotheses addressed by this insight.",
    )
    supportedByViews: Optional[List[ViewRef]] = Field(
        default=None,
        description="Views supporting the insight.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for this insight.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the insight is explicit or inferred.",
    )

    @field_validator("relatedQuestionIds", "relatedHypothesisIds", mode="before")
    @classmethod
    def normalize_related_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.relatedQuestionIds = _dedupe_strings(self.relatedQuestionIds)
        self.relatedHypothesisIds = _dedupe_strings(self.relatedHypothesisIds)
        if self.supportedByViews:
            seen: set[tuple[str, Optional[str]]] = set()
            deduped: List[ViewRef] = []
            for ref in self.supportedByViews:
                key = (ref.viewId, ref.subViewId)
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(ref)
            self.supportedByViews = deduped
        return self


class DecisionItem(BaseModel):
    description: str = Field(
        ...,
        description="Decision or next analytic commitment made at this point.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Why this decision was made.",
    )
    targetQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions impacted by the decision.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for the decision.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the decision is explicit or inferred.",
    )

    @field_validator("targetQuestionIds", mode="before")
    @classmethod
    def normalize_target_question_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.targetQuestionIds = _dedupe_strings(self.targetQuestionIds)
        return self


# =========================================================
# 5. Usage step / transition / episode
# =========================================================


class UsageStep(BaseModel):
    """Smallest process unit with independent analytic meaning inside an episode."""

    stepId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable step identifier.",
    )
    stepIndex: Optional[int] = Field(
        default=None,
        ge=1,
        description="Sequential index of the step within its episode.",
    )
    rawNarrative: Optional[str] = Field(
        default=None,
        description=(
            "Original narrative sentence(s) or concise paraphrase from the paper. A step is not the smallest "
            "UI action; it is the smallest process unit that still has an independent analytic purpose or "
            "result."
        ),
    )
    questionsAddressed: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions directly addressed in this step.",
    )
    hypothesesTouched: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Hypotheses touched in this step.",
    )
    questionEvents: Optional[List[QuestionEvent]] = Field(
        default=None,
        description="Question-level updates that happen in this step.",
    )
    hypothesisEvents: Optional[List[HypothesisEvent]] = Field(
        default=None,
        description="Hypothesis-level updates that happen in this step.",
    )
    intentCanonical: Optional[List[IntentCanonical]] = Field(
        default=None,
        description="Normalized user intents for this step.",
    )
    intentText: Optional[str] = Field(
        default=None,
        description="Free-text statement of the intent.",
    )
    strategyCanonical: Optional[List[StrategyCanonical]] = Field(
        default=None,
        description="Higher-level strategy tags for this step.",
    )
    strategyText: Optional[str] = Field(
        default=None,
        description="Free-text description of the step strategy.",
    )
    operationCanonical: Optional[List[OperationCanonical]] = Field(
        default=None,
        description="Normalized operation tags.",
    )
    operationText: Optional[str] = Field(
        default=None,
        description="Free-text description of the operation.",
    )
    interactionTypes: Optional[List[str]] = Field(
        default=None,
        description="UI interaction types when explicitly mentioned, e.g., click, brush, hover.",
    )
    usedViews: Optional[List[ViewRef]] = Field(
        default=None,
        description=(
            "Views or sub-views directly involved in this step. A step is a process unit, not a structure "
            "unit, so it may reference one or more sub-views when they jointly support the same local "
            "analytic purpose."
        ),
    )
    usedCapabilities: Optional[List[CapabilityRef]] = Field(
        default=None,
        description=(
            "Subview capabilities used in this step. These capture what the analyst directly did in a "
            "sub-view or what the analyst directly read from it."
        ),
    )
    targetDataDescription: Optional[List[str]] = Field(
        default=None,
        description="Data subsets/entities under action in this step.",
    )
    stateBefore: Optional[AnalyticState] = Field(
        default=None,
        description="Analytic state before the step.",
    )
    observations: Optional[List[ObservationItem]] = Field(
        default=None,
        description="Observations produced in this step.",
    )
    interpretationSummary: Optional[str] = Field(
        default=None,
        description="Step-level summary of how the analyst interpreted the evidence.",
    )
    producedInsights: Optional[List[InsightItem]] = Field(
        default=None,
        description="Insights or intermediate results produced by this step.",
    )
    decision: Optional[DecisionItem] = Field(
        default=None,
        description="Decision made at the end of the step.",
    )
    stateAfter: Optional[AnalyticState] = Field(
        default=None,
        description="Analytic state after the step.",
    )
    outcomeSummary: Optional[str] = Field(
        default=None,
        description="Short summary of what this step achieved.",
    )
    frictionTypes: Optional[List[FrictionType]] = Field(
        default=None,
        description="Workflow friction encountered in this step.",
    )
    workaround: Optional[str] = Field(
        default=None,
        description="How the analyst worked around friction, if described.",
    )
    unresolvedQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions that remain unresolved after this step, when explicit.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="How directly this step is supported by the source narrative.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for the whole step.",
    )

    @field_validator(
        "questionsAddressed",
        "hypothesesTouched",
        "interactionTypes",
        "targetDataDescription",
        "unresolvedQuestionIds",
        mode="before",
    )
    @classmethod
    def normalize_string_list_fields(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.questionsAddressed = _dedupe_strings(self.questionsAddressed)
        self.hypothesesTouched = _dedupe_strings(self.hypothesesTouched)
        self.interactionTypes = _dedupe_strings(self.interactionTypes)
        self.targetDataDescription = _dedupe_strings(self.targetDataDescription)
        self.unresolvedQuestionIds = _dedupe_strings(self.unresolvedQuestionIds)

        if self.usedViews:
            seen: set[tuple[str, Optional[str]]] = set()
            deduped: List[ViewRef] = []
            for ref in self.usedViews:
                key = (ref.viewId, ref.subViewId)
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(ref)
            self.usedViews = deduped

        if self.usedCapabilities:
            seen_capabilities: set[tuple[str, str, str]] = set()
            deduped_capabilities: List[CapabilityRef] = []
            for ref in self.usedCapabilities:
                key = (ref.viewId, ref.subViewId, ref.capabilityId)
                if key in seen_capabilities:
                    continue
                seen_capabilities.add(key)
                deduped_capabilities.append(ref)
            self.usedCapabilities = deduped_capabilities

            used_view_keys = {
                (ref.viewId, ref.subViewId)
                for ref in (self.usedViews or [])
            }
            for ref in self.usedCapabilities:
                key = (ref.viewId, ref.subViewId)
                if key not in used_view_keys:
                    if self.usedViews is None:
                        self.usedViews = []
                    self.usedViews.append(ViewRef(viewId=ref.viewId, subViewId=ref.subViewId))
                    used_view_keys.add(key)

        if self.rawNarrative is None and self.evidence is None:
            raise ValueError("UsageStep requires rawNarrative or evidence.")

        has_semantic_payload = any(
            [
                self.questionEvents,
                self.hypothesisEvents,
                self.intentCanonical,
                self.intentText,
                self.strategyCanonical,
                self.strategyText,
                self.operationCanonical,
                self.operationText,
                self.usedCapabilities,
                self.observations,
                self.producedInsights,
                self.decision,
                self.outcomeSummary,
            ]
        )
        if not has_semantic_payload:
            raise ValueError(
                "UsageStep requires at least one semantic field such as intent, operation, observation, "
                "insight, decision, or question/hypothesis event."
            )

        return self


class StepTransition(BaseModel):
    sourceStepId: IdentifierString = Field(
        ...,
        description="Source step ID.",
    )
    targetStepId: IdentifierString = Field(
        ...,
        description="Target step ID.",
    )
    transitionType: TransitionType = Field(
        ...,
        description="Type of transition between two steps.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Why the analysis moved this way.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for the transition.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the transition is explicit or inferred.",
    )


class Episode(BaseModel):
    """Local subtask or phase inside a case study, containing one or more steps."""

    episodeId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable episode identifier.",
    )
    episodeTitle: Optional[str] = Field(
        default=None,
        description="Human-readable label for the episode.",
    )
    localGoal: str = Field(
        ...,
        description=(
            "Goal of this episode. Episodes represent stage-level progress inside a case study rather than "
            "single interactions."
        ),
    )
    focusQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions that dominate this episode.",
    )
    strategyCanonical: Optional[List[StrategyCanonical]] = Field(
        default=None,
        description="Dominant strategy tags for the episode.",
    )
    strategyText: Optional[str] = Field(
        default=None,
        description="Free-text summary of the episode strategy.",
    )
    steps: List[UsageStep] = Field(
        ...,
        description=(
            "Ordered analytic steps in this episode. Split steps when there is a clear sequential shift to "
            "a different local purpose; do not compress an entire stage into a single macro-step."
        ),
    )
    transitions: Optional[List[StepTransition]] = Field(
        default=None,
        description="Explicit transitions among steps inside this episode.",
    )
    episodeOutcomeSummary: Optional[str] = Field(
        default=None,
        description="What the episode achieved overall.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence supporting the episode segmentation as a distinct local phase.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether this episode boundary is explicit or inferred.",
    )

    @field_validator("focusQuestionIds", mode="before")
    @classmethod
    def normalize_focus_question_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.focusQuestionIds = _dedupe_strings(self.focusQuestionIds)
        if not self.steps:
            raise ValueError("Episode must contain at least one UsageStep.")
        return self


# =========================================================
# 6. Case-level outcome
# =========================================================


class CaseOutcome(BaseModel):
    finalInsights: Optional[List[InsightItem]] = Field(
        default=None,
        description="Final findings produced by the case study.",
    )
    finalDecisions: Optional[List[DecisionItem]] = Field(
        default=None,
        description="Final decisions or next actions.",
    )
    unresolvedQuestionIds: Optional[List[IdentifierString]] = Field(
        default=None,
        description="Questions left open after the case.",
    )
    claimedSystemValue: Optional[str] = Field(
        default=None,
        description="How the paper claims the system helped in this case.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for the case-level outcome summary.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether this outcome is explicit or inferred.",
    )

    @field_validator("unresolvedQuestionIds", mode="before")
    @classmethod
    def normalize_unresolved_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.unresolvedQuestionIds = _dedupe_strings(self.unresolvedQuestionIds)
        return self


# =========================================================
# 7. Top-level case study schema
# =========================================================


class CaseStudySpec(BaseModel):
    caseId: Optional[IdentifierString] = Field(
        default=None,
        description="Stable case identifier.",
    )
    caseTitle: Optional[str] = Field(
        default=None,
        description="Case study title or label.",
    )
    caseStudyKind: Optional[CaseStudyKind] = Field(
        default=None,
        description="Type of case study.",
    )
    analyst: Optional[AnalystProfile] = Field(
        default=None,
        description="Analyst/user profile for the case.",
    )
    scenario: ScenarioContext = Field(
        ...,
        description="Problem context and overall goal.",
    )
    questions: Optional[List[QuestionItem]] = Field(
        default=None,
        description="Canonical question inventory for the case.",
    )
    hypotheses: Optional[List[HypothesisItem]] = Field(
        default=None,
        description="Canonical hypothesis inventory for the case.",
    )
    episodes: List[Episode] = Field(
        ...,
        description=(
            "Main stage-level decomposition of the case. Episodes typically represent phase-to-phase "
            "progression across local analytic goals, and each episode contains one or more steps."
        ),
    )
    finalOutcome: Optional[CaseOutcome] = Field(
        default=None,
        description="Final findings and decisions from the case.",
    )
    overallStrategySummary: Optional[str] = Field(
        default=None,
        description="High-level summary of the end-to-end strategy.",
    )
    caseNarrativeSummary: Optional[str] = Field(
        default=None,
        description="Compact prose summary of the full case.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence for the case as a whole.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether the case segmentation is explicit or inferred.",
    )

    @model_validator(mode="after")
    def populate_ids_and_validate(self):
        if not self.episodes:
            raise ValueError("CaseStudySpec requires at least one Episode.")

        case_fallback = "case-1"
        self.caseId = self.caseId or _slugify_identifier(self.caseTitle, case_fallback)

        question_items = list(self.questions or [])
        hypothesis_items = list(self.hypotheses or [])

        valid_question_ids: set[str] = set()
        valid_hypothesis_ids: set[str] = set()

        seen_q_ids: set[str] = set()
        for idx, item in enumerate(question_items, start=1):
            base_qid = item.questionId or _slugify_identifier(
                item.questionText,
                f"{self.caseId}.question-{idx}",
            )
            if not base_qid.startswith(f"{self.caseId}."):
                base_qid = f"{self.caseId}.{base_qid}"
            item.questionId = _make_unique_identifier(base_qid, seen_q_ids)
            valid_question_ids.add(item.questionId)

        seen_h_ids: set[str] = set()
        for idx, item in enumerate(hypothesis_items, start=1):
            base_hid = item.hypothesisId or _slugify_identifier(
                item.hypothesisText,
                f"{self.caseId}.hypothesis-{idx}",
            )
            if not base_hid.startswith(f"{self.caseId}."):
                base_hid = f"{self.caseId}.{base_hid}"
            item.hypothesisId = _make_unique_identifier(base_hid, seen_h_ids)
            valid_hypothesis_ids.add(item.hypothesisId)

        def register_question(question_text: str, question_id: Optional[str] = None) -> str:
            candidate = question_id or _slugify_identifier(
                question_text,
                f"{self.caseId}.question-{len(question_items) + 1}",
            )
            if not candidate.startswith(f"{self.caseId}."):
                candidate = f"{self.caseId}.{candidate}"
            if candidate in valid_question_ids:
                return candidate
            unique = _make_unique_identifier(candidate, seen_q_ids)
            question_items.append(
                QuestionItem(
                    questionId=unique,
                    questionText=question_text,
                    status="Open",
                    inferenceType="StrongInference",
                )
            )
            valid_question_ids.add(unique)
            return unique

        def register_hypothesis(
            hypothesis_text: str,
            hypothesis_id: Optional[str] = None,
            related_question_ids: Optional[List[str]] = None,
        ) -> str:
            candidate = hypothesis_id or _slugify_identifier(
                hypothesis_text,
                f"{self.caseId}.hypothesis-{len(hypothesis_items) + 1}",
            )
            if not candidate.startswith(f"{self.caseId}."):
                candidate = f"{self.caseId}.{candidate}"
            if candidate in valid_hypothesis_ids:
                return candidate
            unique = _make_unique_identifier(candidate, seen_h_ids)
            hypothesis_items.append(
                HypothesisItem(
                    hypothesisId=unique,
                    hypothesisText=hypothesis_text,
                    status="Proposed",
                    relatedQuestionIds=related_question_ids,
                    inferenceType="StrongInference",
                )
            )
            valid_hypothesis_ids.add(unique)
            return unique

        seen_episode_ids: set[str] = set()
        seen_step_ids_global: set[str] = set()

        for eidx, episode in enumerate(self.episodes, start=1):
            base_episode_id = episode.episodeId or _slugify_identifier(
                episode.episodeTitle,
                f"{self.caseId}.episode-{eidx}",
            )
            if not base_episode_id.startswith(f"{self.caseId}."):
                base_episode_id = f"{self.caseId}.{base_episode_id}"
            episode.episodeId = _make_unique_identifier(base_episode_id, seen_episode_ids)

            seen_step_ids_local: set[str] = set()
            for sidx, step in enumerate(episode.steps, start=1):
                base_step_id = step.stepId or f"{episode.episodeId}.step-{sidx}"
                if not base_step_id.startswith(f"{episode.episodeId}."):
                    base_step_id = f"{episode.episodeId}.{base_step_id}"
                unique_local = _make_unique_identifier(base_step_id, seen_step_ids_local)
                if unique_local in seen_step_ids_global:
                    unique_local = _make_unique_identifier(unique_local, seen_step_ids_global)
                else:
                    seen_step_ids_global.add(unique_local)
                step.stepId = unique_local
                if step.stepIndex is None:
                    step.stepIndex = sidx

                for event in step.questionEvents or []:
                    if event.questionId and event.questionId in valid_question_ids:
                        pass
                    elif event.questionText:
                        event.questionId = register_question(event.questionText, event.questionId)
                    else:
                        raise ValueError(
                            f"Step '{step.stepId}' question event references unknown questionId '{event.questionId}'."
                        )

                for event in step.hypothesisEvents or []:
                    normalized_related_qids: Optional[List[str]] = None
                    if event.relatedQuestionIds:
                        normalized_related_qids = []
                        for qid in event.relatedQuestionIds:
                            if qid not in valid_question_ids:
                                raise ValueError(
                                    f"Step '{step.stepId}' hypothesis event references unknown questionId '{qid}'."
                                )
                            normalized_related_qids.append(qid)
                        event.relatedQuestionIds = normalized_related_qids

                    if event.hypothesisId and event.hypothesisId in valid_hypothesis_ids:
                        pass
                    elif event.hypothesisText:
                        event.hypothesisId = register_hypothesis(
                            event.hypothesisText,
                            event.hypothesisId,
                            event.relatedQuestionIds,
                        )
                    else:
                        raise ValueError(
                            f"Step '{step.stepId}' hypothesis event references unknown hypothesisId "
                            f"'{event.hypothesisId}'."
                        )

        self.questions = question_items or None
        self.hypotheses = hypothesis_items or None

        def validate_question_refs(values: Optional[List[str]], label: str):
            for qid in values or []:
                if qid not in valid_question_ids:
                    raise ValueError(f"{label} references unknown questionId '{qid}'.")

        def validate_hypothesis_refs(values: Optional[List[str]], label: str):
            for hid in values or []:
                if hid not in valid_hypothesis_ids:
                    raise ValueError(f"{label} references unknown hypothesisId '{hid}'.")

        for item in self.hypotheses or []:
            validate_question_refs(item.relatedQuestionIds, f"Hypothesis '{item.hypothesisId}' relatedQuestionIds")

        for episode in self.episodes:
            step_indexes = [step.stepIndex for step in episode.steps]
            if len(set(step_indexes)) != len(step_indexes):
                raise ValueError(f"Episode '{episode.episodeId}' contains duplicate stepIndex values.")
            expected_indexes = list(range(1, len(episode.steps) + 1))
            if step_indexes != expected_indexes:
                raise ValueError(
                    f"Episode '{episode.episodeId}' stepIndex values must match the step order 1..n."
                )

            valid_step_ids_in_episode = {step.stepId for step in episode.steps}
            validate_question_refs(episode.focusQuestionIds, f"Episode '{episode.episodeId}' focusQuestionIds")

            for step in episode.steps:
                validate_question_refs(step.questionsAddressed, f"Step '{step.stepId}' questionsAddressed")
                validate_hypothesis_refs(step.hypothesesTouched, f"Step '{step.stepId}' hypothesesTouched")
                validate_question_refs(step.unresolvedQuestionIds, f"Step '{step.stepId}' unresolvedQuestionIds")

                if step.stateBefore:
                    validate_question_refs(
                        step.stateBefore.activeQuestionIds,
                        f"Step '{step.stepId}' stateBefore.activeQuestionIds",
                    )
                    validate_hypothesis_refs(
                        step.stateBefore.activeHypothesisIds,
                        f"Step '{step.stepId}' stateBefore.activeHypothesisIds",
                    )

                if step.stateAfter:
                    validate_question_refs(
                        step.stateAfter.activeQuestionIds,
                        f"Step '{step.stepId}' stateAfter.activeQuestionIds",
                    )
                    validate_hypothesis_refs(
                        step.stateAfter.activeHypothesisIds,
                        f"Step '{step.stepId}' stateAfter.activeHypothesisIds",
                    )

                for insight in step.producedInsights or []:
                    validate_question_refs(
                        insight.relatedQuestionIds,
                        f"Step '{step.stepId}' producedInsight.relatedQuestionIds",
                    )
                    validate_hypothesis_refs(
                        insight.relatedHypothesisIds,
                        f"Step '{step.stepId}' producedInsight.relatedHypothesisIds",
                    )

                if step.decision:
                    validate_question_refs(
                        step.decision.targetQuestionIds,
                        f"Step '{step.stepId}' decision.targetQuestionIds",
                    )

            for transition in episode.transitions or []:
                if transition.sourceStepId not in valid_step_ids_in_episode:
                    raise ValueError(
                        f"Episode '{episode.episodeId}' transition sourceStepId "
                        f"'{transition.sourceStepId}' does not exist in this episode."
                    )
                if transition.targetStepId not in valid_step_ids_in_episode:
                    raise ValueError(
                        f"Episode '{episode.episodeId}' transition targetStepId "
                        f"'{transition.targetStepId}' does not exist in this episode."
                    )

        if self.finalOutcome:
            validate_question_refs(
                self.finalOutcome.unresolvedQuestionIds,
                f"Case '{self.caseId}' finalOutcome.unresolvedQuestionIds",
            )
            for insight in self.finalOutcome.finalInsights or []:
                validate_question_refs(
                    insight.relatedQuestionIds,
                    f"Case '{self.caseId}' finalInsight.relatedQuestionIds",
                )
                validate_hypothesis_refs(
                    insight.relatedHypothesisIds,
                    f"Case '{self.caseId}' finalInsight.relatedHypothesisIds",
                )
            for decision in self.finalOutcome.finalDecisions or []:
                validate_question_refs(
                    decision.targetQuestionIds,
                    f"Case '{self.caseId}' finalDecision.targetQuestionIds",
                )

        return self


# =========================================================
# 8. Paper-level wrapper
# =========================================================


class PaperUsageSpec(BaseModel):
    paperName: Optional[str] = Field(
        default=None,
        description="Paper title.",
    )
    systemName: Optional[str] = Field(
        default=None,
        description="System name, if available.",
    )
    systemSpecPath: Optional[str] = Field(
        default=None,
        description="Path to the linked system specification artifact when available.",
    )
    caseStudies: List[CaseStudySpec] = Field(
        ...,
        description="All extracted case studies in this paper.",
    )
    paperLevelUsageClaims: Optional[List[str]] = Field(
        default=None,
        description="Optional paper-level claims about how the system supports usage.",
    )
    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Paper-level evidence when needed.",
    )
    inferenceType: Optional[InferenceType] = Field(
        default=None,
        description="Whether paper-level usage claims are explicit or inferred.",
    )

    @field_validator("paperLevelUsageClaims", mode="before")
    @classmethod
    def normalize_claims(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        if not self.caseStudies:
            raise ValueError("PaperUsageSpec requires at least one CaseStudySpec.")

        self.paperLevelUsageClaims = _dedupe_strings(self.paperLevelUsageClaims)

        seen_case_ids: set[str] = set()
        for idx, case in enumerate(self.caseStudies, start=1):
            candidate = case.caseId or _slugify_identifier(case.caseTitle, f"case-{idx}")
            candidate = _make_unique_identifier(candidate, seen_case_ids)
            case.caseId = candidate

        return self
