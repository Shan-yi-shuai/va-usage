"""
Extract paper figures with PDFFigures2 and re-render crops locally.

Command-line usage:
- From `code-repo/` for a single PDF:
  `python agentic-extraction/preprocessing/extract_figures.py --pdf agentic-extraction/data/papers/ConceptViz.pdf`
- Batch mode:
  `python agentic-extraction/preprocessing/extract_figures.py --all`

Expected inputs:
- `../data/papers/*.pdf`
- `../data/passages/*_passages.json` for caption recovery

Outputs:
- `../data/figures/<paper>/figures.json`
- `../data/figures/<paper>/crops/`

Configuration:
- Required: `PDFFIGURES2_JAR` or `PDFFIGURES2_CMD`

Setup:
1. Build or download the PDFFigures2 assembly jar from:
   https://github.com/allenai/pdffigures2
2. Expose it via one of:
   - export PDFFIGURES2_JAR=/abs/path/to/pdffigures2.jar
   - env `PDFFIGURES2_JAR=/abs/path/to/pdffigures2-assembly-*.jar`
   - function arg `jar_path=...`
   - env `PDFFIGURES2_CMD='java -jar /abs/path/to/pdffigures2-assembly-*.jar'`

Open-source notes:
- No machine-specific local paths are embedded in this script.
- All published path examples are relative to `agentic-extraction/preprocessing/`.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

import fitz  # PyMuPDF


_FIG_NUM_RE = re.compile(r"\bfig(?:ure)?\.?\s*(\d+)\b", re.IGNORECASE)
SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_EXTRACTION_ROOT = SCRIPT_DIR.parent
DATA_ROOT = AGENTIC_EXTRACTION_ROOT / "data"
DEFAULT_PASSAGES_DIR = DATA_ROOT / "passages"
DEFAULT_PASSAGES_DIR_LABEL = Path("../data/passages")
DEFAULT_PAPERS_DIR = DATA_ROOT / "papers"
DEFAULT_PAPERS_DIR_LABEL = Path("../data/papers")
DEFAULT_FIGURES_DIR = DATA_ROOT / "figures"
DEFAULT_FIGURES_DIR_LABEL = Path("../data/figures")


@dataclass
class Primitive:
    kind: str
    rect: fitz.Rect
    text: str = ""


@dataclass
class Cluster:
    rect: fitz.Rect
    primitives: list[Primitive] = field(default_factory=list)

    @property
    def kinds(self) -> set[str]:
        return {p.kind for p in self.primitives}


def _resolve_pdffigures2_command(
    jar_path: Optional[str] = None,
    command: Optional[str] = None,
) -> list[str]:
    if command:
        return shlex.split(command)

    env_command = os.environ.get("PDFFIGURES2_CMD")
    if env_command:
        return shlex.split(env_command)

    candidate_jar = jar_path or os.environ.get("PDFFIGURES2_JAR")
    if candidate_jar:
        return ["java", "-jar", candidate_jar]

    raise RuntimeError(
        "PDFFigures2 is not configured.\n"
        "Install it first:\n"
        "  git clone https://github.com/allenai/pdffigures2\n"
        "  cd pdffigures2\n"
        "  sbt assembly\n"
        "Then configure one of:\n"
        "  export PDFFIGURES2_JAR=../tools/pdffigures2-assembly.jar\n"
        "  export PDFFIGURES2_CMD='java -jar ../tools/pdffigures2-assembly.jar'"
    )


def resolve_path_arg(raw_value: str, default_label: Path, default_path: Path) -> Path:
    if raw_value == str(default_label):
        return default_path
    return Path(raw_value).expanduser().resolve()


def _find_output_json(output_dir: Path, pdf_stem: str) -> Path:
    candidates = sorted(output_dir.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"No PDFFigures2 JSON found in {output_dir}")

    preferred = [path for path in candidates if path.stem == pdf_stem]
    if preferred:
        return preferred[0]
    if len(candidates) == 1:
        return candidates[0]

    raise FileNotFoundError(
        f"Found multiple JSON files in {output_dir} but none matched stem '{pdf_stem}'"
    )


def _run_pdffigures2(
    pdf_path: Path,
    output_dir: Path,
    jar_path: Optional[str] = None,
    command: Optional[str] = None,
    timeout: int = 600,
) -> Path:
    runner = _resolve_pdffigures2_command(jar_path=jar_path, command=command)

    with tempfile.TemporaryDirectory(prefix="pdffigures2_input_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        input_dir = tmp_dir / "input"
        meta_tmp_dir = tmp_dir / "meta"
        render_dir = tmp_dir / "rendered"
        stats_file = tmp_dir / "stats.json"
        input_dir.mkdir(parents=True, exist_ok=True)
        meta_tmp_dir.mkdir(parents=True, exist_ok=True)
        render_dir.mkdir(parents=True, exist_ok=True)

        staged_pdf = input_dir / pdf_path.name
        shutil.copy2(pdf_path, staged_pdf)

        cmd = runner + [
            str(input_dir),
            "-m",
            f"{render_dir}{os.sep}",
            "-d",
            f"{meta_tmp_dir}{os.sep}",
            "-s",
            str(stats_file),
        ]
        subprocess.run(cmd, check=True, timeout=timeout)
        json_path = _find_output_json(meta_tmp_dir, pdf_path.stem)
        output_dir.mkdir(parents=True, exist_ok=True)
        final_json_path = output_dir / json_path.name
        shutil.copy2(json_path, final_json_path)
        return final_json_path


def _boundary_to_rect(boundary: dict[str, Any]) -> fitz.Rect:
    x0 = float(boundary["x1"])
    y0 = float(boundary["y1"])
    x1 = float(boundary["x2"])
    y1 = float(boundary["y2"])
    return fitz.Rect(x0, y0, x1, y1)


def _clip_to_page(rect: fitz.Rect, page_rect: fitz.Rect) -> fitz.Rect:
    clipped = fitz.Rect(rect)
    clipped.x0 = max(page_rect.x0, clipped.x0)
    clipped.y0 = max(page_rect.y0, clipped.y0)
    clipped.x1 = min(page_rect.x1, clipped.x1)
    clipped.y1 = min(page_rect.y1, clipped.y1)
    return clipped


def _trim_bottom_caption_overlap(
    export_rect: fitz.Rect,
    caption_rect: Optional[fitz.Rect],
    padding: float,
) -> fitz.Rect:
    if caption_rect is None:
        return export_rect

    x_overlap = max(0.0, min(export_rect.x1, caption_rect.x1) - max(export_rect.x0, caption_rect.x0))
    min_x_overlap = min(export_rect.width, caption_rect.width) * 0.35
    if x_overlap < min_x_overlap:
        return export_rect

    # Only trim when the caption sits below the figure bottom or slightly overlaps it.
    if caption_rect.y0 > export_rect.y1 + 12:
        return export_rect
    if caption_rect.y0 <= export_rect.y0:
        return export_rect

    trimmed_y1 = min(export_rect.y1, max(export_rect.y0 + 20, caption_rect.y0 - max(2.0, padding * 0.35)))
    if trimmed_y1 <= export_rect.y0 + 10:
        return export_rect

    return fitz.Rect(export_rect.x0, export_rect.y0, export_rect.x1, trimmed_y1)


def _expand_rect(rect: fitz.Rect, dx: float, dy: Optional[float] = None) -> fitz.Rect:
    if dy is None:
        dy = dx
    return fitz.Rect(rect.x0 - dx, rect.y0 - dy, rect.x1 + dx, rect.y1 + dy)


def _safe_intersects(a: fitz.Rect, b: fitz.Rect) -> bool:
    return not fitz.Rect(a).intersect(b).is_empty


def _normalize_text(s: str) -> str:
    return " ".join(s.split()).strip()


def _is_visual_text_block(block: dict[str, Any], page_rect: fitz.Rect) -> bool:
    text = _normalize_text(
        " ".join(
            span["text"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        )
    )
    if not text:
        return False

    bbox = fitz.Rect(block["bbox"])
    width_ratio = bbox.width / max(1.0, page_rect.width)
    line_count = len(block.get("lines", []))

    if _FIG_NUM_RE.match(text):
        return False
    if len(text) > 120:
        return False
    if line_count > 4:
        return False
    if width_ratio > 0.72 and len(text) > 40:
        return False
    return True


def _page_visual_primitives(page: fitz.Page) -> list[Primitive]:
    page_rect = page.rect
    primitives: list[Primitive] = []
    text_dict = page.get_text("dict")

    for block in text_dict.get("blocks", []):
        block_type = block.get("type")
        rect = fitz.Rect(block["bbox"])

        if block_type == 1:
            primitives.append(Primitive(kind="image", rect=rect))
            continue

        if block_type == 0 and _is_visual_text_block(block, page_rect):
            text = _normalize_text(
                " ".join(
                    span["text"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                )
            )
            primitives.append(Primitive(kind="text", rect=rect, text=text))

    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        rect = fitz.Rect(rect)
        if max(rect.width, rect.height) < 6 or rect.get_area() < 4:
            continue
        primitives.append(Primitive(kind="drawing", rect=rect))

    return primitives


def _page_text_blocks(page: fitz.Page) -> list[tuple[fitz.Rect, str]]:
    blocks: list[tuple[fitz.Rect, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        text = _normalize_text(
            " ".join(
                span["text"]
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            )
        )
        if text:
            blocks.append((fitz.Rect(block["bbox"]), text))
    return blocks


def _cluster_primitives(primitives: list[Primitive], tolerance: float = 14.0) -> list[Cluster]:
    clusters: list[Cluster] = []

    for primitive in sorted(primitives, key=lambda item: (item.rect.y0, item.rect.x0)):
        merged_indices: list[int] = []
        for idx, cluster in enumerate(clusters):
            if _safe_intersects(_expand_rect(cluster.rect, tolerance), primitive.rect):
                merged_indices.append(idx)

        if not merged_indices:
            clusters.append(Cluster(rect=fitz.Rect(primitive.rect), primitives=[primitive]))
            continue

        base = clusters[merged_indices[0]]
        base.rect.include_rect(primitive.rect)
        base.primitives.append(primitive)

        for idx in reversed(merged_indices[1:]):
            other = clusters.pop(idx)
            base.rect.include_rect(other.rect)
            base.primitives.extend(other.primitives)

    return [c for c in clusters if c.rect.get_area() >= 600]


def _figure_numbers(items: Iterable[dict[str, Any]]) -> set[int]:
    numbers: set[int] = set()
    for item in items:
        for text in (item.get("name", ""), item.get("caption", "")):
            m = _FIG_NUM_RE.search(text or "")
            if m:
                numbers.add(int(m.group(1)))
                break
    return numbers


def _find_caption_rect(page: fitz.Page, figure_number: int) -> Optional[fitz.Rect]:
    queries = [
        f"Fig. {figure_number}",
        f"Fig {figure_number}",
        f"Figure {figure_number}",
        f"FIG. {figure_number}",
    ]
    matches: list[fitz.Rect] = []
    for query in queries:
        matches.extend(page.search_for(query))

    if not matches:
        return None

    result = fitz.Rect(matches[0])
    for rect in matches[1:]:
        result.include_rect(rect)
    return result


def _extract_blocks_in_reading_order(
    blocks: list[tuple[fitz.Rect, str]],
) -> list[tuple[fitz.Rect, str]]:
    return sorted(blocks, key=lambda item: (round(item[0].y0, 1), item[0].x0))


def _merge_caption_blocks(blocks: list[tuple[fitz.Rect, str]]) -> str:
    parts: list[str] = []
    for _, text in _extract_blocks_in_reading_order(blocks):
        if not parts:
            parts.append(text)
            continue

        prev = parts[-1]
        if text == prev:
            continue
        if text.lower() in prev.lower():
            continue
        parts.append(text)

    return _normalize_text(" ".join(parts))


def _extract_caption_from_anchor(
    page: fitz.Page,
    anchor_rect: fitz.Rect,
    figure_number: int,
) -> str:
    blocks = _page_text_blocks(page)
    candidates: list[tuple[fitz.Rect, str]] = []

    search_rect = _expand_rect(anchor_rect, 40, 28)
    for rect, text in blocks:
        if not _safe_intersects(search_rect, rect):
            continue
        if figure_number != 1 and not _FIG_NUM_RE.search(text):
            continue
        candidates.append((rect, text))

    if not candidates:
        # Fallback: start from the closest block below the anchor and keep nearby lines.
        below = [
            (rect, text)
            for rect, text in blocks
            if rect.y0 >= anchor_rect.y0 - 8 and rect.y0 <= anchor_rect.y1 + 48
        ]
        below = _extract_blocks_in_reading_order(below)
        if below:
            seed_rect, _ = below[0]
            band_bottom = seed_rect.y1 + 42
            for rect, text in below:
                if rect.y0 <= band_bottom:
                    candidates.append((rect, text))

    return _merge_caption_blocks(candidates)


def _extract_caption_below_region(
    page: fitz.Page,
    region_rect: fitz.Rect,
    figure_number: int,
) -> str:
    blocks = _extract_blocks_in_reading_order(_page_text_blocks(page))
    candidates: list[tuple[fitz.Rect, str]] = []

    x_pad = max(24.0, region_rect.width * 0.08)
    max_y = min(page.rect.y1, region_rect.y1 + page.rect.height * 0.18)
    search_rect = fitz.Rect(
        max(page.rect.x0, region_rect.x0 - x_pad),
        region_rect.y1 - 6,
        min(page.rect.x1, region_rect.x1 + x_pad),
        max_y,
    )

    for rect, text in blocks:
        if rect.y0 < search_rect.y0 or rect.y1 > search_rect.y1:
            continue
        if rect.x1 < search_rect.x0 or rect.x0 > search_rect.x1:
            continue
        if len(text) > 600:
            continue
        candidates.append((rect, text))

    if not candidates:
        return ""

    # Start from an explicit figure label if present.
    for idx, (_, text) in enumerate(candidates):
        m = _FIG_NUM_RE.search(text)
        if m and int(m.group(1)) == figure_number:
            seed_rect = candidates[idx][0]
            band_bottom = seed_rect.y1 + 48
            grouped = [item for item in candidates[idx:] if item[0].y0 <= band_bottom]
            return _merge_caption_blocks(grouped)

    seed_rect = candidates[0][0]
    band_bottom = seed_rect.y1 + 42
    grouped = [item for item in candidates if item[0].y0 <= band_bottom]
    return _merge_caption_blocks(grouped)


def _extract_figure_number(item: dict[str, Any]) -> Optional[int]:
    for text in (item.get("name", ""), item.get("caption", "")):
        m = _FIG_NUM_RE.search(text or "")
        if m:
            return int(m.group(1))
    return None


def _extract_figure_number_from_id(fig_id: str) -> Optional[int]:
    m = re.fullmatch(r"fig_(\d+)", fig_id or "")
    if not m:
        return None
    return int(m.group(1))


def _caption_has_figure_prefix(caption: str) -> bool:
    return bool(re.match(r"^\s*fig(?:ure)?\.?\s*\d+\b", caption or "", re.IGNORECASE))


def _find_caption_start_index(text: str, figure_number: Optional[int]) -> Optional[int]:
    if figure_number is None:
        return None

    patterns = [
        rf"\bfig\.\s*{figure_number}\s*[\.:：\-–—]",
        rf"\bfig\s*{figure_number}\s*[\.:：\-–—]",
        rf"\bfigure\s*{figure_number}\s*[\.:：\-–—]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.start()
    return None


def _truncate_to_caption_start(text: str, figure_number: Optional[int]) -> str:
    normalized = _normalize_text(text)
    start = _find_caption_start_index(normalized, figure_number)
    if start is None:
        return normalized
    return normalized[start:].strip()


def _caption_review_flags(caption: str, figure_number: Optional[int]) -> list[str]:
    caption = _normalize_text(caption)
    flags: list[str] = []

    if not caption:
        flags.append("empty_caption")
        return flags

    if not _caption_has_figure_prefix(caption):
        flags.append("caption_prefix_unexpected")

    caption_num = _extract_figure_number({"caption": caption})
    if figure_number is not None and caption_num is not None and caption_num != figure_number:
        flags.append("caption_number_mismatch")

    if len(caption) < 15:
        flags.append("caption_too_short")
    if len(caption) > 1200:
        flags.append("caption_too_long")
    if re.search(r"\b(Abstract|Introduction|CCS Concepts)\b", caption, re.IGNORECASE):
        flags.append("caption_contains_body_text")

    return flags


def _caption_quality_score(caption: str, figure_number: Optional[int]) -> tuple[int, int]:
    flags = _caption_review_flags(caption, figure_number)
    hard_flags = {
        "empty_caption",
        "caption_prefix_unexpected",
        "caption_number_mismatch",
        "caption_contains_body_text",
    }
    hard_count = sum(1 for flag in flags if flag in hard_flags)
    return hard_count, len(flags)


def _find_passages_json(pdf_stem: str, passages_dir: Path = DEFAULT_PASSAGES_DIR) -> Optional[Path]:
    direct = passages_dir / f"{pdf_stem}_passages.json"
    if direct.exists():
        return direct

    normalized = pdf_stem.lower()
    for path in passages_dir.glob("*_passages.json"):
        stem = path.stem[: -len("_passages")]
        if stem.lower() == normalized:
            return path
    return None


def _load_passage_caption_map(pdf_stem: str, passages_dir: Path = DEFAULT_PASSAGES_DIR) -> dict[int, str]:
    passages_path = _find_passages_json(pdf_stem, passages_dir=passages_dir)
    if passages_path is None:
        return {}

    try:
        payload = json.loads(passages_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    caption_map: dict[int, str] = {}
    for item in payload:
        text = _normalize_text(item.get("text", ""))
        if not text:
            continue

        item_type = item.get("type", "")
        figure_number = _extract_figure_number({"caption": text})
        if figure_number is None:
            continue

        truncated = _truncate_to_caption_start(text, figure_number)
        if not truncated or _find_caption_start_index(truncated, figure_number) != 0:
            continue

        if figure_number not in caption_map:
            caption_map[figure_number] = truncated
            continue

        existing = caption_map[figure_number]
        existing_score = _caption_quality_score(existing, figure_number)
        candidate_score = _caption_quality_score(truncated, figure_number)

        if item_type == "caption" and candidate_score <= existing_score:
            caption_map[figure_number] = truncated
        elif candidate_score < existing_score:
            caption_map[figure_number] = truncated

    return caption_map


def _backfill_caption_from_passages(
    caption: str,
    figure_number: Optional[int],
    passage_caption_map: dict[int, str],
) -> str:
    normalized = _truncate_to_caption_start(caption, figure_number)
    if _find_caption_start_index(normalized, figure_number) == 0:
        return normalized

    if figure_number is None:
        return normalized

    candidate = _normalize_text(passage_caption_map.get(figure_number, ""))
    if not candidate:
        return normalized

    candidate = _truncate_to_caption_start(candidate, figure_number)
    current_score = _caption_quality_score(normalized, figure_number)
    candidate_score = _caption_quality_score(candidate, figure_number)

    if candidate_score < current_score:
        return candidate
    if not normalized:
        return candidate
    return normalized


def _best_teaser_cluster(page: fitz.Page, caption_rect: fitz.Rect) -> Optional[Cluster]:
    candidates: list[tuple[float, Cluster]] = []
    for cluster in _cluster_primitives(_page_visual_primitives(page)):
        if cluster.rect.y1 > caption_rect.y0:
            continue
        if cluster.rect.get_area() < 2500:
            continue

        vertical_gap = max(0.0, caption_rect.y0 - cluster.rect.y1)
        if vertical_gap > page.rect.height * 0.28:
            continue

        score = 0.0
        if "image" in cluster.kinds:
            score += 25
        if "drawing" in cluster.kinds:
            score += 20
        if "text" in cluster.kinds and len(cluster.kinds) > 1:
            score += 8
        score += min(30.0, cluster.rect.get_area() / 4000.0)
        score -= vertical_gap / 3.0
        candidates.append((score, cluster))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _find_first_matching_block(
    text_blocks: list[tuple[fitz.Rect, str]],
    patterns: list[str],
) -> Optional[fitz.Rect]:
    for rect, text in text_blocks:
        lowered = text.lower()
        for pattern in patterns:
            if pattern in lowered:
                return rect
    return None


def _best_front_page_teaser_cluster(page: fitz.Page) -> Optional[Cluster]:
    clusters = _cluster_primitives(_page_visual_primitives(page))
    if not clusters:
        return None

    text_blocks = _page_text_blocks(page)
    abstract_rect = _find_first_matching_block(
        text_blocks,
        ["abstract", "ccs concepts", "keywords", "introduction"],
    )
    title_bottom = 0.0
    if text_blocks:
        # Approximate the title/author band from the first few text blocks on page 1.
        title_bottom = min(
            page.rect.height * 0.28,
            max(rect.y1 for rect, _ in text_blocks[: min(4, len(text_blocks))]),
        )

    candidates: list[tuple[float, Cluster]] = []
    for cluster in clusters:
        if cluster.rect.get_area() < 4000:
            continue
        if cluster.rect.y0 > page.rect.height * 0.68:
            continue

        score = 0.0
        if "image" in cluster.kinds:
            score += 20
        if "drawing" in cluster.kinds:
            score += 18
        if "text" in cluster.kinds and len(cluster.kinds) > 1:
            score += 6

        score += min(40.0, cluster.rect.get_area() / 5000.0)

        if cluster.rect.y0 >= title_bottom:
            score += 20
        else:
            score -= 15

        if abstract_rect is not None:
            if cluster.rect.y1 <= abstract_rect.y0 + 24:
                score += 25
                score -= max(0.0, abstract_rect.y0 - cluster.rect.y1) / 3.0
            elif _safe_intersects(_expand_rect(abstract_rect, 12), cluster.rect):
                score += 12
            else:
                score -= min(40.0, abs(cluster.rect.y0 - abstract_rect.y0) / 5.0)
        else:
            page_mid = page.rect.height * 0.4
            score -= abs(cluster.rect.y0 - page_mid) / 6.0

        candidates.append((score, cluster))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _render_crop(
    page: fitz.Page,
    rect: fitz.Rect,
    crop_path: Path,
    zoom: float,
) -> None:
    pix = page.get_pixmap(
        matrix=fitz.Matrix(zoom, zoom),
        clip=rect,
        alpha=False,
    )
    pix.save(str(crop_path))


def _append_teaser_fallbacks(
    doc: fitz.Document,
    results: list[dict[str, Any]],
    crops_dir: Path,
    zoom: float,
    padding: float,
    passage_caption_map: dict[int, str],
) -> None:
    existing_numbers = _figure_numbers(results)
    if 1 in existing_numbers:
        return

    for page_index in range(min(2, doc.page_count)):
        page = doc.load_page(page_index)
        caption_rect = _find_caption_rect(page, 1)
        if caption_rect is None:
            continue

        cluster = _best_teaser_cluster(page, caption_rect)
        if cluster is None:
            continue

        export_rect = _clip_to_page(_expand_rect(cluster.rect, padding), page.rect)
        crop_path = crops_dir / "000_Figure_1_teaser.png"
        _render_crop(page, export_rect, crop_path, zoom=zoom)

        fallback_caption = (
            _extract_caption_from_anchor(page, caption_rect, 1)
            or _extract_caption_below_region(page, cluster.rect, 1)
            or "Figure 1"
        )
        fallback_caption = _backfill_caption_from_passages(
            caption=fallback_caption,
            figure_number=1,
            passage_caption_map=passage_caption_map,
        )

        results.insert(
            0,
            {
                "index": 0,
                "figure_number": 1,
                "fig_type": "Figure",
                "name": "Figure 1",
                "caption": fallback_caption,
                "page": page_index + 1,
                "region_boundary": {
                    "x1": cluster.rect.x0,
                    "y1": cluster.rect.y0,
                    "x2": cluster.rect.x1,
                    "y2": cluster.rect.y1,
                    "page": page_index,
                },
                "caption_boundary": {
                    "x1": caption_rect.x0,
                    "y1": caption_rect.y0,
                    "x2": caption_rect.x1,
                    "y2": caption_rect.y1,
                    "page": page_index,
                },
                "render_bbox": [
                    export_rect.x0,
                    export_rect.y0,
                    export_rect.x1,
                    export_rect.y1,
                ],
                "file": str(crop_path),
                "status": "ok",
                "source": "teaser_fallback",
            },
        )
        return

    # Some teaser figures on page 1 have no explicit "Fig. 1" caption.
    first_page = doc.load_page(0)
    cluster = _best_front_page_teaser_cluster(first_page)
    if cluster is None:
        return

    export_rect = _clip_to_page(_expand_rect(cluster.rect, padding), first_page.rect)
    crop_path = crops_dir / "000_Figure_1_teaser.png"
    _render_crop(first_page, export_rect, crop_path, zoom=zoom)

    fallback_caption = (
        _extract_caption_below_region(first_page, cluster.rect, 1)
        or "Figure 1"
    )
    fallback_caption = _backfill_caption_from_passages(
        caption=fallback_caption,
        figure_number=1,
        passage_caption_map=passage_caption_map,
    )

    results.insert(
        0,
        {
            "index": 0,
            "figure_number": 1,
            "fig_type": "Figure",
            "name": "Figure 1",
            "caption": fallback_caption,
            "page": 1,
            "region_boundary": {
                "x1": cluster.rect.x0,
                "y1": cluster.rect.y0,
                "x2": cluster.rect.x1,
                "y2": cluster.rect.y1,
                "page": 0,
            },
            "caption_boundary": None,
            "render_bbox": [
                export_rect.x0,
                export_rect.y0,
                export_rect.x1,
                export_rect.y1,
            ],
            "file": str(crop_path),
            "status": "ok",
            "source": "front_page_teaser_fallback",
        },
    )


def extract_figures_with_pdffigures2(
    pdf_path: str,
    out_dir: str,
    *,
    jar_path: Optional[str] = None,
    command: Optional[str] = None,
    zoom: float = 4.0,
    padding: float = 8.0,
    include_tables: bool = False,
    timeout: int = 600,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    pdf_path_obj = Path(pdf_path)
    out_dir_path = Path(out_dir)
    figures_json_path = out_dir_path / "figures.json"
    if figures_json_path.exists() and not overwrite:
        payload = json.loads(figures_json_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Expected a list in {figures_json_path}")
        return payload

    passage_caption_map = _load_passage_caption_map(pdf_path_obj.stem)
    meta_dir = out_dir_path / "pdffigures2"
    crops_dir = out_dir_path / "crops"
    out_dir_path.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    json_path = _run_pdffigures2(
        pdf_path=pdf_path_obj,
        output_dir=meta_dir,
        jar_path=jar_path,
        command=command,
        timeout=timeout,
    )

    with json_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        figures = payload
    elif isinstance(payload, dict):
        figures = payload.get("figures", [])
        if include_tables:
            figures = figures + payload.get("tables", [])
    else:
        raise TypeError(f"Unexpected PDFFigures2 JSON type: {type(payload).__name__}")

    doc = fitz.open(str(pdf_path_obj))
    results: list[dict[str, Any]] = []

    for index, figure in enumerate(figures, start=1):
        fig_type = figure.get("figureType") or figure.get("figType") or "Figure"
        if not include_tables and fig_type.lower() != "figure":
            continue

        figure_number = _extract_figure_number(figure)

        region_boundary = figure.get("regionBoundary")
        if not region_boundary:
            results.append(
                {
                    "index": index,
                    "figure_number": figure_number,
                    "fig_type": fig_type,
                    "caption": figure.get("caption", ""),
                    "name": figure.get("name", ""),
                    "status": "missing_region_boundary",
                }
            )
            continue

        page_index = int(region_boundary.get("page", figure.get("page", 0)))
        page = doc.load_page(page_index)
        region_rect = _boundary_to_rect(region_boundary)
        export_rect = fitz.Rect(
            region_rect.x0 - padding,
            region_rect.y0 - padding,
            region_rect.x1 + padding,
            region_rect.y1 + padding,
        )
        caption_boundary = figure.get("captionBoundary")
        caption_rect = None
        if isinstance(caption_boundary, dict):
            caption_rect = _boundary_to_rect(caption_boundary)

        export_rect = _trim_bottom_caption_overlap(
            export_rect=export_rect,
            caption_rect=caption_rect,
            padding=padding,
        )
        export_rect = _clip_to_page(export_rect, page.rect)

        raw_name = figure.get("name", f"figure_{index:03d}")
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw_name)
        filename = f"{index:03d}_{safe_name}.png"
        crop_path = crops_dir / filename
        _render_crop(page, export_rect, crop_path, zoom=zoom)

        final_caption = _backfill_caption_from_passages(
            caption=figure.get("caption", ""),
            figure_number=figure_number,
            passage_caption_map=passage_caption_map,
        )

        results.append(
            {
                "index": index,
                "figure_number": figure_number,
                "fig_type": fig_type,
                "name": figure.get("name", ""),
                "caption": final_caption,
                "page": page_index + 1,
                "region_boundary": region_boundary,
                "caption_boundary": caption_boundary,
                "render_bbox": [
                    export_rect.x0,
                    export_rect.y0,
                    export_rect.x1,
                    export_rect.y1,
                ],
                "file": str(crop_path),
                "status": "ok",
            }
        )

    _append_teaser_fallbacks(
        doc=doc,
        results=results,
        crops_dir=crops_dir,
        zoom=zoom,
        padding=padding,
        passage_caption_map=passage_caption_map,
    )

    doc.close()

    captions_payload: list[dict[str, str]] = []

    for item in results:
        if item.get("status") != "ok":
            continue
        figure_number = item.get("figure_number")
        if figure_number is None:
            continue

        src_path = Path(item["file"])
        dst_path = crops_dir / f"fig_{figure_number}.png"
        if src_path != dst_path:
            if dst_path.exists():
                dst_path.unlink()
            src_path.replace(dst_path)

        fig_id = f"fig_{figure_number}"
        captions_payload.append(
            {
                "fig_id": fig_id,
                "caption": item.get("caption", ""),
            }
        )
    captions_payload.sort(key=lambda item: int(item["fig_id"].split("_")[1]))

    meta_path = figures_json_path
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(captions_payload, f, ensure_ascii=False, indent=2)

    return captions_payload


def build_review_summary(
    figures_dir: str = str(DEFAULT_FIGURES_DIR),
    papers: Optional[Iterable[str]] = None,
    extraction_failures: Optional[dict[str, str]] = None,
) -> Path:
    figures_root = Path(figures_dir)
    rows: list[dict[str, str]] = []
    paper_order = list(papers) if papers is not None else None
    paper_filter = set(paper_order) if paper_order is not None else None
    failures = extraction_failures or {}
    figures_json_by_paper = {
        path.parent.name: path for path in figures_root.glob("*/figures.json")
    }

    if paper_order is None:
        ordered_papers = list(figures_json_by_paper.keys())
        for paper in failures:
            if paper not in figures_json_by_paper:
                ordered_papers.append(paper)
    else:
        ordered_papers = paper_order

    for paper in ordered_papers:
        if paper_filter is not None and paper not in paper_filter:
            continue

        figures_json = figures_json_by_paper.get(paper)
        if figures_json is None:
            error_message = failures.get(paper, "figures.json not found")
            rows.append(
                {
                    "paper": paper,
                    "num_figures": "0",
                    "needs_review": "yes",
                    "issues": f"figure extraction failed: {error_message}",
                }
            )
            continue

        with figures_json.open("r", encoding="utf-8") as f:
            items = json.load(f)

        issues: list[str] = []
        soft_flags = 0

        def _format_fig_ref(fig_id: str, fig_num: Optional[int]) -> str:
            if fig_num is not None:
                return f"Fig {fig_num}"
            if fig_id:
                return fig_id
            return "unknown"

        figure_numbers: list[int] = []
        seen_numbers: set[int] = set()
        duplicate_numbers = False
        empty_caption_count = 0
        caption_prefix_issue_count = 0
        caption_number_mismatch_count = 0
        body_text_leak_count = 0
        empty_caption_figs: list[str] = []
        caption_prefix_issue_figs: list[str] = []
        caption_number_mismatch_figs: list[str] = []
        body_text_leak_figs: list[str] = []
        has_short_caption = False
        has_long_caption = False

        for item in items:
            fig_id = item.get("fig_id", "")
            caption = (item.get("caption") or "").strip()
            fig_num = _extract_figure_number_from_id(fig_id)
            fig_ref = _format_fig_ref(fig_id, fig_num)
            if fig_num is not None:
                figure_numbers.append(fig_num)
                if fig_num in seen_numbers:
                    duplicate_numbers = True
                seen_numbers.add(fig_num)

            if not caption:
                empty_caption_count += 1
                empty_caption_figs.append(fig_ref)
                continue

            if not re.match(r"^\s*fig(?:ure)?\.?\s*\d+\b", caption, re.IGNORECASE):
                caption_prefix_issue_count += 1
                caption_prefix_issue_figs.append(fig_ref)

            caption_num = _extract_figure_number({"caption": caption})
            if fig_num is not None and caption_num is not None and caption_num != fig_num:
                caption_number_mismatch_count += 1
                caption_number_mismatch_figs.append(fig_ref)

            if len(caption) < 15:
                has_short_caption = True
            if len(caption) > 1200:
                has_long_caption = True
            if re.search(r"\b(Abstract|Introduction|CCS Concepts)\b", caption, re.IGNORECASE):
                body_text_leak_count += 1
                body_text_leak_figs.append(fig_ref)

        starts_at_1 = bool(figure_numbers) and min(figure_numbers) == 1
        sorted_numbers = sorted(set(figure_numbers))
        is_contiguous = bool(sorted_numbers) and sorted_numbers == list(
            range(sorted_numbers[0], sorted_numbers[-1] + 1)
        )
        missing_figure_count = 0
        duplicate_figure_count = 0
        if figure_numbers:
            expected_numbers = set(range(sorted_numbers[0], sorted_numbers[-1] + 1))
            missing_figure_count = len(expected_numbers - set(sorted_numbers))
            duplicate_figure_count = len(figure_numbers) - len(sorted_numbers)

        if not figure_numbers:
            issues.append("figure extraction issue: no figures were extracted")
        if not starts_at_1:
            issues.append("figure numbering issue: extracted figures do not start from Figure 1")
        if figure_numbers and not is_contiguous:
            issues.append(
                "figure extraction issue: "
                f"{missing_figure_count} figure(s) appear to be missing because extracted figure numbers are not contiguous"
            )
        if duplicate_numbers:
            issues.append(
                f"figure extraction issue: {duplicate_figure_count} duplicate figure number occurrence(s) were extracted"
            )
        if empty_caption_count:
            issues.append(
                "caption issue: "
                f"{empty_caption_count} extracted figure(s) have an empty caption "
                f"({', '.join(empty_caption_figs)})"
            )
        if caption_prefix_issue_count:
            issues.append(
                "caption issue: "
                f"{caption_prefix_issue_count} caption(s) do not begin with the expected figure label "
                f"({', '.join(caption_prefix_issue_figs)})"
            )
        if caption_number_mismatch_count:
            issues.append(
                "caption issue: "
                f"{caption_number_mismatch_count} caption(s) mention a different figure number than the extracted figure id "
                f"({', '.join(caption_number_mismatch_figs)})"
            )
        if body_text_leak_count:
            issues.append(
                "caption issue: "
                f"{body_text_leak_count} caption(s) appear to include leaked body text "
                f"({', '.join(body_text_leak_figs)})"
            )

        if has_short_caption:
            soft_flags += 1
        if has_long_caption:
            soft_flags += 1

        hard_issue_count = sum(
            [
                not figure_numbers,
                not starts_at_1,
                bool(figure_numbers and not is_contiguous),
                duplicate_numbers,
                bool(empty_caption_count),
                bool(caption_prefix_issue_count),
                bool(caption_number_mismatch_count),
            ]
        )

        if hard_issue_count > 0 or soft_flags >= 2:
            needs_review = "yes"
        elif soft_flags == 1 or bool(body_text_leak_count):
            needs_review = "maybe"
        else:
            needs_review = "no"

        rows.append(
            {
                "paper": paper,
                "num_figures": str(len(items)),
                "needs_review": needs_review,
                "issues": "; ".join(issues),
            }
        )

    summary_path = figures_root / "review_summary.csv"
    fieldnames = [
        "paper",
        "num_figures",
        "needs_review",
        "issues",
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return summary_path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract paper figures with PDFFigures2.")
    parser.add_argument("--pdf", type=str, help="Path to a single PDF file.")
    parser.add_argument("--out-dir", type=str, help="Output directory for a single PDF run.")
    parser.add_argument(
        "--papers-dir",
        type=str,
        default=str(DEFAULT_PAPERS_DIR_LABEL),
        help="Directory containing input PDFs for batch mode.",
    )
    parser.add_argument(
        "--figures-dir",
        type=str,
        default=str(DEFAULT_FIGURES_DIR_LABEL),
        help="Root output directory for batch mode.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every PDF under --papers-dir.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Only build review_summary.csv from existing extracted figure outputs. Do not run extraction.",
    )
    parser.add_argument("--jar-path", type=str, default=None, help="Explicit PDFFigures2 jar path.")
    parser.add_argument("--command", type=str, default=None, help="Explicit PDFFigures2 command.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing figures.json and related outputs. By default existing outputs are kept.",
    )
    parser.add_argument("--zoom", type=float, default=4.0, help="Crop rendering zoom.")
    parser.add_argument("--padding", type=float, default=8.0, help="Crop padding in PDF points.")
    parser.add_argument(
        "--include-tables",
        action="store_true",
        help="Also keep table regions if PDFFigures2 returns them.",
    )
    parser.add_argument("--timeout", type=int, default=600, help="PDFFigures2 timeout in seconds.")
    return parser


def _run_single_pdf(args: argparse.Namespace) -> str:
    if not args.pdf:
        raise ValueError("--pdf is required unless --all is set.")

    pdf_path = Path(args.pdf).expanduser().resolve()
    if args.out_dir:
        out_dir = Path(args.out_dir).expanduser().resolve()
    else:
        figures_dir = resolve_path_arg(args.figures_dir, DEFAULT_FIGURES_DIR_LABEL, DEFAULT_FIGURES_DIR)
        out_dir = figures_dir / pdf_path.stem

    results = extract_figures_with_pdffigures2(
        pdf_path=str(pdf_path),
        out_dir=str(out_dir),
        jar_path=args.jar_path,
        command=args.command,
        zoom=args.zoom,
        padding=args.padding,
        include_tables=args.include_tables,
        timeout=args.timeout,
        overwrite=args.overwrite,
    )
    print(f"{pdf_path.stem}: exported figures={len(results)} -> {out_dir / 'figures.json'}")
    return pdf_path.stem


def _run_all_papers(args: argparse.Namespace) -> tuple[list[str], dict[str, str]]:
    papers_dir = resolve_path_arg(args.papers_dir, DEFAULT_PAPERS_DIR_LABEL, DEFAULT_PAPERS_DIR)
    figures_dir = resolve_path_arg(args.figures_dir, DEFAULT_FIGURES_DIR_LABEL, DEFAULT_FIGURES_DIR)
    pdf_paths = sorted(papers_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {papers_dir}")

    completed: list[str] = []
    failed: dict[str, str] = {}
    for pdf_path in pdf_paths:
        out_dir = figures_dir / pdf_path.stem
        try:
            results = extract_figures_with_pdffigures2(
                pdf_path=str(pdf_path),
                out_dir=str(out_dir),
                jar_path=args.jar_path,
                command=args.command,
                zoom=args.zoom,
                padding=args.padding,
                include_tables=args.include_tables,
                timeout=args.timeout,
                overwrite=args.overwrite,
            )
            print(f"{pdf_path.stem}: exported figures={len(results)} -> {out_dir / 'figures.json'}")
            completed.append(pdf_path.stem)
        except Exception as exc:
            print(f"{pdf_path.stem}: failed -> {exc}")
            failed[pdf_path.stem] = str(exc).strip() or exc.__class__.__name__

    return completed, failed


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.summary:
        if args.all:
            papers_dir = Path(args.papers_dir)
            expected_papers = [path.stem for path in sorted(papers_dir.glob("*.pdf"))]
            summary_path = build_review_summary(args.figures_dir, papers=expected_papers)
            print(f"review summary: {summary_path}")
            return

        if not args.pdf:
            parser.error("Specify --pdf with --summary for a single paper, or combine --summary with --all.")

        pdf_stem = Path(args.pdf).stem
        summary_path = build_review_summary(args.figures_dir, papers=[pdf_stem])
        print(f"review summary: {summary_path}")
        return

    if args.all:
        completed, failed = _run_all_papers(args)
        summary_path = build_review_summary(
            args.figures_dir,
            papers=[*completed, *failed.keys()],
            extraction_failures=failed,
        )
        print(f"review summary: {summary_path}")
        return

    if not args.pdf:
        parser.error("Specify --pdf for a single run, or use --all for batch mode.")
    try:
        completed = _run_single_pdf(args)
        summary_path = build_review_summary(args.figures_dir, papers=[completed])
    except Exception as exc:
        pdf_stem = Path(args.pdf).stem
        summary_path = build_review_summary(
            args.figures_dir,
            papers=[pdf_stem],
            extraction_failures={pdf_stem: str(exc).strip() or exc.__class__.__name__},
        )
        print(f"{pdf_stem}: failed -> {exc}")
        print(f"review summary: {summary_path}")
        raise
    print(f"review summary: {summary_path}")


if __name__ == "__main__":
    main()
