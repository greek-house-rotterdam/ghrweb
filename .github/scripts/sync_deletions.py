#!/usr/bin/env python3
"""
Handle content files deleted in a pull request (plan item 0.4).

- **A Greek file deleted:** the post is gone, so its Dutch and English
  translations are deleted too.
- **A Dutch or English file deleted, its Greek file still there:** nothing else
  is deleted. The Greek file is listed for translate.py, which writes the
  missing translation again. Deleting a translation is a way to have the bot
  redo it; it never removes the post.

Before this, deleting any language deleted all three, Greek included.

Usage:
    sync_deletions.py [--retranslate-to FILE] DELETED_FILE...

The Greek files to translate again are written to FILE, one per line.
"""

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

from _common import LANGUAGES

SOURCE_LANG = "gr"


def get_counterparts(filepath: Path) -> list[Path]:
    """
    Given a file path like 'src/content/news/gr/post.md',
    return paths for 'src/content/news/nl/post.md' and 'src/content/news/en/post.md'.
    """
    parts = list(filepath.parts)
    for i, part in enumerate(parts):
        if part in LANGUAGES:
            counterparts = []
            for lang in LANGUAGES:
                if lang != part:
                    new_parts = parts.copy()
                    new_parts[i] = lang
                    counterparts.append(Path(*new_parts))
            return counterparts
    return []


def language_of(filepath: Path) -> str | None:
    return next((part for part in filepath.parts if part in LANGUAGES), None)


def plan(deleted: list[Path], exists: Callable[[Path], bool] = Path.exists) -> tuple[list[Path], list[Path]]:
    """Returns (files to delete, Greek files to translate again)."""
    to_delete: list[Path] = []
    to_translate: list[Path] = []
    for path in deleted:
        lang = language_of(path)
        if lang is None:
            continue
        if lang == SOURCE_LANG:
            to_delete += [p for p in get_counterparts(path) if exists(p) and p not in to_delete]
        else:
            greek = next(p for p in get_counterparts(path) if language_of(p) == SOURCE_LANG)
            # If the Greek was deleted in the same pull request, the post is
            # gone: the Greek deletion removes the rest.
            if exists(greek) and greek not in to_translate:
                to_translate.append(greek)
    return to_delete, to_translate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--retranslate-to", type=Path, help="write the Greek files to translate again here")
    parser.add_argument("deleted", nargs="*", type=Path)
    args = parser.parse_args(argv)

    deleted = [Path(str(p).strip("\"'")) for p in args.deleted]
    if not deleted:
        print("No deleted files.")
    to_delete, to_translate = plan(deleted)

    for path in deleted:
        print(f"Deleted in this pull request: {path}")
    for target in to_delete:
        print(f"  Removing the translation of a deleted Greek post: {target}")
        try:
            os.remove(target)
        except OSError as e:
            print(f"  Could not remove {target}: {e}")
    for greek in to_translate:
        print(f"  A translation was deleted; translating {greek} again")

    if args.retranslate_to:
        args.retranslate_to.write_text("".join(f"{p}\n" for p in to_translate), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
