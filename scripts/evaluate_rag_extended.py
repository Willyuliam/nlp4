"""Extended RAG evaluation with answerable/unanswerable splits.

This script keeps the original lightweight, no-extra-dependency style, but
separates answer accuracy from refusal quality and retrieval/evidence quality.
It is intended for final reports where plain string-hit accuracy is too coarse.
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
    "unknown",
    "无法根据给定信息确定",
    "无法回答",
    "证据不足",
    "无法确定",
    "不知道",
)


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: Any) -> str:
    value = str(text or "").lower()
    value = re.sub(r"\s+", " ", value)
    value = value.translate(str.maketrans("", "", string.punctuation))
    return value.strip()


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


def answer_hit(prediction: str, answers: list[str]) -> bool:
    pred = normalize_text(prediction)
    return any(normalize_text(answer) and normalize_text(answer) in pred for answer in answers)


def exact_match(prediction: str, answers: list[str]) -> bool:
    pred = normalize_text(prediction)
    return any(pred == normalize_text(answer) for answer in answers)


def is_refusal(record: dict[str, Any]) -> bool:
    if bool(record.get("refused")):
        return True
    answer = normalize_text(record.get("answer", ""))
    return any(hint in answer for hint in REFUSAL_HINTS)


def label_maps(inputs: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    return {
        item["id"]: {
            str(ctx.get("doc_id", "")): str(ctx.get("label", "unknown"))
            for ctx in item.get("contexts", [])
        }
        for item in inputs
    }


def correct_doc_ids(label_by_doc: dict[str, str]) -> set[str]:
    return {doc_id for doc_id, label in label_by_doc.items() if label in {"correct", "supportive"}}


def selected_doc_ids(record: dict[str, Any]) -> set[str]:
    return {str(doc_id) for doc_id in record.get("selected_doc_ids", []) or [] if doc_id}


def evidence_doc_ids(record: dict[str, Any]) -> set[str]:
    doc_ids: set[str] = set()
    for span in record.get("evidence_spans", []) or []:
        if isinstance(span, dict) and span.get("doc_id"):
            doc_ids.add(str(span["doc_id"]))
    return doc_ids


def prf(predicted: set[str], gold: set[str]) -> tuple[float, float, float]:
    if not predicted and not gold:
        return 1.0, 1.0, 1.0
    if not predicted:
        return 0.0, 0.0, 0.0
    tp = len(predicted & gold)
    precision = tp / len(predicted)
    recall = tp / len(gold) if gold else 0.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    answerable = [row for row in rows if row["answerable"]]
    unanswerable = [row for row in rows if not row["answerable"]]
    refused = [row for row in rows if row["refused"]]
    should_refuse = [row for row in rows if row["should_refuse"]]
    tp_refusal = sum(1 for row in rows if row["refused"] and row["should_refuse"])

    refusal_precision = tp_refusal / len(refused) if refused else 0.0
    refusal_recall = tp_refusal / len(should_refuse) if should_refuse else 0.0
    refusal_f1 = (
        0.0
        if refusal_precision + refusal_recall == 0
        else 2 * refusal_precision * refusal_recall / (refusal_precision + refusal_recall)
    )

    return {
        "count": len(rows),
        "answerable_count": len(answerable),
        "unanswerable_count": len(unanswerable),
        "answer_accuracy_all": mean([float(row["answer_hit"]) for row in rows]),
        "answer_accuracy_answerable": mean([float(row["answer_hit"]) for row in answerable]),
        "exact_match_answerable": mean([float(row["exact_match"]) for row in answerable]),
        "token_f1_answerable": mean([row["token_f1"] for row in answerable]),
        "misinformation_adoption_rate": mean([float(row["wrong_hit"]) for row in rows]),
        "refusal_precision": round(refusal_precision, 4),
        "refusal_recall": round(refusal_recall, 4),
        "refusal_f1": round(refusal_f1, 4),
        "selected_context_precision": mean([row["selected_context_precision"] for row in rows]),
        "selected_context_recall": mean([row["selected_context_recall"] for row in rows]),
        "selected_context_f1": mean([row["selected_context_f1"] for row in rows]),
        "evidence_doc_precision": mean([row["evidence_doc_precision"] for row in rows]),
        "evidence_doc_recall": mean([row["evidence_doc_recall"] for row in rows]),
        "evidence_doc_f1": mean([row["evidence_doc_f1"] for row in rows]),
        "evidence_rate": mean([float(row["has_evidence"]) for row in rows]),
        "strict_supported_rate": mean([float(row["strict_supported"]) for row in rows]),
    }


def evaluate(
    inputs: list[dict[str, Any]],
    references: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    refs = {item["id"]: item for item in references}
    outs = {item["id"]: item for item in outputs}
    labels = label_maps(inputs)

    rows: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item_id, ref in refs.items():
        out = outs.get(item_id, {})
        answer = str(out.get("answer", ""))
        gold_answers = [str(answer) for answer in ref.get("gold_answers", []) if answer]
        wrong_answers = [str(answer) for answer in ref.get("wrong_answers", []) if answer]
        label_by_doc = labels.get(item_id, {})
        correct_docs = correct_doc_ids(label_by_doc)
        selected_docs = selected_doc_ids(out)
        evidence_docs = evidence_doc_ids(out)

        selected_p, selected_r, selected_f1 = prf(selected_docs, correct_docs)
        evidence_p, evidence_r, evidence_f1 = prf(evidence_docs, correct_docs)

        n_noise = sum(1 for label in label_by_doc.values() if label in {"noise", "misinfo", "contradictory"})
        n_docs = len(label_by_doc)
        noise_ratio = round(n_noise / n_docs, 2) if n_docs else 0.0

        answerable = bool(gold_answers)
        should_refuse = not answerable or not correct_docs
        row = {
            "id": item_id,
            "answerable": answerable,
            "should_refuse": should_refuse,
            "missing_output": item_id not in outs,
            "answer_hit": answer_hit(answer, gold_answers) if gold_answers else False,
            "exact_match": exact_match(answer, gold_answers) if gold_answers else False,
            "token_f1": max((token_f1(answer, gold) for gold in gold_answers), default=0.0),
            "wrong_hit": answer_hit(answer, wrong_answers) if wrong_answers else False,
            "refused": is_refusal(out),
            "selected_context_precision": selected_p,
            "selected_context_recall": selected_r,
            "selected_context_f1": selected_f1,
            "evidence_doc_precision": evidence_p,
            "evidence_doc_recall": evidence_r,
            "evidence_doc_f1": evidence_f1,
            "has_evidence": bool(out.get("evidence_spans")),
            "strict_supported": str(out.get("verification_result", "")).lower() == "supported"
            and bool(out.get("evidence_spans")),
            "noise_ratio": noise_ratio,
        }
        rows.append(row)
        groups[str(noise_ratio)].append(row)

    return {
        "overall": summarize(rows),
        "by_noise_ratio": {key: summarize(value) for key, value in sorted(groups.items(), key=lambda item: float(item[0]))},
        "per_item": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()

    result = evaluate(load_json(args.input), load_json(args.reference), load_json(args.output))
    result_text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(result_text, encoding="utf-8")
        print(json.dumps(result["overall"], ensure_ascii=False, indent=2))
    else:
        print(result_text)


if __name__ == "__main__":
    main()
