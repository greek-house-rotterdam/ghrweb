#!/usr/bin/env python3
"""
AI content review — checks content against the style guide using Gemini Flash.

Reads changed .md files, sends frontmatter + body to Gemini, and outputs
structured findings as JSON. The GitHub Action wrapper posts these as PR comments.

Requires: GEMINI_API_KEY environment variable.
"""

import json
import os
import re
import sys
from pathlib import Path

import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

STYLE_GUIDE = Path("docs/content-style-guide.md").read_text(encoding="utf-8")

_TONE_PATH = Path("docs/tone-and-voice-guidelines.md")
TONE_GUIDELINES = _TONE_PATH.read_text(encoding="utf-8") if _TONE_PATH.exists() else ""

SYSTEM_PROMPT = f"""You are a content reviewer for the Greek House in Rotterdam website.
Review the content below against the style guide AND the tone & voice guidelines. Report findings as a JSON array.

Each finding must have:
- "severity": "critical" | "major" | "minor"
- "field": which part of the content (e.g. "title", "description", "body", "frontmatter")
- "message": a clear, concise explanation of the issue and how to fix it

If the content is acceptable, return an empty array: []

Important:
- Be practical, not pedantic. Only flag real issues.
- Do NOT flag grammar or spelling — that's handled by translators.
- Do NOT flag content that is simply short — brevity is fine.
- DO flag harmful, discriminatory, political, or commercial content (critical).
- DO flag missing event details like date/time/location (major).
- DO flag tone issues — overly formal, distant, exclusionary, or shouty language (minor).
- The content may be in Greek, Dutch, or English. Apply the same rules regardless of language.

Return ONLY the JSON array, no other text.

---

STYLE GUIDE:

{STYLE_GUIDE}

---

TONE & VOICE GUIDELINES:

{TONE_GUIDELINES}
"""


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Split markdown into frontmatter dict and body."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    fm = {}
    for line in match.group(1).split("\n"):
        idx = line.find(":")
        if idx == -1:
            continue
        key = line[:idx].strip()
        val = line[idx + 1 :].strip().strip('"').strip("'")
        fm[key] = val

    return fm, match.group(2).strip()


ERROR_MESSAGE_MAX_LEN = 200


def review_content(file_path: str, content: str) -> tuple[list[dict], str | None]:
    """Send content to Gemini and return (findings, error).

    On success, returns the list of findings (possibly empty) and None.
    On failure, returns an empty list and a truncated error message — the
    workflow uses this to post a "review unavailable" PR comment so the
    failure is visible to editors without blocking the merge.
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set, skipping AI review", file=sys.stderr)
        return [], None

    fm, body = parse_frontmatter(content)

    user_prompt = f"""File: {file_path}

Frontmatter:
{json.dumps(fm, ensure_ascii=False, indent=2)}

Body:
{body}
"""

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
        ],
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=30,
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Gemini API {resp.status_code} ({GEMINI_MODEL}): {resp.text}"
            ) from e
        data = resp.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        findings = json.loads(text)

        if not isinstance(findings, list):
            return [], None
        return findings, None

    except Exception as e:
        message = str(e)
        if len(message) > ERROR_MESSAGE_MAX_LEN:
            message = message[:ERROR_MESSAGE_MAX_LEN] + "..."
        print(f"Warning: Gemini API error for {file_path}: {e}", file=sys.stderr)
        return [], message


def severity_emoji(severity: str) -> str:
    return {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(severity, "⚪")


def format_comment(file_path: str, findings: list[dict]) -> str:
    """Format findings as a markdown PR comment."""
    lines = [f"### Content Review: `{file_path}`\n"]

    for f in sorted(findings, key=lambda x: ["critical", "major", "minor"].index(x.get("severity", "minor"))):
        sev = f.get("severity", "minor")
        field = f.get("field", "unknown")
        msg = f.get("message", "")
        lines.append(f"- {severity_emoji(sev)} **{sev.upper()}** ({field}): {msg}")

    return "\n".join(lines)


def format_unavailable_comment(file_path: str, error: str) -> str:
    """Format a PR comment for files the AI reviewer could not process."""
    return (
        f"### Content Review: `{file_path}`\n"
        f"\n"
        f"\u26a0\ufe0f **Content review unavailable** \u2014 "
        f"the AI reviewer could not process this file. Merge is not blocked.\n"
        f"\n"
        f"Error: `{error}`"
    )


def main():
    files = sys.argv[1:]
    if not files:
        print("No files to review.")
        return

    output: list[dict] = []

    for file_path in files:
        path = Path(file_path)
        if not path.exists() or not path.suffix == ".md":
            continue

        content = path.read_text(encoding="utf-8")
        findings, error = review_content(file_path, content)

        if error:
            output.append(
                {
                    "file": file_path,
                    "findings": [],
                    "error": error,
                    "comment": format_unavailable_comment(file_path, error),
                }
            )
        elif findings:
            output.append(
                {
                    "file": file_path,
                    "findings": findings,
                    "error": None,
                    "comment": format_comment(file_path, findings),
                }
            )

    output_path = Path(os.environ.get("REVIEW_OUTPUT", "/tmp/content-review.json"))
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    total_findings = sum(len(f["findings"]) for f in output)
    critical = sum(
        1
        for f in output
        for finding in f["findings"]
        if finding.get("severity") == "critical"
    )
    errored = sum(1 for f in output if f.get("error"))

    print(
        f"Reviewed {len(files)} files. {total_findings} findings ({critical} critical), "
        f"{errored} unavailable."
    )

    if critical > 0:
        print("Critical findings detected — see PR comments.")
    if errored > 0:
        print("Some files could not be reviewed — see PR comments.")


if __name__ == "__main__":
    main()
