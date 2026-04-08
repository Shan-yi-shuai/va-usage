from __future__ import annotations

import hashlib
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.schemas.schema_common import (
    CapabilityRef,
    EvidenceReference,
    IdentifierString,
    NameSource,
    OthersString,
    ViewRef,
    _dedupe_strings,
    _make_unique_identifier,
    _slugify_identifier,
)


def _abbreviate_slug(value: str) -> str:
    parts = [part for part in value.replace(".", "-").split("-") if part]
    if not parts:
        return "x"
    return "".join(part[0] for part in parts)


def _short_ref_token(ref: ViewRef) -> str:
    if ref.subViewId:
        sub_part = ref.subViewId.split(".", 1)[-1]
        return f"{_abbreviate_slug(ref.viewId)}-{_abbreviate_slug(sub_part)}"
    return _abbreviate_slug(ref.viewId)


def _short_coordination_type(value: str) -> str:
    return _abbreviate_slug(value)


def _make_coordination_identifier(
    source: ViewRef,
    coordination_type: str,
    targets: List[ViewRef],
) -> str:
    payload = "|".join(
        [
            source.viewId,
            source.subViewId or "",
            coordination_type,
            *[
                f"{target.viewId}:{target.subViewId or ''}"
                for target in targets
            ],
        ]
    )
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:6]
    return f"coord-{_short_ref_token(source)}-{_short_coordination_type(coordination_type)}-{digest}"


# =========================
# 1. Data ontology taxonomy
# =========================

DatasetType = Union[
    Literal[
        "Tables",
        "NetworksAndTrees",
        "Fields",
        "Geometry",
        "ClusterSetLists",
        "Text",
        "Temporal",
        "Media",
        "Parameter",
    ],
    OthersString,
]
"""
DatasetType taxonomy value.
If not covered by the fixed taxonomy, use others(<description>).
"""

DataType = Union[
    Literal[
        "Item",
        "Items",
        "ItemNodes",
        "Links",
        "Attributes",
        "Position",
        "GridPositions",
    ],
    OthersString,
]
"""
DataType taxonomy value.
If not covered by the fixed taxonomy, use others(<description>).
"""

AttributeType = Union[
    Literal[
        "Categorical",
        "Ordinal",
        "Quantitative",
    ],
    OthersString,
]
"""
AttributeType taxonomy value.
If not covered by the fixed taxonomy, use others(<description>).
"""

OrderingDirection = Union[
    Literal[
        "Sequential",
        "Diverging",
        "Cyclic",
    ],
    OthersString,
]
"""
OrderingDirection taxonomy value.
If not covered by the fixed taxonomy, use others(<description>).
"""


class DataOntology(BaseModel):
    """Data ontology annotation for the system (taxonomy-based)."""

    datasetType: Optional[List[DatasetType]] = Field(
        default=None,
        description=(
            "High-level dataset form(s) based on DatasetType taxonomy. "
            "Multiple values are allowed when a system uses multiple dataset forms. "
            "If not covered, use others(<description>)."
        ),
    )

    dataType: Optional[List[DataType]] = Field(
        default=None,
        description=(
            "Data entity/structure types based on DataType taxonomy. "
            "Multiple values are allowed when a system uses multiple structures. "
            "If not covered, use others(<description>)."
        ),
    )

    attributeType: Optional[List[AttributeType]] = Field(
        default=None,
        description=(
            "Attribute types involved in the system (categorical/ordinal/quantitative) "
            "based on AttributeType taxonomy. Multiple values are allowed. "
            "If not covered, use others(<description>)."
        ),
    )

    orderingDirection: Optional[List[OrderingDirection]] = Field(
        default=None,
        description=(
            "Ordering/scale direction types (sequential/diverging/cyclic) "
            "based on OrderingDirection taxonomy, when applicable (e.g., color scales). "
            "Multiple values are allowed. If not covered, use others(<description>)."
        ),
    )


# =========================
# 2. System category taxonomy
# =========================

SystemCategoryLevel1 = Union[
    Literal[
        "A DS/ML",
        "B Social / Info Ecosystem",
        "C Geo / Urban / Mobility",
        "D Health / Public Health",
        "E Cybersecurity / Risk",
        "F Finance / Business / Operations",
        "G Science / Engineering",
        "H Gov / Legal / Policy",
        "I Education / Collaboration",
    ],
    OthersString,
]
"""
Level-1 system category taxonomy value.
If not covered by the fixed taxonomy, use others(<description>).
"""

SystemCategoryLevel2 = Union[
    Literal[
        # A
        "A1 XAI / Model Understanding",
        "A2 Debugging/Training",
        "A3 AutoML / Feature Engineering / Pipeline",
        "A4 Responsible AI (Fairness/Bias/Compliance)",
        # B
        "B1 Topic/Propagation",
        "B2 Sentiment/Opinion",
        "B3 Community/Interaction",
        "B4 Moderation/Misinformation",
        # C
        "C1 Mobility/Traffic",
        "C2 Urban Ops/IoT",
        "C3 Planning/Siting",
        "C4 Crisis/Resilience",
        # D
        "D1 Clinical Decision",
        "D2 EHR/Patient Journey",
        "D3 Epidemiology/Surveillance",
        "D4 Imaging Workflow",
        # E
        "E1 Situation Awareness",
        "E2 Threat Hunting",
        "E3 Malware/Vuln",
        "E4 SIEM/Alert Triage",
        # F
        "F1 Market/Trading",
        "F2 Risk/Fraud",
        "F3 Customer/CRM",
        "F4 Ops/Supply Chain",
        # G
        "G1 Simulation/Uncertainty",
        "G2 Scientific Observations",
        "G3 Manufacturing/QA",
        "G4 DevOps/AIOps",
        # H
        "H1 Policy Analytics",
        "H2 Public Safety/Justice",
        "H3 Compliance/Audit",
        # I
        "I1 Learning Analytics",
        "I2 Collaborative VA",
        "I3 Human-AI Teaming",
    ],
    OthersString,
]
"""
Level-2 system category taxonomy value.
If not covered by the fixed taxonomy, use others(<description>).
"""


class SystemCategory(BaseModel):
    """Two-level system category annotation."""

    level1: SystemCategoryLevel1 = Field(
        ...,
        description=(
            "High-level domain category (Level-1). "
            "Must be one of the predefined Level-1 categories or others(<description>)."
        ),
    )

    level2: Optional[List[SystemCategoryLevel2]] = Field(
        default=None,
        description=(
            "Sub-category / task-level classification (Level-2). "
            "Multiple values are allowed when the system spans multiple sub-tasks. "
            "Each value must be one of the predefined Level-2 categories or others(<description>)."
        ),
    )

    @model_validator(mode="after")
    def validate_level_prefix(self):
        if not self.level2 or str(self.level1).startswith("others("):
            return self

        expected_prefix = str(self.level1).split()[0][:1]
        for item in self.level2:
            if str(item).startswith("others("):
                continue
            if not str(item).startswith(expected_prefix):
                raise ValueError(
                    f"Level-2 category '{item}' is inconsistent with Level-1 category '{self.level1}'."
                )
        return self


# =========================
# 3. SystemInfo
# =========================


class SystemInfo(BaseModel):
    """Information about the overall system."""

    systemName: Optional[str] = Field(
        None,
        description="Name of the visual analytics system, as used in the paper.",
    )

    dataOntology: Optional[DataOntology] = Field(
        default=None,
        description=(
            "Data ontology annotation for the system, based on the provided data taxonomy. "
            "If the taxonomy cannot describe a case, use others(<description>) in the corresponding field."
        ),
    )

    systemCategory: Optional[List[SystemCategory]] = Field(
        default=None,
        description=(
            "Two-level system classification. "
            "Level-1 indicates the broad application domain; Level-2 indicates specific tasks/subdomains. "
            "Both levels allow others(<description>) when the taxonomy cannot describe a case."
        ),
    )


# =========================
# 4. Visualization view style schema
# =========================


class EncodingInfo(BaseModel):
    """Information about a single encoding channel."""

    field: str = Field(
        ...,
        description="Data field name as used in the system (e.g., 'time', 'country').",
    )

    type: str = Field(
        ...,
        description=(
            "Data type or role of the field in the visualization, e.g., "
            "quantitative, ordinal, nominal, key, identifier, derived attribute, etc."
        ),
    )

    description: str = Field(
        ...,
        description="Textual description of how this field is encoded or interpreted.",
    )


class LayerEncoding(BaseModel):
    """Encodings on different channels for one layer / mark."""

    x: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on the x channel (if any).",
    )

    y: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on the y channel (if any).",
    )

    color: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on the color channel (if any).",
    )

    size: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on the size channel (if any).",
    )

    shape: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on the shape channel (if any).",
    )

    opacity: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on the opacity channel (if any).",
    )

    text: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded as textual labels or annotations (if any).",
    )

    row: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded through row faceting or small multiples (if any).",
    )

    column: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded through column faceting or small multiples (if any).",
    )

    latitude: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on map latitude or vertical geo position (if any).",
    )

    longitude: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields encoded on map longitude or horizontal geo position (if any).",
    )

    source: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields bound to edge/link sources in graph-like views (if any).",
    )

    target: Optional[List[EncodingInfo]] = Field(
        default=None,
        description="List of data fields bound to edge/link targets in graph-like views (if any).",
    )


class LayerInfo(BaseModel):
    """Information about styles of a single layer / mark in a visualization view."""

    layerId: Optional[IdentifierString] = Field(
        default=None,
        description=(
            "Canonical identifier for this visual layer. When omitted, a deterministic identifier can be "
            "generated."
        ),
    )

    markType: str = Field(
        ...,
        description="Mark type, e.g., point, line, bar, area, node, edge, text.",
    )

    encoding: LayerEncoding = Field(
        ...,
        description="Encodings on different channels for this layer.",
    )


class ViewStyleInfo(BaseModel):
    """Visual style specification of a single visualization view or sub-view."""

    layers: List[LayerInfo] = Field(
        ...,
        description="Information about styles of multiple layers / marks in this view.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Optional evidence supporting the visual style extraction.",
    )


SubviewCapabilityKind = Literal[
    "Interaction",
    "Information",
]


class SubviewCapability(BaseModel):
    """A user-visible capability offered by a sub-view."""

    capabilityId: Optional[IdentifierString] = Field(
        default=None,
        description=(
            "Canonical identifier for this capability. When omitted, a deterministic identifier can be "
            "generated."
        ),
    )

    capabilityKind: SubviewCapabilityKind = Field(
        ...,
        description="Whether this capability is an interaction affordance or an information affordance.",
    )

    capabilityName: str = Field(
        ...,
        description=(
            "Short label for the capability, e.g., `Search`, `Brush`, `Hover`, `Show Ranked Features`, "
            "or `Show Token Activations`."
        ),
    )

    description: str = Field(
        ...,
        description=(
            "What the user can do in this sub-view or what information the user can directly obtain from it."
        ),
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Optional evidence supporting this capability extraction.",
    )

    @model_validator(mode="after")
    def validate_payload(self):
        return self


# =========================
# 5. Processing schema
# =========================


class DataProcessingStep(BaseModel):
    """
    A general data processing or analytic step in the system,
    capable of representing both algorithms and models (traditional ML,
    deep learning, LLMs, encoders, rule-based systems, etc.).
    """

    name: str = Field(
        ...,
        description=(
            "The explicit name of this processing step, e.g., "
            "'k-means clustering', 't-SNE embedding', 'Transformer encoder', "
            "'BERT-based classifier', 'LLM reasoning module', "
            "'neural renderer', 'feature aggregation'."
        ),
    )

    category: str = Field(
        ...,
        description=(
            "High-level category such as DR, clustering, ML model, deep learning model, "
            "LLM, encoder, graph neural network, rule-based system, regression, "
            "statistics, feature extraction, recommendation, or pipeline stage."
        ),
    )

    description: str = Field(
        ...,
        description=(
            "Textual description of what this step does in this system, "
            "including its role, transformation, objective, or analysis purpose."
        ),
    )

    input: Optional[List[str]] = Field(
        default=None,
        description=(
            "Input data sources, field names, or intermediate representations "
            "used by this step (e.g., raw data, embeddings, graph, time series)."
        ),
    )

    output: Optional[List[str]] = Field(
        default=None,
        description=(
            "Output or derived attributes (e.g., cluster_id, embedding_2d, "
            "llm_summary, feature_vector, predicted_label)."
        ),
    )

    tasks: Optional[List[str]] = Field(
        default=None,
        description=(
            "High-level analytic tasks supported by this step, "
            "e.g., cluster comparison, anomaly detection, classification, "
            "trend analysis, summarization, recommendation."
        ),
    )


class ViewProcessingInfo(BaseModel):
    """All data processing steps associated with a particular view or sub-view."""

    processingSteps: List[DataProcessingStep] = Field(
        ...,
        description="One view may rely on multiple data processing steps.",
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Optional evidence supporting the processing extraction.",
    )


# =========================
# 6. Non-visual view taxonomy
# =========================

ViewKind = Union[
    Literal[
        "Chatbox",
        "StructuredText",
        "Control",
        "DataPreview",
        "Navigation",
        "Inspector",
        "Form",
        "DashboardContainer",
        "SearchBox",
        "TextInput",
        "ListView",
        "TableView",
        "MediaViewer",
    ],
    OthersString,
]
"""
High-level kind of a view.
Use others(<description>) if the kind cannot be described by the fixed set.
"""

StructuredTextLayout = Union[
    Literal[
        "PlainText",
        "Card",
        "TableLike",
        "List",
        "Timeline",
        "MindMap",
        "Tree",
        "Markdown",
        "RichText",
        "CodeBlock",
    ],
    OthersString,
]
"""
Layout/representation style for structured text views.
Use others(<description>) if the layout cannot be described by the fixed set.
"""

ControlType = Union[
    Literal[
        "Button",
        "Dropdown",
        "MultiSelect",
        "Checkbox",
        "Radio",
        "Slider",
        "RangeSlider",
        "TextInput",
        "SearchBox",
        "Toggle",
        "DatePicker",
        "LegendControl",
        "BrushControl",
    ],
    OthersString,
]
"""
UI control types for control-oriented views.
Use others(<description>) if the control type cannot be described by the fixed set.
"""

PreviewType = Union[
    Literal[
        "Image",
        "Table",
        "Video",
        "Audio",
        "Document",
        "Code",
        "JSON",
        "TextSnippet",
    ],
    OthersString,
]
"""
Data preview types for preview/inspector views.
Use others(<description>) if the preview type cannot be described by the fixed set.
"""

NonVisualSubKind = Union[StructuredTextLayout, ControlType, PreviewType, OthersString]
"""
Subtype taxonomy for a non-visual view.

- If viewKind is StructuredText, subKind should typically be a StructuredTextLayout value.
- If viewKind is Control, subKind should typically be a ControlType value.
- If viewKind is DataPreview (or Inspector when it mainly previews data), subKind should typically be a PreviewType value.
- For other view kinds, use others(<description>) when finer-grained subtype information is useful.
"""


class NonVisualViewSpec(BaseModel):
    """Specification for non-visual views, with kind, optional subtype, and description."""

    viewKind: ViewKind = Field(
        ...,
        description=(
            "High-level kind of this non-visual view. "
            "Must be one of the predefined ViewKind values (e.g., Chatbox, StructuredText, Control, "
            "DataPreview, Navigation, Inspector, Form, DashboardContainer) or others(<description>)."
        ),
    )

    subKind: Optional[NonVisualSubKind] = Field(
        default=None,
        description=(
            "Optional finer-grained subtype under the chosen viewKind, used to capture form factors "
            "such as Card/MindMap/Markdown for structured text, Slider/Dropdown for controls, "
            "or Image/Table/JSON for previews."
        ),
    )

    description: str = Field(
        ...,
        description=(
            "Textual description of the non-visual view, including its purpose, what content it shows, "
            "and how users interact with it."
        ),
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Optional evidence supporting the non-visual view extraction.",
    )


# =========================
# 7. Coordination schema
# =========================


class CoordinationEffect(BaseModel):
    """Effect of an interaction on a target view or sub-view."""

    action: str = Field(
        ...,
        description=(
            "Action type, e.g., filter, highlight, navigate, reconfigure, select, drill-down, "
            "request-details, open-preview, update-parameter, generate-text, or other system-defined actions."
        ),
    )

    target: ViewRef = Field(
        ...,
        description="Canonical target view/sub-view that actually changes.",
    )

    category: Optional[str] = Field(
        default=None,
        description=(
            "Data category for the action, e.g., data item, group, time range, parameter, "
            "document, entity, model, pipeline step, or other categories used in the system."
        ),
    )

    changeMode: Optional[str] = Field(
        default=None,
        description="How the result is changed, e.g., add, remove, replace, toggle, append, overwrite.",
    )


class ViewCoordinationInfo(BaseModel):
    """Coordination specification between views or sub-views."""

    coordinationId: Optional[IdentifierString] = Field(
        default=None,
        description=(
            "Canonical identifier for this coordination relationship. "
            "When omitted, a deterministic identifier can be generated."
        ),
    )

    source: ViewRef = Field(
        ...,
        description="Canonical source view/sub-view that triggers the interaction.",
    )

    sourceCapabilityRef: Optional[CapabilityRef] = Field(
        default=None,
        description=(
            "Preferred reference to the user-visible capability on the source sub-view that triggers this "
            "coordination."
        ),
    )

    targets: List[ViewRef] = Field(
        ...,
        description="Canonical target view/sub-view nodes that receive the effect.",
    )

    targetCapabilityRefs: Optional[List[CapabilityRef]] = Field(
        default=None,
        description=(
            "Preferred references to the user-visible capabilities on target sub-views that are updated or "
            "activated by this coordination."
        ),
    )

    coordinationType: str = Field(
        ...,
        description=(
            "Coordination type, e.g., brushing-linking, overview-detail, drill-down, "
            "details-on-demand, synchronized-scrolling, parameter-binding, "
            "history-navigation, or other coordination patterns."
        ),
    )

    evidence: EvidenceReference = Field(
        ...,
        description="Evidence supporting the coordination relationship as a whole.",
    )

    @model_validator(mode="after")
    def validate_targets(self):
        seen: set[tuple[str, Optional[str]]] = set()
        deduped: List[ViewRef] = []
        for ref in self.targets:
            key = (ref.viewId, ref.subViewId)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ref)
        self.targets = deduped
        if self.targetCapabilityRefs:
            seen_caps: set[tuple[str, str, str]] = set()
            deduped_caps: List[CapabilityRef] = []
            for ref in self.targetCapabilityRefs:
                key = (ref.viewId, ref.subViewId, ref.capabilityId)
                if key in seen_caps:
                    continue
                seen_caps.add(key)
                deduped_caps.append(ref)
            self.targetCapabilityRefs = deduped_caps
        if self.sourceCapabilityRef is None and not self.targetCapabilityRefs:
            raise ValueError(
                "ViewCoordinationInfo requires capability refs to explain the coordination relationship."
            )
        return self


# =========================
# 8. View / sub-view containers
# =========================


class SubView(BaseModel):
    """A sub-view inside a higher-level view; can be visual or non-visual."""

    subViewId: Optional[IdentifierString] = Field(
        default=None,
        description=(
            "Canonical identifier for this sub-view. "
            "When omitted, a deterministic identifier can be generated."
        ),
    )

    subViewName: Optional[str] = Field(
        default=None,
        description="Human-readable name/identifier for this sub-view, if available.",
    )

    nameSource: Optional[NameSource] = Field(
        default=None,
        description="How subViewName was obtained.",
    )

    aliases: Optional[List[str]] = Field(
        default=None,
        description="Optional alternate labels or references used for this sub-view (e.g., figure callouts).",
    )

    description: Optional[str] = Field(
        default=None,
        description=(
            "Brief description of this sub-view, combining its approximate role/content and relative position "
            "(e.g., 'concept search panel on the left', 'detail table in the lower-right')."
        ),
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Optional evidence supporting the sub-view as a coherent UI unit.",
    )

    isVisualizationView: bool = Field(
        ...,
        description=(
            "Whether this sub-view is a visualization view. "
            "If true, viewStyleInfo must be provided and nonVisualViewSpec must be omitted. "
            "If false, nonVisualViewSpec must be provided and viewStyleInfo must be omitted."
        ),
    )

    viewStyleInfo: Optional[ViewStyleInfo] = Field(
        default=None,
        description="Visualization-oriented style specification. Provide when isVisualizationView is true.",
    )

    nonVisualViewSpec: Optional[NonVisualViewSpec] = Field(
        default=None,
        description="Non-visual view specification. Provide when isVisualizationView is false.",
    )

    viewProcessingInfo: Optional[ViewProcessingInfo] = Field(
        default=None,
        description="Processing steps and analytic pipelines supporting this sub-view.",
    )

    capabilities: Optional[List[SubviewCapability]] = Field(
        default=None,
        description=(
            "User-visible capabilities of this sub-view. These capture what the user can directly do in the "
            "sub-view or what information the sub-view can directly provide."
        ),
    )

    @field_validator("aliases", mode="before")
    @classmethod
    def normalize_aliases(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.aliases = _dedupe_strings(self.aliases)

        if self.subViewName and self.nameSource is None:
            self.nameSource = "explicit"
        if not self.subViewName and self.nameSource is None:
            self.nameSource = "generated"

        if self.isVisualizationView:
            if self.viewStyleInfo is None:
                raise ValueError("Visualization sub-views must include viewStyleInfo.")
            if self.nonVisualViewSpec is not None:
                raise ValueError("Visualization sub-views cannot include nonVisualViewSpec.")
        else:
            if self.nonVisualViewSpec is None:
                raise ValueError("Non-visual sub-views must include nonVisualViewSpec.")
            if self.viewStyleInfo is not None:
                raise ValueError("Non-visual sub-views cannot include viewStyleInfo.")
        return self


class ViewSpec(BaseModel):
    """Per-view specification: each element corresponds to one logical view grouping."""

    viewId: Optional[IdentifierString] = Field(
        default=None,
        description=(
            "Canonical identifier for this view. "
            "When omitted, a deterministic identifier can be generated."
        ),
    )

    viewName: Optional[str] = Field(
        default=None,
        description="Human-readable label for this view, if available.",
    )

    nameSource: Optional[NameSource] = Field(
        default=None,
        description="How viewName was obtained.",
    )

    aliases: Optional[List[str]] = Field(
        default=None,
        description="Optional alternate labels or references used for this view (e.g., 'Fig. 1c').",
    )

    description: Optional[str] = Field(
        default=None,
        description="Brief description of the overall role of this top-level view.",
    )

    viewImages: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of local file paths to image assets representing this view "
            "(e.g., screenshots, figure sub-images, UI captures)."
        ),
    )

    evidence: Optional[EvidenceReference] = Field(
        default=None,
        description="Optional evidence supporting the existence and identity of this view.",
    )

    subViews: List[SubView] = Field(
        ...,
        description="List of sub-views contained in this view.",
    )

    @field_validator("aliases", "viewImages", mode="before")
    @classmethod
    def normalize_string_lists(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.aliases = _dedupe_strings(self.aliases)
        self.viewImages = _dedupe_strings(self.viewImages)

        if self.viewName and self.nameSource is None:
            self.nameSource = "explicit"
        if not self.viewName and self.nameSource is None:
            self.nameSource = "generated"

        if not self.subViews:
            raise ValueError("ViewSpec must contain at least one SubView.")
        return self


# =========================
# 9. Top-level SystemSpec
# =========================


class SystemSpec(BaseModel):
    """Top-level specification of a VA system."""

    paperName: Optional[str] = Field(
        None,
        description="Name of the paper.",
    )

    systemInfo: SystemInfo = Field(
        ...,
        description="Information about the overall system, including taxonomy annotations.",
    )

    viewsInfo: List[ViewSpec] = Field(
        ...,
        description="Canonical per-view specifications for the system.",
    )

    coordinationInfo: Optional[List[ViewCoordinationInfo]] = Field(
        default=None,
        description="Coordination relationships between views or sub-views.",
    )

    @model_validator(mode="after")
    def populate_ids_and_validate_refs(self):
        if not self.viewsInfo:
            raise ValueError("SystemSpec requires at least one ViewSpec in viewsInfo.")

        seen_view_ids: set[str] = set()
        seen_subview_ids: set[str] = set()
        seen_coordination_ids: set[str] = set()
        valid_refs: set[tuple[str, Optional[str]]] = set()
        valid_capability_refs: set[tuple[str, str, str]] = set()

        for view_index, view in enumerate(self.viewsInfo, start=1):
            base_view_id = view.viewId or _slugify_identifier(view.viewName, f"view-{view_index}")
            view.viewId = _make_unique_identifier(base_view_id, seen_view_ids)
            valid_refs.add((view.viewId, None))

            local_sub_ids: set[str] = set()
            for sub_index, sub_view in enumerate(view.subViews, start=1):
                base_sub_id = sub_view.subViewId or _slugify_identifier(
                    sub_view.subViewName,
                    f"subview-{sub_index}",
                )
                if not base_sub_id.startswith(f"{view.viewId}."):
                    base_sub_id = f"{view.viewId}.{base_sub_id}"
                candidate = _make_unique_identifier(base_sub_id, local_sub_ids)
                if candidate in seen_subview_ids:
                    candidate = _make_unique_identifier(candidate, seen_subview_ids)
                else:
                    seen_subview_ids.add(candidate)
                sub_view.subViewId = candidate
                valid_refs.add((view.viewId, sub_view.subViewId))

                if sub_view.viewStyleInfo:
                    seen_layer_ids: set[str] = set()
                    for layer_index, layer in enumerate(sub_view.viewStyleInfo.layers, start=1):
                        base_layer_id = layer.layerId or _slugify_identifier(
                            layer.markType,
                            f"layer-{layer_index}",
                        )
                        if not base_layer_id.startswith(f"{sub_view.subViewId}."):
                            base_layer_id = f"{sub_view.subViewId}.{base_layer_id}"
                        layer.layerId = _make_unique_identifier(base_layer_id, seen_layer_ids)

                if sub_view.capabilities:
                    seen_capability_ids: set[str] = set()
                    for capability_index, capability in enumerate(sub_view.capabilities, start=1):
                        base_capability_id = capability.capabilityId or _slugify_identifier(
                            capability.capabilityName,
                            f"capability-{capability_index}",
                        )
                        if not base_capability_id.startswith(f"{sub_view.subViewId}."):
                            base_capability_id = f"{sub_view.subViewId}.{base_capability_id}"
                        capability.capabilityId = _make_unique_identifier(
                            base_capability_id,
                            seen_capability_ids,
                        )
                        valid_capability_refs.add(
                            (view.viewId, sub_view.subViewId, capability.capabilityId)
                        )

        def validate_ref(ref: ViewRef, label: str) -> None:
            key = (ref.viewId, ref.subViewId)
            if key not in valid_refs:
                raise ValueError(f"{label} references unknown view/sub-view: {ref.model_dump()}")

        def validate_capability_ref(ref: CapabilityRef, label: str) -> None:
            key = (ref.viewId, ref.subViewId, ref.capabilityId)
            if key not in valid_capability_refs:
                raise ValueError(
                    f"{label} references unknown view/sub-view capability: {ref.model_dump()}"
                )

        for item in self.coordinationInfo or []:
            base_coordination_id = item.coordinationId or _make_coordination_identifier(
                item.source,
                item.coordinationType,
                item.targets,
            )
            item.coordinationId = _make_unique_identifier(
                base_coordination_id,
                seen_coordination_ids,
            )

            validate_ref(item.source, "Coordination source")
            if item.sourceCapabilityRef is not None:
                validate_capability_ref(item.sourceCapabilityRef, "Coordination source capability")
                if (
                    item.sourceCapabilityRef.viewId != item.source.viewId
                    or item.sourceCapabilityRef.subViewId != item.source.subViewId
                ):
                    raise ValueError(
                        "Coordination sourceCapabilityRef must belong to the declared coordination source."
                    )
            for target_index, target in enumerate(item.targets, start=1):
                validate_ref(target, f"Coordination target {target_index}")
            for target_cap_index, target_cap in enumerate(item.targetCapabilityRefs or [], start=1):
                validate_capability_ref(
                    target_cap,
                    f"Coordination target capability {target_cap_index}",
                )
                target_key = (target_cap.viewId, target_cap.subViewId)
                valid_target_keys = {
                    (target.viewId, target.subViewId)
                    for target in item.targets
                }
                if target_key not in valid_target_keys:
                    raise ValueError(
                        "Coordination targetCapabilityRefs must belong to one of the declared coordination "
                        "targets."
                    )

        return self
