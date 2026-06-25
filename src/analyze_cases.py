"""Generate before/after case comparisons between Naive RAG and EGI-RAG."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from src.utils import load_json, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build EGI-RAG case comparison report.")
    parser.add_argument("--input", required=True, help="Original input JSON with gold answers.")
    parser.add_argument("--baseline", required=True, help="Naive RAG output JSON.")
    parser.add_argument("--egi", required=True, help="EGI-RAG output JSON.")
    parser.add_argument("--output", required=True, help="Markdown report path.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of cases.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    samples = {str(item["id"]): item for item in load_json(args.input) if isinstance(item, dict) and "id" in item}
    baseline = {str(item["id"]): item for item in load_json(args.baseline) if isinstance(item, dict) and "id" in item}
    egi = {str(item["id"]): item for item in load_json(args.egi) if isinstance(item, dict) and "id" in item}

    cases = select_cases(samples, baseline, egi, limit=max(args.limit, 1))
    markdown = render_markdown(cases)
    save_text(args.output, markdown)
    print(f"cases={len(cases)}, output={args.output}")
    return 0


def select_cases(
    samples: dict[str, dict[str, Any]],
    baseline: dict[str, dict[str, Any]],
    egi: dict[str, dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for sample_id, sample in samples.items():
        base_item = baseline.get(sample_id)
        egi_item = egi.get(sample_id)
        if not base_item or not egi_item:
            continue

        gold = normalize_text(sample.get("gold_answers", [""])[0] if sample.get("gold_answers") else "")
        base_answer = normalize_text(base_item.get("answer", ""))
        egi_answer = normalize_text(egi_item.get("answer", ""))
        base_correct = answers_match(base_answer, gold)
        egi_correct = answers_match(egi_answer, gold)

        priority = 0
        if egi_correct and not base_correct:
            priority += 100
        if base_answer and egi_answer and base_answer != egi_answer:
            priority += 20
        if egi_item.get("verification_result") == "supported":
            priority += 10
        if egi_item.get("iteration_count", 0) > 1:
            priority += 5

        case = build_case(sample, base_item, egi_item, base_correct, egi_correct)
        scored.append((priority, sample_id, case))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [case for _, _, case in scored[:limit]]


def build_case(
    sample: dict[str, Any],
    base_item: dict[str, Any],
    egi_item: dict[str, Any],
    base_correct: bool,
    egi_correct: bool,
) -> dict[str, Any]:
    correct_docs = [ctx for ctx in sample.get("contexts", []) if ctx.get("label") == "correct"]
    noise_docs = [ctx for ctx in sample.get("contexts", []) if ctx.get("label") not in {"correct", "unknown", None}]
    return {
        "id": sample.get("id"),
        "question": sample.get("question"),
        "gold_answers": sample.get("gold_answers", []),
        "correct_docs": correct_docs[:2],
        "noise_docs": noise_docs[:2],
        "baseline_answer": base_item.get("answer", ""),
        "baseline_selected_doc_ids": base_item.get("selected_doc_ids", []),
        "baseline_correct": base_correct,
        "egi_answer": egi_item.get("answer", ""),
        "egi_selected_doc_ids": egi_item.get("selected_doc_ids", []),
        "egi_evidence_spans": egi_item.get("evidence_spans", []),
        "egi_doc_scores": egi_item.get("doc_scores", []),
        "egi_iteration_count": egi_item.get("iteration_count", 0),
        "egi_verification_result": egi_item.get("verification_result"),
        "egi_iteration_log": egi_item.get("iteration_log", []),
        "egi_correct": egi_correct,
    }


def render_markdown(cases: list[dict[str, Any]]) -> str:
    lines = [
        "# EGI-RAG 典型案例对比",
        "",
        "自动生成：对比 Naive RAG 与 EGI-RAG 在噪声文档场景下的答案差异。",
        "",
    ]
    if not cases:
        lines.append("未找到可对比案例。")
        return "\n".join(lines) + "\n"

    for index, case in enumerate(cases, 1):
        lines.extend(
            [
                f"## 案例 {index}: {case['id']}",
                "",
                f"**问题**：{case['question']}",
                "",
                f"**参考答案**：{', '.join(case.get('gold_answers') or ['无'])}",
                "",
                "**正确文档摘要**：",
            ]
        )
        for doc in case.get("correct_docs") or []:
            lines.append(f"- `{doc.get('doc_id')}`: {truncate(doc.get('text', ''), 180)}")
        lines.append("")
        lines.append("**噪声/误导文档摘要**：")
        for doc in case.get("noise_docs") or []:
            lines.append(f"- `{doc.get('doc_id')}` ({doc.get('label')}): {truncate(doc.get('text', ''), 180)}")
        lines.extend(
            [
                "",
                f"**Naive RAG 输出** ({'正确' if case['baseline_correct'] else '错误'})：{case['baseline_answer']}",
                "",
                f"选中 doc_ids: {', '.join(case.get('baseline_selected_doc_ids') or []) or '无'}",
                "",
                f"**EGI-RAG 输出** ({'正确' if case['egi_correct'] else '错误'})：{case['egi_answer']}",
                "",
                f"校验结果: {case.get('egi_verification_result')} | 迭代轮数: {case.get('egi_iteration_count')}",
                "",
                f"选中 doc_ids: {', '.join(case.get('egi_selected_doc_ids') or []) or '无'}",
                "",
                "**证据句**：",
            ]
        )
        for evidence in case.get("egi_evidence_spans") or []:
            lines.append(f"- `{evidence.get('doc_id')}`: {evidence.get('text')}")
        lines.append("")
        lines.append("**文档评分（节选）**：")
        for score in (case.get("egi_doc_scores") or [])[:5]:
            lines.append(
                f"- `{score.get('doc_id')}`: label={score.get('label')}, score={score.get('score')}, reason={score.get('reason')}"
            )
        lines.append("")
        lines.append(f"**修正结论**：{_build_conclusion(case)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _build_conclusion(case: dict[str, Any]) -> str:
    if case["egi_correct"] and not case["baseline_correct"]:
        return "EGI-RAG 通过文档评分、证据抽取和一致性校验，避免了 Naive RAG 被噪声文档误导。"
    if case["egi_correct"] and case["baseline_correct"]:
        return "两种方法均答对，但 EGI-RAG 额外提供了可解释的证据链。"
    if not case["egi_correct"] and case["baseline_correct"]:
        return "该样本中 EGI-RAG 仍需改进文档筛选或证据抽取策略。"
    return "两种方法均未答对，可能需要更强的冲突检测或拒答机制。"


def normalize_text(text: Any) -> str:
    return " ".join(str(text or "").strip().lower().split())


def answers_match(prediction: str, gold: str) -> bool:
    if not gold:
        return False
    return gold in prediction or prediction in gold


def truncate(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def save_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
