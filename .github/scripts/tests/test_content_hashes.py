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

These tests also run on content pull requests, after the bot's commit (the
content-tests job in translate.yml). Check how the content fits together,
never what it currently says: no entry has to exist, have a description, etc.
(a test that required a description broke when #90 removed the last one).
"""

import re
from pathlib import Path

from translate import compute_source_hash, is_hand_edited, parse_markdown

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


IMAGE = re.compile(r"!\[[^\]]*\]\((/images/[^)\s]+)\)")


def test_translations_keep_the_greek_photos():
    """A bot translation shows every photo of its Greek source (#200).

    History pages carry their photos in the body, so the bot must copy each
    image path as is. Only translations that are up to date and the bot's own
    are checked: before the bot's run the hash differs, and a hand fix is the
    editor's choice.
    """
    problems = []
    for path in _translations():
        fm, body = _read(path)
        if "source_hash" not in fm or fm.get("translation_locked") or is_hand_edited(fm, body):
            continue
        gfm, gbody = _read(CONTENT / path.parts[-3] / "gr" / path.name)
        if str(fm["source_hash"]) != compute_source_hash(gfm, gbody):
            continue  # not translated yet; the test above reports it
        missing = set(IMAGE.findall(gbody)) - set(IMAGE.findall(body))
        if missing:
            problems.append(f"{_rel(path)}: missing {sorted(missing)}")
    assert problems == []


def test_the_check_compares_something():
    """Guard against a test that passes because it compared nothing."""
    with_source = [p for p in _translations() if "source_hash" in _read(p)[0]]
    assert len(with_source) > 0
    # Descriptions must be part of what is being protected. Checked on the hash
    # itself, not on the real files: no entry has to have a description.
    title_only = compute_source_hash({"title": "Τίτλος"}, "Κείμενο")
    with_description = compute_source_hash({"title": "Τίτλος", "description": "Περιγραφή"}, "Κείμενο")
    assert title_only != with_description
