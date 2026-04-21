#!/usr/bin/env python3
"""Auto-translate content between Greek, Dutch, and English using DeepL API.

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

Requires DEEPL_API_KEY environment variable.
"""

import hashlib
import os
import re
import sys
from pathlib import Path

import deepl
import yaml

CONTENT_DIR = Path("src/content")

LANGUAGES = {
    "gr": {"deepl_source": "EL", "deepl_target": "EL"},
    "nl": {"deepl_source": "NL", "deepl_target": "NL"},
    "en": {"deepl_source": "EN", "deepl_target": "EN-US"},
}

TRANSLATABLE_FIELDS = {"title", "description"}


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


def get_targets(source_lang: str) -> dict[str, str]:
    """Return {lang: deepl_target_code} for all languages except the source."""
    return {
        lang: cfg["deepl_target"]
        for lang, cfg in LANGUAGES.items()
        if lang != source_lang
    }


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


def translate_text(
    translator: deepl.Translator, text: str, source_code: str, target_code: str
) -> str:
    """Translate a string via DeepL. Returns original if text is empty."""
    if not text or not text.strip():
        return text
    result = translator.translate_text(
        text, source_lang=source_code, target_lang=target_code
    )
    return result.text


def translate_file(translator: deepl.Translator, source_path: Path) -> None:
    """Translate a content file to all other languages.

    Skips translation when:
    - The source file is itself a translation (has source_hash in frontmatter)
    - The target file has translation_locked: true
    - The target file's source_hash matches the current source (nothing changed)
    """
    source_lang = get_source_lang(source_path)
    source_code = LANGUAGES[source_lang]["deepl_source"]
    targets = get_targets(source_lang)

    content = source_path.read_text(encoding="utf-8")
    frontmatter, body = parse_markdown(content)

    # Skip files that are themselves translations, not sources
    if "source_hash" in frontmatter:
        print(f"  Skipping (is a translation, not a source)")
        return

    current_hash = compute_source_hash(frontmatter, body)

    for lang, deepl_target in targets.items():
        target_path = Path(
            str(source_path).replace(f"/{source_lang}/", f"/{lang}/")
        )

        # Check if we should skip this target
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

        translated_fm = dict(frontmatter)

        for field in TRANSLATABLE_FIELDS:
            if field in translated_fm and translated_fm[field]:
                translated_fm[field] = translate_text(
                    translator, str(translated_fm[field]), source_code, deepl_target
                )

        translated_fm["lang"] = lang
        translated_fm["source_hash"] = current_hash

        translated_body = translate_text(translator, body, source_code, deepl_target)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            build_markdown(translated_fm, translated_body), encoding="utf-8"
        )
        print(f"  -> {target_path}")


def collect_all_content_files() -> list[Path]:
    """Find all content markdown files across all languages."""
    return sorted(CONTENT_DIR.glob("*/*/*.md"))


def main() -> None:
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        print("Error: DEEPL_API_KEY environment variable not set.")
        sys.exit(1)

    translator = deepl.Translator(api_key)

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
            translate_file(translator, filepath)
        except Exception as e:
            print(f"Error translating {filepath}: {e}")
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
