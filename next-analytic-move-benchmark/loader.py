from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BENCHMARK_DIR = Path(__file__).resolve().parent
BENCHMARK_ROOT = BENCHMARK_DIR / "data"


@dataclass(frozen=True)
class EpisodeAssetRow:
    benchmark_case_id: str
    paper_name: str
    case_index: int
    benchmark_episode_index: int
    benchmark_episode_title: str
    panel_group: list[str]
    asset_dir_name: str
    asset_paths: list[str]
    notes: str


@dataclass(frozen=True)
class EpisodeCompositeRow:
    benchmark_case_id: str
    benchmark_episode_index: int
    composite_path: str
    source_asset_paths: list[str]
    layout_partition: list[int]
    output_width: int
    output_height: int


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def load_case_mapping(
    path: Path = BENCHMARK_ROOT / "selected_case_benchmark_episode_mapping.json",
) -> dict[str, Any]:
    return load_json(path)


def _split_pipe_field(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def _dedupe_in_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def load_episode_asset_rows(
    path: Path = BENCHMARK_ROOT / "benchmark_episode_asset_mapping.csv",
) -> list[EpisodeAssetRow]:
    rows: list[EpisodeAssetRow] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append(
                EpisodeAssetRow(
                    benchmark_case_id=str(raw["benchmark_case_id"]),
                    paper_name=str(raw["paper_name"]),
                    case_index=int(raw["case_index"]),
                    benchmark_episode_index=int(raw["benchmark_episode_index"]),
                    benchmark_episode_title=str(raw["benchmark_episode_title"]),
                    panel_group=_split_pipe_field(str(raw["panel_group"])),
                    asset_dir_name=str(raw["asset_dir_name"]),
                    asset_paths=_split_pipe_field(str(raw["asset_paths"])),
                    notes=str(raw.get("notes") or ""),
                )
            )
    return rows


def load_episode_composite_rows(
    path: Path = BENCHMARK_ROOT / "generated" / "benchmark_episode_composites.json",
) -> list[EpisodeCompositeRow]:
    if not path.exists():
        return []

    payload = load_json(path)
    rows: list[EpisodeCompositeRow] = []
    for raw in payload:
        rows.append(
            EpisodeCompositeRow(
                benchmark_case_id=str(raw["benchmark_case_id"]),
                benchmark_episode_index=int(raw["benchmark_episode_index"]),
                composite_path=str(raw["composite_path"]),
                source_asset_paths=list(raw.get("source_asset_paths", [])),
                layout_partition=[int(part) for part in raw.get("layout_partition", [])],
                output_width=int(raw.get("output_width") or 0),
                output_height=int(raw.get("output_height") or 0),
            )
        )
    return rows


def load_case_manifest(
    path: Path = BENCHMARK_ROOT / "benchmark_case_manifest.json",
) -> list[dict[str, Any]]:
    return load_json(path)


def build_case_manifest() -> list[dict[str, Any]]:
    return load_case_manifest()


def load_samples(
    path: Path = BENCHMARK_ROOT / "benchmark_samples.jsonl",
) -> list[dict[str, Any]]:
    return load_jsonl(path)


def build_samples(case_manifest: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    del case_manifest
    return load_samples()


def _find_case_entry(
    paper_name: str,
    case_index: int | None = None,
    case_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = case_manifest or load_case_manifest()
    matches = [
        case
        for case in manifest
        if str(case.get("paper_name")) == paper_name
        and (case_index is None or int(case.get("case_index") or 0) == case_index)
    ]
    if not matches:
        if case_index is None:
            raise KeyError(f"No benchmark case found for paper {paper_name}.")
        raise KeyError(f"No benchmark case found for {paper_name} case {case_index}.")
    return matches[0]


def load_usage_spec(
    paper_name: str,
    case_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return dict(_find_case_entry(paper_name, case_manifest=case_manifest)["usage_spec"])


def load_system_spec(
    paper_name: str,
    case_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return dict(_find_case_entry(paper_name, case_manifest=case_manifest)["system_spec"])


def load_workflow_spec(
    paper_name: str,
    case_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return dict(_find_case_entry(paper_name, case_manifest=case_manifest)["workflow_spec"])


def resolve_usage_case(
    paper_name: str,
    case_index: int,
    case_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    usage_spec = load_usage_spec(paper_name, case_manifest=case_manifest)
    cases = usage_spec.get("caseStudies", []) or []
    if case_index < 1 or case_index > len(cases):
        raise IndexError(f"{paper_name} case_index {case_index} is out of range.")
    return cases[case_index - 1]


def _build_step_lookup(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for episode_index, episode in enumerate(case.get("episodes", []) or [], start=1):
        for step in episode.get("steps", []) or []:
            step_index = int(step.get("stepIndex") or 0)
            lookup[f"{episode_index}.{step_index}"] = step
    return lookup
