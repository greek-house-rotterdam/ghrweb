#!/usr/bin/env python3
"""
AI content review — checks content against the style guide using Gemini Flash.

Reads changed .md files, sends frontmatter + body to Gemini, and outputs
structured findings as JSON. The GitHub Action wrapper posts these as PR comments.

Requires: GEMINI_API_KEY environment variable.
"""

import json
import os
import sys
from pathlib import Path

import requests  # re-exported for tests that patch content_review.requests.post

from _common import GeminiClient, parse_markdown

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

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

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Forgiving wrapper around the shared YAML parser.

    Content review should never crash on malformed input — fall back to
    empty frontmatter so the reviewer can still look at the body.
    """
    try:
        return parse_markdown(content)
    except ValueError:
        return {}, content


# Per-collection schema hints fed to the reviewer so it doesn't flag missing
# fields that don't exist in the collection (e.g. complaining that a
# history-milestones entry has no `description` — it shouldn't).
# Keys are the collection folder names under src/content/.
COLLECTION_FIELDS: dict[str, dict[str, list[str]]] = {
    "news": {
        "required": ["title", "description", "date", "lang"],
        "optional": ["image"],
        "has_body": True,
    },
    "activities": {
        "required": ["title", "description", "lang"],
        "optional": ["image", "emoji", "schedule", "order"],
        "has_body": True,
    },
    "resources": {
        "required": ["title", "description", "category", "lang"],
        "optional": ["order"],
        "has_body": True,
    },
    "faq": {
        "required": ["question", "answer", "lang"],
        "optional": ["order"],
        "has_body": False,
    },
    "event-translations": {
        "required": ["tt_event_id", "title", "description", "lang"],
        "optional": [],
        "has_body": True,
    },
    "history-sections": {
        "required": ["title", "lang"],
        "optional": ["order"],
        "has_body": True,
    },
    "about-sections": {
        "required": ["title", "lang"],
        "optional": ["order"],
        "has_body": True,
    },
    "history-milestones": {
        "required": ["year", "title", "lang"],
        "optional": ["linkedSection"],
        "has_body": False,
    },
}


def infer_collection(file_path: str) -> str | None:
    """Path is src/content/<collection>/<lang>/<slug>.md."""
    parts = Path(file_path).parts
    try:
        i = parts.index("content")
    except ValueError:
        return None
    return parts[i + 1] if i + 1 < len(parts) else None


def schema_hint(collection: str | None) -> str:
    if collection is None or collection not in COLLECTION_FIELDS:
        return ""
    s = COLLECTION_FIELDS[collection]
    req = ", ".join(s["required"]) or "(none)"
    opt = ", ".join(s["optional"]) or "(none)"
    body_note = (
        "This collection HAS a markdown body."
        if s["has_body"]
        else "This collection has NO markdown body (the schema renders only frontmatter)."
    )
    return (
        f"\n\nCollection: {collection}. "
        f"Required frontmatter fields: {req}. "
        f"Optional frontmatter fields: {opt}. "
        f"{body_note} "
        f"Do NOT flag the absence of any field not listed above — those fields "
        f"do not exist in this collection's schema."
    )


ERROR_MESSAGE_MAX_LEN = 200


def review_content(file_path: str, content: str) -> tuple[list[dict], str | None]:
    """Send content to Gemini and return (findings, error).

    On success, returns the list of findings (possibly empty) and None.
    On failure, returns an empty list and a truncated error message — the
    workflow uses this to post a "review unavailable" PR comment so the
    failure is visible to editors without blocking the merge.

    A missing API key is a failure too: in CI it means the secret is gone,
    and treating it as "no findings" would show a green check for a review
    that never ran.
    """
    if not GEMINI_API_KEY:
        return [], "GEMINI_API_KEY is not set"

    fm, body = parse_frontmatter(content)
    hint = schema_hint(infer_collection(file_path))

    user_prompt = f"""File: {file_path}{hint}

Frontmatter:
{json.dumps(fm, ensure_ascii=False, indent=2, default=str)}

Body:
{body}
"""

    try:
        text = GeminiClient(GEMINI_API_KEY).generate(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            json_mode=True,
            temperature=0.1,
            timeout=30,
            safety_settings=SAFETY_SETTINGS,
        )
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


def comment_marker(file_path: str) -> str:
    """Hidden marker embedded in every comment for this file.

    The workflow's posting step looks for this marker on existing PR
    comments and deletes them before posting a new one, so re-running CI
    on the same PR doesn't pile up duplicate review comments.
    """
    return f"<!-- content-review:{file_path} -->"


def format_comment(file_path: str, findings: list[dict]) -> str:
    """Format findings as a markdown PR comment."""
    lines = [comment_marker(file_path), f"### Content Review: `{file_path}`\n"]

    for f in sorted(findings, key=lambda x: ["critical", "major", "minor"].index(x.get("severity", "minor"))):
        sev = f.get("severity", "minor")
        field = f.get("field", "unknown")
        msg = f.get("message", "")
        lines.append(f"- {severity_emoji(sev)} **{sev.upper()}** ({field}): {msg}")

    return "\n".join(lines)


def format_unavailable_comment(file_path: str, error: str) -> str:
    """Format a PR comment for files the AI reviewer could not process."""
    return (
        f"{comment_marker(file_path)}\n"
        f"### Content Review: `{file_path}`\n"
        f"\n"
        f"⚠️ **Content review unavailable** — "
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
        # Fail the check so a review that didn't run is never green. The
        # check is not required, so this flags the problem without blocking.
        print("Some files could not be reviewed — see PR comments.")
        sys.exit(1)


if __name__ == "__main__":
    main()
