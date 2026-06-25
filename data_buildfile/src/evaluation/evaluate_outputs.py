"""
成员A评估脚本：对 RAG / EGI-RAG 输出计算自动指标。

输入：
  --reference data/samples/rgb_all_reference.json
  --input data/samples/rgb_all_input.json
  --output outputs/rgb_results/naive_rag_output.json

输出：
  JSON 指标文件，可直接放入实验表格。

兼容的 output 每条至少包含：
  id, answer
可选字段：
  selected_doc_ids, evidence_spans, refused, verification_result
"""

from __future__ import annotations

import argparse
import json
import re
import string
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REFUSAL_HINTS = (
    "insufficient evidence",
    "not enough evidence",
    "cannot answer",
    "can't answer",
    "无法回答",
    "证据不足",
    "无法确定",
    "不知道",
)


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: Any) -> str:
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.strip()


def token_f1(prediction: str, gold: str) -> float:
    pred_tokens = normalize_text(prediction).split()
    gold_tokens = normalize_text(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)

    common = Counter(pred_tokens) & Counter(gold_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0

    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def exact_match(prediction: str, gold_answers: list[str]) -> bool:
    pred = normalize_text(prediction)
    return any(pred == normalize_text(gold) for gold in gold_answers)


def answer_hit(prediction: str, candidates: list[str]) -> bool:
    pred = normalize_text(prediction)
    return any(normalize_text(ans) and normalize_text(ans) in pred for ans in candidates)


def is_refusal(record: dict[str, Any]) -> bool:
    if bool(record.get("refused")):
        return True
    answer = normalize_text(record.get("answer", ""))
    return any(hint in answer for hint in REFUSAL_HINTS)


def context_label_map(inputs: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for item in inputs:
        mapping[item["id"]] = {
            ctx.get("doc_id", ""): ctx.get("label", "unknown")
            for ctx in item.get("contexts", [])
        }
    return mapping


def correct_doc_ids(label_by_doc: dict[str, str]) -> set[str]:
    return {
        doc_id
        for doc_id, label in label_by_doc.items()
        if label in {"correct", "supportive"}
    }


def evaluate(
    inputs: list[dict[str, Any]],
    references: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    refs = {item["id"]: item for item in references}
    outs = {item["id"]: item for item in outputs}
    labels = context_label_map(inputs)

    rows = []
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item_id, ref in refs.items():
        missing_output = item_id not in outs
        out = outs.get(item_id, {})
        answer = str(out.get("answer", ""))
        gold_answers = [str(a) for a in ref.get("gold_answers", [])]
        wrong_answers = [str(a) for a in ref.get("wrong_answers", [])]
        label_by_doc = labels.get(item_id, {})
        selected = set(out.get("selected_doc_ids", []) or [])
        correct_docs = correct_doc_ids(label_by_doc)

        em = exact_match(answer, gold_answers) if gold_answers else False
        f1 = max((token_f1(answer, gold) for gold in gold_answers), default=0.0)
        gold_hit = answer_hit(answer, gold_answers) if gold_answers else False
        wrong_hit = answer_hit(answer, wrong_answers) if wrong_answers else False
        refused = is_refusal(out)

        has_correct_context = bool(correct_docs)
        evidence_ok = bool(selected & correct_docs) if selected else False
        needs_refusal = not has_correct_context or not gold_answers
        refusal_ok = False if missing_output else (refused if needs_refusal else not refused)
        faithful = (
            False if missing_output else (
                str(out.get("verification_result", "")).lower() == "supported"
                or bool(out.get("evidence_spans"))
                or evidence_ok
            )
        )

        row = {
            "id": item_id,
            "missing_output": missing_output,
            "exact_match": em,
            "answer_accuracy": gold_hit,
            "f1": f1,
            "wrong_answer_hit": wrong_hit,
            "misinformation_adopted": wrong_hit,
            "evidence_selection_correct": evidence_ok,
            "refusal_correct": refusal_ok,
            "faithful": faithful,
        }
        rows.append(row)

        n_noise = sum(1 for label in label_by_doc.values() if label in {"noise", "misinfo", "contradictory"})
        n_docs = len(label_by_doc)
        noise_ratio = round(n_noise / n_docs, 2) if n_docs else 0.0
        by_group[str(noise_ratio)].append(row)

    def avg(key: str, data: list[dict[str, Any]]) -> float:
        return round(sum(float(row[key]) for row in data) / len(data), 4) if data else 0.0

    overall = {
        "num_reference": len(refs),
        "num_outputs": len(outputs),
        "num_missing_outputs": sum(1 for row in rows if row["missing_output"]),
        "num_evaluated": len(rows),
        "accuracy": avg("answer_accuracy", rows),
        "exact_match": avg("exact_match", rows),
        "f1": avg("f1", rows),
        "misinformation_adoption_rate": avg("misinformation_adopted", rows),
        "evidence_selection_accuracy": avg("evidence_selection_correct", rows),
        "refusal_accuracy": avg("refusal_correct", rows),
        "faithfulness": avg("faithful", rows),
    }

    group_metrics = {
        group: {
            "count": len(group_rows),
            "accuracy": avg("answer_accuracy", group_rows),
            "f1": avg("f1", group_rows),
            "misinformation_adoption_rate": avg("misinformation_adopted", group_rows),
            "evidence_selection_accuracy": avg("evidence_selection_correct", group_rows),
        }
        for group, group_rows in sorted(by_group.items(), key=lambda x: float(x[0]))
    }

    clean_acc = next((m["accuracy"] for g, m in group_metrics.items() if float(g) == 0.0), None)
    if clean_acc is not None:
        for metrics in group_metrics.values():
            metrics["noise_sensitivity_drop"] = round(clean_acc - metrics["accuracy"], 4)

    return {"overall": overall, "by_noise_ratio": group_metrics, "per_item": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()

    result = evaluate(load_json(args.input), load_json(args.reference), load_json(args.output))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(text, encoding="utf-8")
        print(json.dumps(result["overall"], ensure_ascii=False, indent=2))
    else:
        print(text)


if __name__ == "__main__":
    main()
