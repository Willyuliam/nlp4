"""Prompt builders for baseline methods."""

from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = (
    "你是一个严谨的问答系统。请优先给出简洁、直接的中文答案。"
    "如果上下文无法支持答案，请回答“无法根据给定信息确定”。"
)


def build_zero_shot_prompt(question: str) -> str:
    return (
        "请回答下面的问题。只输出答案，不要输出推理过程。\n\n"
        f"问题：{question}\n"
    )


def build_rag_prompt(question: str, contexts: list[dict[str, Any]]) -> str:
    context_text = "\n\n".join(_format_context(index, context) for index, context in enumerate(contexts, 1))
    return (
        "请严格根据给定文档回答问题。若文档没有提供足够证据，请回答“无法根据给定信息确定”。\n\n"
        f"问题：{question}\n\n"
        f"候选文档：\n{context_text}\n\n"
        "答案："
    )


def _format_context(index: int, context: dict[str, Any]) -> str:
    doc_id = context.get("doc_id", f"doc_{index}")
    title = context.get("title") or ""
    text = context.get("text") or ""
    label = context.get("label") or "unknown"
    title_part = f"标题：{title}\n" if title else ""
    return f"[{index}] doc_id={doc_id}, label={label}\n{title_part}正文：{text}"
