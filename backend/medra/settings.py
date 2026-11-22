"""Backend configuration from the environment (and .env in local runs).

The DeepSeek key is read here and only passed to the DeepSeek source: it is
never logged, never sent to the dashboard, and never written to a file. On
Hugging Face it comes from the Space's secrets instead of .env.

    DEEPSEEK_API_KEY       enables the live DeepSeek source
    MEDRA_DEEPSEEK_MODEL   default deepseek-flash (thinking mode on by default)
    MEDRA_MAX_TOKENS       cap on generated tokens (reasoning + answer) per request
    MEDRA_LIVE_DISABLED    "1" = kill switch: refuse live sessions, keep replay/paste
    MEDRA_OLLAMA_URL       local Ollama server, default http://127.0.0.1:11434; set it empty to
                           leave Ollama out of the menu (the deployed Space has none)
    MEDRA_OLLAMA_MODEL     default deepseek-r1:8b
    MEDRA_ACCESS_CODES     "code:n,code:n" = live sessions need a code, n per day (access.py);
                           unset = no code asked for (local runs)
    MEDRA_ALLOWED_ORIGINS  comma-separated origins allowed to call the API from a browser
                           (the GitHub Pages site); unset = same origin only
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from medra.access import parse_codes

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str | None
    deepseek_model: str
    deepseek_url: str
    max_tokens: int
    live_disabled: bool
    ollama_url: str
    ollama_model: str
    access_codes: dict[str, int] = field(default_factory=dict)
    allowed_origins: list[str] = field(default_factory=list)

    def __repr__(self) -> str:  # never show the key or the codes, even in a traceback or debugger
        return (
            f"Settings(deepseek={'set' if self.deepseek_api_key else 'unset'}, model={self.deepseek_model!r}, "
            f"access_codes={len(self.access_codes)})"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # .env is optional and never overrides variables that are already set.
    load_dotenv(_REPO_ROOT / ".env", override=False)
    return Settings(
        deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY") or None,
        deepseek_model=os.environ.get("MEDRA_DEEPSEEK_MODEL", "deepseek-flash"),
        deepseek_url=os.environ.get("MEDRA_DEEPSEEK_URL", "https://api.deepseek.com"),
        max_tokens=int(os.environ.get("MEDRA_MAX_TOKENS", "8192")),
        live_disabled=os.environ.get("MEDRA_LIVE_DISABLED", "") == "1",
        ollama_url=os.environ.get("MEDRA_OLLAMA_URL", "http://127.0.0.1:11434"),
        ollama_model=os.environ.get("MEDRA_OLLAMA_MODEL", "deepseek-r1:8b"),
        access_codes=parse_codes(os.environ.get("MEDRA_ACCESS_CODES", "")),
        allowed_origins=[o.strip() for o in os.environ.get("MEDRA_ALLOWED_ORIGINS", "").split(",") if o.strip()],
    )
