"""Qwen/DashScope client wrapper using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import time


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_MODEL = "qwen-turbo"
MISSING_KEY_MESSAGE = "请设置 DASHSCOPE_API_KEY 或填写本地配置"


class MissingAPIKeyError(RuntimeError):
    """Raised when the client is called without an API key."""


@dataclass(frozen=True)
class QwenConfig:
    provider: str = "qwen"
    api_key: str = ""
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout: int = 180
    max_retries: int = 2


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _read_simple_yaml(path: Path) -> dict[str, str]:
    """Read the flat key/value YAML used by this project without PyYAML."""
    if not path.exists():
        return {}

    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        result[key.strip()] = _strip_quotes(value.strip())
    return result


def load_qwen_config(config_path: str | Path = "configs/model_config.example.yaml") -> QwenConfig:
    """Load config, with environment variables taking priority for secrets."""
    raw = _read_simple_yaml(Path(config_path))

    api_key = os.getenv("DASHSCOPE_API_KEY") or raw.get("api_key", "")
    model = os.getenv("DASHSCOPE_MODEL") or raw.get("model") or DEFAULT_MODEL
    base_url = os.getenv("DASHSCOPE_BASE_URL") or raw.get("base_url") or DEFAULT_BASE_URL

    return QwenConfig(
        provider=raw.get("provider") or "qwen",
        api_key=api_key,
        model=model,
        base_url=base_url,
    )


class QwenClient:
    def __init__(self, config: QwenConfig | None = None):
        self.config = config or load_qwen_config()

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        if not self.config.api_key:
            raise MissingAPIKeyError(MISSING_KEY_MESSAGE)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            self.config.base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                    body = response.read().decode("utf-8")
                break
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                if 400 <= exc.code < 500 and exc.code != 429:
                    raise RuntimeError(f"Qwen API HTTP {exc.code}: {error_body}") from exc
                last_error = RuntimeError(f"Qwen API HTTP {exc.code}: {error_body}")
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc

            if attempt < self.config.max_retries:
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"Qwen API request failed after retries: {last_error}") from last_error

        data = json.loads(body)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Qwen API response: {body}") from exc
