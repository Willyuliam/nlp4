"""Prompt templates for EGI-RAG modules."""

from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = (
    "你是一个严谨的 RAG 证据推理助手。请严格依据给定文档作答，"
    "不要编造文档中不存在的信息。输出格式必须遵守用户要求。"
)

DOC_LABELS = [
    "directly_supportive",
    "partially_relevant",
    "irrelevant",
    "contradictory",
    "misleading",
    "insufficient",
]

VERIFICATION_RESULTS = ["supported", "unsupported", "conflict", "insufficient_evidence"]


def build_document_scorer_prompt(question: str, contexts: list[dict[str, Any]]) -> str:
    docs_text = "\n\n".join(_format_doc(index, doc) for index, doc in enumerate(contexts, 1))
    labels = ", ".join(DOC_LABELS)
    return (
        "请评估每篇候选文档对回答问题的价值。\n"
        f"可选 label：{labels}\n"
        "score 取值 0 到 1，越高表示越可信、越直接支持答案。\n"
        "只输出 JSON 数组，不要输出其他文字：\n"
        '[{"doc_id":"doc_1","label":"directly_supportive","score":0.92,"reason":"简短理由"}]\n\n'
        f"问题：{question}\n\n"
        f"候选文档：\n{docs_text}"
    )


def build_evidence_extractor_prompt(question: str, contexts: list[dict[str, Any]]) -> str:
    docs_text = "\n\n".join(_format_doc(index, doc) for index, doc in enumerate(contexts, 1))
    return (
        "从候选文档中抽取能直接支持问题答案的证据句。"
        "证据句必须来自原文，尽量保持原句，不要改写。\n"
        "只输出 JSON 数组：\n"
        '[{"doc_id":"doc_1","text":"证据句"}]\n'
        "若没有可用证据，输出空数组 []。\n\n"
        f"问题：{question}\n\n"
        f"候选文档：\n{docs_text}"
    )


def build_answer_generator_prompt(question: str, evidence_spans: list[dict[str, Any]]) -> str:
    if not evidence_spans:
        evidence_text = "（无可用证据）"
    else:
        evidence_text = "\n".join(
            f"- [{item.get('doc_id', 'unknown')}] {item.get('text', '')}" for item in evidence_spans
        )
    return (
        "请仅根据下列证据句回答问题。不要引入证据中没有的信息。\n"
        "若证据不足以确定答案，请回答“无法根据给定信息确定”。\n"
        "只输出最终答案，不要输出推理过程。\n\n"
        f"问题：{question}\n\n"
        f"证据句：\n{evidence_text}\n\n"
        "答案："
    )


def build_verifier_prompt(question: str, answer: str, evidence_spans: list[dict[str, Any]]) -> str:
    evidence_text = "\n".join(
        f"- [{item.get('doc_id', 'unknown')}] {item.get('text', '')}" for item in evidence_spans
    ) or "（无证据）"
    results = ", ".join(VERIFICATION_RESULTS)
    return (
        "请检查答案是否被证据支持。\n"
        f"verification_result 只能是：{results}\n"
        "只输出 JSON 对象：\n"
        '{"verification_result":"supported","reason":"简短理由","unsupported_claims":[]}\n\n'
        f"问题：{question}\n"
        f"答案：{answer}\n\n"
        f"证据句：\n{evidence_text}"
    )


def build_corrector_prompt(
    question: str,
    answer: str,
    verification: dict[str, Any],
    doc_scores: list[dict[str, Any]],
) -> str:
    scores_text = "\n".join(
        f"- {item.get('doc_id')}: label={item.get('label')}, score={item.get('score')}, reason={item.get('reason')}"
        for item in doc_scores
    )
    return (
        "上一轮答案未通过证据校验，请给出修正策略。\n"
        "action 只能是 reselect_docs、rewrite_answer 或 refuse。\n"
        "只输出 JSON 对象：\n"
        '{"action":"reselect_docs","reason":"简短理由","preferred_doc_ids":["doc_1"]}\n\n'
        f"问题：{question}\n"
        f"当前答案：{answer}\n"
        f"校验结果：{verification.get('verification_result')}\n"
        f"校验原因：{verification.get('reason')}\n\n"
        f"文档评分：\n{scores_text}"
    )


def _format_doc(index: int, doc: dict[str, Any]) -> str:
    doc_id = doc.get("doc_id", f"doc_{index}")
    title = doc.get("title") or ""
    text = doc.get("text") or ""
    title_part = f"标题：{title}\n" if title else ""
    return f"[{index}] doc_id={doc_id}\n{title_part}正文：{text}"
