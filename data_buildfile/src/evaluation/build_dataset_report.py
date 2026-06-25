"""
生成成员A可放入报告的数据集统计表。

运行：
  python src/evaluation/build_dataset_report.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


SAMPLE_DIR = Path("data/samples")
REPORT_PATH = Path("reports/dataset_statistics.md")


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def summarize(path: Path) -> dict:
    data = load(path)
    labels = Counter()
    docs_per_item = []
    answer_items = 0

    for item in data:
        contexts = item.get("contexts", [])
        docs_per_item.append(len(contexts))
        if item.get("gold_answers"):
            answer_items += 1
        for ctx in contexts:
            labels[ctx.get("label", "unknown")] += 1

    total_docs = sum(labels.values())
    return {
        "name": path.name.replace("_full.json", ""),
        "items": len(data),
        "answer_items": answer_items,
        "total_docs": total_docs,
        "avg_docs": round(sum(docs_per_item) / len(docs_per_item), 2) if docs_per_item else 0,
        "min_docs": min(docs_per_item) if docs_per_item else 0,
        "max_docs": max(docs_per_item) if docs_per_item else 0,
        "labels": labels,
    }


def main() -> None:
    files = sorted(SAMPLE_DIR.glob("*_full.json"))
    summaries = [summarize(path) for path in files]

    lines = [
        "# 数据集统计",
        "",
        "| 数据集 | 样本数 | 有参考答案样本 | 文档总数 | 平均文档数 | 最少/最多文档数 |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for item in summaries:
        lines.append(
            f"| {item['name']} | {item['items']} | {item['answer_items']} | "
            f"{item['total_docs']} | {item['avg_docs']} | {item['min_docs']}/{item['max_docs']} |"
        )

    lines += ["", "## 文档标签分布", ""]
    for item in summaries:
        lines.append(f"### {item['name']}")
        lines.append("")
        lines.append("| 标签 | 数量 | 占比 |")
        lines.append("|---|---:|---:|")
        total = item["total_docs"]
        for label, count in item["labels"].most_common():
            pct = count / total * 100 if total else 0
            lines.append(f"| {label} | {count} | {pct:.1f}% |")
        lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 已生成 {REPORT_PATH}")


if __name__ == "__main__":
    main()
