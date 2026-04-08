"""
Evaluate a Next Analytic Move benchmark run.

Command-line usage:
- From `code-repo/`:
  `python next-analytic-move-benchmark/evaluate_run.py --run-dir next-analytic-move-benchmark/data/runs/context-only/<run-name>`
- Evaluate a direct results file:
  `python next-analytic-move-benchmark/evaluate_run.py --results-path <path-to-results.jsonl>`

Expected inputs:
- a benchmark run output such as `next-analytic-move-benchmark/data/runs/context-only/<run-name>/results.jsonl`
- `next-analytic-move-benchmark/data/benchmark_model_records.jsonl`
- `next-analytic-move-benchmark/data/benchmark_samples.jsonl`

Outputs:
- `<run-dir>/evaluation/summary.json`
- `<run-dir>/evaluation/sample_scores.jsonl`
- `<run-dir>/evaluation/goal_judge_runs.jsonl`

Configuration:
- Structured evaluation works without any model call.
- For semantic goal judging, either:
  - provide `--goal-judge-model`, `--goal-judge-api-key`, and `--goal-judge-base-url` together
  - or set `GOAL_JUDGE_MODEL`, `GOAL_JUDGE_API_KEY`, and `GOAL_JUDGE_BASE_URL` in `.env`

Open-source notes:
- Run this script from the `code-repo/` root.
- This released script evaluates saved runs but does not reconstruct the benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from loader import BENCHMARK_ROOT
from model_io import (
    NextAnalyticMoveBenchmarkRecord,
    NextAnalyticMoveModelOutput,
)


load_dotenv()


DEFAULT_BENCHMARK_RECORDS_PATH = BENCHMARK_ROOT / "benchmark_model_records.jsonl"
DEFAULT_BENCHMARK_SAMPLES_PATH = BENCHMARK_ROOT / "benchmark_samples.jsonl"
DEFAULT_GOAL_JUDGE_PROMPT_VERSION = "goal-judge.v1"
GOAL_JUDGE_API_KEY = os.environ.get("GOAL_JUDGE_API_KEY")
DEFAULT_GOAL_JUDGE_BASE_URL = os.environ.get("GOAL_JUDGE_BASE_URL")
DEFAULT_GOAL_JUDGE_MODEL = os.environ.get("GOAL_JUDGE_MODEL")


def resolve_goal_judge_config(
    *,
    model: Optional[str],
    api_key: Optional[str],
    base_url: Optional[str],
) -> tuple[str, str, str]:
    cli_values = [model, api_key, base_url]
    if any(value for value in cli_values):
        if not all(value for value in cli_values):
            raise ValueError(
                "Use one configuration mode only: either pass --goal-judge-model, --goal-judge-api-key, and "
                "--goal-judge-base-url together, or provide GOAL_JUDGE_MODEL, GOAL_JUDGE_API_KEY, and "
                "GOAL_JUDGE_BASE_URL in .env."
            )
        return str(model), str(api_key), str(base_url)

    env_model = os.environ.get("GOAL_JUDGE_MODEL")
    env_api_key = os.environ.get("GOAL_JUDGE_API_KEY")
    env_base_url = os.environ.get("GOAL_JUDGE_BASE_URL")
    if not (env_model and env_api_key and env_base_url):
        raise ValueError(
            "Missing goal-judge configuration. Either pass --goal-judge-model, --goal-judge-api-key, and "
            "--goal-judge-base-url together, or set GOAL_JUDGE_MODEL, GOAL_JUDGE_API_KEY, and "
            "GOAL_JUDGE_BASE_URL in .env."
        )
    return env_model, env_api_key, env_base_url


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    strings: list[str] = []
    for item in value:
        if isinstance(item, str):
            strings.append(item)
    return _dedupe_strings(strings)


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    parse_error_count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except Exception:
            parse_error_count += 1
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            parse_error_count += 1
    return rows, parse_error_count


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mean(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _stddev(values: list[float]) -> Optional[float]:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _safe_divide(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def _f1(precision: Optional[float], recall: Optional[float]) -> Optional[float]:
    if precision is None or recall is None:
        return None
    if precision == 0.0 and recall == 0.0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def _set_exact_match(predicted: list[str], gold: list[str]) -> bool:
    return set(predicted) == set(gold)


def _extract_text_content(message_content: Any) -> str:
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


def _extract_first_json_object(content: str) -> Optional[str]:
    start = content.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(content)):
        char = content[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : idx + 1]
    return None


@dataclass(frozen=True)
class SystemLookup:
    valid_view_ids: set[str]
    valid_subview_ids: set[str]
    valid_view_or_subview_ids: set[str]
    subview_to_view: dict[str, str]
    capability_to_subview: dict[str, str]
    capability_to_view: dict[str, str]
    valid_capability_ids: set[str]


@dataclass(frozen=True)
class WorkflowLookup:
    stage_pairs: set[tuple[str, str]]
    used_view_ids: set[str]
    used_capability_ids: set[str]


class GoalJudgeOutput(BaseModel):
    judge_score: int = Field(ge=0, le=4)
    rationale: str
    same_stage_as_gold: bool
    reasonable_alternative: bool
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


def _build_system_lookup(record: NextAnalyticMoveBenchmarkRecord) -> SystemLookup:
    valid_view_ids: set[str] = set()
    valid_subview_ids: set[str] = set()
    subview_to_view: dict[str, str] = {}
    capability_to_subview: dict[str, str] = {}
    capability_to_view: dict[str, str] = {}

    for view in record.model_input.system_context.views:
        valid_view_ids.add(view.view_id)
        for subview in view.subviews:
            valid_subview_ids.add(subview.subview_id)
            subview_to_view[subview.subview_id] = view.view_id
            for capability in subview.capabilities:
                capability_to_subview[capability.capability_id] = subview.subview_id
                capability_to_view[capability.capability_id] = view.view_id

    return SystemLookup(
        valid_view_ids=valid_view_ids,
        valid_subview_ids=valid_subview_ids,
        valid_view_or_subview_ids=valid_view_ids | valid_subview_ids,
        subview_to_view=subview_to_view,
        capability_to_subview=capability_to_subview,
        capability_to_view=capability_to_view,
        valid_capability_ids=set(capability_to_subview.keys()),
    )


def _build_workflow_lookup(record: NextAnalyticMoveBenchmarkRecord) -> WorkflowLookup:
    stage_pairs: set[tuple[str, str]] = set()
    used_view_ids: set[str] = set()
    used_capability_ids: set[str] = set()
    for workflow in record.model_input.workflow_context.workflows:
        for stage in workflow.stages:
            stage_pairs.add((workflow.workflow_id, stage.stage_id))
            used_view_ids.update(stage.used_views)
            used_capability_ids.update(stage.used_capabilities)
    return WorkflowLookup(
        stage_pairs=stage_pairs,
        used_view_ids=used_view_ids,
        used_capability_ids=used_capability_ids,
    )


def _view_relaxed_score(predicted_id: str, gold_id: str, lookup: SystemLookup) -> float:
    if predicted_id == gold_id:
        return 1.0
    if lookup.subview_to_view.get(predicted_id) == gold_id:
        return 0.5
    if lookup.subview_to_view.get(gold_id) == predicted_id:
        return 0.5
    return 0.0


def _capability_relaxed_score(predicted_id: str, gold_id: str, lookup: SystemLookup) -> float:
    if predicted_id == gold_id:
        return 1.0

    predicted_subview = lookup.capability_to_subview.get(predicted_id)
    gold_subview = lookup.capability_to_subview.get(gold_id)
    if predicted_subview and gold_subview and predicted_subview == gold_subview:
        return 0.5

    predicted_view = lookup.capability_to_view.get(predicted_id)
    gold_view = lookup.capability_to_view.get(gold_id)
    if predicted_view and gold_view and predicted_view == gold_view:
        return 0.25

    return 0.0


def _best_match_score(
    predicted: list[str],
    gold: list[str],
    score_fn: callable,
) -> float:
    if not predicted or not gold:
        return 0.0

    score_matrix = [
        [float(score_fn(predicted_item, gold_item)) for gold_item in gold]
        for predicted_item in predicted
    ]

    @lru_cache(maxsize=None)
    def _dp(index: int, used_mask: int) -> float:
        if index >= len(predicted):
            return 0.0

        best = _dp(index + 1, used_mask)
        for gold_index, weight in enumerate(score_matrix[index]):
            if weight <= 0.0:
                continue
            if used_mask & (1 << gold_index):
                continue
            best = max(best, weight + _dp(index + 1, used_mask | (1 << gold_index)))
        return best

    return _dp(0, 0)


def _compute_match_metrics(
    predicted: list[str],
    gold: list[str],
    score_fn: callable,
) -> tuple[float, float, float, float]:
    if not predicted and not gold:
        return 1.0, 1.0, 1.0, 0.0

    matched_score = _best_match_score(predicted, gold, score_fn)
    precision = matched_score / len(predicted) if predicted else 0.0
    recall = matched_score / len(gold) if gold else 0.0
    f1 = _f1(precision, recall) or 0.0
    return precision, recall, f1, matched_score


def _view_supported_in_workflow(view_id: str, lookup: SystemLookup, workflow_lookup: WorkflowLookup) -> bool:
    if view_id in workflow_lookup.used_view_ids:
        return True
    parent_view = lookup.subview_to_view.get(view_id)
    if parent_view and parent_view in workflow_lookup.used_view_ids:
        return True
    if view_id in lookup.valid_view_ids:
        for subview_id, candidate_parent_view in lookup.subview_to_view.items():
            if candidate_parent_view == view_id and subview_id in workflow_lookup.used_view_ids:
                return True
    return False


def _extract_prediction_payload(result_row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(result_row, dict):
        return None
    prediction = result_row.get("prediction")
    if isinstance(prediction, dict):
        return prediction
    if isinstance(prediction, str):
        try:
            parsed = json.loads(prediction)
        except Exception:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _invalid_view_ids(predicted_views: list[str], lookup: SystemLookup) -> list[str]:
    return [view_id for view_id in predicted_views if view_id not in lookup.valid_view_or_subview_ids]


def _invalid_capability_ids(predicted_capabilities: list[str], lookup: SystemLookup) -> list[str]:
    return [
        capability_id
        for capability_id in predicted_capabilities
        if capability_id not in lookup.valid_capability_ids
    ]


def _build_goal_judge_payload(
    record: NextAnalyticMoveBenchmarkRecord,
    prediction: NextAnalyticMoveModelOutput,
) -> dict[str, Any]:
    return {
        "sample_id": record.metadata.sample_id,
        "paper_name": record.metadata.paper_name,
        "case_summary": {
            "domain_problem": record.model_input.case_context.scenario.domain_problem,
            "analysis_goal": record.model_input.case_context.scenario.analysis_goal,
            "initial_question": record.model_input.case_context.scenario.initial_question,
        },
        "prefix_episodes": [
            {
                "benchmark_episode_index": episode.benchmark_episode_index,
                "episode_title": episode.episode_title,
                "local_goal": episode.local_goal,
                "used_views": episode.used_views,
                "used_capabilities": episode.used_capabilities,
            }
            for episode in record.model_input.case_context.prefix_episodes
        ],
        "workflow_stages": [
            {
                "workflow_id": workflow.workflow_id,
                "workflow_title": workflow.workflow_title,
                "stage_id": stage.stage_id,
                "stage_index": stage.stage_index,
                "stage_title": stage.stage_title,
                "stage_goal": stage.stage_goal,
                "used_views": stage.used_views,
                "used_capabilities": stage.used_capabilities,
            }
            for workflow in record.model_input.workflow_context.workflows
            for stage in workflow.stages
        ],
        "gold_next_episode": {
            "target_episode_index": record.gold.target_episode_index,
            "target_episode_title": record.gold.target_episode_title,
            "gold_next_goal": record.gold.gold_next_goal,
            "gold_next_views": record.gold.gold_next_views,
            "gold_next_capabilities": record.gold.gold_next_capabilities,
        },
        "prediction": prediction.model_dump(mode="json"),
    }


def _build_goal_judge_messages(
    record: NextAnalyticMoveBenchmarkRecord,
    prediction: NextAnalyticMoveModelOutput,
) -> list[dict[str, Any]]:
    payload = _build_goal_judge_payload(record, prediction)
    rubric = (
        "Score the predicted next goal on a 0-4 rubric.\n"
        "4: Semantically matches the gold next episode's local goal.\n"
        "3: Same analysis stage as gold, but somewhat broader, narrower, or differently phrased.\n"
        "2: Not the gold move, but still a reasonable adjacent next analytic move.\n"
        "1: Weak, generic, or only loosely related.\n"
        "0: Clearly off-track.\n\n"
        "Important guidance:\n"
        "- Judge the next analytic move, not the overall paper objective.\n"
        "- Do not require lexical overlap.\n"
        "- A reasonable alternative can score 2, but not 3 or 4 unless it is effectively the same move/stage.\n"
        "- If the predicted goal is vague (for example, 'continue analysis' or 'inspect more details'), cap it at 1.\n"
        "- Use the predicted views/capabilities as supporting evidence, but focus the score on predicted_next_goal.\n"
        "- Return JSON only."
    )
    user_prompt = (
        f"Prompt version: {DEFAULT_GOAL_JUDGE_PROMPT_VERSION}\n"
        f"{rubric}\n\n"
        "Return exactly one JSON object with keys:\n"
        "- judge_score: integer 0-4\n"
        "- rationale: short explanation\n"
        "- same_stage_as_gold: boolean\n"
        "- reasonable_alternative: boolean\n"
        "- confidence: optional float 0-1\n\n"
        "Case payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return [
        {
            "role": "system",
            "content": (
                "You are a careful benchmark judge for next-step recommendation quality. "
                "Score only according to the rubric and return JSON only."
            ),
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


def _parse_goal_judge_output(content: str) -> GoalJudgeOutput:
    if not content:
        raise RuntimeError("The goal judge returned empty content.")
    try:
        return GoalJudgeOutput.model_validate_json(content)
    except Exception:
        pass

    fragment = _extract_first_json_object(content)
    if fragment:
        return GoalJudgeOutput.model_validate_json(fragment)
    raise RuntimeError(f"Failed to parse goal judge output: {content[:1000]}")


def _load_cached_goal_judgment(
    cache_path: Path,
    judge_model: str,
) -> Optional[dict[str, Any]]:
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("judge_model") != judge_model:
        return None
    if payload.get("prompt_version") != DEFAULT_GOAL_JUDGE_PROMPT_VERSION:
        return None
    judgment = payload.get("judgment")
    if not isinstance(judgment, dict):
        return None
    return payload


def _resolve_goal_judgment_cache_path(
    cache_dir: Path,
    sample_id: str,
    repeat_index: int,
    repeat_count: int,
) -> Path:
    if repeat_count <= 1:
        return cache_dir / f"{sample_id}.json"
    return cache_dir / f"{sample_id}.repeat_{repeat_index:02d}.json"


def _judge_goal_once(
    client: OpenAI,
    judge_model: str,
    record: NextAnalyticMoveBenchmarkRecord,
    prediction: NextAnalyticMoveModelOutput,
    cache_path: Path,
    overwrite_cache: bool,
) -> dict[str, Any]:
    if not overwrite_cache:
        cached = _load_cached_goal_judgment(cache_path, judge_model)
        if cached is not None:
            judgment = GoalJudgeOutput.model_validate(cached["judgment"])
            return {
                "goal_judge_status": "cached",
                "goal_judge_model": judge_model,
                "goal_judge_error": None,
                "goal_judge_rationale": judgment.rationale,
                "goal_judge_same_stage_as_gold": judgment.same_stage_as_gold,
                "goal_judge_reasonable_alternative": judgment.reasonable_alternative,
                "goal_judge_confidence": judgment.confidence,
                "judge_score": judgment.judge_score,
                "goal_score": judgment.judge_score / 4,
            }

    request = {
        "model": judge_model,
        "messages": _build_goal_judge_messages(record, prediction),
        "temperature": 0.0,
    }

    last_error: Optional[str] = None
    for _attempt in range(3):
        try:
            try:
                response = client.chat.completions.create(
                    **request,
                    response_format={"type": "json_object"},
                )
            except Exception:
                response = client.chat.completions.create(**request)

            content = _extract_text_content(response.choices[0].message.content)
            judgment = _parse_goal_judge_output(content)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(
                    {
                        "sample_id": record.metadata.sample_id,
                        "judge_model": judge_model,
                        "prompt_version": DEFAULT_GOAL_JUDGE_PROMPT_VERSION,
                        "judgment": judgment.model_dump(mode="json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return {
                "goal_judge_status": "ok",
                "goal_judge_model": judge_model,
                "goal_judge_error": None,
                "goal_judge_rationale": judgment.rationale,
                "goal_judge_same_stage_as_gold": judgment.same_stage_as_gold,
                "goal_judge_reasonable_alternative": judgment.reasonable_alternative,
                "goal_judge_confidence": judgment.confidence,
                "judge_score": judgment.judge_score,
                "goal_score": judgment.judge_score / 4,
            }
        except Exception as exc:
            last_error = str(exc)

    return {
        "goal_judge_status": "error",
        "goal_judge_model": judge_model,
        "goal_judge_error": last_error,
        "goal_judge_rationale": None,
        "goal_judge_same_stage_as_gold": None,
        "goal_judge_reasonable_alternative": None,
        "goal_judge_confidence": None,
        "judge_score": None,
        "goal_score": None,
    }


def _judge_goal_repeated(
    client: OpenAI,
    judge_model: str,
    record: NextAnalyticMoveBenchmarkRecord,
    prediction: NextAnalyticMoveModelOutput,
    cache_dir: Path,
    overwrite_cache: bool,
    repeat_count: int,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    effective_repeat_count = max(1, repeat_count)
    for repeat_index in range(1, effective_repeat_count + 1):
        cache_path = _resolve_goal_judgment_cache_path(
            cache_dir=cache_dir,
            sample_id=record.metadata.sample_id,
            repeat_index=repeat_index,
            repeat_count=effective_repeat_count,
        )
        run_result = _judge_goal_once(
            client=client,
            judge_model=judge_model,
            record=record,
            prediction=prediction,
            cache_path=cache_path,
            overwrite_cache=overwrite_cache,
        )
        run_result["goal_judge_repeat_index"] = repeat_index
        runs.append(run_result)
    return runs


def _aggregate_goal_judge_status(goal_judge_runs: list[dict[str, Any]]) -> str:
    if not goal_judge_runs:
        return "not_run"

    statuses = [str(run.get("goal_judge_status") or "not_run") for run in goal_judge_runs]
    if len(goal_judge_runs) == 1:
        return statuses[0]

    ok_count = sum(1 for status in statuses if status in {"ok", "cached"})
    if ok_count == len(goal_judge_runs):
        return "multi_run_all_ok"
    if ok_count == 0:
        if all(status == "judge_not_configured" for status in statuses):
            return "multi_run_not_configured"
        if all(status == "skipped_invalid_prediction" for status in statuses):
            return "multi_run_skipped_invalid_prediction"
        return "multi_run_all_error"
    return "multi_run_partial_ok"


def _score_structure(
    gold_views: list[str],
    gold_capabilities: list[str],
    predicted_views: list[str],
    predicted_capabilities: list[str],
    lookup: SystemLookup,
) -> dict[str, Any]:
    (
        view_precision_strict,
        view_recall_strict,
        view_f1_strict,
        _view_strict_match_score,
    ) = _compute_match_metrics(
        predicted_views,
        gold_views,
        lambda predicted_id, gold_id: 1.0 if predicted_id == gold_id else 0.0,
    )
    (
        view_precision_relaxed,
        view_recall_relaxed,
        view_f1_relaxed,
        _view_relaxed_match_score_value,
    ) = _compute_match_metrics(
        predicted_views,
        gold_views,
        lambda predicted_id, gold_id: _view_relaxed_score(predicted_id, gold_id, lookup),
    )

    (
        capability_precision_strict,
        capability_recall_strict,
        capability_f1_strict,
        _capability_strict_match_score,
    ) = _compute_match_metrics(
        predicted_capabilities,
        gold_capabilities,
        lambda predicted_id, gold_id: 1.0 if predicted_id == gold_id else 0.0,
    )
    (
        capability_precision_relaxed,
        capability_recall_relaxed,
        capability_f1_relaxed,
        _capability_relaxed_match_score_value,
    ) = _compute_match_metrics(
        predicted_capabilities,
        gold_capabilities,
        lambda predicted_id, gold_id: _capability_relaxed_score(predicted_id, gold_id, lookup),
    )

    structure_score = (
        0.5 * view_f1_relaxed +
        0.5 * capability_f1_relaxed
    )

    return {
        "view_precision_strict": view_precision_strict,
        "view_recall_strict": view_recall_strict,
        "view_f1_strict": view_f1_strict,
        "view_precision_relaxed": view_precision_relaxed,
        "view_recall_relaxed": view_recall_relaxed,
        "view_f1_relaxed": view_f1_relaxed,
        "capability_precision_strict": capability_precision_strict,
        "capability_recall_strict": capability_recall_strict,
        "capability_f1_strict": capability_f1_strict,
        "capability_precision_relaxed": capability_precision_relaxed,
        "capability_recall_relaxed": capability_recall_relaxed,
        "capability_f1_relaxed": capability_f1_relaxed,
        "view_exact_match": _set_exact_match(predicted_views, gold_views),
        "capability_exact_match": _set_exact_match(predicted_capabilities, gold_capabilities),
        "joint_exact_match": (
            _set_exact_match(predicted_views, gold_views)
            and _set_exact_match(predicted_capabilities, gold_capabilities)
        ),
        "structure_score": structure_score,
    }


def _evaluate_sample(
    record: NextAnalyticMoveBenchmarkRecord,
    sample_manifest_row: dict[str, Any],
    result_row: dict[str, Any] | None,
    goal_judge_client: Optional[OpenAI],
    goal_judge_model: Optional[str],
    goal_judge_cache_dir: Path,
    overwrite_goal_judge_cache: bool,
    skip_goal_judge: bool,
    goal_judge_repeats: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lookup = _build_system_lookup(record)
    workflow_lookup = _build_workflow_lookup(record)

    raw_prediction_payload = _extract_prediction_payload(result_row)
    raw_predicted_views = _coerce_string_list(
        raw_prediction_payload.get("predicted_views") if raw_prediction_payload else None
    )
    raw_predicted_capabilities = _coerce_string_list(
        raw_prediction_payload.get("predicted_capabilities") if raw_prediction_payload else None
    )

    raw_result_status = result_row.get("status") if isinstance(result_row, dict) else None
    completion = bool(result_row) and raw_result_status == "ok"
    json_valid = raw_prediction_payload is not None
    schema_valid = False
    schema_error: Optional[str] = None
    prediction_obj: Optional[NextAnalyticMoveModelOutput] = None
    evaluation_status = "ok"

    if result_row is None:
        evaluation_status = "missing_result"
    elif raw_result_status != "ok":
        evaluation_status = f"result_status_{raw_result_status or 'missing'}"
    elif raw_prediction_payload is None:
        evaluation_status = "prediction_missing_or_non_json"
    else:
        try:
            prediction_obj = NextAnalyticMoveModelOutput.model_validate(raw_prediction_payload)
            schema_valid = True
        except Exception as exc:
            schema_error = str(exc)
            evaluation_status = "schema_invalid"

    gold_views = _dedupe_strings(list(record.gold.gold_next_views))
    gold_capabilities = _dedupe_strings(list(record.gold.gold_next_capabilities))
    predicted_views = list(prediction_obj.predicted_views) if prediction_obj else []
    predicted_capabilities = (
        list(prediction_obj.predicted_capabilities) if prediction_obj else []
    )

    invalid_view_ids = _invalid_view_ids(
        predicted_views if schema_valid else raw_predicted_views,
        lookup,
    )
    invalid_capability_ids = _invalid_capability_ids(
        predicted_capabilities if schema_valid else raw_predicted_capabilities,
        lookup,
    )

    structure_scores = _score_structure(
        gold_views=gold_views,
        gold_capabilities=gold_capabilities,
        predicted_views=predicted_views,
        predicted_capabilities=predicted_capabilities,
        lookup=lookup,
    )

    predicted_capability_parent_supported_count = 0
    for capability_id in predicted_capabilities:
        parent_subview = lookup.capability_to_subview.get(capability_id)
        parent_view = lookup.capability_to_view.get(capability_id)
        if parent_subview in predicted_views or parent_view in predicted_views:
            predicted_capability_parent_supported_count += 1

    predicted_workflow_stage = (
        prediction_obj.predicted_workflow_stage.model_dump(mode="json")
        if prediction_obj and prediction_obj.predicted_workflow_stage is not None
        else None
    )
    workflow_stage_valid = None
    if prediction_obj and prediction_obj.predicted_workflow_stage is not None:
        workflow_stage_valid = (
            prediction_obj.predicted_workflow_stage.workflow_id,
            prediction_obj.predicted_workflow_stage.stage_id,
        ) in workflow_lookup.stage_pairs

    workflow_view_supported_count = sum(
        1
        for view_id in predicted_views
        if _view_supported_in_workflow(view_id, lookup, workflow_lookup)
    )
    workflow_capability_supported_count = sum(
        1 for capability_id in predicted_capabilities if capability_id in workflow_lookup.used_capability_ids
    )

    goal_judge_fields = {
        "goal_judge_status": "skipped_by_flag" if skip_goal_judge else "not_run",
        "goal_judge_model": goal_judge_model,
        "goal_judge_error": None,
        "goal_judge_rationale": None,
        "goal_judge_same_stage_as_gold": None,
        "goal_judge_reasonable_alternative": None,
        "goal_judge_confidence": None,
        "judge_score": None,
        "goal_score": None,
    }
    goal_judge_runs: list[dict[str, Any]] = []

    if not skip_goal_judge:
        if not schema_valid or prediction_obj is None:
            goal_judge_fields.update(
                {
                    "goal_judge_status": "skipped_invalid_prediction",
                    "judge_score": 0,
                    "goal_score": 0.0,
                }
            )
            goal_judge_runs = [
                {
                    **goal_judge_fields,
                    "goal_judge_repeat_index": 1,
                }
            ]
        elif goal_judge_client is None or not goal_judge_model:
            goal_judge_fields.update(
                {
                    "goal_judge_status": "judge_not_configured",
                    "judge_score": None,
                    "goal_score": None,
                }
            )
            goal_judge_runs = [
                {
                    **goal_judge_fields,
                    "goal_judge_repeat_index": 1,
                }
            ]
        else:
            goal_judge_runs = _judge_goal_repeated(
                client=goal_judge_client,
                judge_model=goal_judge_model,
                record=record,
                prediction=prediction_obj,
                cache_dir=goal_judge_cache_dir,
                overwrite_cache=overwrite_goal_judge_cache,
                repeat_count=goal_judge_repeats,
            )
            judge_score_runs = [
                float(run["judge_score"])
                for run in goal_judge_runs
                if run.get("judge_score") is not None
            ]
            goal_score_runs = [
                float(run["goal_score"])
                for run in goal_judge_runs
                if run.get("goal_score") is not None
            ]
            first_run = goal_judge_runs[0] if goal_judge_runs else {}
            aggregate_status = _aggregate_goal_judge_status(goal_judge_runs)
            goal_judge_ok_count = sum(
                1
                for run in goal_judge_runs
                if run.get("goal_judge_status") in {"ok", "cached"}
            )
            goal_judge_fields.update(
                {
                    "goal_judge_status": aggregate_status,
                    "goal_judge_model": goal_judge_model,
                    "goal_judge_error": first_run.get("goal_judge_error"),
                    "goal_judge_rationale": first_run.get("goal_judge_rationale"),
                    "goal_judge_same_stage_as_gold": first_run.get("goal_judge_same_stage_as_gold"),
                    "goal_judge_reasonable_alternative": first_run.get("goal_judge_reasonable_alternative"),
                    "goal_judge_confidence": first_run.get("goal_judge_confidence"),
                    "judge_score": _mean(judge_score_runs),
                    "goal_score": _mean(goal_score_runs),
                    "goal_judge_run_count": len(goal_judge_runs),
                    "goal_judge_ok_count": goal_judge_ok_count,
                    "goal_judge_error_count": len(goal_judge_runs) - goal_judge_ok_count,
                    "judge_score_runs": judge_score_runs,
                    "goal_score_runs": goal_score_runs,
                    "judge_score_std": _stddev(judge_score_runs),
                    "goal_score_std": _stddev(goal_score_runs),
                    "judge_score_min": min(judge_score_runs) if judge_score_runs else None,
                    "judge_score_max": max(judge_score_runs) if judge_score_runs else None,
                    "goal_score_min": min(goal_score_runs) if goal_score_runs else None,
                    "goal_score_max": max(goal_score_runs) if goal_score_runs else None,
                }
            )

    if not goal_judge_runs:
        goal_judge_runs = [
            {
                **goal_judge_fields,
                "goal_judge_repeat_index": 1,
            }
        ]

    goal_judge_fields.setdefault("goal_judge_run_count", len(goal_judge_runs))
    goal_judge_fields.setdefault(
        "goal_judge_ok_count",
        sum(
            1
            for run in goal_judge_runs
            if run.get("goal_judge_status") in {"ok", "cached"}
        ),
    )
    goal_judge_fields.setdefault(
        "goal_judge_error_count",
        len(goal_judge_runs) - int(goal_judge_fields.get("goal_judge_ok_count") or 0),
    )
    goal_judge_fields.setdefault(
        "judge_score_runs",
        [
            float(run["judge_score"])
            for run in goal_judge_runs
            if run.get("judge_score") is not None
        ],
    )
    goal_judge_fields.setdefault(
        "goal_score_runs",
        [
            float(run["goal_score"])
            for run in goal_judge_runs
            if run.get("goal_score") is not None
        ],
    )
    goal_judge_fields.setdefault("judge_score_std", None)
    goal_judge_fields.setdefault("goal_score_std", None)
    goal_judge_fields.setdefault("judge_score_min", goal_judge_fields.get("judge_score"))
    goal_judge_fields.setdefault("judge_score_max", goal_judge_fields.get("judge_score"))
    goal_judge_fields.setdefault("goal_score_min", goal_judge_fields.get("goal_score"))
    goal_judge_fields.setdefault("goal_score_max", goal_judge_fields.get("goal_score"))

    next_move_score = None
    if goal_judge_fields["goal_score"] is not None:
        next_move_score = (
            0.4 * structure_scores["view_f1_relaxed"]
            + 0.4 * structure_scores["capability_f1_relaxed"]
            + 0.2 * float(goal_judge_fields["goal_score"])
        )

    review_reasons: list[str] = []
    if goal_judge_fields["goal_score"] is not None and goal_judge_fields["goal_score"] >= 0.5:
        if structure_scores["structure_score"] < 0.25:
            review_reasons.append("goal_good_but_structure_low")
    if goal_judge_fields["goal_score"] is not None and goal_judge_fields["goal_score"] < 0.25:
        if structure_scores["structure_score"] >= 0.7:
            review_reasons.append("structure_good_but_goal_low")
    if len(invalid_view_ids) + len(invalid_capability_ids) >= 2:
        review_reasons.append("many_invalid_ids")
    if (
        structure_scores["view_f1_relaxed"] - structure_scores["view_f1_strict"] >= 0.5
        or structure_scores["capability_f1_relaxed"] - structure_scores["capability_f1_strict"] >= 0.5
    ):
        review_reasons.append("strict_low_relaxed_high")

    sample_score = {
        "sample_id": record.metadata.sample_id,
        "benchmark_case_id": record.metadata.benchmark_case_id,
        "paper_name": record.metadata.paper_name,
        "case_index": record.metadata.case_index,
        "prefix_length": record.metadata.prefix_length,
        "prefix_episode_indices": record.metadata.prefix_episode_indices,
        "target_episode_index": record.metadata.target_episode_index,
        "case_title": sample_manifest_row.get("case_title"),
        "segmentation_mode": sample_manifest_row.get("segmentation_mode"),
        "target_episode_title": sample_manifest_row.get("target_episode_title"),
        "status": raw_result_status or "missing_result",
        "raw_result_status": raw_result_status,
        "evaluation_status": evaluation_status,
        "completion": completion,
        "json_valid": json_valid,
        "schema_valid": schema_valid,
        "schema_error": schema_error,
        "model_input": record.model_input.model_dump(mode="json"),
        "gold": record.gold.model_dump(mode="json"),
        "prediction": raw_prediction_payload,
        "predicted_workflow_stage": predicted_workflow_stage,
        "workflow_stage_valid": workflow_stage_valid,
        "invalid_view_ids": invalid_view_ids,
        "invalid_capability_ids": invalid_capability_ids,
        "invalid_view_id_count": len(invalid_view_ids),
        "invalid_capability_id_count": len(invalid_capability_ids),
        "raw_predicted_view_count": len(raw_predicted_views),
        "raw_predicted_capability_count": len(raw_predicted_capabilities),
        "predicted_view_count": len(predicted_views),
        "predicted_capability_count": len(predicted_capabilities),
        "workflow_view_supported_count": workflow_view_supported_count,
        "workflow_capability_supported_count": workflow_capability_supported_count,
        "workflow_view_support_rate": _safe_divide(workflow_view_supported_count, len(predicted_views)),
        "workflow_capability_support_rate": _safe_divide(
            workflow_capability_supported_count,
            len(predicted_capabilities),
        ),
        "internal_consistency_supported_count": predicted_capability_parent_supported_count,
        "internal_consistency_total_count": len(predicted_capabilities),
        "internal_consistency_rate": _safe_divide(
            predicted_capability_parent_supported_count,
            len(predicted_capabilities),
        ),
        **structure_scores,
        **goal_judge_fields,
        "goal_judge_runs": goal_judge_runs,
        "next_move_score": next_move_score,
        "review_reasons": review_reasons,
        "needs_review": bool(review_reasons),
    }
    goal_judge_run_rows = [
        {
            "sample_id": record.metadata.sample_id,
            "benchmark_case_id": record.metadata.benchmark_case_id,
            "paper_name": record.metadata.paper_name,
            "repeat_index": run.get("goal_judge_repeat_index"),
            "goal_judge_model": run.get("goal_judge_model"),
            "goal_judge_status": run.get("goal_judge_status"),
            "goal_judge_error": run.get("goal_judge_error"),
            "goal_judge_rationale": run.get("goal_judge_rationale"),
            "goal_judge_same_stage_as_gold": run.get("goal_judge_same_stage_as_gold"),
            "goal_judge_reasonable_alternative": run.get("goal_judge_reasonable_alternative"),
            "goal_judge_confidence": run.get("goal_judge_confidence"),
            "judge_score": run.get("judge_score"),
            "goal_score": run.get("goal_score"),
        }
        for run in goal_judge_runs
    ]
    return sample_score, goal_judge_run_rows


def _build_summary_rows(rows: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(group_key)), []).append(row)

    return [
        {
            group_key: group_value,
            **_summarize_rows(group_rows),
        }
        for group_value, group_rows in sorted(grouped.items(), key=lambda item: item[0])
    ]


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sample_count = len(rows)
    completed_count = sum(1 for row in rows if row["completion"])
    json_valid_count = sum(1 for row in rows if row["json_valid"])
    schema_valid_count = sum(1 for row in rows if row["schema_valid"])
    goal_score_available_count = sum(1 for row in rows if row["goal_score"] is not None)
    goal_judge_sample_ok_count = sum(1 for row in rows if int(row.get("goal_judge_ok_count") or 0) > 0)
    goal_judge_ok_count = sum(int(row.get("goal_judge_ok_count") or 0) for row in rows)
    goal_judge_run_count = sum(int(row.get("goal_judge_run_count") or 0) for row in rows)
    goal_judge_error_count = sum(int(row.get("goal_judge_error_count") or 0) for row in rows)
    goal_judge_not_configured_count = sum(
        1
        for row in rows
        if row["goal_judge_status"] in {"judge_not_configured", "multi_run_not_configured"}
    )
    goal_judge_multi_run_count = sum(
        1 for row in rows if str(row["goal_judge_status"]).startswith("multi_run_")
    )
    review_queue_count = sum(1 for row in rows if row["needs_review"])

    total_raw_predicted_views = sum(row["raw_predicted_view_count"] for row in rows)
    total_raw_predicted_capabilities = sum(row["raw_predicted_capability_count"] for row in rows)
    total_predicted_capabilities = sum(row["predicted_capability_count"] for row in rows)
    total_workflow_view_supported = sum(row["workflow_view_supported_count"] for row in rows)
    total_workflow_capability_supported = sum(
        row["workflow_capability_supported_count"] for row in rows
    )
    total_predicted_views = sum(row["predicted_view_count"] for row in rows)
    total_internal_consistency_supported = sum(
        row["internal_consistency_supported_count"] for row in rows
    )

    metrics_to_average = [
        "view_precision_strict",
        "view_recall_strict",
        "view_f1_strict",
        "view_precision_relaxed",
        "view_recall_relaxed",
        "view_f1_relaxed",
        "capability_precision_strict",
        "capability_recall_strict",
        "capability_f1_strict",
        "capability_precision_relaxed",
        "capability_recall_relaxed",
        "capability_f1_relaxed",
        "structure_score",
        "goal_score",
        "next_move_score",
        "workflow_view_support_rate",
        "workflow_capability_support_rate",
        "internal_consistency_rate",
    ]
    metric_means: dict[str, Any] = {}
    for metric_name in metrics_to_average:
        values = [
            float(row[metric_name])
            for row in rows
            if row.get(metric_name) is not None
        ]
        metric_means[metric_name] = _mean(values)

    return {
        "sample_count": sample_count,
        "completed_count": completed_count,
        "completion_rate": completed_count / sample_count if sample_count else 0.0,
        "json_valid_count": json_valid_count,
        "json_valid_rate": json_valid_count / sample_count if sample_count else 0.0,
        "schema_valid_count": schema_valid_count,
        "schema_valid_rate": schema_valid_count / sample_count if sample_count else 0.0,
        "goal_score_available_count": goal_score_available_count,
        "goal_score_available_rate": (
            goal_score_available_count / sample_count if sample_count else 0.0
        ),
        "goal_judge_sample_ok_count": goal_judge_sample_ok_count,
        "goal_judge_sample_ok_rate": (
            goal_judge_sample_ok_count / sample_count if sample_count else 0.0
        ),
        "goal_judge_ok_count": goal_judge_ok_count,
        "goal_judge_ok_rate": _safe_divide(goal_judge_ok_count, goal_judge_run_count),
        "goal_judge_run_count": goal_judge_run_count,
        "goal_judge_error_count": goal_judge_error_count,
        "goal_judge_error_rate": _safe_divide(goal_judge_error_count, goal_judge_run_count),
        "goal_judge_not_configured_count": goal_judge_not_configured_count,
        "goal_judge_multi_run_count": goal_judge_multi_run_count,
        "view_exact_match_rate": (
            sum(1 for row in rows if row["view_exact_match"]) / sample_count if sample_count else 0.0
        ),
        "capability_exact_match_rate": (
            sum(1 for row in rows if row["capability_exact_match"]) / sample_count
            if sample_count
            else 0.0
        ),
        "joint_exact_match_rate": (
            sum(1 for row in rows if row["joint_exact_match"]) / sample_count if sample_count else 0.0
        ),
        "invalid_view_id_count": sum(row["invalid_view_id_count"] for row in rows),
        "invalid_capability_id_count": sum(row["invalid_capability_id_count"] for row in rows),
        "invalid_view_id_rate": _safe_divide(
            sum(row["invalid_view_id_count"] for row in rows),
            total_raw_predicted_views,
        ),
        "invalid_capability_id_rate": _safe_divide(
            sum(row["invalid_capability_id_count"] for row in rows),
            total_raw_predicted_capabilities,
        ),
        "workflow_view_support_rate_micro": _safe_divide(
            total_workflow_view_supported,
            total_predicted_views,
        ),
        "workflow_capability_support_rate_micro": _safe_divide(
            total_workflow_capability_supported,
            sum(row["predicted_capability_count"] for row in rows),
        ),
        "internal_consistency_rate_micro": _safe_divide(
            total_internal_consistency_supported,
            total_predicted_capabilities,
        ),
        "review_queue_count": review_queue_count,
        **metric_means,
    }


def _load_benchmark_records(path: Path) -> list[NextAnalyticMoveBenchmarkRecord]:
    raw_rows, parse_errors = _read_jsonl(path)
    if parse_errors:
        raise RuntimeError(f"Failed to parse {parse_errors} benchmark record lines from {path}.")
    return [NextAnalyticMoveBenchmarkRecord.model_validate(row) for row in raw_rows]


def _load_sample_manifest(path: Path) -> dict[str, dict[str, Any]]:
    rows, parse_errors = _read_jsonl(path)
    if parse_errors:
        raise RuntimeError(f"Failed to parse {parse_errors} sample manifest lines from {path}.")
    return {
        str(row["sample_id"]): row
        for row in rows
        if isinstance(row.get("sample_id"), str)
    }


def _load_result_rows(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    rows, parse_errors = _read_jsonl(path)
    by_sample_id: dict[str, dict[str, Any]] = {}
    stats = {
        "result_line_parse_error_count": parse_errors,
        "result_rows_without_sample_id_count": 0,
        "duplicate_result_row_count": 0,
        "result_row_count": 0,
    }

    for row in rows:
        stats["result_row_count"] += 1
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str):
            stats["result_rows_without_sample_id_count"] += 1
            continue
        if sample_id in by_sample_id:
            stats["duplicate_result_row_count"] += 1
        by_sample_id[sample_id] = row
    return by_sample_id, stats


def _resolve_results_path(args: argparse.Namespace) -> Path:
    if args.results_path:
        return Path(args.results_path)
    if args.run_dir:
        return Path(args.run_dir) / "results.jsonl"
    raise ValueError("Provide either --results-path or --run-dir.")


def _resolve_output_dir(args: argparse.Namespace, results_path: Path) -> Path:
    if args.output_dir:
        return Path(args.output_dir)
    return results_path.parent / "evaluation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a Next Analytic Move baseline run."
    )
    parser.add_argument(
        "--run-dir",
        help="Run directory containing results.jsonl. Output defaults to <run-dir>/evaluation.",
    )
    parser.add_argument(
        "--results-path",
        help="Optional direct path to results.jsonl. Overrides --run-dir for loading results.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional output directory for evaluation artifacts.",
    )
    parser.add_argument(
        "--benchmark-records-path",
        default=str(DEFAULT_BENCHMARK_RECORDS_PATH),
        help="Path to benchmark_model_records.jsonl.",
    )
    parser.add_argument(
        "--benchmark-samples-path",
        default=str(DEFAULT_BENCHMARK_SAMPLES_PATH),
        help="Path to benchmark_samples.jsonl.",
    )
    parser.add_argument(
        "--sample-id",
        action="append",
        dest="sample_ids",
        help="Optional sample id filter. Can be provided multiple times.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Optional maximum number of samples to evaluate after filtering.",
    )
    parser.add_argument(
        "--skip-goal-judge",
        action="store_true",
        help="Skip the semantic goal judge and only run structured evaluation.",
    )
    parser.add_argument(
        "--goal-judge-model",
        help="Goal-judge model. Must be passed together with --goal-judge-api-key and --goal-judge-base-url unless .env is used.",
    )
    parser.add_argument(
        "--goal-judge-base-url",
        help="Goal-judge base URL. Must be passed together with --goal-judge-model and --goal-judge-api-key unless .env is used.",
    )
    parser.add_argument(
        "--goal-judge-api-key",
        help="Goal-judge API key. Must be passed together with --goal-judge-model and --goal-judge-base-url unless .env is used.",
    )
    parser.add_argument(
        "--overwrite-goal-judge-cache",
        action="store_true",
        help="Re-run semantic goal judging even if a cached judgment exists.",
    )
    parser.add_argument(
        "--goal-judge-repeats",
        type=int,
        default=1,
        help=(
            "Number of repeated goal-judge runs per sample. Each run is recorded "
            "separately; sample-level aggregates use the mean."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = _resolve_results_path(args)
    output_dir = _resolve_output_dir(args, results_path)
    if not results_path.exists():
        raise FileNotFoundError(f"Missing results.jsonl at {results_path}")

    benchmark_records = _load_benchmark_records(Path(args.benchmark_records_path))
    sample_manifest_lookup = _load_sample_manifest(Path(args.benchmark_samples_path))
    result_rows_by_sample_id, result_stats = _load_result_rows(results_path)

    if args.sample_ids:
        wanted = set(args.sample_ids)
        benchmark_records = [
            record for record in benchmark_records if record.metadata.sample_id in wanted
        ]
    if args.max_samples is not None:
        benchmark_records = benchmark_records[: args.max_samples]

    goal_judge_model = None if args.skip_goal_judge else args.goal_judge_model
    resolved_goal_judge_base_url: Optional[str] = None
    goal_judge_client: Optional[OpenAI] = None
    if not args.skip_goal_judge:
        resolved_goal_judge_model, resolved_goal_judge_api_key, resolved_goal_judge_base_url = resolve_goal_judge_config(
            model=args.goal_judge_model,
            api_key=args.goal_judge_api_key,
            base_url=args.goal_judge_base_url,
        )
        goal_judge_model = resolved_goal_judge_model
        goal_judge_client = OpenAI(
            api_key=resolved_goal_judge_api_key,
            base_url=resolved_goal_judge_base_url,
        )

    evaluation_rows: list[dict[str, Any]] = []
    goal_judge_run_rows: list[dict[str, Any]] = []
    goal_judge_cache_dir = output_dir / "goal_judgments"
    for record in benchmark_records:
        sample_manifest_row = sample_manifest_lookup.get(record.metadata.sample_id)
        if sample_manifest_row is None:
            raise KeyError(f"Missing sample manifest row for {record.metadata.sample_id}")
        result_row = result_rows_by_sample_id.get(record.metadata.sample_id)
        sample_row, sample_goal_judge_run_rows = _evaluate_sample(
            record=record,
            sample_manifest_row=sample_manifest_row,
            result_row=result_row,
            goal_judge_client=goal_judge_client,
            goal_judge_model=goal_judge_model,
            goal_judge_cache_dir=goal_judge_cache_dir,
            overwrite_goal_judge_cache=args.overwrite_goal_judge_cache,
            skip_goal_judge=args.skip_goal_judge,
            goal_judge_repeats=args.goal_judge_repeats,
        )
        evaluation_rows.append(sample_row)
        goal_judge_run_rows.extend(sample_goal_judge_run_rows)

    review_queue_rows = [row for row in evaluation_rows if row["needs_review"]]
    summary = {
        "results_path": str(results_path),
        "output_dir": str(output_dir),
        "benchmark_records_path": str(args.benchmark_records_path),
        "benchmark_samples_path": str(args.benchmark_samples_path),
        "skip_goal_judge": args.skip_goal_judge,
        "goal_judge_model": goal_judge_model,
        "goal_judge_base_url": resolved_goal_judge_base_url,
        "goal_judge_repeats": args.goal_judge_repeats,
        "filters": {
            "sample_ids": list(args.sample_ids or []),
            "max_samples": args.max_samples,
        },
        "result_file_stats": result_stats,
        "aggregate": _summarize_rows(evaluation_rows),
    }

    _write_json(output_dir / "config.json", summary)
    _write_jsonl(output_dir / "sample_scores.jsonl", evaluation_rows)
    _write_jsonl(output_dir / "goal_judge_runs.jsonl", goal_judge_run_rows)
    _write_json(output_dir / "summary.json", summary)
    _write_csv(output_dir / "paper_breakdown.csv", _build_summary_rows(evaluation_rows, "paper_name"))
    _write_csv(
        output_dir / "prefix_length_breakdown.csv",
        _build_summary_rows(evaluation_rows, "prefix_length"),
    )
    _write_csv(
        output_dir / "segmentation_mode_breakdown.csv",
        _build_summary_rows(evaluation_rows, "segmentation_mode"),
    )
    _write_jsonl(output_dir / "review_queue.jsonl", review_queue_rows)


if __name__ == "__main__":
    main()
