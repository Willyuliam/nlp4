"""Baseline orchestration for Zero-shot, RAG, CRAG-lite, and Self-RAG-lite."""

from __future__ import annotations

import json
import re
from typing import Any

from src.llm import MissingAPIKeyError, QwenClient
from src.rag_baselines.prompts import (
    SYSTEM_PROMPT,
    build_crag_judgement_prompt,
    build_rag_prompt,
    build_self_check_prompt,
    build_self_rewrite_prompt,
    build_zero_shot_prompt,
)
from src.rag_baselines.reranker import rerank_retrieved_contexts
from src.rag_baselines.retriever import retrieve_contexts


SUPPORTED_METHODS = {"zero_shot", "ordered_rag", "naive_rag", "rerank_rag", "crag_lite", "self_rag_lite"}
PROMPT_VERSION = "formal_v1"
REFUSAL_ANSWER = "无法根据给定信息确定"


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

    if method == "zero_shot":
        return _run_single_generation(sample, method, question, [], [], client, dry_run)
    if method == "ordered_rag":
        selected_contexts = contexts[: max(top_k, 0)]
        return _run_single_generation(
            sample,
            method,
            question,
            selected_contexts,
            selected_contexts,
            client,
            dry_run,
            retrieval_meta={"backend": "input_order", "top_k": max(top_k, 0)},
        )
    if method == "naive_rag":
        selected_contexts, retrieval_meta = retrieve_contexts(question, contexts, top_k=max(top_k, 0))
        return _run_single_generation(
            sample,
            method,
            question,
            selected_contexts,
            selected_contexts,
            client,
            dry_run,
            retrieval_meta=retrieval_meta,
        )
    if method == "rerank_rag":
        retrieved_contexts, retrieval_meta = retrieve_contexts(question, contexts, top_k=max(top_k, 0))
        selected_contexts, rerank_meta = rerank_retrieved_contexts(question, retrieved_contexts, top_n=max(top_n, 0))
        return _run_single_generation(
            sample,
            method,
            question,
            retrieved_contexts,
            selected_contexts,
            client,
            dry_run,
            retrieval_meta=retrieval_meta,
            rerank_meta=rerank_meta,
        )
    if method == "crag_lite":
        return _run_crag_lite(sample, question, contexts, client, dry_run, top_k=top_k, top_n=top_n)
    if method == "self_rag_lite":
        return _run_self_rag_lite(sample, question, contexts, client, dry_run, top_k=top_k, top_n=top_n)

    raise ValueError(f"Unsupported method: {method}")


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


def _run_single_generation(
    sample: dict[str, Any],
    method: str,
    question: str,
    retrieved_contexts: list[dict[str, Any]],
    selected_contexts: list[dict[str, Any]],
    client: QwenClient,
    dry_run: bool,
    retrieval_meta: dict[str, Any] | None = None,
    rerank_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = build_prompt(method, question, selected_contexts)
    record = _base_record(sample, method, retrieved_contexts, selected_contexts)
    if retrieval_meta is not None:
        record["retrieval_meta"] = retrieval_meta
    if rerank_meta is not None:
        record["rerank_meta"] = rerank_meta

    if dry_run:
        record["answer"] = "[DRY_RUN] 未调用模型"
        record["prompt"] = prompt
        return record

    answer = _generate_or_record_error(record, client, prompt)
    if answer is None:
        return record

    record["answer"] = answer.strip()
    record["raw_response"] = answer
    return record


def _run_crag_lite(
    sample: dict[str, Any],
    question: str,
    contexts: list[dict[str, Any]],
    client: QwenClient,
    dry_run: bool,
    top_k: int,
    top_n: int,
) -> dict[str, Any]:
    retrieved_contexts, retrieval_meta = retrieve_contexts(question, contexts, top_k=max(top_k, 0))
    candidate_contexts, rerank_meta = rerank_retrieved_contexts(question, retrieved_contexts, top_n=max(top_n, 0))
    judgement_prompt = build_crag_judgement_prompt(question, candidate_contexts)

    record = _base_record(sample, "crag_lite", retrieved_contexts, candidate_contexts)
    record["retrieval_meta"] = retrieval_meta
    record["rerank_meta"] = rerank_meta

    if dry_run:
        record["answer"] = "[DRY_RUN] 未调用模型"
        record["crag_judgement_prompt"] = judgement_prompt
        record["prompt"] = build_rag_prompt(question, candidate_contexts)
        return record

    judgement_text = _generate_or_record_error(record, client, judgement_prompt)
    if judgement_text is None:
        return record

    judgements, parse_error = _parse_doc_judgements(judgement_text)
    record["doc_judgements"] = judgements
    if parse_error:
        record["doc_judgements_parse_error"] = parse_error

    selected_contexts = _select_crag_contexts(candidate_contexts, judgements)
    record["selected_doc_ids"] = [context.get("doc_id") for context in selected_contexts]
    record["contexts_used"] = selected_contexts

    if not selected_contexts:
        record["answer"] = REFUSAL_ANSWER
        record["raw_response"] = judgement_text
        record["raw_responses"] = {"doc_judgement": judgement_text}
        return record

    answer_prompt = build_rag_prompt(question, selected_contexts)
    answer = _generate_or_record_error(record, client, answer_prompt)
    if answer is None:
        return record

    record["answer"] = answer.strip()
    record["raw_response"] = answer
    record["raw_responses"] = {"doc_judgement": judgement_text, "answer": answer}
    return record


def _run_self_rag_lite(
    sample: dict[str, Any],
    question: str,
    contexts: list[dict[str, Any]],
    client: QwenClient,
    dry_run: bool,
    top_k: int,
    top_n: int,
) -> dict[str, Any]:
    retrieved_contexts, retrieval_meta = retrieve_contexts(question, contexts, top_k=max(top_k, 0))
    selected_contexts, rerank_meta = rerank_retrieved_contexts(question, retrieved_contexts, top_n=max(top_n, 0))
    initial_prompt = build_rag_prompt(question, selected_contexts)
    check_prompt_preview = build_self_check_prompt(question, selected_contexts, "<initial_answer>")

    record = _base_record(sample, "self_rag_lite", retrieved_contexts, selected_contexts)
    record["retrieval_meta"] = retrieval_meta
    record["rerank_meta"] = rerank_meta

    if dry_run:
        record["answer"] = "[DRY_RUN] 未调用模型"
        record["prompt"] = initial_prompt
        record["self_check_prompt_template"] = check_prompt_preview
        return record

    initial_answer = _generate_or_record_error(record, client, initial_prompt)
    if initial_answer is None:
        return record

    first_check_text = _generate_or_record_error(
        record,
        client,
        build_self_check_prompt(question, selected_contexts, initial_answer),
    )
    if first_check_text is None:
        return record

    first_check = _parse_self_check(first_check_text)
    final_answer = initial_answer.strip()
    second_check_text = ""
    second_check: dict[str, Any] | None = None

    if first_check.get("status") != "supported":
        rewrite_prompt = build_self_rewrite_prompt(question, selected_contexts, initial_answer, first_check)
        rewritten = _generate_or_record_error(record, client, rewrite_prompt)
        if rewritten is None:
            return record

        second_check_text = _generate_or_record_error(
            record,
            client,
            build_self_check_prompt(question, selected_contexts, rewritten),
        )
        if second_check_text is None:
            return record
        second_check = _parse_self_check(second_check_text)
        final_answer = rewritten.strip() if second_check.get("status") == "supported" else REFUSAL_ANSWER

    record["initial_answer"] = initial_answer.strip()
    record["self_check_result"] = first_check
    if second_check is not None:
        record["rewrite_check_result"] = second_check
    record["final_answer"] = final_answer
    record["answer"] = final_answer
    record["raw_response"] = final_answer
    record["raw_responses"] = {
        "initial_answer": initial_answer,
        "first_check": first_check_text,
        "second_check": second_check_text,
    }
    return record


def _base_record(
    sample: dict[str, Any],
    method: str,
    retrieved_contexts: list[dict[str, Any]],
    selected_contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": sample.get("id"),
        "method": method,
        "answer": "",
        "retrieved_doc_ids": [context.get("doc_id") for context in retrieved_contexts],
        "selected_doc_ids": [context.get("doc_id") for context in selected_contexts],
        "contexts_used": selected_contexts,
        "prompt_version": PROMPT_VERSION,
        "raw_response": None,
        "error": None,
    }


def _generate_or_record_error(record: dict[str, Any], client: QwenClient, prompt: str) -> str | None:
    try:
        return client.generate(prompt, system_prompt=SYSTEM_PROMPT)
    except MissingAPIKeyError as exc:
        record["error"] = str(exc)
        record["answer"] = ""
    except Exception as exc:  # Keep batch runs alive for later evaluation.
        record["error"] = str(exc)
        record["answer"] = ""
    return None


def _parse_doc_judgements(raw_text: str) -> tuple[list[dict[str, Any]], str | None]:
    data, error = _parse_json(raw_text)
    if not isinstance(data, dict):
        return [], error or "judgement JSON is not an object"
    raw_judgements = data.get("judgements")
    if not isinstance(raw_judgements, list):
        return [], error or "missing judgements list"

    result: list[dict[str, Any]] = []
    allowed = {"reliable", "weak", "irrelevant", "misleading"}
    for item in raw_judgements:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip().lower()
        if label not in allowed:
            label = "weak"
        result.append(
            {
                "doc_id": item.get("doc_id"),
                "label": label,
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return result, error


def _select_crag_contexts(
    contexts: list[dict[str, Any]],
    judgements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    judgement_by_id = {str(item.get("doc_id")): item for item in judgements}
    reliable: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    for context in contexts:
        doc_id = str(context.get("doc_id"))
        label = judgement_by_id.get(doc_id, {}).get("label")
        if label == "reliable":
            reliable.append(context)
        elif label == "weak":
            weak.append(context)

    if reliable:
        return reliable + weak[: max(0, 5 - len(reliable))]
    return weak[:2]


def _parse_self_check(raw_text: str) -> dict[str, Any]:
    data, error = _parse_json(raw_text)
    if not isinstance(data, dict):
        return {"status": "unsupported", "reason": error or "self-check JSON parse failed", "raw": raw_text}

    status = str(data.get("status", "")).strip().lower()
    if status not in {"supported", "unsupported", "conflict", "insufficient"}:
        status = "unsupported"
    return {
        "status": status,
        "reason": str(data.get("reason", "")).strip(),
        "raw": raw_text,
    }


def _parse_json(raw_text: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(raw_text), None
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1)), None
        except json.JSONDecodeError as exc:
            return None, f"JSON parse failed: {exc}"

    start_candidates = [idx for idx in (raw_text.find("{"), raw_text.find("[")) if idx >= 0]
    if not start_candidates:
        return None, "no JSON object or array found"
    start = min(start_candidates)
    end = max(raw_text.rfind("}"), raw_text.rfind("]"))
    if end <= start:
        return None, "no complete JSON object or array found"
    try:
        return json.loads(raw_text[start : end + 1]), None
    except json.JSONDecodeError as exc:
        return None, f"JSON parse failed: {exc}"


def build_prompt(method: str, question: str, contexts: list[dict[str, Any]]) -> str:
    if method == "zero_shot":
        return build_zero_shot_prompt(question)
    return build_rag_prompt(question, contexts)
