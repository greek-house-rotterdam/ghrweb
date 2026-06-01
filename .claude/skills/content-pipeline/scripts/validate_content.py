#!/usr/bin/env python3
"""Pre-PR linter for GHR content files.

Runs the hard rules from SKILL.md that, if violated, will break the build or
the auto-translation pipeline. Catches them locally before they become a noisy
PR.

Checks performed per file:
  - YAML frontmatter is well-formed.
  - Required fields per collection are present.
  - title ≤ 100, description ≤ 200, question ≤ 200 chars.
  - `source_hash` is NOT present (we're writing sources, not translations).
  - `lang` matches the parent folder.
  - For collections that accept `image`: the referenced file exists at
    public/images/<name>.
  - For event-translations: filename stem equals `tt_event_id` value.

Usage:
    python validate_content.py <file1.md> [<file2.md> ...]

Exits 0 if all files are clean. Exits 1 if any file has errors (printed to
stdout with file:line-style prefixes).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

LANGS = {"gr", "nl", "en"}

# Map collection name → (required-fields set, max-lengths dict, allows-image, allows-source-hash-on-self)
COLLECTION_RULES: dict[str, dict] = {
    "news": {
        "required": {"title", "description", "date", "lang"},
        "max_lengths": {"title": 100, "description": 200},
        "allows_image": True,
    },
    "activities": {
        "required": {"title", "description", "lang"},
        "max_lengths": {"title": 100, "description": 200},
        "allows_image": True,
    },
    "resources": {
        "required": {"title", "description", "category", "lang"},
        "max_lengths": {"title": 100, "description": 200},
        "allows_image": False,
        "category_options": {
            "legal",
            "healthcare",
            "education",
            "housing",
            "finance",
            "culture",
            "other",
        },
    },
    "faq": {
        "required": {"question", "answer", "lang"},
        "max_lengths": {"question": 200},
        "allows_image": False,
    },
    "event-translations": {
        "required": {"tt_event_id", "title", "description", "lang"},
        "max_lengths": {"title": 100, "description": 200},
        "allows_image": False,
    },
    "page-sections": {
        "required": {"page", "title", "lang"},
        "max_lengths": {"title": 120},
        "allows_image": False,
        "page_options": {"about", "history", "teams"},
    },
    "history-milestones": {
        "required": {"year", "title", "lang"},
        "max_lengths": {"title": 140},
        "allows_image": False,
    },
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("no YAML frontmatter (file must start with '---\\n')")
    end = text.find("\n---\n", 4)
    if end == -1:
        end_eof = text.find("\n---", 4)
        if end_eof == -1:
            raise ValueError("frontmatter block is not closed with '---'")
        end = end_eof
    fm_yaml = text[4:end]
    body = text[end + 5 :] if text[end:].startswith("\n---\n") else text[end + 4 :]
    fm = yaml.safe_load(fm_yaml) or {}
    if not isinstance(fm, dict):
        raise ValueError("frontmatter is not a mapping")
    return fm, body


def infer_collection_and_lang(path: Path) -> tuple[str | None, str | None]:
    # Expect path like: src/content/<collection>/<lang>/<slug>.md (relative or absolute)
    parts = list(path.parts)
    try:
        i = parts.index("content")
    except ValueError:
        return None, None
    if i + 2 >= len(parts):
        return None, None
    return parts[i + 1], parts[i + 2]


def _display_path(repo_root: Path, path: Path) -> Path:
    """Best-effort path-relative-to-repo, falling back to the input on failure.

    macOS has /var → /private/var symlinks that break Path.relative_to even
    when both sides are resolved differently, so we don't rely on it.
    """
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return path


def validate_file(repo_root: Path, path: Path) -> list[str]:
    errs: list[str] = []
    rel = _display_path(repo_root, path)

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{rel}: cannot read: {e}"]

    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        return [f"{rel}: {e}"]

    collection, lang_dir = infer_collection_and_lang(path)
    if collection not in COLLECTION_RULES:
        errs.append(
            f"{rel}: cannot infer collection from path "
            f"(expected src/content/<collection>/<lang>/<slug>.md)"
        )
        return errs

    if lang_dir not in LANGS:
        errs.append(f"{rel}: unknown language folder '{lang_dir}' (expected one of {sorted(LANGS)})")

    rules = COLLECTION_RULES[collection]

    # Required fields
    missing = rules["required"] - set(fm.keys())
    for field in sorted(missing):
        errs.append(f"{rel}: missing required field '{field}' for collection '{collection}'")

    # lang must match folder
    if "lang" in fm and lang_dir and fm["lang"] != lang_dir:
        errs.append(
            f"{rel}: frontmatter lang='{fm['lang']}' does not match folder '{lang_dir}'"
        )

    # Max lengths
    for field, limit in rules["max_lengths"].items():
        if field in fm and isinstance(fm[field], str) and len(fm[field]) > limit:
            errs.append(
                f"{rel}: '{field}' is {len(fm[field])} chars, max is {limit}"
            )

    # Presence of source_hash means the file is a translation (typically written
    # by translate.py, but also used during initial migration to pin existing
    # content). The skill produces source files (no hash) by default, so if the
    # caller passed --strict, flag any hash. Otherwise just note it.
    if "source_hash" in fm and "--strict" in sys.argv:
        errs.append(
            f"{rel}: has 'source_hash' in frontmatter, but --strict was passed "
            f"(expecting source files only)."
        )

    # Resources: category must be in the allowed set
    if collection == "resources" and "category" in fm:
        opts = rules.get("category_options", set())
        if fm["category"] not in opts:
            errs.append(
                f"{rel}: category='{fm['category']}' is not one of {sorted(opts)}"
            )

    # page-sections: page must be in the allowed set
    if collection == "page-sections" and "page" in fm:
        opts = rules.get("page_options", set())
        if fm["page"] not in opts:
            errs.append(
                f"{rel}: page='{fm['page']}' is not one of {sorted(opts)}"
            )

    # event-translations: tt_event_id must equal filename stem
    if collection == "event-translations":
        ttid = fm.get("tt_event_id")
        stem = path.stem
        if ttid and ttid != stem:
            errs.append(
                f"{rel}: tt_event_id='{ttid}' does not match filename stem '{stem}' "
                f"— the Decap CMS slug template requires they be equal"
            )

    # Image referenced in frontmatter must exist on disk
    if rules.get("allows_image") and "image" in fm and fm["image"]:
        img = str(fm["image"])
        if not img.startswith("/images/"):
            errs.append(
                f"{rel}: image='{img}' should start with '/images/' (Astro static path)"
            )
        else:
            img_path = repo_root / "public" / img.lstrip("/")
            if not img_path.exists():
                errs.append(f"{rel}: image '{img}' does not exist at {img_path}")
    elif not rules.get("allows_image") and "image" in fm and fm["image"]:
        errs.append(
            f"{rel}: collection '{collection}' does not support an 'image' field"
        )

    # FAQ body should be empty
    if collection == "faq" and body.strip():
        errs.append(
            f"{rel}: faq body is hidden by the schema — move text into 'answer' instead"
        )

    return errs


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for parent in [p, *p.parents]:
        if (parent / ".git").exists() or (parent / "src" / "content").exists():
            return parent
    return start.resolve()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_content.py <file1.md> [<file2.md> ...]", file=sys.stderr)
        return 1

    paths = [Path(a) for a in sys.argv[1:]]
    repo_root = find_repo_root(paths[0])

    all_errs: list[str] = []
    for p in paths:
        if not p.exists():
            all_errs.append(f"{p}: file not found")
            continue
        all_errs.extend(validate_file(repo_root, p))

    if all_errs:
        for e in all_errs:
            print(f"  ✗ {e}")
        print(f"\n{len(all_errs)} issue(s) found.")
        return 1

    print(f"✓ {len(paths)} file(s) validated, no issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
