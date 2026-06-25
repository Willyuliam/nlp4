"""EGI-RAG pipeline: document scoring, evidence extraction, verification, iteration."""

from __future__ import annotations

from typing import Any

from src.llm import MissingAPIKeyError, QwenClient
from src.rag_baselines.baselines import normalize_contexts
from src.rag_baselines.rerank import rerank_contexts
from src.egi_rag.json_utils import extract_json_payload
from src.egi_rag.prompts import (
    DOC_LABELS,
    SYSTEM_PROMPT,
    VERIFICATION_RESULTS,
    build_answer_generator_prompt,
    build_corrector_prompt,
    build_document_scorer_prompt,
    build_evidence_extractor_prompt,
    build_verifier_prompt,
)

ABLATION_VARIANTS = {
    "full",
    "wo_doc_scorer",
    "wo_evidence_extraction",
    "wo_verifier",
    "wo_iteration",
}

POSITIVE_LABELS = {"directly_supportive", "partially_relevant"}
NEGATIVE_LABELS = {"contradictory", "misleading", "irrelevant", "insufficient"}
DEFAULT_REFUSAL = "无法根据给定信息确定"


def run_egi_sample(
    sample: dict[str, Any],
    client: QwenClient,
    dry_run: bool = False,
    top_k: int = 8,
    top_n: int = 5,
    max_iterations: int = 2,
    variant: str = "full",
) -> dict[str, Any]:
    if variant not in ABLATION_VARIANTS:
        raise ValueError(f"Unsupported variant: {variant}")

    question = str(sample.get("question", "")).strip()
    contexts = normalize_contexts(sample)
    candidate_contexts = rerank_contexts(question, contexts, top_k=top_k, top_n=top_n)

    record: dict[str, Any] = {
        "id": sample.get("id"),
        "method": "EGI-RAG" if variant == "full" else f"EGI-RAG-{variant}",
        "variant": variant,
        "answer": "",
        "selected_doc_ids": [],
        "evidence_spans": [],
        "doc_scores": [],
        "iteration_count": 0,
        "verification_result": None,
        "iteration_log": [],
        "prompt_version": "egi_midterm_v1",
        "raw_response": None,
        "error": None,
    }

    if dry_run:
        record["answer"] = "[DRY_RUN] 未调用模型"
        record["prompts"] = {
            "document_scorer": build_document_scorer_prompt(question, candidate_contexts),
            "evidence_extractor": build_evidence_extractor_prompt(question, candidate_contexts[:3]),
            "answer_generator": build_answer_generator_prompt(question, []),
            "verifier": build_verifier_prompt(question, "", []),
        }
        record["selected_doc_ids"] = [ctx.get("doc_id") for ctx in candidate_contexts[:3]]
        return record

    try:
        result = _run_pipeline(
            question=question,
            candidate_contexts=candidate_contexts,
            client=client,
            max_iterations=max_iterations,
            variant=variant,
        )
        record.update(result)
    except MissingAPIKeyError as exc:
        record["error"] = str(exc)
    except Exception as exc:
        record["error"] = str(exc)

    return record


def _run_pipeline(
    question: str,
    candidate_contexts: list[dict[str, Any]],
    client: QwenClient,
    max_iterations: int,
    variant: str,
) -> dict[str, Any]:
    iteration_log: list[dict[str, Any]] = []
    active_contexts = list(candidate_contexts)
    doc_scores = _default_doc_scores(active_contexts) if variant == "wo_doc_scorer" else _score_documents(
        question, active_contexts, client
    )
    selected_contexts = _select_contexts_from_scores(active_contexts, doc_scores)

    answer = ""
    evidence_spans: list[dict[str, Any]] = []
    verification_result = "insufficient_evidence"
    verification: dict[str, Any] = {"verification_result": verification_result, "reason": ""}

    effective_max_iterations = 1 if variant == "wo_iteration" else max(1, max_iterations)

    for iteration in range(1, effective_max_iterations + 1):
        if variant == "wo_evidence_extraction":
            evidence_spans = _fallback_evidence_from_contexts(selected_contexts)
        else:
            evidence_spans = _extract_evidence(question, selected_contexts, client)

        answer = _generate_answer(question, evidence_spans, selected_contexts, client, variant)
        if variant == "wo_verifier":
            verification_result = "supported" if evidence_spans else "insufficient_evidence"
            verification = {"verification_result": verification_result, "reason": "verifier disabled"}
        else:
            verification = _verify_answer(question, answer, evidence_spans, client)
            verification_result = str(verification.get("verification_result", "unsupported"))

        iteration_log.append(
            {
                "iteration": iteration,
                "selected_doc_ids": [ctx.get("doc_id") for ctx in selected_contexts],
                "evidence_count": len(evidence_spans),
                "answer": answer,
                "verification_result": verification_result,
                "verification_reason": verification.get("reason", ""),
            }
        )

        if verification_result == "supported":
            break
        if iteration >= effective_max_iterations:
            break

        correction = _plan_correction(question, answer, verification, doc_scores, client)
        action = str(correction.get("action", "refuse"))
        if action == "refuse":
            answer = DEFAULT_REFUSAL
            verification_result = "insufficient_evidence"
            break
        if action == "rewrite_answer":
            answer = DEFAULT_REFUSAL if not evidence_spans else answer
            continue

        preferred_ids = correction.get("preferred_doc_ids") or []
        if preferred_ids:
            selected_contexts = _contexts_by_ids(active_contexts, preferred_ids)
        else:
            selected_contexts = _select_alternate_contexts(active_contexts, doc_scores, selected_contexts)

    if verification_result != "supported" and not answer.strip():
        answer = DEFAULT_REFUSAL

    return {
        "answer": answer.strip(),
        "selected_doc_ids": [ctx.get("doc_id") for ctx in selected_contexts],
        "evidence_spans": evidence_spans,
        "doc_scores": doc_scores,
        "iteration_count": len(iteration_log),
        "verification_result": verification_result,
        "iteration_log": iteration_log,
        "raw_response": answer,
    }


def _score_documents(
    question: str,
    contexts: list[dict[str, Any]],
    client: QwenClient,
) -> list[dict[str, Any]]:
    if not contexts:
        return []

    prompt = build_document_scorer_prompt(question, contexts)
    response = client.generate(prompt, system_prompt=SYSTEM_PROMPT)
    payload = extract_json_payload(response)
    if not isinstance(payload, list):
        raise ValueError("document scorer must return a JSON array")

    score_map = {str(item.get("doc_id")): _normalize_doc_score(item) for item in payload if isinstance(item, dict)}
    results: list[dict[str, Any]] = []
    for context in contexts:
        doc_id = str(context.get("doc_id"))
        if doc_id in score_map:
            results.append(score_map[doc_id])
        else:
            results.append(
                {
                    "doc_id": doc_id,
                    "label": "partially_relevant",
                    "score": 0.3,
                    "reason": "模型未返回该文档评分，使用默认值",
                }
            )
    return results


def _default_doc_scores(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "doc_id": context.get("doc_id"),
            "label": "partially_relevant",
            "score": 0.5,
            "reason": "ablation: doc scorer disabled",
        }
        for context in contexts
    ]


def _normalize_doc_score(item: dict[str, Any]) -> dict[str, Any]:
    label = str(item.get("label", "partially_relevant"))
    if label not in DOC_LABELS:
        label = "partially_relevant"
    try:
        score = float(item.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    score = max(0.0, min(score, 1.0))
    return {
        "doc_id": item.get("doc_id"),
        "label": label,
        "score": score,
        "reason": str(item.get("reason", "")).strip(),
    }


def _select_contexts_from_scores(
    contexts: list[dict[str, Any]],
    doc_scores: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not contexts:
        return []

    score_by_id = {str(item.get("doc_id")): item for item in doc_scores}
    ranked: list[tuple[float, int, dict[str, Any]]] = []
    for index, context in enumerate(contexts):
        doc_id = str(context.get("doc_id"))
        score_item = score_by_id.get(doc_id, {})
        label = str(score_item.get("label", "partially_relevant"))
        score = float(score_item.get("score", 0.0))
        if label in NEGATIVE_LABELS and score < 0.45:
            continue
        priority = score + (0.2 if label in POSITIVE_LABELS else 0.0)
        ranked.append((priority, index, context))

    if not ranked:
        return contexts[:3]

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [context for _, _, context in ranked[:5]]


def _extract_evidence(
    question: str,
    contexts: list[dict[str, Any]],
    client: QwenClient,
) -> list[dict[str, Any]]:
    if not contexts:
        return []

    prompt = build_evidence_extractor_prompt(question, contexts)
    response = client.generate(prompt, system_prompt=SYSTEM_PROMPT)
    payload = extract_json_payload(response)
    if not isinstance(payload, list):
        return []

    evidence: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        evidence.append({"doc_id": item.get("doc_id"), "text": text})
    return evidence


def _fallback_evidence_from_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for context in contexts[:3]:
        text = str(context.get("text", "")).strip()
        if not text:
            continue
        snippet = text[:240].strip()
        evidence.append({"doc_id": context.get("doc_id"), "text": snippet})
    return evidence


def _generate_answer(
    question: str,
    evidence_spans: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    client: QwenClient,
    variant: str,
) -> str:
    if not evidence_spans and not contexts:
        return DEFAULT_REFUSAL

    if variant == "wo_evidence_extraction":
        prompt = build_answer_generator_prompt(question, _fallback_evidence_from_contexts(contexts))
    else:
        prompt = build_answer_generator_prompt(question, evidence_spans)
    return client.generate(prompt, system_prompt=SYSTEM_PROMPT).strip()


def _verify_answer(
    question: str,
    answer: str,
    evidence_spans: list[dict[str, Any]],
    client: QwenClient,
) -> dict[str, Any]:
    prompt = build_verifier_prompt(question, answer, evidence_spans)
    response = client.generate(prompt, system_prompt=SYSTEM_PROMPT)
    payload = extract_json_payload(response)
    if not isinstance(payload, dict):
        return {"verification_result": "unsupported", "reason": "invalid verifier output", "unsupported_claims": []}

    result = str(payload.get("verification_result", "unsupported"))
    if result not in VERIFICATION_RESULTS:
        result = "unsupported"
    payload["verification_result"] = result
    return payload


def _plan_correction(
    question: str,
    answer: str,
    verification: dict[str, Any],
    doc_scores: list[dict[str, Any]],
    client: QwenClient,
) -> dict[str, Any]:
    prompt = build_corrector_prompt(question, answer, verification, doc_scores)
    response = client.generate(prompt, system_prompt=SYSTEM_PROMPT)
    payload = extract_json_payload(response)
    if not isinstance(payload, dict):
        return {"action": "refuse", "reason": "invalid correction output", "preferred_doc_ids": []}
    return payload


def _contexts_by_ids(contexts: list[dict[str, Any]], doc_ids: list[Any]) -> list[dict[str, Any]]:
    id_set = {str(doc_id) for doc_id in doc_ids}
    selected = [context for context in contexts if str(context.get("doc_id")) in id_set]
    return selected or contexts[:3]


def _select_alternate_contexts(
    contexts: list[dict[str, Any]],
    doc_scores: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_ids = {str(item.get("doc_id")) for item in current}
    ranked = sorted(doc_scores, key=lambda item: float(item.get("score", 0.0)), reverse=True)
    alternate_ids = [str(item.get("doc_id")) for item in ranked if str(item.get("doc_id")) not in current_ids]
    if alternate_ids:
        return _contexts_by_ids(contexts, alternate_ids[:3])
    return contexts[:3]
