"""
构造“噪音比例 + 正确文档位置”可控实验集。

用途：
  1. 分析正确文档位置对 RAG 问答结果的影响。
  2. 分析不同噪音比例对模型准确率的影响。
  3. 给成员B/C提供统一输入，便于跑 baseline 和 EGI-RAG。

运行：
  python src/evaluation/build_controlled_noise_sets.py

输出：
  samples/controlled/<dataset>/<dataset>_noiseXX_<position>_input.json
  samples/controlled/<dataset>/<dataset>_noiseXX_<position>_reference.json
  samples/controlled/<dataset>/<dataset>_noiseXX_<position>_full.json
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


SAMPLE_DIR = Path("samples")
OUT_DIR = Path("samples/controlled")
RANDOM_SEED = 42
MAX_DOCS_PER_ITEM = 10
NOISE_RATIOS = [0, 20, 40, 60, 80, 100]
POSITION_MODES = ["front", "middle", "back", "random"]


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def split_contexts(item: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    correct = []
    noise = []
    for ctx in item.get("contexts", []):
        label = ctx.get("label", "unknown")
        if label == "correct":
            correct.append(ctx)
        elif label in {"noise", "misinfo", "contradictory", "unknown"}:
            noise.append(ctx)
    return correct, noise


def place_correct_docs(
    correct_docs: list[dict[str, Any]],
    noise_docs: list[dict[str, Any]],
    mode: str,
    rng: random.Random,
) -> list[dict[str, Any]]:
    correct_docs = list(correct_docs)
    noise_docs = list(noise_docs)
    rng.shuffle(correct_docs)
    rng.shuffle(noise_docs)

    if not correct_docs:
        return noise_docs
    if mode == "front":
        return correct_docs + noise_docs
    if mode == "back":
        return noise_docs + correct_docs
    if mode == "middle":
        mid = len(noise_docs) // 2
        return noise_docs[:mid] + correct_docs + noise_docs[mid:]
    contexts = correct_docs + noise_docs
    rng.shuffle(contexts)
    return contexts


def build_variant_item(
    item: dict[str, Any],
    noise_ratio: int,
    position_mode: str,
    rng: random.Random,
) -> dict[str, Any] | None:
    correct_docs, noise_docs = split_contexts(item)

    if noise_ratio < 100 and not correct_docs:
        return None
    if noise_ratio > 0 and not noise_docs:
        return None

    total_docs = min(MAX_DOCS_PER_ITEM, len(correct_docs) + len(noise_docs))
    if total_docs <= 0:
        return None

    n_noise = round(total_docs * noise_ratio / 100)
    n_correct = total_docs - n_noise

    if noise_ratio < 100:
        n_correct = max(1, n_correct)
    if noise_ratio > 0:
        n_noise = max(1, n_noise)

    n_correct = min(n_correct, len(correct_docs))
    n_noise = min(n_noise, len(noise_docs))

    if noise_ratio == 100:
        selected_correct = []
    else:
        selected_correct = rng.sample(correct_docs, n_correct)
    selected_noise = rng.sample(noise_docs, n_noise) if n_noise else []

    contexts = place_correct_docs(selected_correct, selected_noise, position_mode, rng)
    if not contexts:
        return None

    new_item = {
        "id": item["id"],
        "dataset": item.get("dataset", ""),
        "question": item.get("question", ""),
        "contexts": contexts,
        "gold_answers": item.get("gold_answers", []),
        "wrong_answers": item.get("wrong_answers", []),
        "_meta": {
            **item.get("_meta", {}),
            "controlled_noise_ratio": noise_ratio,
            "correct_position": position_mode,
            "max_docs_per_item": MAX_DOCS_PER_ITEM,
            "n_correct_selected": len(selected_correct),
            "n_noise_selected": len(selected_noise),
        },
    }
    return new_item


def write_variant(dataset: str, variant: str, rows: list[dict[str, Any]]) -> None:
    base = OUT_DIR / dataset / f"{dataset}_{variant}"
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
    save_json(base.with_name(base.name + "_input.json"), inputs)
    save_json(base.with_name(base.name + "_reference.json"), refs)
    save_json(base.with_name(base.name + "_full.json"), rows)


def process_dataset(dataset: str, source_file: Path) -> list[str]:
    data = load_json(source_file)
    written = []

    for noise_ratio in NOISE_RATIOS:
        for position_mode in POSITION_MODES:
            rng = random.Random(f"{RANDOM_SEED}-{dataset}-{noise_ratio}-{position_mode}")
            rows = []
            for item in data:
                row = build_variant_item(item, noise_ratio, position_mode, rng)
                if row is not None:
                    rows.append(row)

            if not rows:
                continue

            variant = f"noise{noise_ratio:03d}_{position_mode}"
            write_variant(dataset, variant, rows)
            written.append(f"{dataset}_{variant}: {len(rows)}")

    return written


def main() -> None:
    jobs = {
        "rgb": SAMPLE_DIR / "rgb_all_full.json",
        "ramdocs": SAMPLE_DIR / "ramdocs_all_full.json",
    }

    all_written = []
    for dataset, path in jobs.items():
        if not path.exists():
            print(f"[SKIP] 未找到 {path}")
            continue
        all_written.extend(process_dataset(dataset, path))

    print("[OK] 已生成可控噪音/位置实验集")
    for line in all_written:
        print("  " + line)


if __name__ == "__main__":
    main()
