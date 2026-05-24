"""Helpers for parsing JSON objects from LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def extract_json_payload(text: str) -> Any:
    """Parse JSON from raw model output, tolerating markdown fences."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("empty model response")

    fence_match = JSON_BLOCK_RE.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise
