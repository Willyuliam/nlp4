r"""Run member B controlled baseline experiments.

Run from the repository root, preferably with the type3 interpreter:
  D:\conda_envs\type3\python.exe scripts\run_member_b_controlled.py
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import subprocess
import sys
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_METHODS = [
    "zero_shot",
    "ordered_rag",
    "naive_rag",
    "rerank_rag",
    "crag_lite",
    "self_rag_lite",
]

METHOD_PARAMS = {
    "zero_shot": {"top_k": 0, "top_n": 0},
    "ordered_rag": {"top_k": 5, "top_n": 5},
    "naive_rag": {"top_k": 5, "top_n": 5},
    "rerank_rag": {"top_k": 8, "top_n": 5},
    "crag_lite": {"top_k": 8, "top_n": 5},
    "self_rag_lite": {"top_k": 8, "top_n": 5},
}


class Job(NamedTuple):
    dataset: str
    ratio: int
    position: str
    method: str
    input_path: Path
    output_path: Path


def planned_variants() -> list[tuple[str, int, str]]:
    variants: list[tuple[str, int, str]] = []

    for ratio in [0, 20, 40, 60, 80, 100]:
        variants.append(("rgb", ratio, "front"))
    for ratio in [60, 100]:
        for position in ["front", "middle", "back", "random"]:
            variants.append(("rgb", ratio, position))
    for ratio in [20, 60, 100]:
        variants.append(("ramdocs", ratio, "front"))

    deduped: list[tuple[str, int, str]] = []
    seen = set()
    for item in variants:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run member B controlled baseline matrix.")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter to use.")
    parser.add_argument("--output-root", default="outputs/controlled", help="Directory for output JSON files.")
    parser.add_argument("--methods", default=",".join(DEFAULT_METHODS), help="Comma-separated method list.")
    parser.add_argument("--limit", type=int, default=None, help="Optional sample limit for smoke runs.")
    parser.add_argument("--workers", type=int, default=1, help="Workers passed to src.run_baseline.")
    parser.add_argument("--job-workers", type=int, default=1, help="Concurrent method/variant jobs.")
    parser.add_argument("--dry-run", action="store_true", help="Generate prompts without API calls.")
    parser.add_argument("--disable-neural", action="store_true", help="Use lexical retrieval/rerank fallback.")
    parser.add_argument("--no-resume", action="store_true", help="Do not reuse existing successful rows.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    methods = [method.strip() for method in args.methods.split(",") if method.strip()]
    unknown = sorted(set(methods) - set(DEFAULT_METHODS))
    if unknown:
        print(f"Unsupported methods in this controlled plan: {unknown}", file=sys.stderr)
        return 2

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    hf_home = REPO_ROOT / ".hf_cache"
    env.setdefault("HF_HOME", str(hf_home))
    env.setdefault("HF_HUB_CACHE", str(hf_home / "hub"))
    env.setdefault("TRANSFORMERS_CACHE", str(hf_home / "hub"))
    env.setdefault("SENTENCE_TRANSFORMERS_HOME", str(hf_home / "models"))
    env.setdefault("RAG_EMBEDDING_MODEL", str(hf_home / "models" / "bge-m3"))
    env.setdefault("RAG_RERANKER_MODEL", str(hf_home / "models" / "bge-reranker-v2-m3"))
    if args.disable_neural:
        env["RAG_DISABLE_NEURAL_RETRIEVER"] = "1"
        env["RAG_DISABLE_NEURAL_RERANKER"] = "1"

    jobs: list[Job] = []
    for dataset, ratio, position in planned_variants():
        variant = f"{dataset}_noise{ratio:03d}_{position}"
        input_path = Path("samples") / "controlled" / dataset / f"{variant}_input.json"
        if not input_path.exists():
            print(f"[SKIP] missing input: {input_path}")
            continue

        dataset_out = output_root / dataset
        dataset_out.mkdir(parents=True, exist_ok=True)

        for method in methods:
            output_path = dataset_out / f"{method}_{variant}_output.json"
            jobs.append(Job(dataset, ratio, position, method, input_path, output_path))

    failed = 0
    if args.job_workers <= 1:
        for job in jobs:
            failed += run_job(job, args, env)
    else:
        with ThreadPoolExecutor(max_workers=args.job_workers) as executor:
            futures = {executor.submit(run_job, job, args, env): job for job in jobs}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    failed += future.result()
                except Exception as exc:
                    failed += 1
                    variant = f"{job.dataset}_noise{job.ratio:03d}_{job.position}"
                    print(f"[FAIL] {job.method} {variant} exception={exc}")

    total = len(jobs)
    print(f"[DONE] jobs={total}, failed={failed}, output_root={output_root}")
    return 1 if failed else 0


def run_job(job: Job, args: argparse.Namespace, env: dict[str, str]) -> int:
    params = METHOD_PARAMS[job.method]
    variant = f"{job.dataset}_noise{job.ratio:03d}_{job.position}"
    command = [
        args.python,
        "-m",
        "src.run_baseline",
        "--method",
        job.method,
        "--input",
        str(job.input_path),
        "--output",
        str(job.output_path),
        "--top_k",
        str(params["top_k"]),
        "--top_n",
        str(params["top_n"]),
        "--workers",
        str(args.workers),
    ]
    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.dry_run:
        command.append("--dry_run")
    if not args.no_resume:
        command.append("--resume")

    print(f"[RUN] {job.method} {variant}")
    result = subprocess.run(command, cwd=REPO_ROOT, env=env)
    if result.returncode != 0:
        print(f"[FAIL] {job.method} {variant} exit={result.returncode}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
