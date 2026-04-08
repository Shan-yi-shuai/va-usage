# Benchmark Data

This directory contains the minimal released data needed to run and evaluate the `Next Analytic Move` benchmark.

Recommended reading order:

1. `benchmark_model_records.jsonl`: the main benchmark input consumed by `run_context_only_baseline.py`
2. `benchmark_samples.jsonl`: sample-level metadata and gold labels consumed by `evaluate_run.py`
3. `episode-composites/`: the prefix and target episode images referenced by the released benchmark records
4. `benchmark_case_manifest.json`: compact case-level reference metadata retained for inspection and lightweight internal helpers

Notes:

- The released benchmark package depends only on the files inside this directory.
- The released package does not include benchmark construction code.
