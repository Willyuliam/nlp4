"""Per-sample retrieval with bge-m3 + FAISS and a deterministic fallback."""

from __future__ import annotations

import os
from typing import Any

from src.rag_baselines.rerank import score_context


DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"

_EMBEDDING_MODEL: Any | None = None
_EMBEDDING_ERROR: str | None = None


def retrieve_contexts(
    question: str,
    contexts: list[dict[str, Any]],
    top_k: int = 20,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Retrieve top-k contexts for one sample.

    The formal path uses bge-m3 embeddings and a temporary FAISS index. If the
    local environment does not have the dependencies or model files, it falls
    back to the project's lightweight lexical scorer so small verification runs
    remain executable.
    """
    limit = max(top_k, 0)
    if limit == 0 or not contexts:
        return [], {"backend": "none", "reason": "empty_contexts_or_top_k"}

    if os.getenv("RAG_DISABLE_NEURAL_RETRIEVER") == "1":
        return _lexical_retrieve(question, contexts, limit, reason="disabled_by_env")

    model, model_error = _get_embedding_model()
    if model is None:
        return _lexical_retrieve(question, contexts, limit, reason=model_error or "embedding_unavailable")

    try:
        import faiss  # type: ignore
    except Exception as exc:
        return _lexical_retrieve(question, contexts, limit, reason=f"faiss_unavailable: {exc}")

    try:
        import numpy as np

        texts = [_context_text(context) for context in contexts]
        doc_embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        query_embedding = model.encode(
            [question],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        doc_embeddings = np.asarray(doc_embeddings, dtype="float32")
        query_embedding = np.asarray(query_embedding, dtype="float32")
        index = faiss.IndexFlatIP(doc_embeddings.shape[1])
        index.add(doc_embeddings)
        scores, indices = index.search(query_embedding, min(limit, len(contexts)))

        retrieved: list[dict[str, Any]] = []
        score_map: dict[str, float] = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            context = dict(contexts[int(idx)])
            context["_retrieval_score"] = float(score)
            retrieved.append(context)
            score_map[str(context.get("doc_id"))] = float(score)
        return retrieved, {
            "backend": "bge-m3+faiss",
            "embedding_model": os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            "top_k": limit,
            "scores": score_map,
        }
    except Exception as exc:
        return _lexical_retrieve(question, contexts, limit, reason=f"neural_retrieval_failed: {exc}")


def _get_embedding_model() -> tuple[Any | None, str | None]:
    global _EMBEDDING_MODEL, _EMBEDDING_ERROR
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL, None
    if _EMBEDDING_ERROR is not None:
        return None, _EMBEDDING_ERROR

    try:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        _EMBEDDING_MODEL = SentenceTransformer(model_name)
        return _EMBEDDING_MODEL, None
    except Exception as exc:
        _EMBEDDING_ERROR = f"embedding_unavailable: {exc}"
        return None, _EMBEDDING_ERROR


def _lexical_retrieve(
    question: str,
    contexts: list[dict[str, Any]],
    top_k: int,
    reason: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored = []
    for index, context in enumerate(contexts):
        scored.append((score_context(question, context), index, context))
    scored.sort(key=lambda item: (-item[0], item[1]))

    retrieved: list[dict[str, Any]] = []
    score_map: dict[str, float] = {}
    for score, _, context in scored[: min(top_k, len(scored))]:
        copied = dict(context)
        copied["_retrieval_score"] = float(score)
        retrieved.append(copied)
        score_map[str(copied.get("doc_id"))] = float(score)
    return retrieved, {
        "backend": "lexical_fallback",
        "reason": reason,
        "top_k": top_k,
        "scores": score_map,
    }


def _context_text(context: dict[str, Any]) -> str:
    title = str(context.get("title") or "").strip()
    text = str(context.get("text") or "").strip()
    return f"{title}\n{text}".strip()
