# Next Analytic Move Benchmark

This directory contains the released `Next Analytic Move` benchmark package.

Use this directory from the `code-repo/` root. The scripts in this folder assume paths such as `next-analytic-move-benchmark/data/...`.

## What Is Included

- `data/benchmark_model_records.jsonl`: the main benchmark input records used for model runs
- `data/benchmark_samples.jsonl`: sample-level metadata and gold annotations used by evaluation
- `data/benchmark_case_manifest.json`: compact case-level manifest retained as reference metadata
- `data/episode-composites/`: prefix and target episode composite images
- `run_context_only_baseline.py`: baseline runner
- `evaluate_run.py`: evaluation script
- `loader.py`, `model_io.py`, `prompting.py`, `schema_common.py`: supporting code

This release includes the minimal benchmark data needed to run and evaluate the released benchmark package. It does not include benchmark construction scripts.
The released package is self-contained: the retained benchmark files depend only on the released episode composite images and do not depend on an external knowledge base.

## Basic Workflow

1. Run a model on the benchmark with `run_context_only_baseline.py`.
2. Evaluate the saved run with `evaluate_run.py`.
3. Inspect the generated prompts, raw responses, parsed responses, and evaluation summaries.

## Run The Baseline

From `code-repo/`:

```bash
python next-analytic-move-benchmark/run_context_only_baseline.py \
  --model <your_model_name> \
  --api-key <your_api_key> \
  --base-url <your_openai_compatible_base_url>
```

Useful options:

- `--dry-run`: materialize prompts and request manifests without calling a model
- `--sample-id <id>`: run only selected samples
- `--max-samples N`: limit the number of samples
- `--no-images`: text-only debugging mode
- `--run-name <name>`: write outputs to `next-analytic-move-benchmark/data/runs/context-only/<name>/`

Configuration rule:

- either pass `--model`, `--api-key`, and `--base-url` together
- or provide `OPENAI_MODEL`, `OPENAI_API_KEY`, and `OPENAI_BASE_URL` in `.env`

Outputs are written under:

- `next-analytic-move-benchmark/data/runs/context-only/<timestamp-or-run-name>/`

Important run artifacts include:

- `results.jsonl`
- `prompts/`
- `request_manifests/`
- `raw_responses/`
- `parsed_responses/`
- `config.json`

## Evaluate A Run

After a run finishes, evaluate it from `code-repo/`:

```bash
python next-analytic-move-benchmark/evaluate_run.py \
  --run-dir next-analytic-move-benchmark/data/runs/context-only/<run-name>
```

Useful options:

- `--results-path <path>`: evaluate a specific `results.jsonl` directly
- `--output-dir <path>`: override the default evaluation output directory
- `--sample-id <id>`: evaluate only selected samples
- `--max-samples N`: limit the number of evaluated samples
- `--skip-goal-judge`: skip semantic goal judging and only run structured evaluation
- `--goal-judge-model <model>`: enable semantic goal judging
- `--goal-judge-api-key <key>`: goal-judge API key
- `--goal-judge-base-url <url>`: custom endpoint for the goal judge
- `--goal-judge-repeats N`: repeat goal judging multiple times per sample

Configuration rule for semantic goal judging:

- either pass `--goal-judge-model`, `--goal-judge-api-key`, and `--goal-judge-base-url` together
- or provide `GOAL_JUDGE_MODEL`, `GOAL_JUDGE_API_KEY`, and `GOAL_JUDGE_BASE_URL` in `.env`

Evaluation outputs are written by default to:

- `<run-dir>/evaluation/`

Important evaluation artifacts include:

- `summary.json`
- `sample_scores.jsonl`
- `goal_judge_runs.jsonl`
- `paper_breakdown.csv`
- `prefix_length_breakdown.csv`
- `segmentation_mode_breakdown.csv`
- `review_queue.jsonl`

## Notes

- If you only want to inspect benchmark inputs and gold labels, start with `data/benchmark_model_records.jsonl` and `data/benchmark_samples.jsonl`.
- If you only want to see the exact prompts produced by the runner, use `--dry-run` first.
- The released package is intended for benchmark use, not for regenerating benchmark data from scratch.
