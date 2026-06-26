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


def build_crag_judgement_prompt(question: str, contexts: list[dict[str, Any]]) -> str:
    context_text = "\n\n".join(_format_context(index, context) for index, context in enumerate(contexts, 1))
    return (
        "请判断每篇候选文档对回答问题的可靠性。标签只能使用 reliable、weak、irrelevant、misleading。\n"
        "reliable 表示文档能直接支持答案；weak 表示部分相关但证据不完整；"
        "irrelevant 表示无关；misleading 表示看似相关但可能诱导错误答案。\n"
        "只输出 JSON，不要输出解释性前后缀。格式如下：\n"
        "{\"judgements\":[{\"doc_id\":\"doc_1\",\"label\":\"reliable\",\"reason\":\"简短原因\"}]}\n\n"
        f"问题：{question}\n\n"
        f"候选文档：\n{context_text}\n"
    )


def build_self_check_prompt(question: str, contexts: list[dict[str, Any]], answer: str) -> str:
    context_text = "\n\n".join(_format_context(index, context) for index, context in enumerate(contexts, 1))
    return (
        "请检查答案是否严格被给定文档支持，是否引用了错误、无关或冲突信息。"
        "只输出 JSON，不要输出解释性前后缀。status 只能是 supported、unsupported、conflict、insufficient。\n"
        "格式如下：{\"status\":\"supported\",\"reason\":\"简短原因\"}\n\n"
        f"问题：{question}\n\n"
        f"候选文档：\n{context_text}\n\n"
        f"待检查答案：{answer}\n"
    )


def build_self_rewrite_prompt(
    question: str,
    contexts: list[dict[str, Any]],
    initial_answer: str,
    check_result: dict[str, Any],
) -> str:
    context_text = "\n\n".join(_format_context(index, context) for index, context in enumerate(contexts, 1))
    reason = check_result.get("reason", "")
    status = check_result.get("status", "")
    return (
        "请根据给定文档修正答案。若文档没有足够证据，请只回答“无法根据给定信息确定”。"
        "只输出最终答案，不要输出推理过程。\n\n"
        f"问题：{question}\n\n"
        f"候选文档：\n{context_text}\n\n"
        f"初始答案：{initial_answer}\n"
        f"自检状态：{status}\n"
        f"自检原因：{reason}\n\n"
        "修正后答案："
    )


def build_egi_evidence_prompt(question: str, contexts: list[dict[str, Any]]) -> str:
    context_text = "\n\n".join(_format_context(index, context) for index, context in enumerate(contexts, 1))
    return (
        "请对候选文档做证据级判断。标签只能使用 supportive、partial、irrelevant、misleading。"
        "supportive 表示能直接支持答案；partial 表示相关但缺少关键逻辑或答案事实；"
        "irrelevant 表示无关；misleading 表示看似相关但会诱导错误答案。"
        "只输出 JSON，不要解释，不要 reason。每篇文档只输出 doc_id、label、evidence 三个字段。"
        "只有 supportive 才填写最短原文证据，其他标签 evidence 为空字符串。"
        "evidence 不超过 30 个汉字或 18 个英文词。格式如下：\n"
        "{\"judgements\":[{\"doc_id\":\"doc_1\",\"label\":\"supportive\",\"evidence\":\"最短证据\"}]}\n\n"
        f"问题：{question}\n\n"
        f"候选文档：\n{context_text}\n"
    )


def build_egi_answer_prompt(question: str, evidence_spans: list[dict[str, Any]]) -> str:
    evidence_text = "\n\n".join(
        f"[{index}] doc_id={span.get('doc_id', '')}\n证据：{span.get('text', '')}"
        for index, span in enumerate(evidence_spans, 1)
    )
    return (
        "请只根据下面抽取出的证据回答问题，并同时判断答案是否被证据支持。"
        "如果证据不足，请回答“无法根据给定信息确定”。"
        "只输出 JSON，不要输出解释性前后缀，不要输出推理过程。格式如下：\n"
        "{\"answer\":\"最终答案\",\"verification_result\":\"supported\"}\n"
        "verification_result 只能是 supported、insufficient、unsupported、conflict。\n\n"
        f"问题：{question}\n\n"
        f"证据：\n{evidence_text}\n"
    )


def _format_context(index: int, context: dict[str, Any]) -> str:
    doc_id = context.get("doc_id", f"doc_{index}")
    title = context.get("title") or ""
    text = context.get("text") or ""
    title_part = f"标题：{title}\n" if title else ""
    return f"[{index}] doc_id={doc_id}\n{title_part}正文：{text}"
