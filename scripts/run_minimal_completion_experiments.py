"""Run the minimal completion experiment matrix without touching old outputs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[1]

METHOD_PARAMS = {
    "naive_rag": {"top_k": 5, "top_n": 5},
    "rerank_rag": {"top_k": 8, "top_n": 5},
    "crag_lite": {"top_k": 8, "top_n": 5},
    "self_rag_lite": {"top_k": 8, "top_n": 5},
    "egi_rag": {"top_k": 8, "top_n": 5},
}


class Job(NamedTuple):
    group: str
    method: str
    input_path: Path
    output_path: Path
    limit: int | None
    disable_neural: bool


def planned_jobs(groups: set[str]) -> list[Job]:
    jobs: list[Job] = []

    if "fair_subset" in groups:
        variants = [
            ("rgb", "rgb_noise060_front"),
            ("rgb", "rgb_noise060_back"),
            ("rgb", "rgb_noise060_random"),
            ("ramdocs", "ramdocs_noise060_front"),
        ]
        methods = ["naive_rag", "rerank_rag", "crag_lite", "self_rag_lite"]
        for dataset, variant in variants:
            for method in methods:
                jobs.append(
                    Job(
                        "fair_subset",
                        method,
                        Path("samples") / "controlled" / dataset / f"{variant}_input.json",
                        Path("outputs") / "fair_subset" / dataset / f"{method}_{variant}_output.json",
                        50,
                        True,
                    )
                )

    if "egi_full" in groups:
        for dataset in ["rgb", "ramdocs"]:
            jobs.append(
                Job(
                    "egi_full",
                    "egi_rag",
                    Path("samples") / f"{dataset}_all_input.json",
                    Path("outputs") / "egi_rag" / dataset / f"egi_rag_{dataset}_all_output.json",
                    None,
                    False,
                )
            )

    if "egi_controlled" in groups:
        variants = [
            ("rgb", "rgb_noise060_back"),
            ("rgb", "rgb_noise100_front"),
            ("ramdocs", "ramdocs_noise060_front"),
            ("ramdocs", "ramdocs_noise100_front"),
        ]
        methods = ["naive_rag", "rerank_rag", "crag_lite", "egi_rag"]
        for dataset, variant in variants:
            for method in methods:
                jobs.append(
                    Job(
                        "egi_controlled",
                        method,
                        Path("samples") / "controlled" / dataset / f"{variant}_input.json",
                        Path("outputs") / "egi_rag" / "controlled" / dataset / f"{method}_{variant}_output.json",
                        100,
                        True,
                    )
                )

    if "custom_noise" in groups:
        methods = ["naive_rag", "rerank_rag", "crag_lite", "egi_rag"]
        for method in methods:
            jobs.append(
                Job(
                    "custom_noise",
                    method,
                    Path("samples") / "custom_noise" / "custom_noise_all_input.json",
                    Path("outputs") / "custom_noise" / f"{method}_custom_noise_all_output.json",
                    None,
                    True,
                )
            )

    return jobs


def base_env(disable_neural: bool) -> dict[str, str]:
    env = os.environ.copy()
    hf_home = REPO_ROOT / ".hf_cache"
    env.setdefault("HF_HOME", str(hf_home))
    env.setdefault("HF_HUB_CACHE", str(hf_home / "hub"))
    env.setdefault("TRANSFORMERS_CACHE", str(hf_home / "hub"))
    env.setdefault("SENTENCE_TRANSFORMERS_HOME", str(hf_home / "models"))
    env.setdefault("RAG_EMBEDDING_MODEL", str(hf_home / "models" / "bge-m3"))
    env.setdefault("RAG_RERANKER_MODEL", str(hf_home / "models" / "bge-reranker-v2-m3"))
    if disable_neural:
        env["RAG_DISABLE_NEURAL_RETRIEVER"] = "1"
        env["RAG_DISABLE_NEURAL_RERANKER"] = "1"
    else:
        env.pop("RAG_DISABLE_NEURAL_RETRIEVER", None)
        env.pop("RAG_DISABLE_NEURAL_RERANKER", None)
    return env


def run_job(job: Job, python: str, dry_run: bool) -> int:
    if not job.input_path.exists():
        print(f"[SKIP] missing input: {job.input_path}")
        return 1

    job.output_path.parent.mkdir(parents=True, exist_ok=True)
    params = METHOD_PARAMS[job.method]
    command = [
        python,
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
        "1",
        "--resume",
    ]
    if job.limit is not None:
        command.extend(["--limit", str(job.limit)])
    if dry_run:
        command.append("--dry_run")

    print(f"[RUN] group={job.group} method={job.method} output={job.output_path}")
    env = base_env(job.disable_neural)
    if job.method == "egi_rag":
        env.setdefault("DASHSCOPE_MAX_TOKENS", "512")
    result = subprocess.run(command, cwd=REPO_ROOT, env=env)
    if result.returncode != 0:
        print(f"[FAIL] group={job.group} method={job.method} exit={result.returncode}")
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal completion experiments.")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument(
        "--groups",
        default="fair_subset,egi_full,egi_controlled,custom_noise",
        help="Comma-separated groups: fair_subset,egi_full,egi_controlled,custom_noise",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    groups = {group.strip() for group in args.groups.split(",") if group.strip()}
    allowed = {"fair_subset", "egi_full", "egi_controlled", "custom_noise"}
    unknown = groups - allowed
    if unknown:
        print(f"Unsupported groups: {sorted(unknown)}", file=sys.stderr)
        return 2

    failed = 0
    jobs = planned_jobs(groups)
    for job in jobs:
        failed += run_job(job, args.python, args.dry_run)
    print(f"[DONE] jobs={len(jobs)}, failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
