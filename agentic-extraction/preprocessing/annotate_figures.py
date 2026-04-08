"""
Annotate extracted figures with semantic roles using a multimodal model.

Command-line usage:
- From `code-repo/`:
  `python agentic-extraction/preprocessing/annotate_figures.py ConceptViz`
- Batch mode:
  `python agentic-extraction/preprocessing/annotate_figures.py --all`

Expected inputs:
- `../data/figures/<paper>/figures.json`
- `../data/figures/<paper>/crops/fig_<n>.png`

Output:
- `../data/figures/<paper>/figure-manifest.json`

Configuration:
- Either:
  - provide `--vision-model`, `--api-key`, and `--base-url` together
  - or set `OPENAI_MODEL`, `OPENAI_API_KEY`, and `OPENAI_BASE_URL` in `.env`

Open-source notes:
- This script does not hard-code a vendor endpoint or model name.
- All published path examples are relative to `agentic-extraction/preprocessing/`.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Literal, Optional

from openai import OpenAI
from pydantic import BaseModel, Field, model_validator

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> bool:
        return False


load_dotenv()


SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_EXTRACTION_ROOT = SCRIPT_DIR.parent
DATA_ROOT = AGENTIC_EXTRACTION_ROOT / "data"
DEFAULT_FIGURES_ROOT = DATA_ROOT / "figures"
DEFAULT_FIGURES_ROOT_LABEL = Path("../data/figures")
VISION_MODEL_ENV_VARS = ("OPENAI_MODEL", "VISION_MODEL", "MODEL")
BASE_URL_ENV_VARS = ("OPENAI_BASE_URL", "BASE_URL")
API_KEY_ENV_VARS = ("OPENAI_API_KEY", "API_KEY")

FigureRole = Literal["interface", "view", "intended_workflow", "case_study", "evaluation", "other"]


def first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def resolve_path_arg(raw_value: str, default_label: Path, default_path: Path) -> Path:
    if raw_value == str(default_label):
        return default_path
    return Path(raw_value).expanduser().resolve()


def resolve_model_config(
    *,
    model: Optional[str],
    api_key: Optional[str],
    base_url: Optional[str],
) -> tuple[str, str, str]:
    cli_values = [model, api_key, base_url]
    if any(value for value in cli_values):
        if not all(value for value in cli_values):
            raise ValueError(
                "Use one configuration mode only: either pass --vision-model, --api-key, and --base-url together, "
                "or provide OPENAI_MODEL, OPENAI_API_KEY, and OPENAI_BASE_URL in .env."
            )
        return str(model), str(api_key), str(base_url)

    env_model = first_env(*VISION_MODEL_ENV_VARS)
    env_api_key = first_env(*API_KEY_ENV_VARS)
    env_base_url = first_env(*BASE_URL_ENV_VARS)
    if not (env_model and env_api_key and env_base_url):
        raise ValueError(
            "Missing model configuration. Either pass --vision-model, --api-key, and --base-url together, "
            "or set OPENAI_MODEL, OPENAI_API_KEY, and OPENAI_BASE_URL in .env."
        )
    return env_model, env_api_key, env_base_url


class FigureRoleScores(BaseModel):
    interface: float = Field(..., ge=0.0, le=1.0)
    view: float = Field(..., ge=0.0, le=1.0)
    intended_workflow: float = Field(..., ge=0.0, le=1.0)
    case_study: float = Field(..., ge=0.0, le=1.0)
    evaluation: float = Field(..., ge=0.0, le=1.0)
    other: float = Field(..., ge=0.0, le=1.0)


class FigureAnnotation(BaseModel):
    fig_id: str
    primary_role: FigureRole
    role_scores: FigureRoleScores
    rationale: str

    @model_validator(mode="after")
    def validate_consistency(self):
        score_map = {
            "interface": self.role_scores.interface,
            "view": self.role_scores.view,
            "intended_workflow": self.role_scores.intended_workflow,
            "case_study": self.role_scores.case_study,
            "evaluation": self.role_scores.evaluation,
            "other": self.role_scores.other,
        }
        max_role = max(score_map, key=score_map.get)
        if self.primary_role != max_role:
            self.primary_role = max_role
        return self


class FigureRecord(BaseModel):
    fig_id: str
    caption: str
    image_path: str
    primary_role: FigureRole
    role_scores: FigureRoleScores
    rationale: str
    interface_rank: int
    is_interface_figure: bool
    manual_verified: bool = False
    notes: Optional[str] = None


class FigureManifest(BaseModel):
    paper_name: str
    interface_figure_id: Optional[str]
    needs_manual_review: bool
    interface_selection_reason: str
    figures: list[FigureRecord]

    @model_validator(mode="after")
    def validate_payload(self):
        interface_count = sum(1 for item in self.figures if item.is_interface_figure)
        if self.interface_figure_id is None:
            if interface_count != 0:
                raise ValueError("FigureManifest with no interface_figure_id must not mark any figure as interface.")
            return self
        if interface_count != 1:
            raise ValueError("FigureManifest with interface_figure_id must contain exactly one interface figure.")
        if self.interface_figure_id not in {item.fig_id for item in self.figures}:
            raise ValueError("interface_figure_id must refer to a figure in `figures`.")
        return self


def encode_image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    with path.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def extract_text_content(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        parts: list[str] = []
        for item in message_content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


def load_figures_payload(figures_dir: Path) -> list[dict[str, Any]]:
    figures_json = figures_dir / "figures.json"
    if not figures_json.exists():
        raise FileNotFoundError(f"Missing figures metadata: {figures_json}")
    payload = json.loads(figures_json.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list in {figures_json}")
    return payload


def build_prompt(caption: str, fig_id: str) -> str:
    return (
        "You are classifying a figure extracted from a visual analytics paper.\n\n"
        "Classify this single figure based on the image and caption.\n"
        "You are judging only this figure, not selecting a figure globally across the paper.\n\n"
        "Use these roles:\n"
        "- interface: the complete main system interface, usually showing the overall application layout with multiple coordinated views or panels\n"
        "- view: a single view, panel, or local interface component; this is not the full system interface even if it is interactive\n"
        "- intended_workflow: a workflow, process, or analysis path explaining how the system should be used\n"
        "- case_study: a figure mainly showing a concrete analysis result, walkthrough, or use example\n"
        "- evaluation: evaluation or experimental result figures such as bar charts, line charts, scatter plots, box plots, ablation plots, benchmark comparisons, or user study summaries\n"
        "- other: algorithm illustration, background concept figure, dataset example, or anything else not covered above\n\n"
        "Score all roles conservatively.\n"
        "Important: only use `interface` for a full system interface. Use `view` for any single panel or partial UI.\n"
        "A main interface figure usually shows multiple coordinated views or panels of the system.\n\n"
        f"Figure id: {fig_id}\n"
        f"Caption:\n{caption}\n\n"
        "Return exactly one JSON object and nothing else.\n"
        "Use this schema:\n"
        "{\n"
        '  "fig_id": "<figure id>",\n'
        '  "primary_role": "interface|view|intended_workflow|case_study|evaluation|other",\n'
        '  "role_scores": {\n'
        '    "interface": 0.0,\n'
        '    "view": 0.0,\n'
        '    "intended_workflow": 0.0,\n'
        '    "case_study": 0.0,\n'
        '    "evaluation": 0.0,\n'
        '    "other": 0.0\n'
        "  },\n"
        '  "rationale": "<brief explanation>"\n'
        "}\n"
        "Scores must be floats between 0 and 1."
    )


def _extract_first_json_object(content: str) -> Optional[str]:
    start = content.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(content)):
        ch = content[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[start : idx + 1]
    return None


def _parse_float_field(content: str, label: str) -> Optional[float]:
    patterns = [
        rf"`?{re.escape(label)}`?\s*[:：]\s*([01](?:\.\d+)?)",
        rf'"{re.escape(label)}"\s*[:：]\s*([01](?:\.\d+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
            except ValueError:
                continue
            return max(0.0, min(1.0, value))
    return None


def _parse_text_fallback_annotation(content: str) -> Optional[FigureAnnotation]:
    score_labels = ["interface", "view", "intended_workflow", "case_study", "evaluation", "other"]
    scores: dict[str, float] = {}
    for label in score_labels:
        value = _parse_float_field(content, label)
        if value is None:
            return None
        scores[label] = value

    primary_role = max(scores, key=scores.get)
    rationale = content.strip()
    if len(rationale) > 1200:
        rationale = rationale[:1200].strip()

    fig_match = re.search(r"Figure id:\s*([A-Za-z0-9_\-]+)", content, re.IGNORECASE)
    fig_id = fig_match.group(1) if fig_match else "unknown"

    return FigureAnnotation(
        fig_id=fig_id,
        primary_role=primary_role,  # type: ignore[arg-type]
        role_scores=FigureRoleScores(**scores),
        rationale=rationale,
    )


def parse_annotation_response(content: str) -> FigureAnnotation:
    if not content:
        raise RuntimeError("The model returned empty content.")

    try:
        return FigureAnnotation.model_validate_json(content)
    except Exception:
        pass

    json_fragment = _extract_first_json_object(content)
    if json_fragment:
        try:
            return FigureAnnotation.model_validate_json(json_fragment)
        except Exception:
            pass

    fallback = _parse_text_fallback_annotation(content)
    if fallback is not None:
        return fallback

    raise RuntimeError(f"Failed to parse figure annotation response: {content[:1000]}")


def annotate_single_figure(
    client: OpenAI,
    model_name: str,
    image_path: Path,
    caption: str,
    fig_id: str,
) -> FigureAnnotation:
    prompt_text = build_prompt(caption, fig_id)
    image_url = encode_image_to_data_url(image_path)
    request = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You classify visual analytics figures into interface, intended workflow, "
                    "case study, evaluation, view, or other. Return exactly one JSON object with no markdown. "
                    "Only label a figure as interface if it shows the complete system interface."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    }

    try:
        response = client.chat.completions.create(
            **request,
            response_format={"type": "json_object"},
        )
    except Exception:
        response = client.chat.completions.create(**request)

    content = extract_text_content(response.choices[0].message.content)
    annotation = parse_annotation_response(content)
    annotation.fig_id = fig_id
    return annotation


def needs_manual_review(interface_scores: list[tuple[str, float]]) -> bool:
    if len(interface_scores) <= 1:
        return False
    ordered = sorted(interface_scores, key=lambda item: item[1], reverse=True)
    top_score = ordered[0][1]
    second_score = ordered[1][1]
    if top_score < 0.5:
        return True
    if (top_score - second_score) < 0.12:
        return True
    return False


def build_manifest(
    paper_name: str,
    figures_payload: list[dict[str, Any]],
    annotations: dict[str, FigureAnnotation],
    figures_dir: Path,
) -> FigureManifest:
    interface_scores: list[tuple[str, float]] = []
    interface_primary_candidates: list[tuple[str, float]] = []
    for item in figures_payload:
        fig_id = item["fig_id"]
        annotation = annotations[fig_id]
        interface_scores.append((fig_id, annotation.role_scores.interface))
        if annotation.primary_role == "interface":
            interface_primary_candidates.append((fig_id, annotation.role_scores.interface))

    ranked_interface = sorted(interface_scores, key=lambda item: item[1], reverse=True)
    ranked_primary_interface = sorted(interface_primary_candidates, key=lambda item: item[1], reverse=True)

    interface_figure_id: Optional[str] = None
    no_interface_found = False
    if ranked_primary_interface:
        interface_figure_id = ranked_primary_interface[0][0]
    else:
        no_interface_found = True

    manual_review = needs_manual_review(interface_scores)
    if no_interface_found:
        manual_review = True

    figures: list[FigureRecord] = []
    rank_lookup = {fig_id: idx for idx, (fig_id, _) in enumerate(ranked_interface, start=1)}
    cwd = Path.cwd().resolve()
    for item in figures_payload:
        fig_id = item["fig_id"]
        caption = (item.get("caption") or "").strip()
        image_path = figures_dir / "crops" / f"{fig_id}.png"
        if not image_path.exists():
            raise FileNotFoundError(f"Missing figure crop for {fig_id}: {image_path}")
        resolved_image_path = image_path.resolve()
        try:
            image_path_str = str(resolved_image_path.relative_to(cwd))
        except ValueError:
            image_path_str = str(resolved_image_path)
        annotation = annotations[fig_id]
        figures.append(
            FigureRecord(
                fig_id=fig_id,
                caption=caption,
                image_path=image_path_str,
                primary_role=annotation.primary_role,
                role_scores=annotation.role_scores,
                rationale=annotation.rationale,
                interface_rank=rank_lookup[fig_id],
                is_interface_figure=(interface_figure_id is not None and fig_id == interface_figure_id),
            )
        )

    top_score = ranked_interface[0][1] if ranked_interface else 0.0
    second_score = ranked_interface[1][1] if len(ranked_interface) > 1 else 0.0
    if interface_figure_id is None:
        reason = (
            "No figure was classified with primary_role=interface. "
            f"The highest interface score in the paper is {top_score:.2f}, so no interface figure was selected."
        )
        if manual_review:
            reason += " Manual review is recommended to confirm whether the paper lacks a full interface figure or the annotations are incorrect."
    else:
        reason = (
            f"Selected {interface_figure_id} as the unique interface figure because it has the "
            f"highest interface score ({top_score:.2f}); next best score is {second_score:.2f}."
        )
        if manual_review:
            reason += " Manual review is recommended because the interface selection is weak or ambiguous."

    return FigureManifest(
        paper_name=paper_name,
        interface_figure_id=interface_figure_id,
        needs_manual_review=manual_review,
        interface_selection_reason=reason,
        figures=figures,
    )


def annotate_figures_for_paper(
    paper_name: str,
    figures_root: Path = DEFAULT_FIGURES_ROOT,
    vision_model: str = "",
    api_key: str = "",
    base_url: str = "",
    overwrite: bool = False,
) -> Path:
    figures_dir = figures_root / paper_name
    output_path = figures_dir / "figure-manifest.json"
    if output_path.exists() and not overwrite:
        return output_path

    figures_payload = load_figures_payload(figures_dir)

    client = OpenAI(api_key=api_key, base_url=base_url)

    annotations: dict[str, FigureAnnotation] = {}
    for item in figures_payload:
        fig_id = item["fig_id"]
        caption = (item.get("caption") or "").strip()
        image_path = figures_dir / "crops" / f"{fig_id}.png"
        if not image_path.exists():
            raise FileNotFoundError(f"Missing figure crop for {fig_id}: {image_path}")
        annotations[fig_id] = annotate_single_figure(
            client=client,
            model_name=vision_model,
            image_path=image_path,
            caption=caption,
            fig_id=fig_id,
        )

    manifest = build_manifest(paper_name, figures_payload, annotations, figures_dir)
    output_path.write_text(
        json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Annotate extracted figures with richer roles using a multimodal LLM."
    )
    parser.add_argument(
        "paper_name",
        nargs="?",
        help="Paper name under ../data/figures/. Omit when using --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Annotate all papers under the figures root that contain figures.json.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing figure-manifest.json. By default existing manifests are kept.",
    )
    parser.add_argument(
        "--figures-root",
        default=str(DEFAULT_FIGURES_ROOT_LABEL),
        help="Root directory containing per-paper figure folders. Defaults to ../data/figures.",
    )
    parser.add_argument(
        "--vision-model",
        help="Vision model name. Must be passed together with --api-key and --base-url unless .env is used.",
    )
    parser.add_argument(
        "--api-key",
        help="API key. Must be passed together with --vision-model and --base-url unless .env is used.",
    )
    parser.add_argument(
        "--base-url",
        help="OpenAI-compatible base URL. Must be passed together with --vision-model and --api-key unless .env is used.",
    )
    args = parser.parse_args()
    if args.all and args.paper_name:
        parser.error("Provide either a paper_name or --all, not both.")
    if not args.all and not args.paper_name:
        parser.error("Provide a paper_name or use --all.")
    return args


def iter_paper_names(figures_root: Path) -> list[str]:
    papers: list[str] = []
    for figures_json in sorted(figures_root.glob("*/figures.json")):
        papers.append(figures_json.parent.name)
    return papers


def main() -> None:
    args = parse_args()
    vision_model, api_key, base_url = resolve_model_config(
        model=args.vision_model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    figures_root = resolve_path_arg(
        args.figures_root,
        DEFAULT_FIGURES_ROOT_LABEL,
        DEFAULT_FIGURES_ROOT,
    )

    if args.all:
        paper_names = iter_paper_names(figures_root)
        if not paper_names:
            raise FileNotFoundError(f"No figures.json files found under {figures_root}")
        for paper_name in paper_names:
            try:
                manifest_path = annotate_figures_for_paper(
                    paper_name=paper_name,
                    figures_root=figures_root,
                    vision_model=vision_model,
                    api_key=api_key,
                    base_url=base_url,
                    overwrite=args.overwrite,
                )
                print(f"Saved figure manifest -> {manifest_path}")
            except Exception as exc:
                print(f"{paper_name}: failed -> {exc}")
        return

    manifest_path = annotate_figures_for_paper(
        paper_name=args.paper_name,
        figures_root=figures_root,
        vision_model=vision_model,
        api_key=api_key,
        base_url=base_url,
        overwrite=args.overwrite,
    )
    print(f"Saved figure manifest -> {manifest_path}")


if __name__ == "__main__":
    main()
