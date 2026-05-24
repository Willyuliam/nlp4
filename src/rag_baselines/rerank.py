"""Lightweight local reranker for the midterm prototype."""

from __future__ import annotations

import math
import re
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


def score_context(question: str, context: dict[str, Any]) -> float:
    query_tokens = tokenize(question)
    text = f"{context.get('title', '')} {context.get('text', '')}"
    doc_tokens = tokenize(text)
    if not query_tokens or not doc_tokens:
        return 0.0

    query_set = set(query_tokens)
    doc_set = set(doc_tokens)
    overlap = query_set & doc_set
    coverage = len(overlap) / max(len(query_set), 1)
    density = sum(1 for token in doc_tokens if token in query_set) / max(len(doc_tokens), 1)
    length_penalty = 1.0 / math.sqrt(max(len(doc_tokens), 1))
    return coverage + density + length_penalty


def rerank_contexts(question: str, contexts: list[dict[str, Any]], top_k: int, top_n: int) -> list[dict[str, Any]]:
    candidates = contexts[: max(top_k, 0)]
    scored = []
    for index, context in enumerate(candidates):
        scored.append((score_context(question, context), index, context))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [context for _, _, context in scored[: max(top_n, 0)]]
