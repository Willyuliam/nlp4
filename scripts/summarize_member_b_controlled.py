"""Summarize member B controlled outputs into a Markdown table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.evaluate_outputs import evaluate


OUTPUT_RE = re.compile(
    r"^(?P<method>.+?)_(?P<dataset>rgb|ramdocs)_noise(?P<ratio>\d{3})_(?P<position>front|middle|back|random)_output$"
)


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize controlled baseline outputs.")
    parser.add_argument("--output-root", default="outputs/controlled")
    parser.add_argument("--save", default="reports/member_b_controlled_summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root)
    rows = []

    for output_path in sorted(output_root.glob("*/*_output.json")):
        match = OUTPUT_RE.match(output_path.stem)
        if not match:
            continue
        info = match.groupdict()
        dataset = info["dataset"]
        ratio = info["ratio"]
        position = info["position"]
        reference_path = Path("samples") / "controlled" / dataset / f"{dataset}_noise{ratio}_{position}_reference.json"
        input_path = Path("samples") / "controlled" / dataset / f"{dataset}_noise{ratio}_{position}_input.json"
        if not reference_path.exists() or not input_path.exists():
            continue

        result = evaluate(load_json(input_path), load_json(reference_path), load_json(output_path))["overall"]
        rows.append(
            {
                "dataset": dataset,
                "method": info["method"],
                "ratio": ratio,
                "position": position,
                **result,
            }
        )

    lines = [
        "# Member B Controlled Experiment Summary",
        "",
        "| Dataset | Method | Noise | Position | Outputs | Missing | Accuracy | F1 | Misinfo Adopt | Evidence Acc | Refusal Acc | Faithfulness |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {dataset} | {method} | {ratio}% | {position} | {num_outputs} | {num_missing_outputs} | "
            "{accuracy:.4f} | {f1:.4f} | {misinformation_adoption_rate:.4f} | "
            "{evidence_selection_accuracy:.4f} | {refusal_accuracy:.4f} | {faithfulness:.4f} |".format(
                **row
            )
        )

    save_path = Path(args.save)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {save_path} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
