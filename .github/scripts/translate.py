#!/usr/bin/env python3
"""Auto-translate content between Greek, Dutch, and English using Gemini Flash.

Detects the source language from the file path and translates to the other two.
Works with Decap CMS collections that write to src/content/{collection}/{lang}/.

Translated files receive a `source_hash` frontmatter field — a fingerprint of the
source content they were derived from. On subsequent runs, the hash is compared:
if the source hasn't changed, translation is skipped, preserving any manual edits
made by reviewers. Files with `translation_locked: true` in frontmatter are never
overwritten, even when the source changes.

Files that already contain `source_hash` are recognized as translations (not sources)
and are skipped when passed as input, preventing cascade translation.

Usage:
    # Translate specific files (used by GitHub Actions workflow)
    python translate.py src/content/news/gr/welcome.md
    python translate.py src/content/events/nl/sample-event.md

    # Translate all content files
    python translate.py --all

Requires GEMINI_API_KEY environment variable.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

import requests
import yaml

CONTENT_DIR = Path("src/content")
GUIDELINES_PATH = Path("docs/tone-and-voice-guidelines.md")

GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

LANGUAGES = {
    "gr": "Greek",
    "nl": "Dutch",
    "en": "English",
}

TRANSLATABLE_FIELDS = {"title", "description"}


def load_guidelines() -> str:
    """Read the tone & voice guidelines. Returns empty string if not present."""
    if GUIDELINES_PATH.exists():
        return GUIDELINES_PATH.read_text(encoding="utf-8")
    return ""


def build_system_prompt(source_lang: str, target_lang: str, guidelines: str) -> str:
    """System prompt for Gemini — includes website context and tone/voice rules."""
    return f"""You translate content for the website of the Greek House in Rotterdam (Ένωση Ελλήνων Ολλανδίας / Το Ελληνικό Σπίτι στο Ρότερνταμ) — a Greek cultural association in the Netherlands.

Translate from {source_lang} to {target_lang}, following the tone and voice guidelines below.

Translation rules:
- Preserve markdown formatting in the body: headings (#), lists, links, emphasis, code blocks, line breaks.
- Translate naturally, not word-for-word. Adapt idioms when they would not carry over.
- Keep emojis, URLs, hashtags, dates, times, prices, and proper names unchanged.
- Match the warmth and approachability of the source — do not make it more formal.
- For Dutch/English: avoid sounding like a literal translation from Greek.

Return ONLY a JSON object with this exact shape (omit any field that is missing or empty in the source):
{{"title": "...", "description": "...", "body": "..."}}

---

TONE & VOICE GUIDELINES:

{guidelines}
"""


def compute_source_hash(frontmatter: dict, body: str) -> str:
    """Compute a hash of the translatable content from a source file.

    Used to detect whether the source has changed since the last translation,
    so that manual edits to translated files are not overwritten.
    """
    parts = []
    for field in sorted(TRANSLATABLE_FIELDS):
        if field in frontmatter and frontmatter[field]:
            parts.append(f"{field}:{frontmatter[field]}")
    parts.append(f"body:{body}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def get_source_lang(filepath: Path) -> str:
    """Extract language code from file path (e.g. src/content/news/gr/welcome.md -> gr)."""
    for part in filepath.parts:
        if part in LANGUAGES:
            return part
    raise ValueError(f"No known language in path: {filepath}")


def get_target_langs(source_lang: str) -> list[str]:
    """Return the two language codes that are NOT the source."""
    return [lang for lang in LANGUAGES if lang != source_lang]


def parse_markdown(text: str) -> tuple[dict, str]:
    """Split markdown into frontmatter dict and body string."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        raise ValueError("No valid YAML frontmatter found")
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2).strip()
    return frontmatter, body


def build_markdown(frontmatter: dict, body: str) -> str:
    """Reconstruct markdown file from frontmatter and body."""
    fm_yaml = yaml.dump(
        frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return f"---\n{fm_yaml}---\n\n{body}\n"


def translate_payload(
    api_key: str,
    source_lang: str,
    target_lang: str,
    payload: dict[str, str],
    guidelines: str,
) -> dict[str, str]:
    """Send the translatable fields to Gemini in one call, return translated fields.

    `payload` keys are field names (title, description, body); values are source text.
    Empty values are kept empty without calling the API.
    """
    non_empty = {k: v for k, v in payload.items() if v and v.strip()}
    if not non_empty:
        return {k: v for k, v in payload.items()}

    source_name = LANGUAGES[source_lang]
    target_name = LANGUAGES[target_lang]

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Source language: {source_name}\n"
                            f"Target language: {target_name}\n\n"
                            f"Source content (JSON):\n"
                            f"{json.dumps(non_empty, ensure_ascii=False, indent=2)}"
                        )
                    }
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": build_system_prompt(source_name, target_name, guidelines)}
            ]
        },
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    resp = requests.post(
        GEMINI_URL,
        params={"key": api_key},
        json=body,
        timeout=60,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(
            f"Gemini API {resp.status_code} ({GEMINI_MODEL}): {resp.text}"
        ) from e
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    translated = json.loads(text)

    # Preserve empty fields from the original payload
    result = {k: v for k, v in payload.items()}
    for k, v in translated.items():
        if k in result and isinstance(v, str):
            result[k] = v
    return result


def translate_file(api_key: str, source_path: Path, guidelines: str) -> None:
    """Translate a content file to all other languages.

    Skips translation when:
    - The source file is itself a translation (has source_hash in frontmatter)
    - The target file has translation_locked: true
    - The target file's source_hash matches the current source (nothing changed)
    """
    source_lang = get_source_lang(source_path)
    target_langs = get_target_langs(source_lang)

    content = source_path.read_text(encoding="utf-8")
    frontmatter, body = parse_markdown(content)

    if "source_hash" in frontmatter:
        print("  Skipping (is a translation, not a source)")
        return

    current_hash = compute_source_hash(frontmatter, body)

    for target_lang in target_langs:
        target_path = Path(
            str(source_path).replace(f"/{source_lang}/", f"/{target_lang}/")
        )

        if target_path.exists():
            existing_content = target_path.read_text(encoding="utf-8")
            try:
                existing_fm, _ = parse_markdown(existing_content)
                if existing_fm.get("translation_locked"):
                    print(f"  -- {target_path} (locked, skipping)")
                    continue
                if existing_fm.get("source_hash") == current_hash:
                    print(f"  -- {target_path} (source unchanged, skipping)")
                    continue
            except ValueError:
                pass  # Can't parse existing file, retranslate it

        # Build the payload for one Gemini call
        source_payload = {
            field: str(frontmatter[field])
            for field in TRANSLATABLE_FIELDS
            if field in frontmatter and frontmatter[field]
        }
        source_payload["body"] = body

        translated = translate_payload(
            api_key, source_lang, target_lang, source_payload, guidelines
        )

        translated_fm = dict(frontmatter)
        for field in TRANSLATABLE_FIELDS:
            if field in translated and field in translated_fm:
                translated_fm[field] = translated[field]

        translated_fm["lang"] = target_lang
        translated_fm["source_hash"] = current_hash

        translated_body = translated.get("body", body)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            build_markdown(translated_fm, translated_body), encoding="utf-8"
        )
        print(f"  -> {target_path}")


def collect_all_content_files() -> list[Path]:
    """Find all content markdown files across all languages."""
    return sorted(CONTENT_DIR.glob("*/*/*.md"))


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    guidelines = load_guidelines()
    if not guidelines:
        print(
            f"Warning: {GUIDELINES_PATH} not found — translating without tone/voice context.",
            file=sys.stderr,
        )

    if "--all" in sys.argv:
        files = collect_all_content_files()
        if not files:
            print("No content files found.")
            return
        print(f"Translating all {len(files)} content file(s)...")
    else:
        paths = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
        files = [Path(p) for p in paths]

    if not files:
        print("No files to translate.")
        return

    for filepath in files:
        if not filepath.exists():
            print(f"Skipping (not found): {filepath}")
            continue
        print(f"Translating: {filepath} ({get_source_lang(filepath)})")
        try:
            translate_file(api_key, filepath, guidelines)
        except Exception as e:
            print(f"Error translating {filepath}: {e}")
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
