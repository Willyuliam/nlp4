"""CLI entrypoint for EGI-RAG runs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from src.egi_rag import ABLATION_VARIANTS, run_egi_sample
from src.llm import QwenClient, load_qwen_config
from src.utils import load_json, save_json, validate_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EGI-RAG (member C).")
    parser.add_argument("--input", required=True, help="Path to input JSON array.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of samples to run.")
    parser.add_argument("--top_k", type=int, default=8, help="Candidate contexts before scoring.")
    parser.add_argument("--top_n", type=int, default=5, help="Contexts kept after local rerank.")
    parser.add_argument("--max_iterations", type=int, default=2, help="Maximum correction iterations.")
    parser.add_argument(
        "--variant",
        default="full",
        choices=sorted(ABLATION_VARIANTS),
        help="Ablation variant for EGI-RAG.",
    )
    parser.add_argument("--dry_run", action="store_true", help="Write prompts without calling Qwen API.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing output rows with the same id, and save progress after every sample.",
    )
    parser.add_argument(
        "--config",
        default="configs/model_config.example.yaml",
        help="Model config path. Secrets should normally be provided through DASHSCOPE_API_KEY.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    data = load_json(input_path)
    samples = validate_samples(data)
    if args.limit is not None:
        samples = samples[: max(args.limit, 0)]

    if not samples:
        save_json(args.output, [])
        print("当前没有样本：已生成空输出文件。")
        return 0

    config = load_qwen_config(args.config)
    client = QwenClient(config)
    method_name = "EGI-RAG" if args.variant == "full" else f"EGI-RAG-{args.variant}"

    existing_results = load_existing_results(args.output, method_name) if args.resume else {}
    results: list[dict[str, Any]] = []
    for index, sample in enumerate(samples, 1):
        sample_id = str(sample.get("id"))
        if sample_id in existing_results:
            result = existing_results[sample_id]
            print(f"[{index}/{len(samples)}] skip existing id={sample_id}")
        else:
            print(f"[{index}/{len(samples)}] run id={sample_id}")
            result = run_egi_sample(
                sample=sample,
                client=client,
                dry_run=args.dry_run,
                top_k=args.top_k,
                top_n=args.top_n,
                max_iterations=args.max_iterations,
                variant=args.variant,
            )
        results.append(result)
        save_json(args.output, results)

    error_count = sum(1 for item in results if item.get("error"))
    print(
        f"method={method_name}, samples={len(results)}, errors={error_count}, output={args.output}"
    )
    if error_count and not args.dry_run:
        print("如错误为 API Key 缺失，请设置 DASHSCOPE_API_KEY 或填写本地配置。")
    return 0


def load_existing_results(output_path: str | Path, method: str) -> dict[str, dict[str, Any]]:
    path = Path(output_path)
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    if not isinstance(data, list):
        return {}

    results: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("method") != method:
            continue
        if item.get("error"):
            continue
        sample_id = item.get("id")
        if sample_id is None:
            continue
        results[str(sample_id)] = item
    return results


if __name__ == "__main__":
    raise SystemExit(main())
