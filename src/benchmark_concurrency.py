"""Small-scale API concurrency benchmark for RAG baseline runs."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import statistics
import time
from typing import Any

from src.llm import QwenClient, load_qwen_config
from src.rag_baselines.baselines import SUPPORTED_METHODS, run_sample
from src.utils import load_json, save_json, validate_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Qwen API concurrency on a small RAG sample.")
    parser.add_argument("--input", default="samples/rgb_input.json", help="Input JSON array.")
    parser.add_argument("--output", default="outputs/debug/concurrency_benchmark.json", help="Summary output JSON.")
    parser.add_argument("--method", default="rerank_rag", choices=sorted(SUPPORTED_METHODS))
    parser.add_argument("--limit", type=int, default=8, help="Samples per concurrency level.")
    parser.add_argument("--workers", default="1,2,4,8,16", help="Comma-separated worker counts.")
    parser.add_argument("--top_k", type=int, default=20)
    parser.add_argument("--top_n", type=int, default=5)
    parser.add_argument("--config", default="configs/model_config.example.yaml")
    parser.add_argument(
        "--disable_neural_retrieval",
        action="store_true",
        help="Disable local bge/FAISS dependencies so the benchmark focuses on API concurrency.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workers = _parse_workers(args.workers)
    data = validate_samples(load_json(args.input))
    samples = data[: max(args.limit, 0)]
    if not samples:
        save_json(args.output, {"error": "no samples selected"})
        return 1

    if args.disable_neural_retrieval:
        os.environ["RAG_DISABLE_NEURAL_RETRIEVER"] = "1"
        os.environ["RAG_DISABLE_NEURAL_RERANKER"] = "1"

    config = load_qwen_config(args.config)
    summary: dict[str, Any] = {
        "input": args.input,
        "method": args.method,
        "sample_count_per_level": len(samples),
        "model": config.model,
        "max_tokens": config.max_tokens,
        "enable_thinking": config.enable_thinking,
        "has_api_key": bool(config.api_key),
        "workers": [],
    }

    for worker_count in workers:
        result = _run_level(
            samples=samples,
            method=args.method,
            worker_count=worker_count,
            top_k=args.top_k,
            top_n=args.top_n,
            config_path=args.config,
        )
        summary["workers"].append(result)
        save_json(args.output, summary)
        print(
            f"workers={worker_count}, ok={result['ok_count']}/{result['sample_count']}, "
            f"errors={result['error_count']}, wall={result['wall_seconds']:.2f}s, "
            f"throughput={result['throughput_per_minute']:.1f}/min"
        )

        # Stop escalating once a level is clearly failing.
        if result["error_count"] and result["ok_count"] == 0:
            print("该并发档全部失败，停止继续升高并发。")
            break

    return 0


def _run_level(
    samples: list[dict[str, Any]],
    method: str,
    worker_count: int,
    top_k: int,
    top_n: int,
    config_path: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(_run_one, sample, method, top_k, top_n, config_path)
            for sample in samples
        ]
        for future in as_completed(futures):
            rows.append(future.result())
    wall = time.perf_counter() - started

    latencies = [row["latency_seconds"] for row in rows]
    ok_rows = [row for row in rows if not row.get("error")]
    errors = [row.get("error") for row in rows if row.get("error")]
    first_error = next((error for error in errors if error), None)
    return {
        "worker_count": worker_count,
        "sample_count": len(samples),
        "ok_count": len(ok_rows),
        "error_count": len(errors),
        "first_error": first_error,
        "wall_seconds": round(wall, 3),
        "throughput_per_minute": round(len(rows) / wall * 60, 2) if wall > 0 else 0,
        "latency_seconds": {
            "avg": round(statistics.mean(latencies), 3),
            "p50": round(statistics.median(latencies), 3),
            "p95": round(_percentile(latencies, 0.95), 3),
            "max": round(max(latencies), 3),
        },
    }


def _run_one(
    sample: dict[str, Any],
    method: str,
    top_k: int,
    top_n: int,
    config_path: str,
) -> dict[str, Any]:
    client = QwenClient(load_qwen_config(config_path))
    started = time.perf_counter()
    result = run_sample(
        sample=sample,
        method=method,
        client=client,
        dry_run=False,
        top_k=top_k,
        top_n=top_n,
    )
    latency = time.perf_counter() - started
    return {
        "id": result.get("id"),
        "error": result.get("error"),
        "latency_seconds": latency,
    }


def _parse_workers(raw: str) -> list[int]:
    result = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value <= 0:
            raise ValueError("--workers values must be positive")
        result.append(value)
    if not result:
        raise ValueError("--workers cannot be empty")
    return result


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * pct) - 1))
    return ordered[index]


if __name__ == "__main__":
    raise SystemExit(main())
