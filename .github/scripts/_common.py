"""Shared utilities for the content-automation scripts.

Three things live here so the individual scripts don't redefine them:

  - LANGUAGES:        the set of supported language codes, keyed by code, value is the display name
  - parse_markdown / build_markdown: YAML-frontmatter codec used across translate/review/etc.
  - GeminiClient:     one-call wrapper around the Gemini REST API, with retry on
                      transient failures (network errors and 5xx). 4xx responses
                      and JSON-decode errors are surfaced immediately — they are
                      not retryable.

Tests in .github/scripts/tests/ patch `RETRY_BACKOFF_BASE` to 0 so retry paths
do not slow the suite.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
import yaml

LANGUAGES: dict[str, str] = {
    "gr": "Greek",
    "nl": "Dutch",
    "en": "English",
}

GEMINI_MODEL_DEFAULT = "gemini-3-flash-preview"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0


def parse_markdown(text: str) -> tuple[dict[str, Any], str]:
    """Split markdown into (frontmatter dict, body string).

    Raises ValueError if the document has no `---\\n…\\n---` block. Body
    whitespace is stripped (matches existing translate.py behavior).
    """
    if not text.startswith("---\n"):
        raise ValueError("No valid YAML frontmatter found")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("No valid YAML frontmatter found")
    fm_yaml = text[4:end]
    body = text[end + 5 :]
    frontmatter = yaml.safe_load(fm_yaml) or {}
    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter is not a mapping")
    return frontmatter, body.strip()


def build_markdown(frontmatter: dict[str, Any], body: str) -> str:
    """Reconstruct a markdown file from frontmatter + body."""
    fm_yaml = yaml.dump(
        frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return f"---\n{fm_yaml}---\n\n{body}\n"


class GeminiClient:
    """Thin client for Gemini's generateContent endpoint.

    Retries on connection errors, timeouts, and 5xx responses up to
    MAX_RETRIES times with exponential backoff. 4xx responses raise
    immediately (auth / model / quota failures are not retryable).
    """

    def __init__(self, api_key: str, *, model: str | None = None):
        self.api_key = api_key
        self.model = model or os.environ.get("GEMINI_MODEL", GEMINI_MODEL_DEFAULT)
        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

    def generate(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
        temperature: float = 0.2,
        timeout: int = 60,
        safety_settings: list[dict] | None = None,
    ) -> str:
        """Call the model and return the raw text from the first candidate.

        On HTTP failure raises RuntimeError with the status and body so the
        caller can surface it to the user (PR comment, CI log, etc.).
        """
        body: dict[str, Any] = {
            "contents": [{"parts": [{"text": user}]}],
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {"temperature": temperature},
        }
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"
        if safety_settings:
            body["safetySettings"] = safety_settings

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.post(
                    self.url,
                    params={"key": self.api_key},
                    json=body,
                    timeout=timeout,
                )
            except (requests.ConnectionError, requests.Timeout):
                if attempt + 1 >= MAX_RETRIES:
                    raise
                time.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                continue

            try:
                resp.raise_for_status()
            except requests.HTTPError as e:
                status = getattr(resp, "status_code", 0)
                if status >= 500 and attempt + 1 < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                    continue
                raise RuntimeError(
                    f"Gemini API {status} ({self.model}): {resp.text}"
                ) from e

            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        raise RuntimeError(f"Gemini API call failed after {MAX_RETRIES} attempts")
