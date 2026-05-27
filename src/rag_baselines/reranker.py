"""Neural reranking with bge-reranker-v2-m3 and a lightweight fallback."""

from __future__ import annotations

import os
from typing import Any

from src.rag_baselines.rerank import score_context


DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

_RERANKER: Any | None = None
_RERANKER_ERROR: str | None = None


def rerank_retrieved_contexts(
    question: str,
    contexts: list[dict[str, Any]],
    top_n: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    limit = max(top_n, 0)
    if limit == 0 or not contexts:
        return [], {"backend": "none", "reason": "empty_contexts_or_top_n"}

    if os.getenv("RAG_DISABLE_NEURAL_RERANKER") == "1":
        return _lexical_rerank(question, contexts, limit, reason="disabled_by_env")

    reranker, error = _get_reranker()
    if reranker is None:
        return _lexical_rerank(question, contexts, limit, reason=error or "reranker_unavailable")

    try:
        pairs = [[question, _context_text(context)] for context in contexts]
        scores = reranker.compute_score(pairs, normalize=True)
        if not isinstance(scores, list):
            scores = [scores]

        scored = []
        for index, (score, context) in enumerate(zip(scores, contexts)):
            scored.append((float(score), index, context))
        scored.sort(key=lambda item: (-item[0], item[1]))

        selected: list[dict[str, Any]] = []
        score_map: dict[str, float] = {}
        for score, _, context in scored[: min(limit, len(scored))]:
            copied = dict(context)
            copied["_rerank_score"] = float(score)
            selected.append(copied)
            score_map[str(copied.get("doc_id"))] = float(score)
        return selected, {
            "backend": "bge-reranker-v2-m3",
            "reranker_model": os.getenv("RAG_RERANKER_MODEL", DEFAULT_RERANKER_MODEL),
            "top_n": limit,
            "scores": score_map,
        }
    except Exception as exc:
        return _lexical_rerank(question, contexts, limit, reason=f"neural_rerank_failed: {exc}")


def _get_reranker() -> tuple[Any | None, str | None]:
    global _RERANKER, _RERANKER_ERROR
    if _RERANKER is not None:
        return _RERANKER, None
    if _RERANKER_ERROR is not None:
        return None, _RERANKER_ERROR

    try:
        from FlagEmbedding import FlagReranker

        model_name = os.getenv("RAG_RERANKER_MODEL", DEFAULT_RERANKER_MODEL)
        _RERANKER = FlagReranker(model_name, use_fp16=True)
        return _RERANKER, None
    except Exception as exc:
        _RERANKER_ERROR = f"reranker_unavailable: {exc}"
        return None, _RERANKER_ERROR


def _lexical_rerank(
    question: str,
    contexts: list[dict[str, Any]],
    top_n: int,
    reason: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored = []
    for index, context in enumerate(contexts):
        scored.append((score_context(question, context), index, context))
    scored.sort(key=lambda item: (-item[0], item[1]))

    selected: list[dict[str, Any]] = []
    score_map: dict[str, float] = {}
    for score, _, context in scored[: min(top_n, len(scored))]:
        copied = dict(context)
        copied["_rerank_score"] = float(score)
        selected.append(copied)
        score_map[str(copied.get("doc_id"))] = float(score)
    return selected, {
        "backend": "lexical_fallback",
        "reason": reason,
        "top_n": top_n,
        "scores": score_map,
    }


def _context_text(context: dict[str, Any]) -> str:
    title = str(context.get("title") or "").strip()
    text = str(context.get("text") or "").strip()
    return f"{title}\n{text}".strip()
