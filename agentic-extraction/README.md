# Agentic Extraction

This directory contains the released materials for the agentic extraction method used in the paper.

## Directory Overview

- `preprocessing/`: scripts for generating the preprocessing artifacts
- `data/`: released preprocessing artifacts used as inputs to extraction
- `skills/`: released extraction, review, and revision skills together with shared knowledge, intended for code agents such as Codex and Claude Code
- `schemas/`: target schemas for system specs, intended workflows, and case studies
- `.env.example`: example environment configuration for multimodal preprocessing scripts

## Recommended Reading Order

1. Start with `preprocessing/` to see how paper PDFs are converted into passages, figures, view crops, and preprocess summaries.
2. Then browse `data/` to inspect the released preprocessing artifacts, including the four-paper `knowledge-base/` subset used by the released skills.
3. Next read `skills/README.md` to understand how the extraction pipeline is organized.
4. Use `schemas/` when you want to inspect the target output formats referenced by the skills.

## Configuration

For scripts that call a model, there are only two supported modes:

- pass `model`, `api key`, and `base url` explicitly on the command line
- or copy `.env.example` to `.env` and configure everything there

Do not mix command-line model arguments with partial `.env` configuration.
