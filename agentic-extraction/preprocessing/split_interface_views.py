"""
Split an interface figure into top-level view crops with a multimodal model.

Command-line usage:
- From `code-repo/`:
  `python agentic-extraction/preprocessing/split_interface_views.py ConceptViz`
- Batch mode:
  `python agentic-extraction/preprocessing/split_interface_views.py --all`

Expected input:
- `../data/figures/<paper>/figure-manifest.json`

Outputs:
- `../data/view-images/<paper>/<n>.png`
- `../data/view-images/<paper>/manifest.json`

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
from pathlib import Path
from typing import Any, List, Optional, Union

from PIL import Image
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> bool:
        return False


load_dotenv()


SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_EXTRACTION_ROOT = SCRIPT_DIR.parent
DATA_ROOT = AGENTIC_EXTRACTION_ROOT / "data"
DEFAULT_OUTPUT_ROOT = DATA_ROOT / "view-images"
DEFAULT_OUTPUT_ROOT_LABEL = Path("../data/view-images")
DEFAULT_FIGURES_ROOT = DATA_ROOT / "figures"
DEFAULT_FIGURES_ROOT_LABEL = Path("../data/figures")
VISION_MODEL_ENV_VARS = ("OPENAI_MODEL", "VISION_MODEL", "MODEL")
BASE_URL_ENV_VARS = ("OPENAI_BASE_URL", "BASE_URL")
API_KEY_ENV_VARS = ("OPENAI_API_KEY", "API_KEY")
MIN_BOX_SIZE = 24
MAX_COORD = 1000


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


class ViewRegion(BaseModel):
    view_id: Union[str, int] = Field(..., description="Stable temporary identifier such as view-1.")
    short_label: Optional[str] = Field(
        default=None,
        description="Short descriptive label if the caption names the region.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief explanation of what this view shows or controls.",
    )
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence that this is a distinct top-level view.",
    )
    left: int = Field(..., ge=0, le=MAX_COORD)
    top: int = Field(..., ge=0, le=MAX_COORD)
    right: int = Field(..., ge=0, le=MAX_COORD)
    bottom: int = Field(..., ge=0, le=MAX_COORD)

    @field_validator("right")
    @classmethod
    def validate_right(cls, value: int, info):
        left = info.data.get("left", 0)
        if value <= left:
            raise ValueError("right must be greater than left")
        return value

    @field_validator("bottom")
    @classmethod
    def validate_bottom(cls, value: int, info):
        top = info.data.get("top", 0)
        if value <= top:
            raise ValueError("bottom must be greater than top")
        return value

    @field_validator("view_id", mode="before")
    @classmethod
    def normalize_view_id(cls, value: Union[str, int]) -> str:
        if isinstance(value, int):
            return f"view-{value}"
        text = str(value).strip()
        if text.isdigit():
            return f"view-{text}"
        return text


class ViewRegionList(BaseModel):
    items: List[ViewRegion]


class NoInterfaceFigureError(RuntimeError):
    """Raised when a paper has no selected interface figure in its manifest."""


def encode_image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    with path.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def load_caption(args: argparse.Namespace) -> str:
    if args.caption:
        return args.caption.strip()
    if args.caption_file:
        return Path(args.caption_file).read_text(encoding="utf-8").strip()
    raise ValueError("Provide --caption or --caption-file.")


def load_interface_figure_from_manifest(
    paper_name: str,
    figures_root: Path = DEFAULT_FIGURES_ROOT,
) -> tuple[Path, str]:
    figures_dir = figures_root / paper_name
    manifest_path = figures_dir / "figure-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing figure manifest: {manifest_path}")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    interface_figure_id = payload.get("interface_figure_id")
    figures = payload.get("figures", [])
    if not isinstance(figures, list):
        raise ValueError(f"Invalid figure manifest: {manifest_path}")
    if not interface_figure_id:
        raise NoInterfaceFigureError(f"no interface figure is selected in {manifest_path}")

    figure_record = next((item for item in figures if item.get("fig_id") == interface_figure_id), None)
    if figure_record is None:
        raise ValueError(f"Interface figure {interface_figure_id} not found in {manifest_path}")

    image_path = figure_record.get("image_path")
    caption = (figure_record.get("caption") or "").strip()
    if not image_path:
        raise ValueError(f"Missing image_path for {interface_figure_id} in {manifest_path}")
    if not caption:
        raise ValueError(f"Missing caption for {interface_figure_id} in {manifest_path}")

    image_path_obj = Path(image_path)
    if not image_path_obj.is_absolute():
        image_path_obj = (Path.cwd() / image_path_obj).resolve()
    return image_path_obj, caption


def build_prompt(caption: str) -> str:
    return (
        "You are segmenting a visual analytics system interface into top-level views.\n\n"
        "Task:\n"
        "1. Inspect the full interface image.\n"
        "2. Use the caption as supporting evidence.\n"
        "3. Identify top-level views or major panels only.\n"
        "4. Do not split a view into small internal widgets unless the caption clearly treats them as separate views.\n"
        "5. Prefer slightly larger boxes over boxes that crop away labels or axes.\n"
        "6. Return coordinates normalized to a 0-1000 scale over the full image.\n"
        "7. Sort views in reading order: top-to-bottom, then left-to-right.\n\n"
        "Caption:\n"
        f"{caption}\n\n"
        "Return a JSON object with field `items`. Each item must contain:\n"
        "- view_id\n"
        "- short_label\n"
        "- description\n"
        "- confidence\n"
        "- left\n"
        "- top\n"
        "- right\n"
        "- bottom\n"
    )


def extract_text_content(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        parts: List[str] = []
        for item in message_content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


def invoke_layout_model(
    client: OpenAI,
    model_name: str,
    image_path: Path,
    caption: str,
) -> ViewRegionList:
    image_url = encode_image_to_data_url(image_path)
    prompt_text = build_prompt(caption)
    request = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "You identify top-level interface views from screenshots.",
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
    if not content:
        raise RuntimeError("The model returned empty content.")
    return ViewRegionList.model_validate_json(content)


def to_pixel_box(region: ViewRegion, width: int, height: int) -> tuple[int, int, int, int]:
    left = max(0, round(region.left / MAX_COORD * width))
    top = max(0, round(region.top / MAX_COORD * height))
    right = min(width, round(region.right / MAX_COORD * width))
    bottom = min(height, round(region.bottom / MAX_COORD * height))

    if right - left < MIN_BOX_SIZE:
        right = min(width, left + MIN_BOX_SIZE)
    if bottom - top < MIN_BOX_SIZE:
        bottom = min(height, top + MIN_BOX_SIZE)
    return left, top, right, bottom


def save_crops_and_manifest(
    image: Image.Image,
    regions: List[ViewRegion],
    paper_name: str,
    output_root: Path,
) -> List[Path]:
    output_dir = output_root / paper_name
    output_dir.mkdir(parents=True, exist_ok=True)

    width, height = image.size
    manifest: List[dict[str, Any]] = []
    saved_paths: List[Path] = []

    for idx, region in enumerate(regions, start=1):
        left, top, right, bottom = to_pixel_box(region, width, height)
        crop = image.crop((left, top, right, bottom))
        file_name = f"{idx}.png"
        output_path = output_dir / file_name
        crop.save(output_path)
        saved_paths.append(output_path)

        manifest.append(
            {
                "index": idx,
                "file_name": file_name,
                "view_id": region.view_id,
                "short_label": region.short_label,
                "description": region.description,
                "confidence": region.confidence,
                "bbox_normalized": {
                    "left": region.left,
                    "top": region.top,
                    "right": region.right,
                    "bottom": region.bottom,
                },
                "bbox_pixels": {
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                },
            }
        )

    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return saved_paths


def split_interface_views(
    image_path: Path,
    paper_name: str,
    caption: str,
    vision_model: str = "",
    api_key: str = "",
    base_url: str = "",
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> List[Path]:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path).convert("RGB")
    client = OpenAI(api_key=api_key, base_url=base_url)
    layout = invoke_layout_model(client, vision_model, image_path, caption)
    if not layout.items:
        raise RuntimeError("The multimodal model returned no view regions.")
    return save_crops_and_manifest(image, layout.items, paper_name, output_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split an interface figure into numbered view crops with a multimodal LLM."
    )
    parser.add_argument(
        "paper_name",
        nargs="?",
        help="Paper/system name used under ../data/view-images/. Omit when using --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Split interface views for all papers under the figures root that contain figure-manifest.json.",
    )
    parser.add_argument("--image-path", help="Override path to the full interface image.")
    parser.add_argument("--caption", help="Override interface caption text.")
    parser.add_argument("--caption-file", help="Path to a text file containing the interface caption.")
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
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT_LABEL),
        help="Root directory for output crops. Defaults to ../data/view-images.",
    )
    args = parser.parse_args()
    if args.all and args.paper_name:
        parser.error("Provide either a paper_name or --all, not both.")
    if args.all and (args.image_path or args.caption or args.caption_file):
        parser.error("--all cannot be combined with --image-path, --caption, or --caption-file.")
    if not args.all and not args.paper_name:
        parser.error("Provide a paper_name or use --all.")
    return args


def iter_paper_names(figures_root: Path) -> List[str]:
    paper_names: List[str] = []
    for manifest_path in sorted(figures_root.glob("*/figure-manifest.json")):
        paper_names.append(manifest_path.parent.name)
    return paper_names


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
    output_root = resolve_path_arg(
        args.output_root,
        DEFAULT_OUTPUT_ROOT_LABEL,
        DEFAULT_OUTPUT_ROOT,
    )

    if args.all:
        paper_names = iter_paper_names(figures_root)
        if not paper_names:
            raise FileNotFoundError(f"No figure-manifest.json files found under {figures_root}")
        for paper_name in paper_names:
            try:
                image_path, caption = load_interface_figure_from_manifest(
                    paper_name=paper_name,
                    figures_root=figures_root,
                )
                saved = split_interface_views(
                    image_path=image_path,
                    paper_name=paper_name,
                    caption=caption,
                    vision_model=vision_model,
                    api_key=api_key,
                    base_url=base_url,
                    output_root=output_root,
                )
                print(f"Saved {len(saved)} crops -> {output_root / paper_name}")
            except NoInterfaceFigureError as exc:
                print(f"{paper_name}: skipped -> {exc}")
            except Exception as exc:
                print(f"{paper_name}: failed -> {exc}")
        return

    if args.image_path:
        image_path = Path(args.image_path)
        caption = load_caption(args)
    else:
        try:
            image_path, caption = load_interface_figure_from_manifest(
                paper_name=args.paper_name,
                figures_root=figures_root,
            )
        except NoInterfaceFigureError as exc:
            print(f"{args.paper_name}: skipped -> {exc}")
            return

        saved = split_interface_views(
            image_path=image_path,
            paper_name=args.paper_name,
            caption=caption,
            vision_model=vision_model,
            api_key=api_key,
            base_url=base_url,
            output_root=output_root,
        )
    print(f"Saved {len(saved)} crops -> {output_root / args.paper_name}")


if __name__ == "__main__":
    main()
