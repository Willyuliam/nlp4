"""Summarize all available RAG outputs with extended metrics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate_rag_extended import evaluate


CONTROLLED_RE = re.compile(
    r"^(?P<method>.+?)_(?P<dataset>rgb|ramdocs)_noise(?P<ratio>\d{3})_(?P<position>front|middle|back|random)_output$"
)
FULL_RE = re.compile(r"^(?P<prefix>rgb|ramdocs)_(?P<method>.+?)_output$")
NEURAL_FULL_RE = re.compile(r"^(?P<prefix>rgb|ramdocs)_neural_(?P<method>.+?)_output$")
EGI_FULL_RE = re.compile(r"^(?P<method>.+?)_(?P<dataset>rgb|ramdocs)_all_output$")
CUSTOM_RE = re.compile(r"^(?P<method>.+?)_custom_noise_(?P<tag>all|rgb|ramdocs)_output$")


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_paths(output_path: Path) -> dict[str, Any] | None:
    stem = output_path.stem

    controlled = CONTROLLED_RE.match(stem)
    if controlled:
        info = controlled.groupdict()
        dataset = info["dataset"]
        ratio = info["ratio"]
        position = info["position"]
        variant = f"{dataset}_noise{ratio}_{position}"
        return {
            "group": "controlled",
            "dataset": dataset,
            "setting": f"noise{ratio}_{position}",
            "method": info["method"],
            "input": Path("samples") / "controlled" / dataset / f"{variant}_input.json",
            "reference": Path("samples") / "controlled" / dataset / f"{variant}_reference.json",
        }

    egi_full = EGI_FULL_RE.match(stem)
    if egi_full:
        info = egi_full.groupdict()
        dataset = info["dataset"]
        return {
            "group": "full",
            "dataset": dataset,
            "setting": "all",
            "method": info["method"],
            "input": Path("samples") / f"{dataset}_all_input.json",
            "reference": Path("samples") / f"{dataset}_all_reference.json",
        }

    custom = CUSTOM_RE.match(stem)
    if custom:
        info = custom.groupdict()
        tag = info["tag"]
        return {
            "group": "custom_noise",
            "dataset": "custom_noise",
            "setting": tag,
            "method": info["method"],
            "input": Path("samples") / "custom_noise" / f"custom_noise_{tag}_input.json",
            "reference": Path("samples") / "custom_noise" / f"custom_noise_{tag}_reference.json",
        }

    neural = NEURAL_FULL_RE.match(stem)
    if neural:
        info = neural.groupdict()
        dataset = info["prefix"]
        return {
            "group": "full_neural_baseline",
            "dataset": dataset,
            "setting": "all",
            "method": info["method"],
            "input": Path("samples") / f"{dataset}_all_input.json",
            "reference": Path("samples") / f"{dataset}_all_reference.json",
        }

    full = FULL_RE.match(stem)
    if full:
        info = full.groupdict()
        dataset = info["prefix"]
        return {
            "group": "full_baseline",
            "dataset": dataset,
            "setting": "all",
            "method": info["method"],
            "input": Path("samples") / f"{dataset}_all_input.json",
            "reference": Path("samples") / f"{dataset}_all_reference.json",
        }

    return None


def summarize(output_roots: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for root in output_roots:
        for output_path in sorted(root.rglob("*_output.json")):
            if output_path in seen:
                continue
            seen.add(output_path)
            resolved = resolve_paths(output_path)
            if resolved is None:
                continue
            input_path = resolved["input"]
            reference_path = resolved["reference"]
            if not input_path.exists() or not reference_path.exists():
                continue
            outputs = load_json(output_path)
            output_ids = {str(row.get("id")) for row in outputs if isinstance(row, dict)}
            inputs = [row for row in load_json(input_path) if str(row.get("id")) in output_ids]
            references = [row for row in load_json(reference_path) if str(row.get("id")) in output_ids]
            metrics = evaluate(inputs, references, outputs)["overall"]
            rows.append(
                {
                    "output": str(output_path),
                    "outputs": len(outputs),
                    "errors": sum(1 for row in outputs if isinstance(row, dict) and row.get("error")),
                    **{key: value for key, value in resolved.items() if key not in {"input", "reference"}},
                    **metrics,
                }
            )
    return rows


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "Group",
        "Dataset",
        "Setting",
        "Method",
        "N",
        "Err",
        "AnsAcc",
        "F1",
        "Misinfo",
        "R@5",
        "R@10",
        "MRR",
        "nDCG@5",
        "EvF1",
        "StrictSup",
        "RefF1",
    ]
    lines = [
        "# Extended Experiment Summary",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append(
            "| {group} | {dataset} | {setting} | {method} | {outputs} | {errors} | "
            "{answer_accuracy_answerable:.4f} | {token_f1_answerable:.4f} | {misinformation_adoption_rate:.4f} | "
            "{retrieved_recall_at_5:.4f} | {retrieved_recall_at_10:.4f} | {retrieved_mrr:.4f} | "
            "{retrieved_ndcg_at_5:.4f} | {evidence_doc_f1:.4f} | {strict_supported_rate:.4f} | "
            "{refusal_f1:.4f} |".format(**row)
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-roots",
        nargs="+",
        default=[
            "outputs/controlled",
            "outputs/fair_subset",
            "outputs/egi_rag",
            "outputs/egi_rag_plus",
            "outputs/custom_noise",
            "outputs/rgb_results",
            "outputs/ramdocs_results",
        ],
    )
    parser.add_argument("--save-json", type=Path, default=Path("reports/extended_experiment_summary.json"))
    parser.add_argument("--save-md", type=Path, default=Path("reports/extended_experiment_summary.md"))
    args = parser.parse_args()

    rows = summarize([Path(root) for root in args.output_roots])
    write_json(args.save_json, rows)
    write_markdown(args.save_md, rows)
    print(f"[OK] rows={len(rows)} json={args.save_json} md={args.save_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
