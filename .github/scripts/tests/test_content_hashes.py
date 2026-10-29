"""Hash checks on the real files in src/content.

The hashes must not change when the way `compute_source_hash` treats optional
fields (like `description`) is touched: a changed hash would make the bot
re-translate every file, and flag every hand correction as "kept".

  (a) a Greek source hashes to the `source_hash` of its Dutch and English files;
  (b) a Dutch or English file hashes to its own `translation_hash`.
"""

from pathlib import Path

import pytest

from translate import compute_source_hash, parse_markdown

CONTENT = Path(__file__).resolve().parents[3] / "src" / "content"

# Files that are known not to match, as (path, field): reason. Do not add a file
# here just to make the test pass: a new mismatch means a hash changed by
# accident.
#
# The Dutch FAQ 03 file was corrected by hand on purpose (feature A9: kept hand
# fixes), but it is not an exception: when A9 added `translation_hash`, it was
# computed from the text as it was then, so the file matches. A later hand fix
# to any file would show up here as a mismatch, and then belongs in this list.
KNOWN_MISMATCHES: dict[tuple[str, str], str] = {}


def _rel(path: Path) -> str:
    return path.relative_to(CONTENT.parents[1]).as_posix()


def _translations() -> list[Path]:
    files = []
    for lang in ("nl", "en"):
        files += sorted(CONTENT.glob(f"*/{lang}/*.md"))
    return files


def _read(path: Path):
    return parse_markdown(path.read_text(encoding="utf-8"))


def test_content_directory_is_found():
    assert _translations(), f"no content found under {CONTENT}"


def _mismatches(check) -> list[str]:
    problems = []
    for path in _translations():
        fm, body = _read(path)
        problem = check(path, fm, body)
        if problem and (_rel(path), problem[0]) not in KNOWN_MISMATCHES:
            problems.append(f"{_rel(path)}: {problem[1]}")
    return problems


def test_source_hash_matches_the_greek_source():
    def check(path, fm, body):
        if "source_hash" not in fm:
            return None  # hand-written and locked: no hash to compare
        greek = CONTENT / path.parts[-3] / "gr" / path.name
        assert greek.exists(), f"{_rel(path)} has no Greek source"
        gfm, gbody = _read(greek)
        expected = compute_source_hash(gfm, gbody)
        if str(fm["source_hash"]) != expected:
            return ("source_hash", f"source_hash {fm['source_hash']} != {expected}")

    assert _mismatches(check) == []


def test_translation_hash_matches_the_translations_own_text():
    def check(path, fm, body):
        if "translation_hash" not in fm:
            return None
        expected = compute_source_hash(fm, body)
        if str(fm["translation_hash"]) != expected:
            return (
                "translation_hash",
                f"translation_hash {fm['translation_hash']} != {expected}",
            )

    assert _mismatches(check) == []


def test_known_mismatches_are_still_mismatches():
    """A listed exception that now matches should be removed from the list."""
    for (rel, field), reason in KNOWN_MISMATCHES.items():
        path = CONTENT.parents[1] / rel
        assert path.exists(), f"{rel} is listed but no longer exists"
        fm, body = _read(path)
        assert field in ("source_hash", "translation_hash")
        assert str(fm["translation_hash"]) != compute_source_hash(fm, body), (
            f"{rel} matches now ({reason}); remove it from KNOWN_MISMATCHES"
        )


def test_every_hash_is_checked_for_at_least_one_file():
    """Guard against a test that passes because it compared nothing."""
    with_source = [p for p in _translations() if "source_hash" in _read(p)[0]]
    with_own = [p for p in _translations() if "translation_hash" in _read(p)[0]]
    assert len(with_source) > 0
    assert len(with_own) > 0
    # Descriptions must be part of what is being protected.
    assert any(_read(p)[0].get("description") for p in with_source)
