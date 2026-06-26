"""Run or inspect the controlled noise-ratio experiment matrix.

This runner is intentionally separate from the earlier member-B scripts: it can
extend the existing controlled outputs without overwriting successful rows, and
it includes EGI-RAG+ for the final paper's noise-ratio comparison.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[1]

METHOD_PARAMS = {
    "zero_shot": {"top_k": 0, "top_n": 0},
    "ordered_rag": {"top_k": 5, "top_n": 5},
    "naive_rag": {"top_k": 5, "top_n": 5},
    "rerank_rag": {"top_k": 8, "top_n": 5},
    "crag_lite": {"top_k": 8, "top_n": 5},
    "self_rag_lite": {"top_k": 8, "top_n": 5},
    "egi_rag": {"top_k": 8, "top_n": 5},
    "egi_rag_plus": {"top_k": 8, "top_n": 5},
}


class Job(NamedTuple):
    dataset: str
    ratio: int
    position: str
    method: str
    input_path: Path
    output_path: Path
    expected_rows: int
    existing_rows: int
    complete: bool


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_int_csv(value: str) -> list[int]:
    return [int(item) for item in parse_csv(value)]


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def count_successful_outputs(path: Path, method: str) -> int:
    rows = load_json_list(path)
    return sum(
        1
        for row in rows
        if isinstance(row, dict)
        and row.get("method") == method
        and not row.get("error")
        and not row.get("doc_judgements_parse_error")
    )


def build_jobs(args: argparse.Namespace) -> list[Job]:
    jobs: list[Job] = []
    methods = parse_csv(args.methods)
    unknown_methods = sorted(set(methods) - set(METHOD_PARAMS))
    if unknown_methods:
        raise ValueError(f"Unsupported methods: {unknown_methods}")

    for dataset in parse_csv(args.datasets):
        if dataset not in {"rgb", "ramdocs"}:
            raise ValueError(f"Unsupported dataset: {dataset}")
        for ratio in parse_int_csv(args.ratios):
            for position in parse_csv(args.positions):
                variant = f"{dataset}_noise{ratio:03d}_{position}"
                input_path = Path("samples") / "controlled" / dataset / f"{variant}_input.json"
                expected_rows = len(load_json_list(REPO_ROOT / input_path))
                if expected_rows == 0:
                    continue
                for method in methods:
                    output_path = Path(args.output_root) / dataset / f"{method}_{variant}_output.json"
                    existing_rows = count_successful_outputs(REPO_ROOT / output_path, method)
                    if args.limit is not None:
                        expected_for_run = min(expected_rows, max(args.limit, 0))
                    else:
                        expected_for_run = expected_rows
                    complete = existing_rows >= expected_for_run
                    jobs.append(
                        Job(
                            dataset=dataset,
                            ratio=ratio,
                            position=position,
                            method=method,
                            input_path=input_path,
                            output_path=output_path,
                            expected_rows=expected_for_run,
                            existing_rows=existing_rows,
                            complete=complete,
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
    return env


def write_plan(path: Path, jobs: Iterable[Job]) -> None:
    rows = list(jobs)
    pending = [job for job in rows if not job.complete]
    key_status = "set" if os.environ.get("DASHSCOPE_API_KEY") else "missing"
    lines = [
        "# Controlled Noise Completion Plan",
        "",
        f"- Total planned jobs: {len(rows)}",
        f"- Complete jobs: {len(rows) - len(pending)}",
        f"- Pending jobs: {len(pending)}",
        f"- DASHSCOPE_API_KEY: {key_status}",
        "",
        "## Run Commands",
        "",
        "Plan only:",
        "",
        "```powershell",
        "python scripts\\run_controlled_noise_completion.py --plan-only",
        "```",
        "",
        "Run the default EGI-RAG and EGI-RAG+ noise-ratio matrix with resume:",
        "",
        "```powershell",
        "$env:DASHSCOPE_API_KEY=\"你的百炼 API Key\"",
        "python scripts\\run_controlled_noise_completion.py --workers 1",
        "python scripts\\summarize_extended_experiments.py",
        "```",
        "",
        "If baseline RAMDocs 0/40/80 ratios are also needed, add baseline methods explicitly:",
        "",
        "```powershell",
        "python scripts\\run_controlled_noise_completion.py `",
        "  --methods zero_shot,ordered_rag,naive_rag,rerank_rag,crag_lite,self_rag_lite `",
        "  --datasets ramdocs --ratios 0,40,80 --positions front",
        "```",
        "",
        "## Pending Jobs",
        "",
        "| Dataset | Noise | Position | Method | Existing | Expected | Output |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for job in pending:
        lines.append(
            "| {dataset} | {ratio}% | {position} | {method} | {existing} | {expected} | `{output}` |".format(
                dataset=job.dataset,
                ratio=job.ratio,
                position=job.position,
                method=job.method,
                existing=job.existing_rows,
                expected=job.expected_rows,
                output=job.output_path.as_posix(),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_job(job: Job, args: argparse.Namespace) -> int:
    if job.complete and not args.force:
        print(
            f"[SKIP] complete method={job.method} dataset={job.dataset} "
            f"noise={job.ratio:03d} position={job.position}"
        )
        return 0

    params = METHOD_PARAMS[job.method]
    output_path = REPO_ROOT / job.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
        "--resume",
    ]
    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.dry_run:
        command.append("--dry_run")

    print(
        f"[RUN] method={job.method} dataset={job.dataset} "
        f"noise={job.ratio:03d} position={job.position}"
    )
    env = base_env(args.disable_neural)
    if job.method in {"egi_rag", "egi_rag_plus"}:
        env.setdefault("DASHSCOPE_MAX_TOKENS", "512")
    result = subprocess.run(command, cwd=REPO_ROOT, env=env)
    if result.returncode != 0:
        print(f"[FAIL] method={job.method} output={job.output_path} exit={result.returncode}")
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Complete controlled noise-ratio experiments.")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--datasets", default="rgb,ramdocs")
    parser.add_argument("--ratios", default="0,20,40,60,80,100")
    parser.add_argument("--positions", default="front")
    parser.add_argument(
        "--methods",
        default="egi_rag,egi_rag_plus",
        help="Comma-separated methods. Add baseline methods if they need reruns.",
    )
    parser.add_argument("--output-root", default="outputs/egi_rag/controlled")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--disable-neural", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument(
        "--plan-path",
        default="reports/controlled_noise_completion_plan.md",
        help="Where to write the pending-job plan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        jobs = build_jobs(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    write_plan(REPO_ROOT / args.plan_path, jobs)
    pending = [job for job in jobs if not job.complete]
    print(
        f"[PLAN] jobs={len(jobs)} complete={len(jobs) - len(pending)} "
        f"pending={len(pending)} plan={args.plan_path}"
    )
    if args.plan_only:
        return 0
    if not args.dry_run and not os.environ.get("DASHSCOPE_API_KEY"):
        print("Missing DASHSCOPE_API_KEY; use --dry-run for prompt checks or set the key before running.", file=sys.stderr)
        return 3

    failed = 0
    for job in jobs:
        failed += run_job(job, args)
    print(f"[DONE] jobs={len(jobs)} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
