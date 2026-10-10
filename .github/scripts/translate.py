#!/usr/bin/env python3
"""Auto-translate content between Greek, Dutch, and English using Gemini Flash.

Detects the source language from the file path and translates to the other two.
Works with Decap CMS collections that write to src/content/{collection}/{lang}/.

Translated files receive a `source_hash` frontmatter field — a fingerprint of the
source content they were derived from. On subsequent runs, the hash is compared:
if the source hasn't changed, translation is skipped, preserving any manual edits
made by reviewers. Files with `translation_locked: true` in frontmatter are never
overwritten, even when the source changes. A target with neither `source_hash` nor
the lock was written by hand: the job fails instead of overwriting it.

Besides `source_hash`, the bot stores `translation_hash`: the same hash over the
translation's own text, as the bot wrote it. If a target's current text no longer
matches it, someone corrected it by hand. When the Greek then changes, that
translation is kept (not re-translated), its `source_hash` is brought up to date
so it is flagged once, and it is listed in the file named by $KEPT_REPORT for the
PR status comment. A target without `translation_hash` is re-translated as before; remove
the field (or delete the file) to hand a translation back to the bot.

On every run each existing target also gets the source's shared fields (image,
date, order, ...), locked or not, without an API call.

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
import sys
from pathlib import Path

import requests  # re-exported for tests that patch translate.requests.post

from _common import LANGUAGES, GeminiClient, _QuotedStr, build_markdown, parse_markdown

CONTENT_DIR = Path("src/content")
GUIDELINES_PATH = Path("docs/tone-and-voice-guidelines.md")

# Frontmatter fields holding text to translate, besides the body. FAQ entries
# keep their text in question/answer and have an empty body. Everything else
# (date, order, image, emoji, category, …) is copied from the source as is.
TRANSLATABLE_FIELDS = {"title", "description", "question", "answer", "schedule"}

# Frontmatter keys a translation owns. Every other key of the source is a shared
# field and is kept equal to the source on every run (see sync_shared_fields).
TRANSLATION_OWN_FIELDS = TRANSLATABLE_FIELDS | {
    "lang",
    "source_hash",
    "translation_hash",
    "translation_locked",
}


class HandWrittenTargetError(Exception):
    """A target file has no source_hash and isn't locked: a human wrote it."""


class NonGreekSourceError(Exception):
    """A Dutch or English file without source_hash was passed as a source."""


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

Return ONLY a JSON object with exactly the keys of the source content JSON, each value translated. For example:
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


def is_hand_edited(frontmatter: dict, body: str) -> bool:
    """True when a translation's text differs from what the bot wrote.

    Needs `translation_hash`; without it the history is unknown, so the file
    counts as not hand-edited.
    """
    recorded = frontmatter.get("translation_hash")
    if not recorded:
        return False
    return compute_source_hash(frontmatter, body) != str(recorded)


def get_source_lang(filepath: Path) -> str:
    """Extract language code from file path (e.g. src/content/news/gr/welcome.md -> gr)."""
    for part in filepath.parts:
        if part in LANGUAGES:
            return part
    raise ValueError(f"No known language in path: {filepath}")


def get_target_langs(source_lang: str) -> list[str]:
    """Return the two language codes that are NOT the source."""
    return [lang for lang in LANGUAGES if lang != source_lang]


def translate_payload(
    api_key: str,
    source_lang: str,
    target_lang: str,
    payload: dict[str, str],
    guidelines: str,
) -> dict[str, str]:
    """Send the translatable fields to Gemini in one call, return translated fields.

    `payload` keys are field names (TRANSLATABLE_FIELDS and body); values are source text.
    Empty values are kept empty without calling the API.
    """
    non_empty = {k: v for k, v in payload.items() if v and v.strip()}
    if not non_empty:
        return {k: v for k, v in payload.items()}

    source_name = LANGUAGES[source_lang]
    target_name = LANGUAGES[target_lang]

    user_text = (
        f"Source language: {source_name}\n"
        f"Target language: {target_name}\n\n"
        f"Source content (JSON):\n"
        f"{json.dumps(non_empty, ensure_ascii=False, indent=2)}"
    )
    system_text = build_system_prompt(source_name, target_name, guidelines)

    text = GeminiClient(api_key).generate(
        system=system_text,
        user=user_text,
        json_mode=True,
        timeout=60,
    )
    translated = json.loads(text)

    # Preserve empty fields from the original payload
    result = {k: v for k, v in payload.items()}
    for k, v in translated.items():
        if k in result and isinstance(v, str):
            result[k] = v
    return result


def sync_shared_fields(source_fm: dict, target_fm: dict) -> dict:
    """Return target_fm with its shared fields made equal to the source's.

    Shared fields are all source keys except TRANSLATION_OWN_FIELDS. Existing
    keys keep their position, new ones are appended, and shared keys the source
    no longer has are removed. The translation's own fields are never touched.
    """
    shared = {k: v for k, v in source_fm.items() if k not in TRANSLATION_OWN_FIELDS}
    synced = {}
    for k, v in target_fm.items():
        if k in TRANSLATION_OWN_FIELDS:
            synced[k] = v
        elif k in shared:
            synced[k] = shared[k]
        # else: the source dropped this shared field, so drop it here too
    for k, v in shared.items():
        if k not in synced:
            synced[k] = v
    return synced


def _quote_hashes(frontmatter: dict) -> dict:
    """Force quoting of translation_hash (a hex string like 780186204e18 can
    otherwise be read back as a number). source_hash is quoted by _common."""
    fm = dict(frontmatter)
    if isinstance(fm.get("translation_hash"), str):
        fm["translation_hash"] = _QuotedStr(fm["translation_hash"])
    return fm


def translate_file(
    api_key: str, source_path: Path, guidelines: str
) -> list[tuple[Path, str]]:
    """Translate a content file to all other languages.

    Returns the targets kept because they were corrected by hand, as
    (path, label) pairs; the label is the Greek title or question.

    Skips translation when:
    - The source file is itself a translation (has source_hash in frontmatter)
    - The target file has translation_locked: true
    - The target file's source_hash matches the current source (nothing changed)
    - The Greek changed, but the target was corrected by hand (its text no longer
      matches its translation_hash). It is kept, and its source_hash is updated.

    Skipped or not, every existing target gets the source's shared fields (image,
    date, order, ...) so they never drift. That needs no API call, and it also
    applies to locked targets: the lock protects the text, not the image.

    Raises HandWrittenTargetError, before writing anything, when a target exists,
    isn't locked and has no source_hash: it was written by hand, and translating
    would overwrite it.

    Raises NonGreekSourceError for a Dutch or English file without source_hash
    that isn't locked: entries are written in Greek. A locked one is a
    hand-written translation and is skipped.
    """
    source_lang = get_source_lang(source_path)
    target_langs = get_target_langs(source_lang)

    content = source_path.read_text(encoding="utf-8")
    frontmatter, body = parse_markdown(content)

    kept: list[tuple[Path, str]] = []

    if "source_hash" in frontmatter:
        print("  Skipping (is a translation, not a source)")
        return kept

    if source_lang != "gr":
        if frontmatter.get("translation_locked"):
            print("  Skipping (a locked, hand-written translation)")
            return kept
        raise NonGreekSourceError(
            f"{source_path} is a {LANGUAGES[source_lang]} file without source_hash, "
            f"so it looks like a source, but entries are written in Greek. Create "
            f"the entry in the Greek collection instead (src/content/.../gr/), and "
            f"the {LANGUAGES[source_lang]} version is generated from it. To keep "
            f"this file as a hand-written translation, ask the admin to add "
            f"`translation_locked: true` to its frontmatter."
        )

    label = str(frontmatter.get("title") or frontmatter.get("question") or "")

    current_hash = compute_source_hash(frontmatter, body)

    # Check every target first, so a hand-written one stops the run before
    # anything is written for this source.
    plan = []  # (target_lang, target_path, existing_fm or None, up_to_date)
    for target_lang in target_langs:
        target_path = Path(
            str(source_path).replace(f"/{source_lang}/", f"/{target_lang}/")
        )
        existing_fm = existing_body = None
        up_to_date = False
        keep = False
        if target_path.exists():
            try:
                existing_fm, existing_body = parse_markdown(
                    target_path.read_text(encoding="utf-8")
                )
            except ValueError:
                pass  # Can't parse existing file, retranslate it
            else:
                if existing_fm.get("translation_locked"):
                    up_to_date = True
                elif "source_hash" not in existing_fm:
                    raise HandWrittenTargetError(
                        f"{target_path} was written by hand (it has no source_hash) "
                        f"and is not locked, so translating {source_path} would "
                        f"overwrite it. To keep it as it is, add "
                        f"`translation_locked: true` to its frontmatter. To let it "
                        f"be regenerated from the Greek, delete the file or add "
                        f"`source_hash: '{current_hash}'` to it."
                    )
                elif existing_fm.get("source_hash") == current_hash:
                    up_to_date = True
                elif is_hand_edited(existing_fm, existing_body):
                    keep = True
        plan.append(
            (target_lang, target_path, existing_fm, existing_body, up_to_date, keep)
        )

    for target_lang, target_path, existing_fm, existing_body, up_to_date, keep in plan:
        if keep:
            # Greek changed, but a human corrected this translation: keep the
            # text. source_hash moves to the current one so it is flagged once;
            # translation_hash stays, so the file still counts as hand-edited.
            synced_fm = sync_shared_fields(frontmatter, existing_fm)
            synced_fm["source_hash"] = current_hash
            target_path.write_text(
                build_markdown(_quote_hashes(synced_fm), existing_body),
                encoding="utf-8",
            )
            print(
                f"::warning title=Kept a hand-corrected translation::{target_path} "
                f"was corrected by hand, so it was not re-translated although "
                f"{source_path} changed. Check it."
            )
            kept.append((target_path, label))
            continue

        if up_to_date:
            synced_fm = sync_shared_fields(frontmatter, existing_fm)
            if synced_fm != existing_fm:
                target_path.write_text(
                    build_markdown(_quote_hashes(synced_fm), existing_body),
                    encoding="utf-8",
                )
                print(f"  ~~ {target_path} (shared fields synced)")
            elif existing_fm.get("translation_locked"):
                print(f"  -- {target_path} (locked, skipping)")
            else:
                print(f"  -- {target_path} (source unchanged, skipping)")
            continue

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

        # Hash the text as it will read back from the file (the body is
        # stripped on parse), so the hash matches until someone edits it.
        written, written_body = parse_markdown(
            build_markdown(translated_fm, translated_body)
        )
        translated_fm["translation_hash"] = compute_source_hash(written, written_body)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            build_markdown(_quote_hashes(translated_fm), translated_body),
            encoding="utf-8",
        )
        print(f"  -> {target_path}")

    return kept


def collect_all_content_files() -> list[Path]:
    """Find all content markdown files across all languages."""
    return sorted(CONTENT_DIR.glob("*/*/*.md"))


def kept_report_lines(kept: list[tuple[Path, str]]) -> str:
    """Markdown bullets for the PR notice, one per kept translation."""
    lines = []
    for path, label in kept:
        lang = get_source_lang(path).upper()
        name = f"«{label}» " if label else ""
        lines.append(f"- {name}({lang}): `{path}`")
    return "\n".join(lines) + "\n" if lines else ""


def write_kept_report(kept: list[tuple[Path, str]]) -> None:
    """Write the kept list to $KEPT_REPORT, for the workflow's PR notice step."""
    report = os.environ.get("KEPT_REPORT")
    if report and kept:
        Path(report).write_text(kept_report_lines(kept), encoding="utf-8")


def write_failure_report(kind: str, message: str) -> None:
    """Write why the run failed to $TRANSLATE_REPORT (JSON), for the PR status comment.

    Only the two known, editor-fixable errors are reported: their messages name
    files and say what to do. Other exceptions may carry API details, so the
    status comment just says it was a technical problem.
    """
    report = os.environ.get("TRANSLATE_REPORT")
    if report:
        Path(report).write_text(
            json.dumps({"kind": kind, "message": message}, ensure_ascii=False),
            encoding="utf-8",
        )


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

    kept: list[tuple[Path, str]] = []
    for filepath in files:
        if not filepath.exists():
            print(f"Skipping (not found): {filepath}")
            continue
        print(f"Translating: {filepath} ({get_source_lang(filepath)})")
        try:
            kept += translate_file(api_key, filepath, guidelines)
        except NonGreekSourceError as e:
            print(f"::error title=Entry not in Greek::{e}")
            write_failure_report("non-greek", str(e))
            print(f"Error translating {filepath}: {e}")
            sys.exit(1)
        except HandWrittenTargetError as e:
            # ::error:: shows up as an annotation on the workflow run
            print(f"::error title=Hand-written translation::{e}")
            write_failure_report("hand-written", str(e))
            print(f"Error translating {filepath}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error translating {filepath}: {e}")
            sys.exit(1)

    write_kept_report(kept)
    print("Done.")


if __name__ == "__main__":
    main()
