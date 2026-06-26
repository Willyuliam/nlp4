"""Summarize newly added fair-subset, EGI-RAG, and custom-noise outputs."""

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


CONTROLLED_RE = re.compile(
    r"^(?P<method>.+?)_(?P<dataset>rgb|ramdocs)_noise(?P<ratio>\d{3})_(?P<position>front|middle|back|random)_output$"
)
FULL_RE = re.compile(r"^(?P<method>.+?)_(?P<dataset>rgb|ramdocs)_all_output$")
CUSTOM_RE = re.compile(r"^(?P<method>.+?)_custom_noise_(?P<tag>all|rgb|ramdocs)_output$")


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_inputs(output_path: Path) -> tuple[str, str, Path, Path] | None:
    stem = output_path.stem
    controlled = CONTROLLED_RE.match(stem)
    if controlled:
        info = controlled.groupdict()
        dataset = info["dataset"]
        ratio = info["ratio"]
        position = info["position"]
        variant = f"{dataset}_noise{ratio}_{position}"
        return (
            info["method"],
            f"{dataset} noise{ratio} {position}",
            Path("samples") / "controlled" / dataset / f"{variant}_input.json",
            Path("samples") / "controlled" / dataset / f"{variant}_reference.json",
        )

    full = FULL_RE.match(stem)
    if full:
        info = full.groupdict()
        dataset = info["dataset"]
        return (
            info["method"],
            f"{dataset} all",
            Path("samples") / f"{dataset}_all_input.json",
            Path("samples") / f"{dataset}_all_reference.json",
        )

    custom = CUSTOM_RE.match(stem)
    if custom:
        info = custom.groupdict()
        tag = info["tag"]
        return (
            info["method"],
            f"custom_noise {tag}",
            Path("samples") / "custom_noise" / f"custom_noise_{tag}_input.json",
            Path("samples") / "custom_noise" / f"custom_noise_{tag}_reference.json",
        )
    return None


def summarize(output_root: Path) -> list[dict[str, Any]]:
    rows = []
    for output_path in sorted(output_root.rglob("*_output.json")):
        resolved = resolve_inputs(output_path)
        if resolved is None:
            continue
        method, setting, input_path, reference_path = resolved
        if not input_path.exists() or not reference_path.exists():
            continue

        outputs = load_json(output_path)
        output_ids = {str(row.get("id")) for row in outputs if isinstance(row, dict)}
        inputs = [row for row in load_json(input_path) if str(row.get("id")) in output_ids]
        references = [row for row in load_json(reference_path) if str(row.get("id")) in output_ids]
        result = evaluate(inputs, references, outputs)["overall"]
        rows.append(
            {
                "setting": setting,
                "method": method,
                "errors": sum(1 for row in outputs if row.get("error")),
                **result,
            }
        )
    return rows


def write_markdown(save_path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        f"# {save_path.stem}",
        "",
        "| Setting | Method | Outputs | Missing | Errors | Accuracy | F1 | Misinfo Adopt | Evidence Acc | Refusal Acc | Faithfulness |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {setting} | {method} | {num_outputs} | {num_missing_outputs} | {errors} | "
            "{accuracy:.4f} | {f1:.4f} | {misinformation_adoption_rate:.4f} | "
            "{evidence_selection_accuracy:.4f} | {refusal_accuracy:.4f} | {faithfulness:.4f} |".format(
                **row
            )
        )

    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize new experiment outputs.")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--save", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = summarize(args.output_root)
    write_markdown(args.save, rows)
    print(f"[OK] wrote {args.save} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
