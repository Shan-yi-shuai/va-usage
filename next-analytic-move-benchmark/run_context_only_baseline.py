"""
Run the context-only baseline on the Next Analytic Move benchmark.

Command-line usage:
- From `code-repo/`:
  `python next-analytic-move-benchmark/run_context_only_baseline.py --model <model> --api-key <key> --base-url <url>`
- Dry-run mode:
  `python next-analytic-move-benchmark/run_context_only_baseline.py --dry-run --max-samples 5`

Expected input:
- `next-analytic-move-benchmark/data/benchmark_model_records.jsonl`

Outputs:
- `next-analytic-move-benchmark/data/runs/context-only/<run-name-or-timestamp>/results.jsonl`
- `next-analytic-move-benchmark/data/runs/context-only/<run-name-or-timestamp>/prompts/`
- `next-analytic-move-benchmark/data/runs/context-only/<run-name-or-timestamp>/parsed_responses/`

Configuration:
- Either:
  - provide `--model`, `--api-key`, and `--base-url` together
  - or set `OPENAI_MODEL`, `OPENAI_API_KEY`, and `OPENAI_BASE_URL` in `.env`

Open-source notes:
- Run this script from the `code-repo/` root.
- This released script runs the benchmark but does not rebuild benchmark data.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

from loader import BENCHMARK_ROOT
from model_io import NextAnalyticMoveModelOutput
from prompting import build_context_only_prompt


load_dotenv()


DEFAULT_INPUT_PATH = BENCHMARK_ROOT / "benchmark_model_records.jsonl"
RUNS_ROOT = BENCHMARK_ROOT / "runs" / "context-only"
MAX_ATTEMPTS = 5


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
                "Use one configuration mode only: either pass --model, --api-key, and --base-url together, "
                "or provide OPENAI_MODEL, OPENAI_API_KEY, and OPENAI_BASE_URL in .env."
            )
        return str(model), str(api_key), str(base_url)

    env_model = os.environ.get("OPENAI_MODEL")
    env_api_key = os.environ.get("OPENAI_API_KEY")
    env_base_url = os.environ.get("OPENAI_BASE_URL")
    if not (env_model and env_api_key and env_base_url):
        raise ValueError(
            "Missing model configuration. Either pass --model, --api-key, and --base-url together, "
            "or set OPENAI_MODEL, OPENAI_API_KEY, and OPENAI_BASE_URL in .env."
        )
    return env_model, env_api_key, env_base_url


def encode_image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    with path.open("rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


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


def extract_first_json_object(content: str) -> Optional[str]:
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


def parse_model_output(content: str) -> NextAnalyticMoveModelOutput:
    if not content:
        raise RuntimeError("The model returned empty content.")
    try:
        return NextAnalyticMoveModelOutput.model_validate_json(content)
    except Exception:
        pass

    fragment = extract_first_json_object(content)
    if fragment:
        return NextAnalyticMoveModelOutput.model_validate_json(fragment)

    raise RuntimeError(f"Failed to parse model output as JSON: {content[:1000]}")


def load_records(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rows.append(json.loads(stripped))
    return rows


def make_messages(record: dict[str, Any], prompt_text: str, include_images: bool) -> list[dict[str, Any]]:
    user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt_text}]
    if include_images:
        for index, image_entry in enumerate(
            record["model_input"]["visual_context"].get("prefix_episode_images", []),
            start=1,
        ):
            image_path = Path(image_entry["image_path"])
            if not image_path.exists():
                raise FileNotFoundError(f"Missing prefix image: {image_path}")
            user_content.append(
                {
                    "type": "text",
                    "text": (
                        f"Attached image {index} corresponds to benchmark episode "
                        f"{image_entry['benchmark_episode_index']}: {image_entry['episode_title']}."
                    ),
                }
            )
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": encode_image_to_data_url(image_path)},
                }
            )

    return [
        {
            "role": "system",
            "content": (
                "You are a careful benchmark model. Follow the task contract exactly "
                "and return JSON only."
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def resolve_run_dir(run_name: Optional[str]) -> Path:
    if run_name:
        return RUNS_ROOT / run_name
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return RUNS_ROOT / timestamp


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_sample(
    client: Optional[OpenAI],
    model_name: str,
    record: dict[str, Any],
    run_dir: Path,
    include_images: bool,
    dry_run: bool,
) -> dict[str, Any]:
    sample_id = str(record["metadata"]["sample_id"])
    prompt_text = build_context_only_prompt(record)
    prompt_path = run_dir / "prompts" / f"{sample_id}.txt"
    request_manifest_path = run_dir / "request_manifests" / f"{sample_id}.json"
    raw_response_path = run_dir / "raw_responses" / f"{sample_id}.txt"
    parsed_response_path = run_dir / "parsed_responses" / f"{sample_id}.json"

    write_text(prompt_path, prompt_text)
    write_json(
        request_manifest_path,
        {
            "sample_id": sample_id,
            "model": model_name,
            "include_images": include_images,
            "image_entries": record["model_input"]["visual_context"].get("prefix_episode_images", []),
        },
    )

    if dry_run:
        result = {
            "sample_id": sample_id,
            "status": "dry_run",
            "model": model_name,
            "prompt_path": str(prompt_path),
            "request_manifest_path": str(request_manifest_path),
            "attached_image_count": len(
                record["model_input"]["visual_context"].get("prefix_episode_images", [])
            )
            if include_images
            else 0,
        }
        write_json(parsed_response_path, result)
        return result

    if client is None:
        raise RuntimeError("OpenAI client is required for non-dry-run execution.")

    messages = make_messages(record, prompt_text, include_images=include_images)
    request = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.0,
    }

    try:
        response = client.chat.completions.create(
            **request,
            response_format={"type": "json_object"},
        )
    except Exception:
        response = client.chat.completions.create(**request)

    content = extract_text_content(response.choices[0].message.content)
    write_text(raw_response_path, content)

    parsed = parse_model_output(content)
    result = {
        "sample_id": sample_id,
        "status": "ok",
        "model": model_name,
        "prompt_path": str(prompt_path),
        "request_manifest_path": str(request_manifest_path),
        "raw_response_path": str(raw_response_path),
        "parsed_response_path": str(parsed_response_path),
        "usage": (
            response.usage.model_dump()
            if getattr(response, "usage", None) is not None
            and hasattr(response.usage, "model_dump")
            else None
        ),
        "prediction": parsed.model_dump(mode="json"),
    }
    write_json(parsed_response_path, result)
    return result


def run_sample_with_retries(
    client: Optional[OpenAI],
    model_name: str,
    record: dict[str, Any],
    run_dir: Path,
    include_images: bool,
    dry_run: bool,
    max_attempts: int = MAX_ATTEMPTS,
) -> dict[str, Any]:
    sample_id = str(record["metadata"]["sample_id"])
    last_error: Optional[Exception] = None

    for attempt_count in range(1, max_attempts + 1):
        try:
            result = run_sample(
                client=client,
                model_name=model_name,
                record=record,
                run_dir=run_dir,
                include_images=include_images,
                dry_run=dry_run,
            )
            result["attempt_count"] = attempt_count
            parsed_response_path = run_dir / "parsed_responses" / f"{sample_id}.json"
            write_json(parsed_response_path, result)
            return result
        except Exception as exc:
            last_error = exc

    return {
        "sample_id": sample_id,
        "status": "error",
        "model": model_name,
        "attempt_count": max_attempts,
        "error": repr(last_error) if last_error is not None else "Unknown error",
    }


def collect_existing_result_ids(results_path: Path) -> set[str]:
    if not results_path.exists():
        return set()
    seen: set[str] = set()
    for line in results_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except Exception:
            continue
        sample_id = row.get("sample_id")
        if isinstance(sample_id, str):
            seen.add(sample_id)
    return seen


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False))
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the context-only baseline on the Next Analytic Move benchmark."
    )
    parser.add_argument(
        "--input-path",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to benchmark_model_records.jsonl.",
    )
    parser.add_argument(
        "--model",
        help="Model name. Must be passed together with --api-key and --base-url unless .env is used.",
    )
    parser.add_argument(
        "--run-name",
        help="Optional run directory name under next-analytic-move-benchmark/data/runs/context-only/.",
    )
    parser.add_argument(
        "--base-url",
        help="OpenAI-compatible base URL. Must be passed together with --model and --api-key unless .env is used.",
    )
    parser.add_argument(
        "--api-key",
        help="API key. Must be passed together with --model and --base-url unless .env is used.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Optional maximum number of samples to run.",
    )
    parser.add_argument(
        "--sample-id",
        action="append",
        dest="sample_ids",
        help="Optional sample id filter. Can be provided multiple times.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only materialize prompts and request manifests without calling the model.",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Do not attach prefix episode images. Useful for text-only debugging.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-run samples even if they already exist in results.jsonl.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_path)
    records = load_records(input_path)

    if args.sample_ids:
        wanted = set(args.sample_ids)
        records = [record for record in records if record["metadata"]["sample_id"] in wanted]
    if args.max_samples is not None:
        records = records[: max(0, args.max_samples)]

    run_dir = resolve_run_dir(args.run_name)
    results_path = run_dir / "results.jsonl"
    config_path = run_dir / "config.json"
    existing_ids = set() if args.overwrite else collect_existing_result_ids(results_path)

    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    if not args.dry_run:
        model_name, api_key, base_url = resolve_model_config(
            model=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
        )
    else:
        model_name = args.model or os.environ.get("OPENAI_MODEL") or "dry-run"
        base_url = args.base_url or os.environ.get("OPENAI_BASE_URL") or "dry-run"

    write_json(
        config_path,
        {
            "input_path": str(input_path),
            "model": model_name,
            "base_url": base_url,
            "api_key_source": "cli" if args.api_key else ("env" if not args.dry_run else "not_required"),
            "dry_run": args.dry_run,
            "include_images": not args.no_images,
            "max_attempts": MAX_ATTEMPTS,
            "created_at_utc": datetime.now(UTC).isoformat(),
        },
    )

    client = None if args.dry_run else OpenAI(api_key=api_key, base_url=base_url)

    processed = 0
    skipped = 0
    failed = 0

    for record in records:
        sample_id = str(record["metadata"]["sample_id"])
        if sample_id in existing_ids:
            skipped += 1
            continue

        result = run_sample_with_retries(
            client=client,
            model_name=model_name,
            record=record,
            run_dir=run_dir,
            include_images=not args.no_images,
            dry_run=bool(args.dry_run),
        )

        if result["status"] == "error":
            failed += 1
            append_jsonl(results_path, result)
            continue

        append_jsonl(results_path, result)
        processed += 1

    write_json(
        run_dir / "summary.json",
        {
            "model": args.model,
            "dry_run": bool(args.dry_run),
            "include_images": not args.no_images,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "run_dir": str(run_dir),
        },
    )


if __name__ == "__main__":
    main()
