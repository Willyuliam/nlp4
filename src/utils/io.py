"""JSON I/O and sample validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    ensure_parent_dir(target)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def validate_samples(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise ValueError("input JSON must be an array")

    samples: list[dict[str, Any]] = []
    for index, item in enumerate(data, 1):
        if not isinstance(item, dict):
            raise ValueError(f"sample #{index} must be an object")
        if "id" not in item:
            raise ValueError(f"sample #{index} missing required field: id")
        if not str(item.get("question", "")).strip():
            raise ValueError(f"sample #{index} missing required field: question")
        if "contexts" not in item and "context" not in item:
            raise ValueError(f"sample #{index} missing required field: contexts")
        samples.append(item)
    return samples
