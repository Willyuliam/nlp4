"""Baseline orchestration for Zero-shot, Naive RAG, and Rerank RAG."""

from __future__ import annotations

from typing import Any

from src.llm import MissingAPIKeyError, QwenClient
from src.rag_baselines.prompts import SYSTEM_PROMPT, build_rag_prompt, build_zero_shot_prompt
from src.rag_baselines.rerank import rerank_contexts


SUPPORTED_METHODS = {"zero_shot", "naive_rag", "rerank_rag"}


def run_sample(
    sample: dict[str, Any],
    method: str,
    client: QwenClient,
    dry_run: bool,
    top_k: int,
    top_n: int,
) -> dict[str, Any]:
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"Unsupported method: {method}")

    question = str(sample.get("question", "")).strip()
    contexts = normalize_contexts(sample)
    selected_contexts = select_contexts(method, question, contexts, top_k=top_k, top_n=top_n)
    prompt = build_prompt(method, question, selected_contexts)

    record = {
        "id": sample.get("id"),
        "method": method,
        "answer": "",
        "selected_doc_ids": [context.get("doc_id") for context in selected_contexts],
        "contexts_used": selected_contexts,
        "prompt_version": "midterm_v1",
        "raw_response": None,
        "error": None,
    }

    if dry_run:
        record["answer"] = "[DRY_RUN] 未调用模型"
        record["prompt"] = prompt
        return record

    try:
        answer = client.generate(prompt, system_prompt=SYSTEM_PROMPT)
    except MissingAPIKeyError as exc:
        record["error"] = str(exc)
        record["answer"] = ""
        return record
    except Exception as exc:  # Keep batch runs alive for later evaluation.
        record["error"] = str(exc)
        record["answer"] = ""
        return record

    record["answer"] = answer.strip()
    record["raw_response"] = answer
    return record


def normalize_contexts(sample: dict[str, Any]) -> list[dict[str, Any]]:
    contexts = sample.get("contexts")
    if isinstance(contexts, list):
        return [_normalize_context(context, index) for index, context in enumerate(contexts, 1)]

    context_text = sample.get("context")
    if isinstance(context_text, str) and context_text.strip():
        return [{"doc_id": "context_1", "title": "", "text": context_text, "label": "unknown"}]

    return []


def _normalize_context(context: Any, index: int) -> dict[str, Any]:
    if isinstance(context, str):
        return {"doc_id": f"doc_{index}", "title": "", "text": context, "label": "unknown"}
    if not isinstance(context, dict):
        return {"doc_id": f"doc_{index}", "title": "", "text": str(context), "label": "unknown"}

    return {
        "doc_id": context.get("doc_id", f"doc_{index}"),
        "title": context.get("title", ""),
        "text": context.get("text", ""),
        "label": context.get("label", "unknown"),
    }


def select_contexts(
    method: str,
    question: str,
    contexts: list[dict[str, Any]],
    top_k: int,
    top_n: int,
) -> list[dict[str, Any]]:
    if method == "zero_shot":
        return []
    if method == "naive_rag":
        return contexts[: max(top_k, 0)]
    if method == "rerank_rag":
        return rerank_contexts(question, contexts, top_k=top_k, top_n=top_n)
    raise ValueError(f"Unsupported method: {method}")


def build_prompt(method: str, question: str, contexts: list[dict[str, Any]]) -> str:
    if method == "zero_shot":
        return build_zero_shot_prompt(question)
    return build_rag_prompt(question, contexts)
