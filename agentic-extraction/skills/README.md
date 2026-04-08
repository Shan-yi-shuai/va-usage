# Agentic Extraction Skills

This directory is the main entry point for the released agentic extraction method.

These skills are primarily intended for code agents such as Codex and Claude Code. Humans can read them as documentation, but their main role is to be loaded, adapted, or followed by agentic coding assistants. For the concrete usage flow, start with `skill-guides/`.

Recommended reading order:

1. Start with `skill-guides/` for a high-level explanation of the three extraction pipelines: system spec, intended workflow, and case study.
2. Then browse `system-spec-skills/`, `intended-workflow-skills/`, and `case-study-skills/` to see the concrete extraction, review, and revision skills.
3. Use `knowledge/` as the shared memory layer for recurring failure patterns, experience candidates, and promotion history.
4. Use `../schemas/` when you need the target output schemas referenced by the skills.

Directory summary:

- `skill-guides/`: human-readable guides for understanding the skill structure and typical usage flow
- `system-spec-skills/`: skills for extracting, reviewing, and revising `SystemSpec`
- `intended-workflow-skills/`: skills for extracting, reviewing, and revising `PaperWorkflowSpec`
- `case-study-skills/`: skills for extracting, reviewing, and revising `PaperUsageSpec`
- `knowledge/`: shared reusable guidance accumulated across papers
