# Preprocessing

This directory contains the preprocessing scripts that generate the artifacts stored under `../data/`.

These scripts cover the released preprocessing pipeline:

- `extract_passages.py`: extract paragraph-level passages from PDFs
- `extract_figures.py`: extract figure crops and figure metadata
- `annotate_figures.py`: assign figure roles and build `figure-manifest.json`
- `split_interface_views.py`: crop top-level interface views from the selected interface figure
- `build_preprocessing_summary.py`: build the entry summaries in `data/preprocess-summaries/`

In this release, the scripts are documented with relative paths such as `../data/...`, while the implementations resolve those defaults against the local `agentic-extraction/` package directory.

For the multimodal scripts, model configuration is read from environment variables such as `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_BASE_URL` instead of hard-coded vendor defaults.

Configuration rule:

- either pass `--vision-model`, `--api-key`, and `--base-url` together on the command line
- or provide `OPENAI_MODEL`, `OPENAI_API_KEY`, and `OPENAI_BASE_URL` in `../.env`

The abstract-extraction helper logic is embedded directly in `extract_passages.py`.
