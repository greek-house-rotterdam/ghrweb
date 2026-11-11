"""Hash checks on the real files in src/content.

A Greek source must hash to the `source_hash` of its Dutch and English files.
The bot keeps this true on every run, so a mismatch on `main` means either the
hash formula changed by accident (every file would mismatch, and the bot would
re-translate everything) or a Greek edit was merged without the bot running.

`translation_hash` is deliberately not compared with the files' own text here:
a Dutch or English file whose text differs from it is a hand fix, which the
bot keeps (feature A9), and editors make those through the CMS. The hash
format itself is pinned in test_optional_description.py
(test_hash_with_a_description_is_unchanged).
"""

from pathlib import Path

from translate import compute_source_hash, parse_markdown

CONTENT = Path(__file__).resolve().parents[3] / "src" / "content"


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


def test_source_hash_matches_the_greek_source():
    problems = []
    for path in _translations():
        fm, _ = _read(path)
        if "source_hash" not in fm:
            continue  # hand-written and locked: no hash to compare
        greek = CONTENT / path.parts[-3] / "gr" / path.name
        assert greek.exists(), f"{_rel(path)} has no Greek source"
        gfm, gbody = _read(greek)
        expected = compute_source_hash(gfm, gbody)
        if str(fm["source_hash"]) != expected:
            problems.append(f"{_rel(path)}: source_hash {fm['source_hash']} != {expected}")
    assert problems == []


def test_the_check_compares_something():
    """Guard against a test that passes because it compared nothing."""
    with_source = [p for p in _translations() if "source_hash" in _read(p)[0]]
    assert len(with_source) > 0
    # Descriptions must be part of what is being protected.
    assert any(_read(p)[0].get("description") for p in with_source)
