#!/usr/bin/env python3
"""
Verify that all content exists in all three languages (gr, nl, en).
Scans src/content/ and ensures that for every file in one language,
a corresponding file exists in the other two with the same filename.
"""

import os
import re
import sys
from pathlib import Path

from _common import LANGUAGES, parse_markdown

CONTENT_DIR = Path("src/content")

def get_collections():
    """Return a list of collection directories (e.g. news, events)."""
    if not CONTENT_DIR.exists():
        return []
    return [d for d in CONTENT_DIR.iterdir() if d.is_dir()]

def verify_collection(collection_dir: Path) -> list[str]:
    """Check a single collection for missing translations."""
    errors = []
    
    # gather all filenames (slugs) across all languages
    all_slugs = set()
    for lang in LANGUAGES:
        lang_dir = collection_dir / lang
        if lang_dir.exists():
            for f in lang_dir.glob("*.md"):
                all_slugs.add(f.name)
    
    # check for missing files
    for slug in all_slugs:
        for lang in LANGUAGES:
            expected_file = collection_dir / lang / slug
            if not expected_file.exists():
                errors.append(f"Missing: {expected_file}")
                
    return errors

URL_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
URL_SLUG_MAX_LENGTH = 60


def check_url_slugs(collection_dir: Path) -> list[str]:
    """Check the optional `url_slug` (short page address) of every file.

    Same rule as the site build (src/content.config.ts): lowercase Latin
    letters, numbers and single hyphens, at most 60 characters. Empty is fine.
    """
    errors = []
    for lang in LANGUAGES:
        lang_dir = collection_dir / lang
        if not lang_dir.exists():
            continue
        for f in sorted(lang_dir.glob("*.md")):
            try:
                frontmatter, _ = parse_markdown(f.read_text(encoding="utf-8"))
            except Exception:
                continue  # unreadable frontmatter is the build's job to report
            value = frontmatter.get("url_slug")
            if value in (None, ""):
                continue
            if (
                not isinstance(value, str)
                or len(value) > URL_SLUG_MAX_LENGTH
                or not URL_SLUG_PATTERN.match(value)
            ):
                errors.append(
                    f"{f}: url_slug {value!r} is not valid. Use only lowercase "
                    f"Latin letters, numbers and single hyphens (at most "
                    f"{URL_SLUG_MAX_LENGTH} characters), e.g. pascha-2026."
                )
    return errors


def main():
    print(f"Verifying content integrity in {CONTENT_DIR}...")

    collections = get_collections()
    all_errors = []
    slug_errors = []

    for collection in collections:
        # Skip if it doesn't look like a content collection (no lang folders)
        if not any((collection / lang).exists() for lang in LANGUAGES):
            continue
            
        print(f"Checking collection: {collection.name}")
        errors = verify_collection(collection)
        all_errors.extend(errors)
        slug_errors.extend(check_url_slugs(collection))

    if slug_errors:
        print("\n❌ A short page address (url_slug) is not valid:")
        for error in slug_errors:
            print(f"  - {error}")
        if not all_errors:
            sys.exit(1)

    if all_errors:
        print("\n❌ Content integrity check failed! The following files are missing:")
        for error in sorted(all_errors):
            print(f"  - {error}")
        report = os.environ.get("VERIFY_REPORT")
        if report:
            # For the PR status comment: one bullet per missing file.
            Path(report).write_text(
                "".join(f"- `{e.removeprefix('Missing: ')}`\n" for e in sorted(all_errors)),
                encoding="utf-8",
            )
        print("\nThis usually means the translation workflow failed or hasn't run yet.")
        sys.exit(1)
    
    print("\n✅ All content is present in all languages.")

if __name__ == "__main__":
    main()
