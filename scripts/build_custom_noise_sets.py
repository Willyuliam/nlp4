"""Build a small custom-noise set for logic-gap RAG robustness tests.

The generated set is intentionally small to keep later API calls bounded. It
keeps 1-2 original correct documents per sample and adds three synthetic noise
documents:
  - logic_gap: overlaps with the question but omits the answer relation.
  - value_swap: gives a plausible but wrong answer.
  - high_overlap_irrelevant: repeats question terms while staying irrelevant.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any


SAMPLE_DIR = Path("samples")
OUT_DIR = SAMPLE_DIR / "custom_noise"
RANDOM_SEED = 20260626
PER_DATASET = 30


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def select_rows(rows: list[dict[str, Any]], dataset: str, limit: int) -> list[dict[str, Any]]:
    candidates = []
    for row in rows:
        gold_answers = [str(answer).strip() for answer in row.get("gold_answers", []) if str(answer).strip()]
        correct_docs = [ctx for ctx in row.get("contexts", []) if ctx.get("label") == "correct"]
        if not gold_answers or not correct_docs:
            continue
        primary = gold_answers[0]
        if len(primary) > 40:
            continue
        candidates.append(row)

    rng = random.Random(f"{RANDOM_SEED}-{dataset}")
    rng.shuffle(candidates)
    return candidates[:limit]


def make_wrong_answer(gold: str, wrong_answers: list[str]) -> str:
    for answer in wrong_answers:
        answer = str(answer).strip()
        if answer and normalize(answer) != normalize(gold):
            return answer

    number_match = re.search(r"\d+", gold)
    if number_match:
        value = number_match.group(0)
        replacement = str(int(value) + 1)
        return gold[: number_match.start()] + replacement + gold[number_match.end() :]

    words = re.findall(r"[A-Za-z]+|[\u4e00-\u9fff]+", gold)
    if words:
        return f"not {gold}"
    return "unknown alternative answer"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def question_terms(question: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+", question)
    return " ".join(tokens[:18]) if tokens else question


def build_custom_contexts(row: dict[str, Any], rng: random.Random) -> tuple[list[dict[str, Any]], str]:
    question = str(row.get("question", "")).strip()
    gold_answers = [str(answer).strip() for answer in row.get("gold_answers", []) if str(answer).strip()]
    gold = gold_answers[0] if gold_answers else ""
    wrong = make_wrong_answer(gold, [str(answer) for answer in row.get("wrong_answers", [])])
    terms = question_terms(question)

    correct_docs = [dict(ctx) for ctx in row.get("contexts", []) if ctx.get("label") == "correct"]
    rng.shuffle(correct_docs)
    selected_correct = correct_docs[: min(2, len(correct_docs))]

    custom_docs = [
        {
            "doc_id": "custom_logic_gap",
            "title": "Logic-gap distractor",
            "text": (
                f"This passage discusses the topic and entities in the question: {terms}. "
                "It gives background and related context, but it does not state the key relation "
                "or factual value needed to answer the question."
            ),
            "label": "noise",
            "noise_type": "logic_gap",
        },
        {
            "doc_id": "custom_value_swap",
            "title": "Value-swap misleading distractor",
            "text": (
                f"A conflicting source about {terms} claims that the answer is {wrong}. "
                "This statement is presented as a direct answer, but it is not the gold answer."
            ),
            "label": "misinfo",
            "noise_type": "value_swap",
        },
        {
            "doc_id": "custom_high_overlap_irrelevant",
            "title": "High-overlap irrelevant distractor",
            "text": (
                f"The words {terms} appear in this passage many times, but the passage only "
                "describes search terms, metadata, and unrelated background. It contains no "
                "usable evidence for the requested answer."
            ),
            "label": "noise",
            "noise_type": "high_overlap_irrelevant",
        },
    ]

    contexts = selected_correct + custom_docs
    rng.shuffle(contexts)
    return contexts, wrong


def convert_dataset(dataset: str, rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    rng = random.Random(f"{RANDOM_SEED}-{dataset}-contexts")
    selected = select_rows(rows, dataset, limit)
    converted = []
    for index, row in enumerate(selected):
        contexts, wrong = build_custom_contexts(row, rng)
        wrong_answers = list(dict.fromkeys([*(row.get("wrong_answers", []) or []), wrong]))
        converted.append(
            {
                "id": f"custom_{dataset}_{index:04d}",
                "dataset": f"custom_{dataset}",
                "question": row.get("question", ""),
                "contexts": contexts,
                "gold_answers": row.get("gold_answers", []),
                "wrong_answers": wrong_answers,
                "_meta": {
                    "source_id": row.get("id"),
                    "source_dataset": row.get("dataset", dataset),
                    "custom_noise_types": ["logic_gap", "value_swap", "high_overlap_irrelevant"],
                    "n_correct_selected": sum(1 for ctx in contexts if ctx.get("label") == "correct"),
                    "n_noise_selected": sum(1 for ctx in contexts if ctx.get("label") != "correct"),
                },
            }
        )
    return converted


def write_dataset(tag: str, rows: list[dict[str, Any]]) -> None:
    inputs = [
        {
            "id": row["id"],
            "dataset": row["dataset"],
            "question": row["question"],
            "contexts": row["contexts"],
            "_meta": row["_meta"],
        }
        for row in rows
    ]
    refs = [
        {
            "id": row["id"],
            "gold_answers": row["gold_answers"],
            "wrong_answers": row["wrong_answers"],
            "_meta": row["_meta"],
        }
        for row in rows
    ]
    save_json(OUT_DIR / f"{tag}_input.json", inputs)
    save_json(OUT_DIR / f"{tag}_reference.json", refs)
    save_json(OUT_DIR / f"{tag}_full.json", rows)


def main() -> int:
    rgb = convert_dataset("rgb", load_json(SAMPLE_DIR / "rgb_all_full.json"), PER_DATASET)
    ramdocs = convert_dataset("ramdocs", load_json(SAMPLE_DIR / "ramdocs_all_full.json"), PER_DATASET)
    combined = rgb + ramdocs

    write_dataset("custom_noise_rgb", rgb)
    write_dataset("custom_noise_ramdocs", ramdocs)
    write_dataset("custom_noise_all", combined)

    print(f"[OK] wrote custom noise sets: rgb={len(rgb)}, ramdocs={len(ramdocs)}, all={len(combined)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
