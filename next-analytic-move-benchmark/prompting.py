from __future__ import annotations

import json
from copy import deepcopy
from typing import Any


def _prepare_model_input_payload(model_input: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(model_input)
    image_entries = payload.get("visual_context", {}).get("prefix_episode_images", []) or []
    normalized_images: list[dict[str, Any]] = []
    for index, entry in enumerate(image_entries, start=1):
        normalized_images.append(
            {
                "benchmark_episode_index": entry.get("benchmark_episode_index"),
                "episode_title": entry.get("episode_title"),
                "image_ref": f"attached_image_{index}",
            }
        )
    if "visual_context" in payload:
        payload["visual_context"]["prefix_episode_images"] = normalized_images
    return payload


def _build_output_contract() -> dict[str, Any]:
    return {
        "predicted_next_goal": "string",
        "predicted_views": ["canonical_subview_or_view_id"],
        "predicted_capabilities": ["canonical_capability_id"],
        "predicted_workflow_stage": {
            "workflow_id": "canonical_workflow_id",
            "stage_id": "canonical_stage_id",
        },
        "rationale": "brief explanation",
        "confidence": 0.0,
        "retrieved_evidence": [
            {
                "paper_name": "source paper name",
                "source_type": "workflow_transition or episode_transition",
                "source_id": "retrieval card id",
                "reason": "why this evidence was helpful",
            }
        ],
    }


def build_context_only_prompt(record: dict[str, Any]) -> str:
    model_input = _prepare_model_input_payload(record["model_input"])
    output_contract = _build_output_contract()
    output_contract["retrieved_evidence"] = []

    return (
        "You are running the context-only baseline for the Next Analytic Move benchmark.\n\n"
        "Your task is to predict the next meaningful analytic move after the provided prefix episodes.\n"
        "Use only the structured context and attached prefix episode images in this request.\n"
        "Do not rely on external retrieval, external papers, or hidden future episodes.\n\n"
        "Rules:\n"
        "1. Return exactly one JSON object and no extra prose.\n"
        "2. Use only canonical ids that appear in the provided context.\n"
        "3. `predicted_views` should use canonical subview ids when available, otherwise view ids.\n"
        "4. `predicted_capabilities` should use canonical capability ids.\n"
        "5. `predicted_workflow_stage` is optional and may be null.\n"
        "6. For this context-only baseline, set `retrieved_evidence` to an empty list.\n"
        "7. Base your prediction on the current case state, not on generic best practices.\n\n"
        "Output JSON contract:\n"
        f"{json.dumps(output_contract, ensure_ascii=False, indent=2)}\n\n"
        "Benchmark input:\n"
        f"{json.dumps(model_input, ensure_ascii=False, indent=2)}\n"
    )


def _prepare_retrieval_payload(retrieval_result: dict[str, Any]) -> dict[str, Any]:
    query_state = retrieval_result.get("query_state", {}) or {}
    retrieved_patterns = retrieval_result.get("retrieved_patterns", []) or []

    def _normalize_stage_hypotheses(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in items:
            normalized.append(
                {
                    "workflow_id": item.get("workflow_id"),
                    "workflow_title": item.get("workflow_title"),
                    "stage_id": item.get("stage_id"),
                    "stage_title": item.get("stage_title"),
                    "stage_index": item.get("stage_index"),
                    "stage_goal": item.get("stage_goal"),
                    "score": item.get("score"),
                    "reason": item.get("reason"),
                }
            )
        return normalized

    normalized_patterns: list[dict[str, Any]] = []
    for item in retrieved_patterns:
        evidence_payload = item.get("evidence_payload", {}) or {}
        abstract_next_move = item.get("abstract_next_move", {}) or {}
        normalized_patterns.append(
            {
                "rank": item.get("rank"),
                "card_id": item.get("card_id"),
                "paper_name": item.get("paper_name"),
                "source_type": item.get("source_type"),
                "score": item.get("score"),
                "reason": item.get("reason"),
                "abstract_next_move": {
                    "goal_summary": abstract_next_move.get("goal_summary"),
                    "stage_title": abstract_next_move.get("stage_title"),
                    "stage_goal": abstract_next_move.get("stage_goal"),
                    "intent_labels": abstract_next_move.get("intent_labels", []),
                    "operation_labels": abstract_next_move.get("operation_labels", []),
                    "strategy_labels": abstract_next_move.get("strategy_labels", []),
                    "view_hints": abstract_next_move.get("view_hints", []),
                    "capability_hints": abstract_next_move.get("capability_hints", []),
                },
                "source_summary": evidence_payload,
            }
        )

    return {
        "query_state": {
            "scenario_text": query_state.get("scenario_text"),
            "prefix_episode_count": query_state.get("prefix_episode_count"),
            "prefix_local_goals": query_state.get("prefix_local_goals", []),
            "prefix_view_ids": query_state.get("prefix_view_ids", []),
            "prefix_capability_ids": query_state.get("prefix_capability_ids", []),
            "last_episode_title": query_state.get("last_episode_title"),
            "last_episode_goal": query_state.get("last_episode_goal"),
            "current_stage_hypotheses": _normalize_stage_hypotheses(
                query_state.get("current_stage_hypotheses", [])
            ),
            "candidate_next_stage_hypotheses": _normalize_stage_hypotheses(
                query_state.get("candidate_next_stage_hypotheses", [])
            ),
        },
        "retrieved_patterns": normalized_patterns,
    }


def build_rag_v1_prompt(record: dict[str, Any], retrieval_result: dict[str, Any]) -> str:
    model_input = _prepare_model_input_payload(record["model_input"])
    output_contract = _build_output_contract()
    retrieval_payload = _prepare_retrieval_payload(retrieval_result)

    return (
        "You are running the retrieval-augmented baseline (RAG v1) for the Next Analytic Move benchmark.\n\n"
        "Your task is to predict the next meaningful analytic move after the provided prefix episodes.\n"
        "Use the benchmark input, the attached prefix episode images, and the cross-paper retrieval context.\n\n"
        "How to use retrieval:\n"
        "- Treat retrieval as analogical evidence about likely next-step patterns.\n"
        "- Use it to infer the probable next goal, stage progression, and companion views/capabilities.\n"
        "- Then ground that pattern back into the current paper's canonical ids.\n"
        "- Never copy foreign-paper view ids or capability ids into `predicted_views` or `predicted_capabilities`.\n\n"
        "Rules:\n"
        "1. Return exactly one JSON object and no extra prose.\n"
        "2. Use only canonical ids that appear in the provided benchmark input.\n"
        "3. `predicted_views` should use canonical subview ids when available, otherwise view ids.\n"
        "4. `predicted_capabilities` should use canonical capability ids.\n"
        "5. `predicted_workflow_stage` is optional and may be null.\n"
        "6. `retrieved_evidence` may cite only evidence items that appear in the provided retrieval context.\n"
        "7. If you use retrieval evidence, copy the exact `paper_name`, `source_type`, and `card_id` as `source_id`.\n"
        "8. Base the final prediction on the current case state, not on generic best practices alone.\n\n"
        "Output JSON contract:\n"
        f"{json.dumps(output_contract, ensure_ascii=False, indent=2)}\n\n"
        "Benchmark input:\n"
        f"{json.dumps(model_input, ensure_ascii=False, indent=2)}\n\n"
        "Retrieval context:\n"
        f"{json.dumps(retrieval_payload, ensure_ascii=False, indent=2)}\n"
    )
