"""
Build a compact markdown summary of preprocessing artifacts for one paper.

Command-line usage:
- From `code-repo/`:
  `python agentic-extraction/preprocessing/build_preprocessing_summary.py ConceptViz`
- Batch mode:
  `python agentic-extraction/preprocessing/build_preprocessing_summary.py --all`

Inputs:
- `../data/passages/`
- `../data/figures/`
- `../data/view-images/`

Output:
- `../data/preprocess-summaries/<paper>.md`

Open-source notes:
- Path examples are documented relative to `agentic-extraction/preprocessing/`.
- The summary only stores relative references to released artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_EXTRACTION_ROOT = SCRIPT_DIR.parent
REPO_ROOT = AGENTIC_EXTRACTION_ROOT.parent
DATA_ROOT = AGENTIC_EXTRACTION_ROOT / "data"
PAPERS_ROOT = DATA_ROOT / "papers"
PASSAGES_ROOT = DATA_ROOT / "passages"
FIGURES_ROOT = DATA_ROOT / "figures"
VIEW_IMAGES_ROOT = DATA_ROOT / "view-images"
DEFAULT_OUTPUT_ROOT = DATA_ROOT / "preprocess-summaries"
DEFAULT_OUTPUT_ROOT_LABEL = Path("../data/preprocess-summaries")
PAPER_META_PATH = REPO_ROOT / "paper-meta.json"


def relpath(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def resolve_path_arg(raw_value: str, default_label: Path, default_path: Path) -> Path:
    if raw_value == str(default_label):
        return default_path
    return Path(raw_value).expanduser().resolve()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_paper_full_name_map() -> dict[str, str]:
    if not PAPER_META_PATH.exists():
        return {}
    payload = load_json(PAPER_META_PATH)
    if not isinstance(payload, list):
        return {}

    full_name_map: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        paper_name = item.get("paper_name")
        paper_full_name = item.get("paper_full_name")
        if isinstance(paper_name, str) and isinstance(paper_full_name, str):
            full_name_map[paper_name] = paper_full_name
    return full_name_map


class SummaryWriteStatus(str, Enum):
    CREATED = "created"
    OVERWRITTEN = "overwritten"
    SKIPPED = "skipped"


def build_condensed_figures(paper_name: str) -> tuple[Optional[str], list[dict[str, Any]]]:
    figure_dir = FIGURES_ROOT / paper_name
    figure_manifest_path = figure_dir / "figure-manifest.json"
    figures_json_path = figure_dir / "figures.json"

    condensed: list[dict[str, Any]] = []
    if figure_manifest_path.exists():
        manifest = load_json(figure_manifest_path)
        for item in manifest.get("figures", []):
            condensed.append(
                {
                    "fig_id": item.get("fig_id"),
                    "image_path": item.get("image_path"),
                    "caption": item.get("caption", ""),
                    "primary_role": item.get("primary_role"),
                }
            )
        return relpath(figure_dir), condensed

    if figures_json_path.exists():
        payload = load_json(figures_json_path)
        if isinstance(payload, list):
            for item in payload:
                fig_id = item.get("fig_id")
                condensed.append(
                    {
                        "fig_id": fig_id,
                        "image_path": relpath(figure_dir / "crops" / f"{fig_id}.png") if fig_id else None,
                        "caption": item.get("caption", ""),
                        "primary_role": None,
                    }
                )
        return relpath(figure_dir), condensed

    return None, []


def collect_missing_parts(paper_name: str) -> list[str]:
    pdf_path = PAPERS_ROOT / f"{paper_name}.pdf"
    passages_path = PASSAGES_ROOT / f"{paper_name}_passages.json"
    view_images_dir = VIEW_IMAGES_ROOT / paper_name
    figure_dir = FIGURES_ROOT / paper_name
    figure_manifest_path = figure_dir / "figure-manifest.json"
    figures_json_path = figure_dir / "figures.json"

    missing: list[str] = []
    if not pdf_path.exists():
        missing.append("pdf")
    if not passages_path.exists():
        missing.append("passages")
    if not figure_manifest_path.exists() and not figures_json_path.exists():
        missing.append("figures")
    if not view_images_dir.exists():
        missing.append("view-images")
    return missing


def build_summary_markdown(paper_name: str) -> str:
    passages_path = PASSAGES_ROOT / f"{paper_name}_passages.json"
    view_images_dir = VIEW_IMAGES_ROOT / paper_name
    figures_dir, condensed_figures = build_condensed_figures(paper_name)
    paper_full_name_map = load_paper_full_name_map()

    paper_payload = {
        "paper_name": paper_name,
        "paper_full_name": paper_full_name_map.get(paper_name),
    }
    passages_payload = {
        "path": relpath(passages_path) if passages_path.exists() else None,
    }
    figures_payload = {
        "directory": figures_dir,
        "items": condensed_figures,
    }
    view_images_payload = {
        "directory": relpath(view_images_dir) if view_images_dir.exists() else None,
    }

    return "\n".join(
        [
            f"# Preprocess Summary: {paper_name}",
            "",
            "This file summarizes the preprocessing artifacts for one paper. The actual artifacts remain stored in their original locations. Use this file as the single entry point before running agentic extraction.",
            "",
            "## Paper",
            "",
            "This section identifies the paper.",
            "",
            "```json",
            json.dumps(paper_payload, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Passages",
            "",
            "This section points to the paragraph-level passage file extracted from the PDF.",
            "",
            "```json",
            json.dumps(passages_payload, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Figures",
            "",
            "This section points to the figure directory and embeds a condensed figure manifest. Each item only keeps the fields most useful for downstream extraction.",
            "",
            "```json",
            json.dumps(figures_payload, ensure_ascii=False, indent=2),
            "```",
            "",
            "## View Images",
            "",
            "This section points to the directory containing interface-view crops derived from the interface figure.",
            "",
            "```json",
            json.dumps(view_images_payload, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )


def build_summary_for_paper(
    paper_name: str,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    overwrite: bool = False,
) -> tuple[Path, SummaryWriteStatus]:
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / f"{paper_name}.md"
    if output_path.exists() and not overwrite:
        return output_path, SummaryWriteStatus.SKIPPED
    output_path.write_text(build_summary_markdown(paper_name), encoding="utf-8")
    status = SummaryWriteStatus.OVERWRITTEN if overwrite else SummaryWriteStatus.CREATED
    return output_path, status


def write_paper_index_csv(paper_names: list[str], output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "paper-index.csv"
    paper_full_name_map = load_paper_full_name_map()

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["paper_name", "paper_full_name"])
        for paper_name in paper_names:
            writer.writerow([paper_name, paper_full_name_map.get(paper_name, "")])

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a markdown summary of preprocessing artifacts for one paper."
    )
    parser.add_argument(
        "paper_name",
        nargs="?",
        help="Paper name used across ../data/papers, ../data/figures, and ../data/view-images. Omit when using --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Build summaries for all papers discovered under ../data/papers, ../data/figures, ../data/passages, or ../data/view-images.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing summary file. By default existing summaries are kept.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT_LABEL),
        help="Output directory for markdown summaries. Defaults to ../data/preprocess-summaries.",
    )
    args = parser.parse_args()
    if args.all and args.paper_name:
        parser.error("Provide either a paper_name or --all, not both.")
    if not args.all and not args.paper_name:
        parser.error("Provide a paper_name or use --all.")
    return args


def iter_paper_names() -> list[str]:
    paper_names: set[str] = set()
    for path in PAPERS_ROOT.glob("*.pdf"):
        paper_names.add(path.stem)
    for path in PASSAGES_ROOT.glob("*_passages.json"):
        stem = path.stem
        if stem.endswith("_passages"):
            paper_names.add(stem[: -len("_passages")])
    for path in FIGURES_ROOT.glob("*/figures.json"):
        paper_names.add(path.parent.name)
    for path in FIGURES_ROOT.glob("*/figure-manifest.json"):
        paper_names.add(path.parent.name)
    for path in VIEW_IMAGES_ROOT.iterdir() if VIEW_IMAGES_ROOT.exists() else []:
        if path.is_dir():
            paper_names.add(path.name)
    return sorted(paper_names)


def main() -> None:
    args = parse_args()
    output_root = resolve_path_arg(
        args.output_root,
        DEFAULT_OUTPUT_ROOT_LABEL,
        DEFAULT_OUTPUT_ROOT,
    )

    if args.all:
        paper_names = iter_paper_names()
        if not paper_names:
            raise FileNotFoundError("No papers found under ../data/papers, ../data/passages, ../data/figures, or ../data/view-images.")
        for paper_name in paper_names:
            try:
                missing = collect_missing_parts(paper_name)
                if missing:
                    print(f"{paper_name}: missing -> {', '.join(missing)}")
                    continue
                output_path, status = build_summary_for_paper(
                    paper_name=paper_name,
                    output_root=output_root,
                    overwrite=args.overwrite,
                )
                if status == SummaryWriteStatus.SKIPPED:
                    print(f"Kept existing preprocess summary -> {output_path}")
                else:
                    print(f"Saved preprocess summary -> {output_path}")
            except Exception as exc:
                print(f"{paper_name}: failed -> {exc}")
        index_path = write_paper_index_csv(paper_names, output_root)
        print(f"Saved paper index -> {index_path}")
        return

    missing = collect_missing_parts(args.paper_name)
    if missing:
        print(f"{args.paper_name}: missing -> {', '.join(missing)}")
        return
    output_path, status = build_summary_for_paper(
        paper_name=args.paper_name,
        output_root=output_root,
        overwrite=args.overwrite,
    )
    if status == SummaryWriteStatus.SKIPPED:
        print(f"Kept existing preprocess summary -> {output_path}")
    else:
        print(f"Saved preprocess summary -> {output_path}")


if __name__ == "__main__":
    main()
